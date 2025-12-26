#!/bin/bash

# ================= 全局配置 =================

# 【核心】强制使用 C 语言区域设置
# 确保 ASCII 排序顺序：Space(32) < . (46) < 0 (48) < 1 (49)
# 排序结果：父域名在前，子域名在后；同名时黑名单在前，白名单在后
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
                # 🛡️ 确保文件末尾有换行符
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

# 2. 域名标准化 (修复 53kf 丢失问题)
# 逻辑顺序：去空 -> 去注释 -> 去修饰符 -> 【先】去前缀 -> 【后】字符校验
normalize_domain() {
    tr 'A-Z' 'a-z' | tr -d '\r' \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | sed 's/[\$#].*//g' \
    | sed -E 's/^(0\.0\.0\.0|127\.0\.0\.1)[[:space:]]+//g' \
    | sed 's/^!.*//g' \
    | sed 's/^@@//g' \
    | sed 's/||//g; s/\^//g; s/|//g' \
    | sed 's/domain-keyword,//g' \
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

# 3. 自身去重 (简单排序)
optimize_self() {
    echo "🧠 执行自身简单去重..."
    sort -u "$1" > "$2"
}

# 4. 关键词过滤 (仅处理 grep，不涉及白名单逻辑)
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

# 5. 【核心算法】双向智能白名单过滤
# 逻辑目标：
# - 白名单 mmstat.com -> 删除黑名单 cnzz.mmstat.com (Parent kills Child)
# - 白名单 wgo.mmstat.com -> 删除黑名单 +.mmstat.com (Child kills Parent)
apply_advanced_whitelist_filter() {
    local block_in=$1
    local allow_in=$2
    local final_out=$3

    echo "🛡️  应用双向白名单过滤 (Parent<->Child)..."

    # 步骤 A: 准备白名单 [反转] [1]
    awk '{ 
        key=$0; reversed=""; len=length(key);
        for(i=len;i>=1;i--) reversed=reversed substr(key,i,1);
        print reversed, 1 
    }' "$allow_in" > "${WORK_DIR}/algo_input.txt"

    # 步骤 B: 准备黑名单 [反转] [0] [原始]
    # 注意：original 保留原始行（含 +.），pure 用于排序比较
    awk '{ 
        original=$0; pure=original;
        sub(/^\+\./,"",pure); sub(/^\./,"",pure);
        reversed=""; len=length(pure);
        for(i=len;i>=1;i--) reversed=reversed substr(pure,i,1);
        print reversed, 0, original 
    }' "$block_in" >> "${WORK_DIR}/algo_input.txt"

    # 步骤 C: 排序与过滤
    # 排序后示例:
    # 1. moc.tatsmm 0 (+.mmstat.com 黑)
    # 2. moc.tatsmm 1 (mmstat.com 白)
    # 3. moc.tatsmm.zznc 0 (cnzz.mmstat.com 黑)
    
    sort "${WORK_DIR}/algo_input.txt" | awk '
    BEGIN { FS=" " }
    {
        key = $1
        type = $2
        original = $3

        # === 逻辑 1: Active Root (白名单父域名 杀 黑名单子域名) ===
        # 场景：Active="moc.tatsmm"(白), Current="moc.tatsmm.zznc"(黑)
        if (active_white_root != "" && index(key, active_white_root ".") == 1) {
            # 这是一个被白名单覆盖的子域名，删除。
            next
        }

        # === 逻辑 2: Buffer (白名单子域名/同名 杀 黑名单父域名) ===
        # 场景：Buffer="moc.tatsmm"(黑), Current="moc.tatsmm"(白) -> Buffer死
        # 场景：Buffer="moc.tatsmm"(黑), Current="moc.tatsmm.ogw"(白) -> Buffer死
        is_child_or_equal = (buffered_key != "" && (index(key, buffered_key ".") == 1 || key == buffered_key));

        if (is_child_or_equal) {
            if (type == 1) {
                # 白名单出现！反杀黑名单 Buffer
                buffered_key = ""
                buffered_line = ""
                
                # 【关键】将当前白名单设为 Active Root，继续保护后续子域名
                active_white_root = key
            } else {
                # 黑名单子域名。Buffer (黑父) 覆盖了 Current (黑子)。
                # 自身去重优化：丢弃黑子，保留黑父。
                # (如果不想合并黑名单，可以把这里改为 print original)
            }
        } else {
            # === 新的分支 ===
            # 输出之前安全的黑名单 Buffer
            if (buffered_line != "") print buffered_line

            if (type == 1) {
                # 新的白名单根
                active_white_root = key
                buffered_key = ""
                buffered_line = ""
            } else {
                # 新的黑名单根
                buffered_key = key
                buffered_line = original
                # 进入黑名单领地，之前的白名单保护失效
                active_white_root = "" 
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

    # 最终兜底去重
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

    # 清洗：去除 @@ 行，标准化域名 (normalize_domain 已修复)
    grep -vE '^\s*@@' "${WORK_DIR}/raw_ads.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_ads.txt"
    
    # 关键词过滤
    apply_keyword_filter "${WORK_DIR}/clean_ads.txt" "${WORK_DIR}/filter_ads.txt"

    # 处理白名单 (在线 + 本地 keyword 强转白名单)
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

    # 核心：双向白名单过滤
    apply_advanced_whitelist_filter "${WORK_DIR}/opt_ads.txt" "${WORK_DIR}/opt_allow.txt" "${WORK_DIR}/final_ads.txt"

    # 输出 (mode=add_prefix)
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
    # 逻辑：保留原始格式，优先保留 +.
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
    # 模块4特殊处理：先转成 +. 格式进行处理，保留 sed 逻辑
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

    # 输出 (mode=none, 保持 SED 处理后的格式)
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
