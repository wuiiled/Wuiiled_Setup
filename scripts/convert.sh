#!/bin/bash

# ================= 全局性能优化 =================

# 强制使用 ASCII 排序，极大提升 sort 速度并确保逻辑正确
export LC_ALL=C

WORK_DIR=$(mktemp -d)
trap "rm -rf ${WORK_DIR}" EXIT

# 检查工具
CHECK_MIHOMO() {
    if ! command -v mihomo &> /dev/null; then
        echo "⚠️  未检测到 mihomo 命令，跳过 .mrs 转换。"
        return 1
    fi
    return 0
}

# ================= 核心工具函数 =================

# 1. 并行下载 (极速下载)
download_files_parallel() {
    local output_file=$1
    shift
    local urls=("$@")
    local temp_map_dir="${WORK_DIR}/dl_map_$$"
    mkdir -p "$temp_map_dir"

    echo "⬇️  启动并行下载 [${#urls[@]} 个源]..."
    local pids=()
    local i=0
    for url in "${urls[@]}"; do
        local temp_out="${temp_map_dir}/${i}.txt"
        (
            if curl -sLf --connect-timeout 15 --retry 3 "$url" > "$temp_out"; then
                # 确保文件末尾有换行
                [ -n "$(tail -c1 "$temp_out")" ] && echo "" >> "$temp_out"
                echo "   ✅ 完成: $(basename "$url")"
            else
                echo "   ❌ 失败: $url"
                rm -f "$temp_out"
            fi
        ) &
        pids+=($!)
        ((i++))
    done
    wait "${pids[@]}"
    cat "${temp_map_dir}"/*.txt > "$output_file" 2>/dev/null
}

# 2. 域名标准化 (去注释/修饰符/IP)
normalize_domain() {
    tr 'A-Z' 'a-z' | tr -d '\r' \
    | sed 's/[\$#].*//g' \
    | sed -E 's/^(0\.0\.0\.0|127\.0\.0\.1)[[:space:]]+//g' \
    | sed 's/^!.*//g' \
    | sed 's/^@@//g' \
    | sed 's/||//g; s/\^//g; s/|//g' \
    | sed 's/domain-keyword,//g' \
    | sed -E 's/^[[:space:]]*//' \
    | sed 's/^domain-suffix,//g' \
    | sed 's/^domain,//g' \
    | awk -F, '{print $1}' \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | grep -v "*" \
    | grep -v "[^a-z0-9.-]" \
    | grep -vE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' \
    | grep -E '^[a-z0-9]' \
    | grep -E '[a-z0-9]$' \
    | awk '/\./ {print $0}'
}

# 3. 自身去重优化 (去除子域名冗余)
# 逻辑：反转 -> 排序 -> 比较相邻行 -> 再次反转
optimize_self() {
    echo "🧠 执行自身智能去重..."
    cat "$1" | rev | sort | awk '
        NR==1 {prev=$0; print; next} 
        {
            # 如果当前行以 prev + "." 开头，说明是子域名，跳过
            if (index($0, prev ".") != 1) {
                print
                prev=$0
            }
        }' | rev | sort > "$2"
}

# 4. 关键词过滤
apply_keyword_filter() {
    local keyword_file="scripts/exclude-keyword.txt"
    if [ -f "$keyword_file" ]; then
        echo "🔍 应用本地关键词排除..."
        grep -v -f "$keyword_file" "$1" > "$2"
    else
        cp "$1" "$2"
    fi
}

