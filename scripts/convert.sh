#!/bin/bash

# ================= 全局配置 =================

# 【核心】强制使用 C 语言区域设置
# 确保 ASCII 排序顺序：Space(32) < . (46) < 0 (48) < 1 (49)
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

# 1. 并行下载
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
    rm -rf "$temp_map_dir"
}

# 2. 域名标准化 (修复 Bug 核心)
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
    | sed 's/^\+\.//g' \
    | sed 's/^\.//g' \
    | sed 's/\.$//' \
    | grep -v "*" \
    | grep -v "[^a-z0-9._-]" \
    | grep -vE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' \
    | grep -E '^[a-z0-9_]' \
    | grep -E '[a-z0-9_]$' \
    | awk '/\./ {print $0}'
}
# 修复说明：
# 1. 增加了 sed 's/^\+\.//g' 和 sed 's/^\.//g'：先去除行首的 +. 或 .
# 2. grep 增加了 _ (下划线)，防止误杀部分 CDN 域名。
# 3. 这样 +.accwww9.53kf.com 会被清洗为 accwww9.53kf.com，从而通过 grep 检查。

# 3. 自身去重 (仅排序)
optimize_self() {
    echo "🧠 执行自身简单去重..."
    sort -u "$1" > "$2"
}

# 4. 关键词过滤
apply_keyword_filter() {
    local keyword_file="scripts/exclude-keyword.txt"
    if [ -f "$keyword_file" ] && [ -s "$keyword_file" ]; then
        echo "🔍 应用关键词排除..."
        local before=$(wc -l < "$1")
        grep -v -f "$keyword_file" "$1" > "$2"
        local after=$(wc -l < "$2")
        echo "   -> 过滤掉了 $((before - after)) 行规则"
    else
        cp "$1" "$2"
    fi
}

