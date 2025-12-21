#!/bin/bash

# ================= 全局配置与辅助函数 =================

# 临时工作目录 (全局统一管理)
WORK_DIR=$(mktemp -d)
trap "rm -rf ${WORK_DIR}" EXIT

# 【全局变量】白名单源 (模块1和模块4共用)
# 包含 AdRules, CDN, blahdns 以及新加入的 AdGuardSDNSFilter exceptions
ALLOW_URLS=(
    "https://raw.githubusercontent.com/Cats-Team/AdRules/refs/heads/script/script/allowlist.txt"
    "https://raw.githubusercontent.com/mawenjian/china-cdn-domain-whitelist/refs/heads/master/china-cdn-domain-whitelist.txt"
    "https://raw.githubusercontent.com/zoonderkins/blahdns/refs/heads/master/hosts/whitelist.txt"
    "https://raw.githubusercontent.com/AdguardTeam/AdGuardSDNSFilter/master/Filters/exceptions.txt"
)

# 检查 mihomo 是否安装
CHECK_MIHOMO() {
    if ! command -v mihomo &> /dev/null; then
        echo "⚠️  未检测到 mihomo 命令，将跳过 .mrs 格式转换。"
        return 1
    fi
    return 0
}

# 下载函数 (显示行数和状态)
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
            echo "✅ 成功 ($lines 行)"
        else
            echo "❌ 失败 (404/网络错误)"
            echo "   👉 请检查链接: $url"
        fi
        rm -f "$temp_dl"
    done
}

# 核心清洗函数 (用于 ADs 和 AI 模块以及白名单处理)
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
# 更新说明：
# sed 's/^!.*//g' : 去除 ! 开头的注释行
# sed 's/^@@//g' : 去除行首的 @@ (用于白名单清洗，拦截名单会在进入此函数前被 grep -v 剔除)

# 智能去重函数 (主域名覆盖子域名)
optimize_list() {
    local input_file=$1
    local output_file=$2
    echo "🧠 正在智能去重 (主域名覆盖子域名)..."
    cat "$input_file" \
    | rev | sort | awk 'NR==1 {prev=$0; print; next} {if (index($0, prev ".") != 1) {print; prev=$0}}' | rev | sort > "$output_file"
}

# 关键词过滤函数
apply_keyword_filter() {
    local input_file=$1
    local output_file=$2
    local keyword_file="scripts/exclude-keyword.txt"
    if [ -f "$keyword_file" ]; then
        echo "🔍 应用本地关键词排除 ($keyword_file)..."
        grep -v -f "$keyword_file" "$input_file" > "$output_file"
    else
        cp "$input_file" "$output_file"
    fi
}

# 添加最终前缀 (+.)
add_final_prefix() {
    local input_file=$1
    local output_file=$2
    echo "✨ 正在添加最终前缀 (+.)..."
    sed 's/^/+./' "$input_file" > "$output_file"
}

# 添加文件头信息
add_header_info() {
    local file=$1
    local count=$(wc -l < "$file")
    local current_date=$(date +"%Y-%m-%d %H:%M:%S")
    local temp_header=$(mktemp)
    echo "# Count: $count" > "$temp_header"
    echo "# Updated: $current_date" >> "$temp_header"
    cat "$file" >> "$temp_header"
    mv "$temp_header" "$file"
    echo "📊 最终行数: $count"
}

# 转换为 MRS 格式
convert_to_mrs() {
    local src=$1
    local dst=$2
    if CHECK_MIHOMO; then
        echo "🔄 正在转换为 binary (.mrs) 格式..."
        mihomo convert-ruleset domain text "$src" "$dst"
    fi
}

# ================= 模块 1: ADs (去广告) =================

generate_ads_merged() {
    echo "=== 开始生成 ADs 规则 ==="
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

    # 1. 下载
    download_files "${WORK_DIR}/raw_block_all.txt" "${BLOCK_URLS[@]}"
    download_files "${WORK_DIR}/raw_allow_all.txt" "${ALLOW_URLS[@]}"

    # 2. 处理拦截规则
    echo "🧹 处理拦截规则..."
    # 【重点】直接使用 grep -v 剔除以 @@ 开头的行 (以及可能存在的空格)
    # 这样这些例外规则就不会进入黑名单
    grep -vE '^\s*@@' "${WORK_DIR}/raw_block_all.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_block.txt"

    apply_keyword_filter "${WORK_DIR}/clean_block.txt" "${WORK_DIR}/filtered_block.txt"

    # 3. 处理白名单
    echo "🧹 处理白名单..."
    # 白名单需要 normalize_domain 去除 @@ 前缀，还原为纯域名
    cat "${WORK_DIR}/raw_allow_all.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_allow.txt"

    optimize_list "${WORK_DIR}/filtered_block.txt" "${WORK_DIR}/opt_block.txt"
    optimize_list "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/opt_allow.txt"

    echo "🛡️  正在应用白名单过滤..."
    cat "${WORK_DIR}/opt_allow.txt" | rev | sed 's/$/!/' > "${WORK_DIR}/allow_rev_tagged.txt"
    cat "${WORK_DIR}/opt_block.txt" | rev > "${WORK_DIR}/block_rev.txt"

    cat "${WORK_DIR}/allow_rev_tagged.txt" "${WORK_DIR}/block_rev.txt" \
    | sort \
    | awk '/!$/ { root = substr($0, 1, length($0)-1); next; } { if ($0 == root) next; if (root != "" && index($0, root ".") == 1) next; print; }' \
    | rev > "${WORK_DIR}/final_pure.txt"

    add_final_prefix "${WORK_DIR}/final_pure.txt" "$OUTPUT_FILE"
    convert_to_mrs "$OUTPUT_FILE" "ADs_merged.mrs"
    add_header_info "$OUTPUT_FILE"
    echo "✅ ADs 规则生成完成。"
}