# 5. 【核心优化】高级白名单过滤 (Buffer 算法 - 批量处理版)
# 解决了 "wgo.mmstat.com" (白) 去除 "+.mmstat.com" (黑) 的问题
# 速度提升关键：所有 rev 操作都在 awk 外部批量完成
apply_advanced_whitelist_filter() {
    local block_in=$1
    local allow_in=$2
    local final_out=$3

    echo "🛡️  应用高级白名单过滤 (批量流式处理)..."

    # --- 步骤 A: 预处理白名单 ---
    # 格式: [反转域名] [标记1]
    # 例如: moc.elgoog 1
    cat "$allow_in" | rev | awk '{print $0, 1}' > "${WORK_DIR}/input_stream.txt"

    # --- 步骤 B: 预处理黑名单 ---
    # 黑名单可能带 +., 我们需要提取纯域名进行反转排序，同时保留原始行
    # 格式: [反转纯域名] [标记0] [原始行]
    # 例如: moc.elgoog 0 +.google.com
    awk '{
        original = $0;
        # 去除开头修饰符
        sub(/^\+\./, "", $0);
        sub(/^\./, "", $0);
        print $0, 0, original;
    }' "$block_in" \
    | rev \
    | awk '{
        # rev 会把 "moc.elgoog 0 moc.elgoog.+" 翻转成 "+.google.com 0 google.com"
        # 我们需要修正列的顺序。
        # 上一步 pipe 给 rev 后，整行被翻转了。
        # 输入: moc.elgoog 0 +.google.com
        # rev后: moc.elgoog.+ 0 google.com
        # 这很麻烦，所以我们在 awk 内部只打印纯域名给 rev，剩下的拼接
        
        # 修正策略：不使用全行 rev，而是分别处理
    }' 
    
    # --- 修正步骤 B (更高效的方法) ---
    # 我们使用 paste 拼接 "反转纯域名" 和 "原始信息"
    
    # 1. 提取纯域名并反转
    awk '{sub(/^\+\./,""); sub(/^\./,""); print}' "$block_in" | rev > "${WORK_DIR}/block_rev_keys.txt"
    # 2. 拼接: [反转Key] 0 [原始行]
    paste -d ' ' "${WORK_DIR}/block_rev_keys.txt" <(yes 0 | head -n $(wc -l < "$block_in")) "$block_in" >> "${WORK_DIR}/input_stream.txt"

    # --- 步骤 C: 排序与 Buffer 逻辑 ---
    # 排序优先级: 字符顺序。 0 (ASCII 48) < 1 (ASCII 49)。
    # 同域名下，黑名单(0) 会排在 白名单(1) 前面。
    # 父域名 (短) 会排在 子域名 (长) 前面。

    sort "${WORK_DIR}/input_stream.txt" | awk '
    {
        key = $1
        type = $2
        # $3 是原始行 (仅黑名单有)
        original = $3
        
        # 判断：当前 Key 是否是 Buffered Key 的子域名 (或者完全相等)
        is_child_or_equal = (buffered_key != "" && (index(key, buffered_key ".") == 1 || key == buffered_key));

        if (is_child_or_equal) {
            if (type == 1) {
                # 场景：Buffer是 "moc.tatsmm" (黑)，当前是 "moc.tatsmm.ogw" (白)
                # 结论：白名单子域名存在 -> 杀死父级黑名单
                buffered_key = ""
                buffered_line = ""
            }
            # 场景：Buffer是黑，当前也是黑子域名 -> 自身冗余，忽略
        } else {
            # 新的分支，输出之前安全的黑名单
            if (buffered_line != "") {
                print buffered_line
            }

            # 更新 Buffer
            if (type == 0) {
                buffered_key = key
                buffered_line = original
            } else {
                buffered_key = ""
                buffered_line = ""
            }
        }
    }
    END {
        if (buffered_line != "") print buffered_line
    }' > "$final_out"
}

# 6. 输出封装
finalize_output() {
    local src=$1
    local dst=$2
    local mode=$3

    if [ "$mode" == "add_prefix" ]; then
        echo "✨ 添加统一前缀 (+.)..."
        sed 's/^/+./' "$src" > "${src}.tmp" && mv "${src}.tmp" "$src"
    fi

    local count=$(wc -l < "$src")
    local date=$(date +"%Y-%m-%d %H:%M:%S")
    # 添加头部
    sed -i "1i # Count: $count\n# Updated: $date" "$src"
    
    if [ -n "$dst" ] && CHECK_MIHOMO; then
        echo "🔄 转换为 MRS..."
        mihomo convert-ruleset domain text "$src" "$dst"
    fi
    echo "📊 完成: $dst (行数: $count)"
}

