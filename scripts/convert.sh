#!/bin/bash

# ================= 全局配置 =================

# 【核心】强制使用 C 语言区域设置
# 1. 确保 ASCII 排序顺序稳定 (Space < . < 0 < 1)
# 2. 只有这样，Buffer 算法才能正确识别父子域名关系
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

# 1. 并行下载 (极速)
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

# 2. 域名标准化
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

# 3. 自身去重 (子域名覆盖)
optimize_self() {
    echo "🧠 执行自身智能去重..."
    # 逻辑: 排序后，相邻比较。如果 index($0, prev ".")==1，说明当前行是上一行的子域名，保留当前行，上一行被覆盖(但awk流式处理很难覆盖上一行)。
    # 更优逻辑: 反转 -> 排序。这样 子域名(长) 会排在 父域名(短) 后面 (例如 moc.qq vs moc.qq.ad)。
    # 等等，Space(32) < .(46)。
    # moc.qq (end) vs moc.qq.ad
    # 排序后: moc.qq 先出现。
    # 我们希望保留父域名(短)，去除子域名(长)。
    # 所以: 如果当前行以 prev + "." 开头，说明当前行是子域名，丢弃。
    
    cat "$1" | rev | sort | awk '
        NR==1 {prev=$0; print; next} 
        {
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

# 5. 【核心通用算法】高级白名单过滤 (Buffer 算法)
# 适用于 模块1 和 模块4
# 输入 Blocklist (可能含 +.) 和 Whitelist (纯域名)
apply_advanced_whitelist_filter() {
    local block_in=$1
    local allow_in=$2
    local final_out=$3

    echo "🛡️  应用高级白名单过滤 (Buffer 算法)..."

    # --- 步骤 A: 准备白名单 ---
    # 格式: [反转纯域名] [1]
    # 例如: moc.tatsmm.ogw 1
    awk '{ 
        key=$0; 
        reversed = ""; len = length(key);
        for (i=len; i>=1; i--) reversed = reversed substr(key, i, 1);
        print reversed, 1 
    }' "$allow_in" > "${WORK_DIR}/algo_input.txt"

    # --- 步骤 B: 准备黑名单 ---
    # 格式: [反转纯域名] [0] [原始行]
    # 例如: moc.tatsmm 0 +.mmstat.com
    awk '{ 
        original=$0;
        pure=original;
        sub(/^\+\./, "", pure);
        sub(/^\./, "", pure);
        reversed = ""; len = length(pure);
        for (i=len; i>=1; i--) reversed = reversed substr(pure, i, 1);
        print reversed, 0, original 
    }' "$block_in" >> "${WORK_DIR}/algo_input.txt"

    # --- 步骤 C: 排序与 Buffer 逻辑 ---
    # 排序关键: Space(32) < .(46) < 0(48) < 1(49)
    # 1. 父域名 (moc.tatsmm) 会排在 子域名 (moc.tatsmm.ogw) 之前。
    # 2. 同域名下，黑名单 (0) 会排在 白名单 (1) 之前。
    
    sort "${WORK_DIR}/algo_input.txt" | awk '
    {
        key = $1
        type = $2
        original = $3
        
        # 判断缓冲区的黑名单是否覆盖了当前行
        # 情况1: Buffer(父) vs 当前(子)。例如 moc.tatsmm vs moc.tatsmm.ogw
        # 情况2: Buffer(相等) vs 当前(相等)。例如 moc.tatsmm vs moc.tatsmm
        
        is_related = (buffered_key != "" && (index(key, buffered_key ".") == 1 || key == buffered_key));

        if (is_related) {
            if (type == 1) {
                # 发现白名单子域名/同名域名！
                # 这意味着之前的 Buffer (黑名单父域名) 会误杀白名单，必须删除 Buffer。
                buffered_key = ""
                buffered_line = ""
            }
            # 如果是黑名单子域名 (type 0)，则是冗余，忽略
        } else {
            # 无关的新分支，说明之前的 Buffer 安全存活
            if (buffered_line != "") {
                print buffered_line
            }

            # 更新 Buffer
            if (type == 0) {
                buffered_key = key
                buffered_line = original
            } else {
                # 白名单不进 Buffer，只负责杀
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

    # 【修复点】使用 Buffer 算法处理模块 1，彻底解决父子域名冲突
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

    # 【修复点】使用 Buffer 算法
    apply_advanced_whitelist_filter "${WORK_DIR}/clean_rd.txt" "${WORK_DIR}/clean_rd_allow.txt" "${WORK_DIR}/final_rd.txt"

    finalize_output "${WORK_DIR}/final_rd.txt" "Reject_Drop_merged.mrs" "none"
    mv "${WORK_DIR}/final_rd.txt" "Reject_Drop_merged.txt"
}

# ================= 主程序入口 =================

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
