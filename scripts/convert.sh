#!/bin/bash

# ================= 全局配置 =================

# 【核心】强制使用 C 语言区域设置，确保 ASCII 排序顺序稳定
export LC_ALL=C

WORK_DIR=$(mktemp -d)
trap "rm -rf ${WORK_DIR}" EXIT

# 白名单源
ALLOW_URLS=(
    "https://raw.githubusercontent.com/Cats-Team/AdRules/refs/heads/script/script/allowlist.txt"
    "https://raw.githubusercontent.com/mawenjian/china-cdn-domain-whitelist/refs/heads/master/china-cdn-domain-whitelist.txt"
    "https://raw.githubusercontent.com/zoonderkins/blahdns/refs/heads/master/hosts/whitelist.txt"
    "https://raw.githubusercontent.com/AdguardTeam/AdGuardSDNSFilter/master/Filters/exceptions.txt"
)

# 检查工具
CHECK_MIHOMO() {
    if ! command -v mihomo &> /dev/null; then
        echo "⚠️  未检测到 mihomo 命令，跳过转换。"
        return 1
    fi
    return 0
}

# 下载函数
download_files() {
    local output_file=$1
    shift
    local urls=("$@")
    for url in "${urls[@]}"; do
        local filename=$(basename "$url")
        echo -n "⬇️  下载: $filename ... "
        local temp_dl=$(mktemp)
        if curl -sLf --connect-timeout 15 --retry 3 "$url" > "$temp_dl"; then
            local lines=$(wc -l < "$temp_dl")
            cat "$temp_dl" >> "$output_file"
            echo "" >> "$output_file"
            echo "✅ ($lines 行)"
        else
            echo "❌ 失败"
        fi
        rm -f "$temp_dl"
    done
}

# 核心清洗函数 (仅保留纯域名)
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

# 自身去重函数
optimize_list() {
    local input_file=$1
    local output_file=$2
    echo "🧠 自身智能去重..."
    cat "$input_file" \
    | rev | sort | awk 'NR==1 {prev=$0; print; next} {if (index($0, prev ".") != 1) {print; prev=$0}}' | rev | sort > "$output_file"
}

# 关键词过滤
apply_keyword_filter() {
    local input_file=$1
    local output_file=$2
    local keyword_file="scripts/exclude-keyword.txt"
    if [ -f "$keyword_file" ]; then
        echo "🔍 应用关键词排除..."
        grep -v -f "$keyword_file" "$input_file" > "$output_file"
    else
        cp "$input_file" "$output_file"
    fi
}

# 添加前缀
add_final_prefix() {
    sed 's/^/+./' "$1" > "$2"
}

# 添加文件头
add_header_info() {
    local file=$1
    local count=$(wc -l < "$file")
    local date=$(date +"%Y-%m-%d %H:%M:%S")
    local tmp=$(mktemp)
    echo "# Count: $count" > "$tmp"
    echo "# Updated: $date" >> "$tmp"
    cat "$file" >> "$tmp"
    mv "$tmp" "$file"
    echo "📊 最终行数: $count"
}

convert_to_mrs() {
    [ -n "$1" ] && CHECK_MIHOMO && mihomo convert-ruleset domain text "$1" "$2"
}

# ================= 模块 1: ADs =================