# ================= 资源配置 =================

ALLOW_URLS=(
    "https://raw.githubusercontent.com/Cats-Team/AdRules/refs/heads/script/script/allowlist.txt"
    "https://raw.githubusercontent.com/mawenjian/china-cdn-domain-whitelist/refs/heads/master/china-cdn-domain-whitelist.txt"
    "https://raw.githubusercontent.com/zoonderkins/blahdns/refs/heads/master/hosts/whitelist.txt"
    "https://raw.githubusercontent.com/AdguardTeam/AdGuardSDNSFilter/master/Filters/exceptions.txt"
)

# ================= 模块定义 =================

generate_ads() {
    echo "=== 🚀 模块 1: ADs 规则 ==="
    local BLOCK_URLS=(
        "https://raw.githubusercontent.com/pmkol/easymosdns/rules/ad_domain_list.txt"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/rules/Custom_Reject.txt"
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt"
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_3.txt"
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_4.txt"
        "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-Surge-RULE-SET.list"
        "https://raw.githubusercontent.com/ForestL18/rules-dat/mihomo/geo/classical/pcdn.list"
        "https://raw.githubusercontent.com/ForestL18/rules-dat/refs/heads/mihomo/geo/classical/reject.list"
        "https://a.dove.isdumb.one/pihole.txt"
        "https://raw.githubusercontent.com/limbopro/Adblock4limbo/main/rule/Surge/Adblock4limbo_surge.list"
    )

    download_files_parallel "${WORK_DIR}/raw_ads.txt" "${BLOCK_URLS[@]}"
    download_files_parallel "${WORK_DIR}/raw_allow.txt" "${ALLOW_URLS[@]}"

    # 清洗：拦截列表去 @@，白名单去修饰符
    grep -vE '^\s*@@' "${WORK_DIR}/raw_ads.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_ads.txt"
    apply_keyword_filter "${WORK_DIR}/clean_ads.txt" "${WORK_DIR}/filter_ads.txt"
    cat "${WORK_DIR}/raw_allow.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_allow.txt"

    # 自身去重
    optimize_self "${WORK_DIR}/filter_ads.txt" "${WORK_DIR}/opt_ads.txt"
    optimize_self "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/opt_allow.txt"

    # 高级白名单过滤 (复用优化后的函数)
    apply_advanced_whitelist_filter "${WORK_DIR}/opt_ads.txt" "${WORK_DIR}/opt_allow.txt" "${WORK_DIR}/final_ads.txt"

    finalize_output "${WORK_DIR}/final_ads.txt" "ADs_merged.mrs" "add_prefix"
    mv "${WORK_DIR}/final_ads.txt" "ADs_merged.txt"
}

generate_ai() {
    echo "=== 🚀 模块 2: AI 规则 ==="
    local AI_URLS=(
        "https://github.com/MetaCubeX/meta-rules-dat/raw/meta/geo/geosite/category-ai-!cn.list"
        "https://ruleset.skk.moe/List/non_ip/ai.conf"
        "https://github.com/DustinWin/ruleset_geodata/raw/mihomo-ruleset/ai.list"
        "https://raw.githubusercontent.com/ConnersHua/RuleGo/refs/heads/master/Surge/Ruleset/Extra/AI.list"
    )
    download_files_parallel "${WORK_DIR}/raw_ai.txt" "${AI_URLS[@]}"
    cat "${WORK_DIR}/raw_ai.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_ai.txt"
    optimize_self "${WORK_DIR}/clean_ai.txt" "${WORK_DIR}/opt_ai.txt"
    finalize_output "${WORK_DIR}/opt_ai.txt" "AIs_merged.mrs" "add_prefix"
    mv "${WORK_DIR}/opt_ai.txt" "AIs_merged.txt"
}

