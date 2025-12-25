#!/bin/bash

# ================= 全局配置 =================

# 【核心】强制使用 C 语言区域设置
# 1. 确保 sort 速度最快
# 2. 确保 ASCII 排序顺序：Space(32) < . (46) < 0 (48) < 1 (49)
#    这是算法正确识别父子域名、区分黑白名单的基础
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

# 1. 并行下载 (极速模式)
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
                # 确保文件末尾有换行，防止拼接错误
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

# 2. 域名标准化 (去除装饰符、IP、注释、空格)
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
    # 逻辑：反转 -> 排序 -> 比较相邻行 -> 再次反转
    # 如果当前行是上一行的子域名 (index=1)，则丢弃当前行 (保留短的父域名)
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

# 5. 【核心算法】高级白名单过滤 (Buffer + Active Root)
# 解决了双向覆盖：
# A. 白名单是黑名单子域名 (wgo.mmstat.com vs mmstat.com) -> Buffer Logic 解决
# B. 黑名单是白名单子域名 (ad.google.com vs google.com) -> Active Root Logic 解决
# C. 完全相等 -> 任意 Logic 解决
apply_advanced_whitelist_filter() {
    local block_in=$1
    local allow_in=$2
    local final_out=$3

    echo "🛡️  应用全向白名单过滤算法..."

    # --- 步骤 A: 准备白名单 ---
    # 格式: [反转纯域名] [1]
    awk '{ 
        key=$0; 
        reversed = ""; len = length(key);
        for (i=len; i>=1; i--) reversed = reversed substr(key, i, 1);
        print reversed, 1 
    }' "$allow_in" > "${WORK_DIR}/algo_input.txt"

    # --- 步骤 B: 准备黑名单 ---
    # 格式: [反转纯域名] [0] [原始行]
    # 保留原始行是为了输出时保留 "+."
    awk '{ 
        original=$0;
        pure=original;
        sub(/^\+\./, "", pure);
        sub(/^\./, "", pure);
        reversed = ""; len = length(pure);
        for (i=len; i>=1; i--) reversed = reversed substr(pure, i, 1);
        print reversed, 0, original 
    }' "$block_in" >> "${WORK_DIR}/algo_input.txt"

    # --- 步骤 C: 排序与双向过滤 ---
    # 排序顺序: 父域名(短) < 子域名(长) ; 0(Block) < 1(Allow)
    sort -k1,1 "${WORK_DIR}/algo_input.txt" | awk '
    BEGIN { FS=" " }
    {
        key = $1
        type = $2
        original = $3 # 仅 Block 有

        # === 逻辑 1: 白名单父域名覆盖检测 (Active Root) ===
        # 如果当前 Key 是 active_white_root 的子域名，说明它被一个更短的白名单覆盖了
        # 例子: active=moc.elgoog (google.com), key=moc.elgoog.da (ad.google.com)
        if (active_white_root != "" && index(key, active_white_root ".") == 1) {
            # 这是一个被白名单覆盖的子域名
            if (type == 1) {
                # 白名单子域名，更新 active root 吗？不需要，保留短的即可。
                # 但为了严谨，我们可以不操作，它自然被保护。
                next 
            } else {
                # 黑名单子域名，被白名单父域名覆盖 -> 删除
                next 
            }
        }

        # === 逻辑 2: 缓冲区检测 (Buffer) ===
        # 检查当前 Key 是否是 Buffer (黑名单父域名) 的子域名或相等
        # 例子: Buffer=moc.tatsmm (mmstat.com), Key=moc.tatsmm.ogw (wgo.mmstat.com)
        is_child_or_equal = (buffered_key != "" && (index(key, buffered_key ".") == 1 || key == buffered_key));

        if (is_child_or_equal) {
            if (type == 1) {
                # 关键：白名单子域名出现！
                # 说明之前的黑名单 Buffer (父域名) 过于宽泛，误杀了这个白名单。
                # 必须杀死 Buffer。
                buffered_key = ""
                buffered_line = ""
                
                # 同时，将当前白名单设为 active，以防止后续更长的黑名单子域名
                active_white_root = key
            }
            # 如果是 type 0 (黑名单子域名)，它是冗余的，忽略
        } else {
            # === 新的分支 ===
            # 先输出之前确认为安全的 Buffer
            if (buffered_line != "") {
                print buffered_line
            }

            if (type == 1) {
                # 这是一个新的白名单根
                active_white_root = key
                
                # 白名单不进 Buffer
                buffered_key = ""
                buffered_line = ""
            } else {
                # 这是一个新的黑名单根
                buffered_key = key
                buffered_line = original
                
                # 黑名单阻断了之前的白名单覆盖吗？
                # 不，黑名单也是一种覆盖。但这里我们只处理去重。
                # 我们重置 active_white_root 吗？
                # 不，因为 input 已经排序。
                # 如果 key 是 "moc.a"，active 是 "moc"，则会在逻辑1被处理。
                # 如果代码走到这里，说明 key 不是 active 的子域名。
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

    # 再次去重，确保万无一失
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

# ================= 模块 1: ADs =================

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

    # 清洗
    grep -vE '^\s*@@' "${WORK_DIR}/raw_ads.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_ads.txt"
    apply_keyword_filter "${WORK_DIR}/clean_ads.txt" "${WORK_DIR}/filter_ads.txt"
    cat "${WORK_DIR}/raw_allow.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_allow.txt"

    # 自身去重
    optimize_self "${WORK_DIR}/filter_ads.txt" "${WORK_DIR}/opt_ads.txt"
    optimize_self "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/opt_allow.txt"

    # 核心过滤
    apply_advanced_whitelist_filter "${WORK_DIR}/opt_ads.txt" "${WORK_DIR}/opt_allow.txt" "${WORK_DIR}/final_ads.txt"

    finalize_output "${WORK_DIR}/final_ads.txt" "ADs_merged.mrs" "add_prefix"
    mv "${WORK_DIR}/final_ads.txt" "ADs_merged.txt"
}

# ================= 模块 2: AI =================

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

# ================= 模块 3: Fake IP =================

generate_fakeip() {
    echo "=== 🚀 模块 3: Fake IP ==="
    local FAKE_IP_URLS=(
        "https://raw.githubusercontent.com/vernesong/OpenClash/refs/heads/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list"
        "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list"
        "https://raw.githubusercontent.com/DustinWin/ruleset_geodata/refs/heads/mihomo-ruleset/fakeip-filter.list"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/fake-ip-addon.txt"
    )
    download_files_parallel "${WORK_DIR}/raw_fakeip.txt" "${FAKE_IP_URLS[@]}"
    
    # 逻辑：保留原始格式，优先保留 +.
    echo "🧹 清洗..."
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

# ================= 模块 4: Reject Drop =================

generate_reject() {
    echo "=== 🚀 模块 4: Reject Drop ==="
    local BLOCK_URLS=(
        "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/rules/Custom_Reject-drop.txt"
    )
    download_files_parallel "${WORK_DIR}/raw_rd.txt" "${BLOCK_URLS[@]}"

    echo "🧹 SED 清洗..."
    # 【修复】增加去尾部空格，防止 wgo.mmstat.com 匹配失败
    cat "${WORK_DIR}/raw_rd.txt" \
    | tr -d '\r' | sed '/^#/d; /skk\.moe/d; /^$/d; s/^DOMAIN-SUFFIX,/+./; s/^DOMAIN,//; /^\+\.$/d; /^[[:space:]]*$/d' \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | sort -u > "${WORK_DIR}/clean_rd.txt"

    if [ -f "${WORK_DIR}/clean_allow.txt" ]; then
        echo "♻️  复用模块 1 白名单..."
        cp "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/clean_rd_allow.txt"
    else
        echo "ℹ️  下载白名单..."
        download_files_parallel "${WORK_DIR}/raw_allow_temp.txt" "${ALLOW_URLS[@]}"
        cat "${WORK_DIR}/raw_allow_temp.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_rd_allow.txt"
    fi

    # 核心过滤
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