generate_ads_merged() {
    echo "=== 生成 ADs 规则 ==="
    OUTPUT_FILE="ADs_merged.txt"
    BLOCK_URLS=(
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

    download_files "${WORK_DIR}/raw_block_all.txt" "${BLOCK_URLS[@]}"
    download_files "${WORK_DIR}/raw_allow_all.txt" "${ALLOW_URLS[@]}"

    grep -vE '^\s*@@' "${WORK_DIR}/raw_block_all.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_block.txt"
    apply_keyword_filter "${WORK_DIR}/clean_block.txt" "${WORK_DIR}/filtered_block.txt"
    
    cat "${WORK_DIR}/raw_allow_all.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_allow.txt"

    optimize_list "${WORK_DIR}/filtered_block.txt" "${WORK_DIR}/opt_block.txt"
    optimize_list "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/opt_allow.txt"

    echo "🛡️  应用白名单过滤..."
    cat "${WORK_DIR}/opt_allow.txt" | rev | sed 's/$/!/' > "${WORK_DIR}/allow_rev.txt"
    cat "${WORK_DIR}/opt_block.txt" | rev | sed 's/$/~/' > "${WORK_DIR}/block_rev.txt"

    cat "${WORK_DIR}/allow_rev.txt" "${WORK_DIR}/block_rev.txt" \
    | sort \
    | awk '{
        if ($0 ~ /!$/) {
            allow_root = substr($0, 1, length($0)-1);
        } else {
            block_domain = substr($0, 1, length($0)-1);
            if (block_domain == allow_root) next;
            if (allow_root != "" && index(block_domain, allow_root ".") == 1) next;
            if (allow_root != "" && index(allow_root, block_domain ".") == 1) next;
            print block_domain;
        }
    }' \
    | rev > "${WORK_DIR}/final_pure.txt"

    add_final_prefix "${WORK_DIR}/final_pure.txt" "$OUTPUT_FILE"
    convert_to_mrs "$OUTPUT_FILE" "ADs_merged.mrs"
    add_header_info "$OUTPUT_FILE"
    echo "✅ ADs 规则完成"
}

# ================= 模块 2: AI =================

generate_ais_merged() {
    echo "=== 生成 AI 规则 ==="
    OUTPUT_FILE="AIs_merged.txt"
    AI_URLS=(
        "https://github.com/MetaCubeX/meta-rules-dat/raw/meta/geo/geosite/category-ai-!cn.list"
        "https://ruleset.skk.moe/List/non_ip/ai.conf"
        "https://github.com/DustinWin/ruleset_geodata/raw/mihomo-ruleset/ai.list"
        "https://raw.githubusercontent.com/ConnersHua/RuleGo/refs/heads/master/Surge/Ruleset/Extra/AI.list"
    )
    download_files "${WORK_DIR}/raw_ai.txt" "${AI_URLS[@]}"
    cat "${WORK_DIR}/raw_ai.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_ai.txt"
    optimize_list "${WORK_DIR}/clean_ai.txt" "${WORK_DIR}/opt_ai.txt"
    add_final_prefix "${WORK_DIR}/opt_ai.txt" "$OUTPUT_FILE"
    convert_to_mrs "$OUTPUT_FILE" "AIs_merged.mrs"
    add_header_info "$OUTPUT_FILE"
    echo "✅ AI 规则完成"
}

# ================= 模块 3: Fake IP =================

generate_Fake_IP_Filter_merged() {
    echo "=== 生成 Fake IP 规则 ==="
    OUTPUT_FILE="Fake_IP_Filter_merged.txt"
    FAKE_IP_URLS=(
        "https://raw.githubusercontent.com/vernesong/OpenClash/refs/heads/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list"
        "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list"
        "https://raw.githubusercontent.com/DustinWin/ruleset_geodata/refs/heads/mihomo-ruleset/fakeip-filter.list"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/fake-ip-addon.txt"
    )
    download_files "${WORK_DIR}/raw_fakeip.txt" "${FAKE_IP_URLS[@]}"
    
    echo "🧹 处理 Fake IP (优先保留 +. 版本)..."
    cat "${WORK_DIR}/raw_fakeip.txt" \
    | tr -d '\r' \
    | grep -vE '^\s*($|#|!)' \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | awk '{
        origin = $0;
        root = origin;
        sub(/^\+\./, "", root);
        sub(/^\./, "", root);
        if (!(root in seen)) { seen[root] = origin; } 
        else { if (seen[root] !~ /^\+\./ && origin ~ /^\+\./) seen[root] = origin; }
    } END { for (r in seen) print seen[r]; }' \
    | sort > "$OUTPUT_FILE"

    convert_to_mrs "$OUTPUT_FILE" "Fake_IP_Filter_merged.mrs"
    add_header_info "$OUTPUT_FILE"
    echo "✅ Fake IP 规则完成"
}

# ================= 模块 4: Reject Drop =================