generate_fakeip() {
    echo "=== 🚀 模块 3: Fake IP ==="
    local FAKE_IP_URLS=(
        "https://raw.githubusercontent.com/vernesong/OpenClash/refs/heads/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list"
        "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list"
        "https://raw.githubusercontent.com/DustinWin/ruleset_geodata/refs/heads/mihomo-ruleset/fakeip-filter.list"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/fake-ip-addon.txt"
    )
    download_files_parallel "${WORK_DIR}/raw_fakeip.txt" "${FAKE_IP_URLS[@]}"
    
    echo "🧹 清洗与冲突解决..."
    # 逻辑：去除注释 -> AWK 关联数组去重 (优先保留+.) -> 排序
    cat "${WORK_DIR}/raw_fakeip.txt" \
    | tr -d '\r' | grep -vE '^\s*($|#|!)' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | awk '{
        origin = $0; root = origin;
        sub(/^\+\./, "", root); sub(/^\./, "", root);
        if (!(root in seen)) { seen[root] = origin; } 
        else { if (seen[root] !~ /^\+\./ && origin ~ /^\+\./) seen[root] = origin; }
    } END { for (r in seen) print seen[r]; }' | sort > "${WORK_DIR}/final_fakeip.txt"

    finalize_output "${WORK_DIR}/final_fakeip.txt" "Fake_IP_Filter_merged.mrs" "none"
    mv "${WORK_DIR}/final_fakeip.txt" "Fake_IP_Filter_merged.txt"
}

generate_reject() {
    echo "=== 🚀 模块 4: Reject Drop ==="
    local BLOCK_URLS=(
        "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/rules/Custom_Reject-drop.txt"
    )
    download_files_parallel "${WORK_DIR}/raw_rd.txt" "${BLOCK_URLS[@]}"

    echo "🧹 SED 清洗..."
    cat "${WORK_DIR}/raw_rd.txt" \
    | tr -d '\r' | sed '/^#/d; /skk\.moe/d; /^$/d; s/^DOMAIN-SUFFIX,/+./; s/^DOMAIN,//; /^\+\.$/d; /^[[:space:]]*$/d' \
    | sort -u > "${WORK_DIR}/clean_rd.txt"

    # 复用或下载白名单
    if [ -f "${WORK_DIR}/clean_allow.txt" ]; then
        echo "♻️  复用模块 1 白名单..."
        cp "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/clean_rd_allow.txt"
    else
        echo "ℹ️  下载白名单..."
        download_files_parallel "${WORK_DIR}/raw_allow_temp.txt" "${ALLOW_URLS[@]}"
        cat "${WORK_DIR}/raw_allow_temp.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_rd_allow.txt"
        optimize_self "${WORK_DIR}/clean_rd_allow.txt" "${WORK_DIR}/opt_allow.txt"
        cp "${WORK_DIR}/opt_allow.txt" "${WORK_DIR}/clean_rd_allow.txt"
    fi

    # 高级过滤 (Buffer算法)
    apply_advanced_whitelist_filter "${WORK_DIR}/clean_rd.txt" "${WORK_DIR}/clean_rd_allow.txt" "${WORK_DIR}/final_rd.txt"

    finalize_output "${WORK_DIR}/final_rd.txt" "Reject_Drop_merged.mrs" "none"
    mv "${WORK_DIR}/final_rd.txt" "Reject_Drop_merged.txt"
}

# ================= 主程序 =================

main() {
    local target=${1:-all}
    case "$target" in
        ads) generate_ads ;;
        ais) generate_ai ;;
        fakeip) generate_fakeip ;;
        reject) generate_reject ;;
        all)
            generate_ads
            generate_ai
            generate_fakeip
            generate_reject
            ;;
        *)
            echo "用法: $0 [ads|ais|fakeip|reject|all]"
            exit 1
            ;;
    esac
}

main "$@"
