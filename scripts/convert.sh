#!/bin/bash

# ================= 全局配置 =================

# 【核心】强制使用 C 语言区域设置
# 确保 ASCII 排序顺序：Tab(9) < Space(32) < * (42) < . (46) < 0 (48) < 1 (49)
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

# 2. 域名标准化 (通用)
normalize_domain() {
    tr 'A-Z' 'a-z' | tr -d '\r' \
    | sed -E '
        s/^[[:space:]]*//; s/[[:space:]]*$//;    
        s/[\$#].*//g;                            
        s/^(0\.0\.0\.0|127\.0\.0\.1)[[:space:]]+//g; 
        s/^!.*//; s/^@@//;                       
        s/\|\|//; s/\^//; s/\|//;                
        s/^domain-keyword,//; s/^domain-suffix,//; s/^domain,//; 
        s/^([^,]+).*/\1/;                        
        s/^\+\.//; s/^\.//; s/\.$//              
    ' \
    | grep -vE '(\*|[^a-z0-9._ -]|^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$)' \
    | grep -E '^[a-z0-9_]' \
    | awk '/\./ {print $0}'
}

# 3. 关键词过滤
apply_keyword_filter() {
    local keyword_file="scripts/exclude-keyword.txt"
    if [ -f "$keyword_file" ] && [ -s "$keyword_file" ]; then
        echo "🔍 应用关键词排除..."
        grep -v -f "$keyword_file" "$1" > "$2"
    else
        cp "$1" "$2"
    fi
}

# 4. 【通用算法】智能覆盖去重 (Tab分隔符版)
# 逻辑：+.domain (Priority 0) 覆盖 domain/sub.domain (Priority 1)
optimize_smart_self() {
    local input=$1
    local output=$2

    echo "🧠 执行智能覆盖去重 (+. 覆盖子域名)..."

    # 准备数据：[反转] \t [优先级] \t [原始]
    awk -v OFS="\t" '{ 
        original=$0; pure=original; priority=1;
        # 移除行首空格
        sub(/^[[:space:]]+/, "", pure);
        
        # 识别通配前缀 (+. 或 .)
        if (sub(/^\+\./, "", pure) || sub(/^\./, "", pure)) { 
            priority=0; 
        } 
        
        reversed=""; len=length(pure);
        for(i=len;i>=1;i--) reversed=reversed substr(pure,i,1);
        print reversed, priority, original 
    }' "$input" > "${WORK_DIR}/self_algo.txt"

    # 排序与去重 (Tab排序确保父在前)
    sort -t $'\t' "${WORK_DIR}/self_algo.txt" | awk -F "\t" '
    {
        key = $1
        prio = $2
        original = $3

        # 检查是否被 Buffer (Priority 0 的 +.) 覆盖
        is_child_or_equal = (buffered_key != "" && (index(key, buffered_key ".") == 1 || key == buffered_key));

        if (is_child_or_equal && buffered_prio == 0) {
            # 被覆盖，丢弃
            next
        } else {
            # 未被覆盖，输出上一个 Buffer
            if (buffered_line != "") print buffered_line

            # 更新 Buffer
            if (prio == 0) {
                buffered_key = key
                buffered_prio = prio
                buffered_line = original
            } else {
                print original
                buffered_key = ""
                buffered_line = ""
            }
        }
    }
    END {
        if (buffered_line != "") print buffered_line
    }' > "$output"
}