generate_reject_drop_merged() {
    echo "=== 生成 Reject Drop 规则 ==="
    OUTPUT_FILE="Reject_Drop_merged.txt"
    BLOCK_URLS=(
        "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/rules/Custom_Reject-drop.txt"
    )
    
    download_files "${WORK_DIR}/raw_rd_block.txt" "${BLOCK_URLS[@]}"

    echo "🧹 清洗黑名单 (sed + 去重)..."
    cat "${WORK_DIR}/raw_rd_block.txt" \
    | tr -d '\r' \
    | sed '/^#/d; /skk\.moe/d; /^$/d; s/^DOMAIN-SUFFIX,/+./; s/^DOMAIN,//; /^\+\.$/d; /^[[:space:]]*$/d' \
    | sort -u \
    > "${WORK_DIR}/clean_rd_block.txt"

    if [ -f "${WORK_DIR}/clean_allow.txt" ]; then
        echo "♻️  复用白名单..."
        cp "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/clean_rd_allow.txt"
    else
        echo "ℹ️  下载白名单..."
        download_files "${WORK_DIR}/raw_allow_temp.txt" "${ALLOW_URLS[@]}"
        cat "${WORK_DIR}/raw_allow_temp.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_rd_allow.txt"
    fi

    echo "🛡️  应用白名单 (双向覆盖+完全一致覆盖)..."
    
    # 1. 准备白名单: reversed pure + type 1
    cat "${WORK_DIR}/clean_rd_allow.txt" | rev | awk '{print $0, 1}' > "${WORK_DIR}/rd_merged_input.txt"

    # 2. 准备黑名单: reversed pure + type 0 + original line
    awk '{
        pure = $0;
        sub(/^\+\./, "", pure);
        sub(/^\./, "", pure);
        cmd = "echo " pure " | rev";
        cmd | getline rev_pure;
        close(cmd);
        print rev_pure, 0, $0;
    }' "${WORK_DIR}/clean_rd_block.txt" >> "${WORK_DIR}/rd_merged_input.txt"

    # 3. 排序 + 过滤
    # 排序说明: 纯字符串排序。
    # 由于 0 (ASCII 48) < 1 (ASCII 49)，同域名下黑名单(0)排在白名单(1)前面。
    sort "${WORK_DIR}/rd_merged_input.txt" \
    | awk '
    {
        key = $1
        type = $2
        original = $3
        
        # 逻辑：
        # buffered_key 存储的是一个尚未输出的黑名单父域名 (如 moc.tatsmm)
        # key 是当前行 (如 moc.tatsmm.ogw)
        
        # 1. 检查当前行是否是 Buffer 的子域名/或完全相等
        is_child_or_equal = (buffered_key != "" && (index(key, buffered_key ".") == 1 || key == buffered_key));

        if (is_child_or_equal) {
            # 当前行与 Buffer 有父子关系或相等
            if (type == 1) {
                # 当前是白名单 (如 wgo.mmstat.com)
                # 意味着之前的 Buffer (如 mmstat.com) 过于宽泛，必须删除！
                buffered_key = ""
                buffered_line = ""
            }
            # 如果是 type 0 (黑名单子域名)，则作为冗余去重，忽略
        } else {
            # 没有关系，说明是新分支
            # 先把旧的 Buffer 输出来 (它安全了)
            if (buffered_line != "") {
                print buffered_line
            }

            # 更新 Buffer
            if (type == 0) {
                buffered_key = key
                buffered_line = original
            } else {
                # 白名单不用存，因为它只用来"杀"前面的黑名单
                buffered_key = ""
                buffered_line = ""
            }
        }
    }
    END {
        if (buffered_line != "") print buffered_line
    }' > "$OUTPUT_FILE"

    convert_to_mrs "$OUTPUT_FILE" "Reject_Drop_merged.mrs"
    add_header_info "$OUTPUT_FILE"
    echo "✅ Reject Drop 规则完成"
}

# ================= 主程序 =================

main() {
    case "$1" in
        ads) generate_ads_merged ;;
        ais) generate_ais_merged ;;
        fakeip) generate_Fake_IP_Filter_merged ;;
        reject) generate_reject_drop_merged ;;
        all)
            generate_ads_merged
            generate_ais_merged
            generate_Fake_IP_Filter_merged
            generate_reject_drop_merged
            ;;
        *)
            echo "用法: $0 [ads|ais|fakeip|reject|all]"
            exit 1
            ;;
    esac
}

main "$@"
