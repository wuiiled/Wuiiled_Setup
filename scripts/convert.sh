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
                # 🛡️ 确保文件末尾有换行符，防止拼接错误
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

# 2. 域名标准化 (已修复 53kf 问题)
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
# 说明：先执行 sed 去除 +. 再执行 grep，确保 +.accwww9.53kf.com 能通过校验。

# 3. 自身去重 (仅排序)
optimize_self() {
    echo "🧠 执行自身简单去重..."
    sort -u "$1" > "$2"
}

# 4. 关键词过滤 (仅保留 grep 逻辑，不再处理白名单)
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

# 5. 【核心算法】精准白名单过滤
# 逻辑：
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
    # 注意：纯域名用于比较，原始行用于输出
    awk '{ 
        original=$0; pure=original;
        sub(/^\+\./,"",pure); sub(/^\./,"",pure);
        reversed=""; len=length(pure);
        for(i=len;i>=1;i--) reversed=reversed substr(pure,i,1);
        print reversed, 0, original 
    }' "$block_in" >> "${WORK_DIR}/algo_input.txt"

    # 步骤 C: 排序与过滤
    # 排序顺序: moc.tatsmm (0) -> moc.tatsmm (1) -> moc.tatsmm.zznc (0)
    sort "${WORK_DIR}/algo_input.txt" | awk '
    BEGIN { FS=" "
