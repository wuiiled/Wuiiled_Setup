#!/bin/bash

# ================= 全局配置 =================

# 【性能与逻辑核心】强制使用 C 语言区域设置
# 1. 提升 sort 速度 (数倍于 UTF-8)。
# 2. 确保 ASCII 排序顺序：! (33) < . (46) < ~ (126)。
#    这是 "Buffer" 去重算法生效的基础。
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

# ================= 通用函数库 =================

# 🚀 并行下载函数
# 启动所有 curl 进程在后台运行，最后等待全部结束
download_files_parallel() {
    local output_file=$1
    shift
    local urls=("$@")
    local pids=()
    local temp_map_dir="${WORK_DIR}/dl_map_$$"
    mkdir -p "$temp_map_dir"

    echo "⬇️  启动并行下载 [${#urls[@]} 个文件]..."

    local i=0
    for url in "${urls[@]}"; do
        local filename=$(basename "$url")
        local temp_out="${temp_map_dir}/${i}.txt"
        
        # 后台运行 curl
        (
            if curl -sLf --connect-timeout 15 --retry 3 "$url" > "$temp_out"; then
                echo "   ✅ 完成: $filename ($(wc -l < "$temp_out") 行)"
                # 确保末尾有换行
                echo "" >> "$temp_out"
            else
                echo "   ❌ 失败: $url"
                rm -f "$temp_out"
            fi
        ) &
        pids+=($!)
        ((i++))
    done

    # 等待所有子进程结束
    wait "${pids[@]}"

    # 合并文件
    cat "${temp_map_dir}"/*.txt > "$output_file" 2>/dev/null
    echo "⬇️  所有下载任务结束。"
}

# 标准清洗函数 (用于 ADs/AI/白名单)
# 功能：去空、去注释、去 AdGuard 修饰符、去 IP、提取纯域名
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

# 自身去重 (子域名覆盖)
optimize_self() {
    echo "🧠 执行自身智能去重..."
    # 逻辑：反转排序，如果前一个是后一个的前缀，说明前一个是子域名
    cat "$1" | rev | sort | awk 'NR==1 {prev=$0; print; next} {if (index($0, prev ".") != 1) {print; prev=$0}}' | rev | sort > "$2"
}

# 关键词过滤
apply_keyword_filter() {
    local keyword_file="scripts/exclude-keyword.txt"
    if [ -f "$keyword_file" ]; then
        echo "🔍 应用本地关键词排除..."
        grep -v -f "$keyword_file" "$1" > "$2"
    else
        cp "$1" "$2"
    fi
}

# 🛡️ 高级白名单过滤算法 (核心逻辑复用)
# 输入参数：$1=黑名单文件(可能含+.), $2=白名单文件(纯域名), $3=输出文件
# 逻辑：双向去重。如果 White 是 Block 的子域名，或者 Block 是 White 的子域名，都删除 Block。
apply_advanced_whitelist_filter() {
    local block_in=$1
    local allow_in=$2
    local final_out=$3

    echo "🛡️  应用高级白名单过滤 (Buffer 算法)..."

    # 1. 准备输入流
    # 白名单: 反转纯域名 + 标记 "1"
    # 黑名单: 反转纯域名 + 标记 "0" + 原始行(用于保留+.)
    
    # 使用临时文件避免管道过长导致的潜在缓冲区问题
    cat "$allow_in" | rev | awk '{print $0, 1}' > "${WORK_DIR}/algo_input.txt"
    
    awk '{
        pure = $0;
        sub(/^\+\./, "", pure);
        sub(/^\./, "", pure);
        cmd = "echo " pure " | rev";
        cmd | getline rev_pure;
        close(cmd);
        print rev_pure, 0, $0;
    }' "$block_in" >> "${WORK_DIR}/algo_input.txt"

    # 2. 排序与处理
    # 排序后：
    # moc.tatsmm 0 (黑名单父)
    # moc.tatsmm.ogw 1 (白名单子)
    
    sort "${WORK_DIR}/algo_input.txt" | awk '
    {
        key = $1
        type = $2
        original = $3
        
        # 判断：当前 Key 是否是 Buffered Key 的子域名 (或者完全相等)
        # 例如: key="moc.tatsmm.ogw", buffered="moc.tatsmm"
        is_child_or_equal = (buffered_key != "" && (index(key, buffered_key ".") == 1 || key == buffered_key));

        if (is_child_or_equal) {
            if (type == 1) {
                # 命中白名单！白名单是黑名单的子域名 -> 删除父级黑名单 (清空 Buffer)
                buffered_key = ""
                buffered_line = ""
            }
            # 如果是黑名单子域名 (type 0)，则它是冗余规则 -> 忽略，保留父级 Buffer
        } else {
            # 无父子关系，进入新分支
            # 输出之前安全的黑名单
            if (buffered_line != "") {
                print buffered_line
            }

            # 更新 Buffer
            if (type == 0) {
                buffered_key = key
                buffered_line = original
            } else {
                # 白名单不需要缓存，它只负责"杀"前面的 Buffer
                buffered_key = ""
                buffered_line = ""
            }
        }
    }
    END {
        if (buffered_line != "") print buffered_line
    }' > "$final_out"
}

# 格式转换与统计
finalize_output() {
    local src=$1
    local dst=$2 # Optional MRS name
    local prefix_mode=$3 # "add_prefix" or "none"

    if [ "$prefix_mode" == "add_prefix" ]; then
        echo "✨ 添加统一前缀 (+.)..."
        sed 's/^/+./' "$src" > "${src}.tmp" && mv "${src}.tmp" "$src"
    fi

    # 统计信息
    local count=$(wc -l < "$src")
    local date=$(date +"%Y-%m-%d %H:%M:%S")
    local header=$(mktemp)
    echo "# Count: $count" > "$header"
    echo "# Updated: $date" >> "$header"
    cat "$src" >> "$header"
    mv "$header" "$src"
    
    # 转换
    if [ -n "$dst" ] && CHECK_MIHOMO; then
        echo "🔄 转换为 MRS..."
        mihomo convert-ruleset domain text "$src" "$dst"
    fi
    
    echo "📊 完成: $src (行数: $count)"
}

# ================= 资源配置 =================

# 共享白名单
ALLOW_URLS=(
    "https://raw.githubusercontent.com/Cats-Team/AdRules/refs/heads/script/script/allowlist.txt"
    "https://raw.githubusercontent.com/mawenjian/china-cdn-domain-whitelist/refs/heads/master/china-cdn-domain-whitelist.txt"
    "https://raw.githubusercontent.com/zoonderkins/blahdns/refs/heads/master/hosts/whitelist.txt"
    "https://raw.githubusercontent.com/AdguardTeam/AdGuardSDNSFilter/master/Filters/exceptions.txt"
)

# ================= 模块 1: ADs =================

generate_ads() {
    echo "=== 🚀 模块 1: ADs 规则 ==="
    local OUT="ADs_merged.txt"
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

    # 1. 并行下载
    download_files_parallel "${WORK_DIR}/raw_ads.txt" "${BLOCK_URLS[@]}"
    download_files_parallel "${WORK_DIR}/raw_allow.txt" "${ALLOW_URLS[@]}"

    # 2. 清洗
    # 拦截列表：去除 @@ 行
    grep -vE '^\s*@@' "${WORK_DIR}/raw_ads.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_ads.txt"
    apply_keyword_filter "${WORK_DIR}/clean_ads.txt" "${WORK_DIR}/filter_ads.txt"
    
    # 白名单：标准清洗 (包含去除 @@)
    cat "${WORK_DIR}/raw_allow.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_allow.txt"

    # 3. 自身去重 (子域名优化)
    optimize_self "${WORK_DIR}/filter_ads.txt" "${WORK_DIR}/opt_ads.txt"
    optimize_self "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/opt_allow.txt"

    # 4. 高级白名单过滤 (Buffer算法)
    apply_advanced_whitelist_filter "${WORK_DIR}/opt_ads.txt" "${WORK_DIR}/opt_allow.txt" "${WORK_DIR}/final_ads.txt"

    # 5. 输出
    finalize_output "${WORK_DIR}/final_ads.txt" "ADs_merged.mrs" "add_prefix"
    mv "${WORK_DIR}/final_ads.txt" "$OUT"
}

# ================= 模块 2: AI =================

generate_ai() {
    echo "=== 🚀 模块 2: AI 规则 ==="
    local OUT="AIs_merged.txt"
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
    mv "${WORK_DIR}/opt_ai.txt" "$OUT"
}

# ================= 模块 3: Fake IP =================

generate_fakeip() {
    echo "=== 🚀 模块 3: Fake IP 规则 ==="
    local OUT="Fake_IP_Filter_merged.txt"
    local FAKE_IP_URLS=(
        "https://raw.githubusercontent.com/vernesong/OpenClash/refs/heads/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list"
        "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list"
        "https://raw.githubusercontent.com/DustinWin/ruleset_geodata/refs/heads/mihomo-ruleset/fakeip-filter.list"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/fake-ip-addon.txt"
    )

    download_files_parallel "${WORK_DIR}/raw_fakeip.txt" "${FAKE_IP_URLS[@]}"

    echo "🧹 清洗与冲突解决 (优先保留 +.)..."
    cat "${WORK_DIR}/raw_fakeip.txt" \
    | tr -d '\r' \
    | grep -vE '^\s*($|#|!)' \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | awk '{
        origin = $0;
        root = origin;
        sub(/^\+\./, "", root);
        sub(/^\./, "", root);
        # 关联数组逻辑：如果根域名已存在，仅当新记录以 +. 开头时覆盖
        if (!(root in seen)) { seen[root] = origin; } 
        else { if (seen[root] !~ /^\+\./ && origin ~ /^\+\./) seen[root] = origin; }
    } END { for (r in seen) print seen[r]; }' \
    | sort > "${WORK_DIR}/final_fakeip.txt"

    finalize_output "${WORK_DIR}/final_fakeip.txt" "Fake_IP_Filter_merged.mrs" "none"
    mv "${WORK_DIR}/final_fakeip.txt" "$OUT"
}

# ================= 模块 4: Reject Drop =================

generate_reject() {
    echo "=== 🚀 模块 4: Reject Drop 规则 ==="
    local OUT="Reject_Drop_merged.txt"
    local BLOCK_URLS=(
        "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/rules/Custom_Reject-drop.txt"
    )

    download_files_parallel "${WORK_DIR}/raw_rd.txt" "${BLOCK_URLS[@]}"

    echo "🧹 执行特定 SED 清洗..."
    cat "${WORK_DIR}/raw_rd.txt" \
    | tr -d '\r' \
    | sed '/^#/d; /skk\.moe/d; /^$/d; s/^DOMAIN-SUFFIX,/+./; s/^DOMAIN,//; /^\+\.$/d; /^[[:space:]]*$/d' \
    | sort -u > "${WORK_DIR}/clean_rd.txt"

    # 准备白名单 (复用或下载)
    if [ -f "${WORK_DIR}/clean_allow.txt" ]; then
        echo "♻️  复用模块 1 白名单..."
        cp "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/clean_rd_allow.txt"
    else
        echo "ℹ️  下载并处理白名单..."
        download_files_parallel "${WORK_DIR}/raw_allow_temp.txt" "${ALLOW_URLS[@]}"
        cat "${WORK_DIR}/raw_allow_temp.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_rd_allow.txt"
    fi

    # 复用核心算法 (Buffer)
    apply_advanced_whitelist_filter "${WORK_DIR}/clean_rd.txt" "${WORK_DIR}/clean_rd_allow.txt" "${WORK_DIR}/final_rd.txt"

    finalize_output "${WORK_DIR}/final_rd.txt" "Reject_Drop_merged.mrs" "none"
    mv "${WORK_DIR}/final_rd.txt" "$OUT"
}

# ================= 主程序入口 =================

main() {
    local target=$1
    if [ -z "$target" ]; then target="all"; fi

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