# 5. 【核心算法】智能白名单过滤
# 逻辑保持不变：
# - 白名单子域名 (wgo.mmstat.com) -> 删除 黑名单父域名 (+.mmstat.com) [防误杀]
# - 白名单父域名 (xhscdn.com) -> 保留 黑名单子域名 (ads.xhscdn.com) [精准拦截]
apply_advanced_whitelist_filter() {
    local block_in=$1
    local allow_in=$2
    local final_out=$3

    echo "🛡️  应用智能白名单过滤..."

    # 步骤 A: 准备白名单 [反转] [1]
    awk '{ 
        key=$0; reversed=""; len=length(key);
        for(i=len;i>=1;i--) reversed=reversed substr(key,i,1);
        print reversed, 1 
    }' "$allow_in" > "${WORK_DIR}/algo_input.txt"

    # 步骤 B: 准备黑名单 [反转] [0] [原始]
    # 注意：这里会处理原始行 (original)，确保模块4的 +. 能保留
    awk '{ 
        original=$0; pure=original;
        sub(/^\+\./,"",pure); sub(/^\./,"",pure);
        reversed=""; len=length(pure);
        for(i=len;i>=1;i--) reversed=reversed substr(pure,i,1);
        print reversed, 0, original 
    }' "$block_in" >> "${WORK_DIR}/algo_input.txt"

    # 步骤 C: 排序与过滤
    sort "${WORK_DIR}/algo_input.txt" | awk '
    BEGIN { FS=" " }
    {
        key = $1
        type = $2
        original = $3

        # Buffer 检测: 检查当前 Key 是否是 Buffer (黑名单父域名) 的子域名
        is_child_or_equal = (buffered_key != "" && (index(key, buffered_key ".") == 1 || key == buffered_key));

        if (is_child_or_equal) {
            if (type == 1) {
                # 白名单子域名出现 -> 杀死 Buffer (黑名单父域名)
                buffered_key = ""
                buffered_line = ""
            } else {
                # 黑名单子域名 -> 保留 (不进行父子合并，确保精准黑名单不丢失)
                if (buffered_line != "") print buffered_line
                buffered_key = key
                buffered_line = original
            }
        } else {
            # 新分支
            if (buffered_line != "") print buffered_line

            if (type == 1) {
                # 白名单不进 Buffer
                buffered_key = ""
                buffered_line = ""
            } else {
                # 黑名单进 Buffer
                buffered_key = key
                buffered_line = original
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

    # 最终去重排序
    sort -u "$src" -o "$src"

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
        "https://raw.githubusercontent.com/Cats-Team/AdRules/main/adrules_domainset.txt"
        "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/refs/heads/release/reject-list.txt"
        "https://ruleset.skk.moe/Clash/domainset/reject.txt"
    )

    download_files_parallel "${WORK_DIR}/raw_ads.txt" "${BLOCK_URLS[@]}"
    download_files_parallel "${WORK_DIR}/raw_allow.txt" "${ALLOW_URLS[@]}"

    # 清洗：去除 @@ 行，标准化域名
    # 修复点：normalize_domain 现在会剥离 +. 前缀，使 53kf.com 能通过检查
    grep -vE '^\s*@@' "${WORK_DIR}/raw_ads.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_ads.txt"
    
    # 关键词过滤
    apply_keyword_filter "${WORK_DIR}/clean_ads.txt" "${WORK_DIR}/filter_ads.txt"

    # 处理白名单 (合并本地)
    echo "📥 合并本地白名单 (scripts/exclude-keyword.txt)..."
    local_allow="scripts/exclude-keyword.txt"
    if [ -f "$local_allow" ]; then
        grep -vE '^\s*($|#)' "$local_allow" > "${WORK_DIR}/local_allow_clean.txt"
        cat "${WORK_DIR}/raw_allow.txt" "${WORK_DIR}/local_allow_clean.txt" > "${WORK_DIR}/merged_allow_raw.txt"
    else
        cp "${WORK_DIR}/raw_allow.txt" "${WORK_DIR}/merged_allow_raw.txt"
    fi
    cat "${WORK_DIR}/merged_allow_raw.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_allow.txt"

    # 简单去重
    optimize_self "${WORK_DIR}/filter_ads.txt" "${WORK_DIR}/opt_ads.txt"
    optimize_self "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/opt_allow.txt"

    # 白名单过滤
    apply_advanced_whitelist_filter "${WORK_DIR}/opt_ads.txt" "${WORK_DIR}/opt_allow.txt" "${WORK_DIR}/final_ads.txt"

    # 输出 (mode=add_prefix: 统一添加 +.)
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
    | tr -d '\r' | sed '/^[[:space:]]*#/d; /skk\.moe/d; /^$/d; s/^DOMAIN-SUFFIX,/+./; s/^DOMAIN,//; /^\+\.$/d; /^[[:space:]]*$/d' \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | sort -u > "${WORK_DIR}/clean_rd.txt"

    # 处理白名单
    echo "📥 准备白名单..."
    local_allow="scripts/exclude-keyword.txt"
    
    if [ -f "${WORK_DIR}/clean_allow.txt" ]; then
        cp "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/clean_rd_allow.txt"
    else
        download_files_parallel "${WORK_DIR}/raw_allow_temp.txt" "${ALLOW_URLS[@]}"
        if [ -f "$local_allow" ]; then
            grep -vE '^\s*($|#)' "$local_allow" > "${WORK_DIR}/local_allow_clean.txt"
            cat "${WORK_DIR}/raw_allow_temp.txt" "${WORK_DIR}/local_allow_clean.txt" > "${WORK_DIR}/merged_allow_raw.txt"
        else
            cp "${WORK_DIR}/raw_allow_temp.txt" "${WORK_DIR}/merged_allow_raw.txt"
        fi
        cat "${WORK_DIR}/merged_allow_raw.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_rd_allow.txt"
    fi

    apply_advanced_whitelist_filter "${WORK_DIR}/clean_rd.txt" "${WORK_DIR}/clean_rd_allow.txt" "${WORK_DIR}/final_rd.txt"

    # 输出 (mode=none: 保持源文件的前缀逻辑)
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