# ================= 模块 2: AI (人工智能) =================

generate_ais_merged() {
    echo "=== 开始生成 AI 规则 ==="
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
    echo "✅ AI 规则生成完成。"
}

# ================= 模块 3: Fake IP Filter =================

generate_Fake_IP_Filter_merged() {
    echo "=== 开始生成 Fake IP Filter 规则 ==="
    OUTPUT_FILE="Fake_IP_Filter_merged.txt"

    FAKE_IP_URLS=(
        "https://raw.githubusercontent.com/vernesong/OpenClash/refs/heads/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list"
        "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list"
        "https://raw.githubusercontent.com/DustinWin/ruleset_geodata/refs/heads/mihomo-ruleset/fakeip-filter.list"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/fake-ip-addon.txt"
    )

    download_files "${WORK_DIR}/raw_fakeip.txt" "${FAKE_IP_URLS[@]}"

    echo "🧹 处理 Fake IP 规则..."
    cat "${WORK_DIR}/raw_fakeip.txt" \
    | tr -d '\r' \
    | grep -vE '^\s*($|#|!)' \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | awk '{
        origin = $0;
        root = origin;
        sub(/^\+\./, "", root);
        sub(/^\./, "", root);
        if (!(root in seen)) {
            seen[root] = origin;
        } else {
            if (seen[root] !~ /^\+\./ && origin ~ /^\+\./) {
                seen[root] = origin;
            }
        }
    } END {
        for (r in seen) { print seen[r]; }
    }' \
    | sort \
    > "$OUTPUT_FILE"

    convert_to_mrs "$OUTPUT_FILE" "Fake_IP_Filter_merged.mrs"
    add_header_info "$OUTPUT_FILE"
    echo "✅ Fake IP 规则生成完成。"
}

# ================= 模块 4: Reject Drop =================

generate_reject_drop_merged() {
    echo "=== 开始生成 Reject Drop 规则 ==="
    OUTPUT_FILE="Reject_Drop_merged.txt"

    BLOCK_URLS=(
        "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/rules/Custom_Reject-drop.txt"
    )
    download_files "${WORK_DIR}/raw_rd_block.txt" "${BLOCK_URLS[@]}"

    echo "🧹 清洗黑名单 (执行特定 sed 规则)..."
    cat "${WORK_DIR}/raw_rd_block.txt" \
    | tr -d '\r' \
    | sed '/^#/d; /skk\.moe/d; /^$/d; s/^DOMAIN-SUFFIX,/+./; s/^DOMAIN,//; /^\+\.$/d; /^[[:space:]]*$/d' \
    > "${WORK_DIR}/clean_rd_block.txt"

    # 复用白名单逻辑
    if [ -f "${WORK_DIR}/clean_allow.txt" ]; then
        echo "♻️  复用模块 1 已生成的白名单..."
        cp "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/clean_rd_allow.txt"
    else
        echo "ℹ️  未找到已有白名单，正在下载并清洗..."
        download_files "${WORK_DIR}/raw_allow_temp.txt" "${ALLOW_URLS[@]}"
        cat "${WORK_DIR}/raw_allow_temp.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_rd_allow.txt"
    fi

    echo "🛡️  应用白名单过滤..."
    awk 'NR==FNR { allow[$0]=1; next } 
    {
        clean_domain = $0;
        sub(/^\+\./, "", clean_domain);
        sub(/^\./, "", clean_domain);
        if (!(clean_domain in allow)) {
            print $0;
        }
    }' "${WORK_DIR}/clean_rd_allow.txt" "${WORK_DIR}/clean_rd_block.txt" > "${WORK_DIR}/filtered_rd_block.txt"

    echo "🧠 正在去重..."
    sort -u "${WORK_DIR}/filtered_rd_block.txt" > "$OUTPUT_FILE"

    convert_to_mrs "$OUTPUT_FILE" "Reject_Drop_merged.mrs"
    add_header_info "$OUTPUT_FILE"
    echo "✅ Reject Drop 规则生成完成。"
}

# ================= 主程序入口 =================

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

# 执行主函数
main "$@"