# 5. 【ADs/Reject 算法】双向智能白名单过滤
apply_advanced_whitelist_filter() {
    local block_in=$1
    local allow_in=$2
    local final_out=$3

    echo "🛡️  应用双向白名单过滤..."

    # 步骤 A: 准备白名单
    awk -v OFS="\t" '{ 
        key=$0; reversed=""; len=length(key);
        for(i=len;i>=1;i--) reversed=reversed substr(key,i,1);
        print reversed, 1 
    }' "$allow_in" > "${WORK_DIR}/algo_input.txt"

    # 步骤 B: 准备黑名单
    awk -v OFS="\t" '{ 
        original=$0; pure=original;
        sub(/^\+\./,"",pure); sub(/^\./,"",pure);
        reversed=""; len=length(pure);
        for(i=len;i>=1;i--) reversed=reversed substr(pure,i,1);
        print reversed, 0, original 
    }' "$block_in" >> "${WORK_DIR}/algo_input.txt"

    # 步骤 C: 排序与过滤
    sort -t $'\t' "${WORK_DIR}/algo_input.txt" | awk -F "\t" '
    {
        key = $1
        type = $2
        original = $3

        # 逻辑 1: 父杀子 (Active Root)
        if (active_white_root != "" && index(key, active_white_root ".") == 1) {
            next
        }

        # 逻辑 2: 子杀父 (Buffer)
        is_child_or_equal = (buffered_key != "" && (index(key, buffered_key ".") == 1 || key == buffered_key));

        if (is_child_or_equal) {
            if (type == 1) {
                # 白名单出现 -> 杀死 Buffer
                buffered_key = ""
                buffered_line = ""
                active_white_root = key
            }
        } else {
            if (buffered_line != "") print buffered_line

            if (type == 1) {
                active_white_root = key
                buffered_key = ""
                buffered_line = ""
            } else {
                buffered_key = key
                buffered_line = original
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
    "https://raw.githubusercontent.com/zoonderkins/blahdns/refs/heads/master/hosts/whitelist.txt"
    "https://raw.githubusercontent.com/AdguardTeam/AdGuardSDNSFilter/master/Filters/exceptions.txt"
)

# ================= 模块定义 =================

generate_ads() {
    echo "=== 🚀 模块 1: ADs 规则 (ads-reject) ==="
    local BLOCK_URLS=(
        "https://raw.githubusercontent.com/pmkol/easymosdns/rules/ad_domain_list.txt"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/Reject-addon.txt"
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt"
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_3.txt"
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_4.txt"
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

    grep -vE '^\s*@@' "${WORK_DIR}/raw_ads.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_ads.txt"
    apply_keyword_filter "${WORK_DIR}/clean_ads.txt" "${WORK_DIR}/filter_ads.txt"

    echo "📥 合并本地白名单..."
    local_allow="scripts/exclude-keyword.txt"
    if [ -f "$local_allow" ]; then
        grep -vE '^\s*($|#)' "$local_allow" > "${WORK_DIR}/local_allow_clean.txt"
        cat "${WORK_DIR}/raw_allow.txt" "${WORK_DIR}/local_allow_clean.txt" > "${WORK_DIR}/merged_allow_raw.txt"
    else
        cp "${WORK_DIR}/raw_allow.txt" "${WORK_DIR}/merged_allow_raw.txt"
    fi
    cat "${WORK_DIR}/merged_allow_raw.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_allow.txt"

    optimize_smart_self "${WORK_DIR}/filter_ads.txt" "${WORK_DIR}/opt_ads.txt"
    optimize_smart_self "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/opt_allow.txt"

    apply_advanced_whitelist_filter "${WORK_DIR}/opt_ads.txt" "${WORK_DIR}/opt_allow.txt" "${WORK_DIR}/final_ads.txt"

    finalize_output "${WORK_DIR}/final_ads.txt" "ADs_merged.mrs" "add_prefix"
    mv "${WORK_DIR}/final_ads.txt" "ADs_merged.txt"
}

generate_ai() {
    echo "=== 🚀 模块 2: AI 规则 (ais) ==="
    local AI_URLS=(
        "https://github.com/MetaCubeX/meta-rules-dat/raw/meta/geo/geosite/category-ai-!cn.list"
        "https://ruleset.skk.moe/List/non_ip/ai.conf"
        "https://github.com/DustinWin/ruleset_geodata/raw/mihomo-ruleset/ai.list"
        "https://raw.githubusercontent.com/ConnersHua/RuleGo/refs/heads/master/Surge/Ruleset/Extra/AI.list"
    )
    download_files_parallel "${WORK_DIR}/raw_ai.txt" "${AI_URLS[@]}"
    cat "${WORK_DIR}/raw_ai.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_ai.txt"
    
    optimize_smart_self "${WORK_DIR}/clean_ai.txt" "${WORK_DIR}/opt_ai.txt"
    
    finalize_output "${WORK_DIR}/opt_ai.txt" "AIs_merged.mrs" "add_prefix"
    mv "${WORK_DIR}/opt_ai.txt" "AIs_merged.txt"
}

generate_fakeip() {
    echo "=== 🚀 模块 3: Fake IP (fakeip) ==="
    local FAKE_IP_URLS=(
        "https://raw.githubusercontent.com/vernesong/OpenClash/refs/heads/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list"
        "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list"
        "https://raw.githubusercontent.com/DustinWin/ruleset_geodata/refs/heads/mihomo-ruleset/fakeip-filter.list"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/fake-ip-addon.txt"
        "https://ruleset.skk.moe/Internal/clash_fake_ip_filter.yaml"
    )
    download_files_parallel "${WORK_DIR}/raw_fakeip_dl.txt" "${FAKE_IP_URLS[@]}"
    
    echo "🧹 清洗..."
    cat "${WORK_DIR}/raw_fakeip_dl.txt" \
    | grep -vE '^\s*(dns:|fake-ip-filter:)' \
    | sed 's/^\s*-\s*//' \
    | tr -d "\"'\\" \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | grep -vE '^\s*($|#)' \
    | sort -u > "${WORK_DIR}/clean_fakeip.txt"

    optimize_smart_self "${WORK_DIR}/clean_fakeip.txt" "${WORK_DIR}/final_fakeip.txt"

    finalize_output "${WORK_DIR}/final_fakeip.txt" "Fake_IP_Filter_merged.mrs" "none"
    mv "${WORK_DIR}/final_fakeip.txt" "Fake_IP_Filter_merged.txt"
}

generate_reject() {
    echo "=== 🚀 模块 4: Reject Drop (ads-drop) ==="
    local BLOCK_URLS=(
        "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/rules/Custom_Reject-drop.txt"
    )
    download_files_parallel "${WORK_DIR}/raw_rd.txt" "${BLOCK_URLS[@]}"

    echo "🧹 SED 清洗..."
    cat "${WORK_DIR}/raw_rd.txt" \
    | tr -d '\r' \
    | sed -E '
        /^[[:space:]]*#/d; /skk\.moe/d; /^$/d;
        s/^DOMAIN-SUFFIX,/+./; s/^DOMAIN,//;
        /^\+\.$/d; s/^[[:space:]]*//; s/[[:space:]]*$//
    ' | sort -u > "${WORK_DIR}/clean_rd.txt"

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

    finalize_output "${WORK_DIR}/final_rd.txt" "Reject_Drop_merged.mrs" "none"
    mv "${WORK_DIR}/final_rd.txt" "Reject_Drop_merged.txt"
}

generate_cn() {
    echo "=== 🚀 模块 5: CN 规则 (cn) ==="
    
    local CN_URLS_1=(
        "https://static-file-global.353355.xyz/rules/cn-additional-list.txt"
    )
    local CN_URLS_2=(
        "https://ruleset.skk.moe/Clash/non_ip/domestic.txt"
    )

    download_files_parallel "${WORK_DIR}/raw_cn_1.txt" "${CN_URLS_1[@]}"
    download_files_parallel "${WORK_DIR}/raw_cn_2.txt" "${CN_URLS_2[@]}"

    echo "📊 List 1 原始行数: $(wc -l < "${WORK_DIR}/raw_cn_1.txt")"
    echo "📊 List 2 原始行数: $(wc -l < "${WORK_DIR}/raw_cn_2.txt")"

    echo "🧹 清洗 List 1 (纯域名)..."
    # 严格清洗流水线：转小写 -> 去注释 -> 去空格 -> 去空行 -> 去IP -> 排序去重
    cat "${WORK_DIR}/raw_cn_1.txt" \
    | tr 'A-Z' 'a-z' \
    | tr -d '\r' \
    | sed 's/#.*//g' \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | sed '/^$/d' \
    | grep -vE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' \
    | sort -u \
    > "${WORK_DIR}/clean_cn_1_base.txt"
    
    echo "📊 List 1 纯净去重后行数: $(wc -l < "${WORK_DIR}/clean_cn_1_base.txt")"
    
    # 统一加前缀
    sed 's/^/+./' "${WORK_DIR}/clean_cn_1_base.txt" > "${WORK_DIR}/clean_cn_1.txt"

    echo "🧹 清洗 List 2 (Clash格式)..."
    cat "${WORK_DIR}/raw_cn_2.txt" \
    | tr 'A-Z' 'a-z' \
    | tr -d '\r' \
    | grep -v "skk\.moe" \
    | sed '/^[[:space:]]*#/d; /^$/d' \
    | grep -E '^(domain-suffix|domain),' \
    | sed -E 's/^domain-suffix,[[:space:]]*/+./; s/^domain,[[:space:]]*//' \
    | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' \
    | sed '/^$/d' \
    > "${WORK_DIR}/clean_cn_2.txt"
    
    echo "📊 List 2 清洗后行数: $(wc -l < "${WORK_DIR}/clean_cn_2.txt")"

    cat "${WORK_DIR}/clean_cn_1.txt" "${WORK_DIR}/clean_cn_2.txt" > "${WORK_DIR}/merged_cn_raw.txt"
    echo "📊 合并后总行数: $(wc -l < "${WORK_DIR}/merged_cn_raw.txt")"

    optimize_smart_self "${WORK_DIR}/merged_cn_raw.txt" "${WORK_DIR}/final_cn.txt"
    echo "📊 智能去重后最终行数: $(wc -l < "${WORK_DIR}/final_cn.txt")"

    finalize_output "${WORK_DIR}/final_cn.txt" "CN_merged.mrs" "none"
    mv "${WORK_DIR}/final_cn.txt" "CN_merged.txt"
}

# ================= 主程序入口 =================

main() {
    local target=${1:-all}
    case "$target" in
        ads-reject) generate_ads ;;    
        ais)        generate_ai ;;
        fakeip)     generate_fakeip ;;
        ads-drop)   generate_reject ;; 
        cn)         generate_cn ;;
        all)
            generate_ads
            generate_ai
            generate_fakeip
            generate_reject
            generate_cn
            ;;
        *)
            echo "用法: $0 [ads-reject|ais|fakeip|ads-drop|cn|all]"
            exit 1
            ;;
    esac
}

main "$@"
