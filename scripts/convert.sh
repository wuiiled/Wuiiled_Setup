#!/bin/bash

# ================= 全局配置 =================

# 强制使用 C 语言区域设置，确保 ASCII 排序一致性
export LC_ALL=C

# 使用 mktemp 创建全局工作目录，并确保脚本退出时自动清理
WORK_DIR=$(mktemp -d)
trap "rm -rf ${WORK_DIR}" EXIT

# 检查 mihomo 工具是否存在
CHECK_MIHOMO() {
    if ! command -v mihomo &> /dev/null; then
        echo "⚠️  未检测到 mihomo 命令，跳过 .mrs 转换。"
        return 1
    fi
    return 0
}

# ================= 核心工具函数 =================

# 1. 并行下载
# 优化：使用 -A 模拟浏览器 UA，防止 403；使用通用 mktemp 写法
download_files_parallel() {
    local output_file=$1
    shift
    local urls=("$@")
    
    # 兼容性修复：使用最通用的 mktemp 模板写法
    local temp_map_dir
    temp_map_dir=$(mktemp -d "${WORK_DIR}/dl_map.XXXXXX")

    local pids=()
    local i=0
    
    for url in "${urls[@]}"; do
        local temp_out="${temp_map_dir}/${i}.txt"
        (
            # 增加 -A 参数模拟浏览器，防止被拦截
            if curl -sLf --connect-timeout 20 --retry 3 -A "Mozilla/5.0 (compatible; MihomoRuleConverter/1.0)" "$url" > "$temp_out"; then
                # 确保文件最后一行有换行符
                [ -n "$(tail -c1 "$temp_out")" ] && echo "" >> "$temp_out"
            else
                # 下载失败时不报错退出，但删除空文件
                rm -f "$temp_out"
            fi
        ) &
        pids+=($!)
        ((i++))
    done

    wait "${pids[@]}"
    
    # 检查是否有成功下载的文件
    if compgen -G "${temp_map_dir}/*.txt" > /dev/null; then
        cat "${temp_map_dir}"/*.txt > "$output_file"
    else
        # 如果全部失败，创建一个空文件防止报错
        touch "$output_file"
    fi
    rm -rf "$temp_map_dir"
}

# 2. 域名标准化
# 优化：合并 sed/grep/awk 管道，提升性能
normalize_domain() {
    tr -d '\r' \
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
    | awk '
    /\./ && !/\*/ && /^[a-z0-9_]/ && !/^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/ {
        print $0
    }'
}

# 3. 关键词过滤
# 优化：使用 mktemp 防止并行冲突
apply_keyword_filter() {
    local input=$1
    local output=$2
    local keyword_file="scripts/exclude-keyword.txt"
    
    if [ -f "$keyword_file" ] && [ -s "$keyword_file" ]; then
        local tmp_kw
        tmp_kw=$(mktemp "${WORK_DIR}/kw.XXXXXX")
        tr 'A-Z' 'a-z' < "$keyword_file" > "$tmp_kw"
        grep -v -f "$tmp_kw" "$input" > "$output"
        rm -f "$tmp_kw"
    else
        cp "$input" "$output"
    fi
}

# 4. 智能覆盖去重 (Python 版)
# 逻辑：+.domain 覆盖 domain/sub.domain
# 优化：动态生成 Python 脚本，利用列表比较实现完美层级去重
optimize_smart_self() {
    local input=$1
    local output=$2
    
    # 使用通用 mktemp 格式创建 Python 脚本
    local dedup_script
    dedup_script=$(mktemp "${WORK_DIR}/dedup_script.XXXXXX.py")

    cat << 'EOF' > "$dedup_script"
import sys

def main():
    lines = []
    try:
        # 稳健地读取所有行
        lines = sys.stdin.read().splitlines()
    except Exception:
        pass

    data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
            
        clean = line
        is_wildcard = False
        if clean.startswith("+."):
            clean = clean[2:]
            is_wildcard = True
        elif clean.startswith("."):
            clean = clean[1:]
            is_wildcard = True
        
        parts = clean.split(".")
        parts.reverse()
        
        # 只有有效的域名才处理
        if len(parts) > 0:
            data.append({
                'parts': parts,
                'is_wildcard': is_wildcard,
                'original': line,
                'sort_key': (parts, not is_wildcard)
            })

    data.sort(key=lambda x: x['sort_key'])

    last_wildcard_parts = None
    for item in data:
        current_parts = item['parts']
        is_covered = False
        if last_wildcard_parts:
            # 判断是否是上一个通配符域名的子域名
            if len(current_parts) >= len(last_wildcard_parts):
                if current_parts[:len(last_wildcard_parts)] == last_wildcard_parts:
                    is_covered = True
        
        if not is_covered:
            print(item['original'])
            if item['is_wildcard']:
                last_wildcard_parts = current_parts
            else:
                last_wildcard_parts = None

if __name__ == "__main__":
    main()
EOF

    # 检查输入文件是否存在且不为空
    if [ -s "$input" ]; then
        python3 "$dedup_script" < "$input" > "$output"
    else
        touch "$output"
    fi
    
    rm -f "$dedup_script"
}

# 5. 双向白名单过滤
# 优化：使用 mktemp 防止并行冲突
apply_advanced_whitelist_filter() {
    local block_in=$1
    local allow_in=$2
    local final_out=$3
    
    local tmp_algo_input
    tmp_algo_input=$(mktemp "${WORK_DIR}/algo_input.XXXXXX")

    awk -v OFS="\t" '{ 
        key=$0; reversed=""; len=length(key);
        for(i=len;i>=1;i--) reversed=reversed substr(key,i,1);
        print reversed, 1 
    }' "$allow_in" > "$tmp_algo_input"

    awk -v OFS="\t" '{ 
        original=$0; pure=original;
        sub(/^\+\./,"",pure); sub(/^\./,"",pure);
        reversed=""; len=length(pure);
        for(i=len;i>=1;i--) reversed=reversed substr(pure,i,1);
        print reversed, 0, original 
    }' "$block_in" >> "$tmp_algo_input"

    sort -t $'\t' "$tmp_algo_input" | awk -F "\t" '
    {
        key = $1; type = $2; original = $3
        if (active_white_root != "" && index(key, active_white_root ".") == 1) { next }
        is_child_or_equal = (buffered_key != "" && (index(key, buffered_key ".") == 1 || key == buffered_key));
        if (is_child_or_equal) {
            if (type == 1) { buffered_key = ""; buffered_line = ""; active_white_root = key }
        } else {
            if (buffered_line != "") print buffered_line
            if (type == 1) { active_white_root = key; buffered_key = ""; buffered_line = "" }
            else { buffered_key = key; buffered_line = original; active_white_root = "" }
        }
    }
    END { if (buffered_line != "") print buffered_line }' > "$final_out"

    rm -f "$tmp_algo_input"
}

# 6. 输出封装
finalize_output() {
    local src=$1
    local dst=$2
    local mode=$3

    if [ -s "$src" ]; then
        sort -u "$src" -o "$src"
        if [ "$mode" == "add_prefix" ]; then
            sed 's/^/+./' "$src" > "${src}.tmp" && mv "${src}.tmp" "$src"
        fi
        
        local count=$(wc -l < "$src")
        local date=$(date +"%Y-%m-%d %H:%M:%S")
        sed -i "1i # Count: $count\n# Updated: $date" "$src"
        
        if [ -n "$dst" ] && CHECK_MIHOMO; then
            echo "🔄 [${BASHPID:-$$}] 转换 $dst..."
            mihomo convert-ruleset domain text "$src" "$dst"
        fi
        echo "📊 [${BASHPID:-$$}] 完成: $dst (行数: $count)"
    else
        echo "⚠️  [${BASHPID:-$$}] 警告: $dst 源文件为空，跳过生成。"
    fi
}

# ================= 资源配置 =================

ALLOW_URLS=(
    "https://raw.githubusercontent.com/Cats-Team/AdRules/refs/heads/script/script/allowlist.txt"
    "https://raw.githubusercontent.com/zoonderkins/blahdns/refs/heads/master/hosts/whitelist.txt"
    "https://raw.githubusercontent.com/AdguardTeam/AdGuardSDNSFilter/master/Filters/exceptions.txt"
)

# ================= 模块定义 =================

generate_ads-reject() {
    local mod_dir="${WORK_DIR}/ads"
    mkdir -p "$mod_dir"
    echo "=== 🚀 [ADS] 启动 ==="

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

    download_files_parallel "${mod_dir}/raw_ads.txt" "${BLOCK_URLS[@]}"
    download_files_parallel "${mod_dir}/raw_allow.txt" "${ALLOW_URLS[@]}"

    tr 'A-Z' 'a-z' < "${mod_dir}/raw_ads.txt" | grep -vE '^\s*@@' | normalize_domain | sort -u > "${mod_dir}/clean_ads.txt"
    apply_keyword_filter "${mod_dir}/clean_ads.txt" "${mod_dir}/filter_ads.txt"

    local_allow="scripts/exclude-keyword.txt"
    if [ -f "$local_allow" ]; then
        grep -vE '^\s*($|#)' "$local_allow" | tr 'A-Z' 'a-z' > "${mod_dir}/local_allow_clean.txt"
        cat "${mod_dir}/raw_allow.txt" "${mod_dir}/local_allow_clean.txt" > "${mod_dir}/merged_allow_raw.txt"
    else
        cp "${mod_dir}/raw_allow.txt" "${mod_dir}/merged_allow_raw.txt"
    fi
    tr 'A-Z' 'a-z' < "${mod_dir}/merged_allow_raw.txt" | normalize_domain | sort -u > "${mod_dir}/clean_allow.txt"

    optimize_smart_self "${mod_dir}/filter_ads.txt" "${mod_dir}/opt_ads.txt"
    optimize_smart_self "${mod_dir}/clean_allow.txt" "${mod_dir}/opt_allow.txt"

    apply_advanced_whitelist_filter "${mod_dir}/opt_ads.txt" "${mod_dir}/opt_allow.txt" "${mod_dir}/final_ads.txt"

    finalize_output "${mod_dir}/final_ads.txt" "ADs_merged.mrs" "add_prefix"
    mv "${mod_dir}/final_ads.txt" "ADs_merged.txt"
}

generate_ai() {
    local mod_dir="${WORK_DIR}/ai"
    mkdir -p "$mod_dir"
    echo "=== 🚀 [AI] 启动 ==="

    local AI_URLS=(
        "https://github.com/MetaCubeX/meta-rules-dat/raw/meta/geo/geosite/category-ai-!cn.list"
        "https://ruleset.skk.moe/List/non_ip/ai.conf"
        "https://github.com/DustinWin/ruleset_geodata/raw/mihomo-ruleset/ai.list"
        "https://raw.githubusercontent.com/ConnersHua/RuleGo/refs/heads/master/Surge/Ruleset/Extra/AI.list"
    )
    download_files_parallel "${mod_dir}/raw_ai.txt" "${AI_URLS[@]}"
    tr 'A-Z' 'a-z' < "${mod_dir}/raw_ai.txt" | normalize_domain | sort -u > "${mod_dir}/clean_ai.txt"
    
    optimize_smart_self "${mod_dir}/clean_ai.txt" "${mod_dir}/opt_ai.txt"
    
    finalize_output "${mod_dir}/opt_ai.txt" "AIs_merged.mrs" "add_prefix"
    mv "${mod_dir}/opt_ai.txt" "AIs_merged.txt"
}

generate_fakeip() {
    local mod_dir="${WORK_DIR}/fakeip"
    mkdir -p "$mod_dir"
    echo "=== 🚀 [FakeIP] 启动 ==="

    local FAKE_IP_URLS=(
        "https://raw.githubusercontent.com/vernesong/OpenClash/refs/heads/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list"
        "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list"
        "https://raw.githubusercontent.com/DustinWin/ruleset_geodata/refs/heads/mihomo-ruleset/fakeip-filter.list"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/fake-ip-addon.txt"
        "https://ruleset.skk.moe/Internal/clash_fake_ip_filter.yaml"
    )
    download_files_parallel "${mod_dir}/raw_fakeip_dl.txt" "${FAKE_IP_URLS[@]}"
    
    # 【修复】使用 4 个反斜杠正确转义，消除 tr warning
    tr 'A-Z' 'a-z' < "${mod_dir}/raw_fakeip_dl.txt" \
    | grep -vE '^\s*(dns:|fake-ip-filter:)' \
    | sed 's/^\s*-\s*//' \
    | tr -d "\"'\\\\" \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | grep -vE '^\s*($|#)' \
    | sort -u > "${mod_dir}/clean_fakeip.txt"

    optimize_smart_self "${mod_dir}/clean_fakeip.txt" "${mod_dir}/final_fakeip.txt"

    finalize_output "${mod_dir}/final_fakeip.txt" "Fake_IP_Filter_merged.mrs" "none"
    mv "${mod_dir}/final_fakeip.txt" "Fake_IP_Filter_merged.txt"
}

generate_ads-drop() {
    local mod_dir="${WORK_DIR}/drop"
    mkdir -p "$mod_dir"
    echo "=== 🚀 [Drop] 启动 ==="

    local BLOCK_URLS=(
        "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/rules/Custom_Reject-drop.txt"
    )
    download_files_parallel "${mod_dir}/raw_rd.txt" "${BLOCK_URLS[@]}"

    cat "${mod_dir}/raw_rd.txt" \
    | tr -d '\r' | tr 'A-Z' 'a-z' | sed -E '
        /^[[:space:]]*#/d; /skk\.moe/d; /^$/d;
        s/^domain-suffix,/+./; s/^domain,//;
        /^\+\.$/d; s/^[[:space:]]*//; s/[[:space:]]*$//
    ' | sort -u > "${mod_dir}/clean_rd.txt"

    # 复用或下载白名单
    download_files_parallel "${mod_dir}/raw_allow_temp.txt" "${ALLOW_URLS[@]}"
    
    local_allow="scripts/exclude-keyword.txt"
    if [ -f "$local_allow" ]; then
        grep -vE '^\s*($|#)' "$local_allow" | tr 'A-Z' 'a-z' > "${mod_dir}/local_allow_clean.txt"
        cat "${mod_dir}/raw_allow_temp.txt" "${mod_dir}/local_allow_clean.txt" > "${mod_dir}/merged_allow_raw.txt"
    else
        cp "${mod_dir}/raw_allow_temp.txt" "${mod_dir}/merged_allow_raw.txt"
    fi
    tr 'A-Z' 'a-z' < "${mod_dir}/merged_allow_raw.txt" | normalize_domain | sort -u > "${mod_dir}/clean_rd_allow.txt"

    apply_advanced_whitelist_filter "${mod_dir}/clean_rd.txt" "${mod_dir}/clean_rd_allow.txt" "${mod_dir}/final_rd.txt"

    finalize_output "${mod_dir}/final_rd.txt" "Reject_Drop_merged.mrs" "none"
    mv "${mod_dir}/final_rd.txt" "Reject_Drop_merged.txt"
}

generate_cn() {
    local mod_dir="${WORK_DIR}/cn"
    mkdir -p "$mod_dir"
    echo "=== 🚀 [CN] 启动 ==="
    
    local CN_URLS_1=( "https://static-file-global.353355.xyz/rules/cn-additional-list.txt" )
    local CN_URLS_2=( "https://ruleset.skk.moe/Clash/non_ip/domestic.txt" )

    download_files_parallel "${mod_dir}/raw_cn_1.txt" "${CN_URLS_1[@]}"
    download_files_parallel "${mod_dir}/raw_cn_2.txt" "${CN_URLS_2[@]}"

    cat "${mod_dir}/raw_cn_1.txt" | tr -d '\r' | tr 'A-Z' 'a-z' \
    | sed '/^[[:space:]]*#/d; /^$/d; s/^[[:space:]]*//; s/[[:space:]]*$//; s/^/+./' \
    > "${mod_dir}/clean_cn_1.txt"

    cat "${mod_dir}/raw_cn_2.txt" | tr -d '\r' | tr 'A-Z' 'a-z' \
    | grep -v "skk\.moe" | sed '/^[[:space:]]*#/d; /^$/d' \
    | grep -E '^(domain-suffix|domain),' \
    | sed 's/^domain-suffix,/+./; s/^domain,//' \
    | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' \
    > "${mod_dir}/clean_cn_2.txt"

    cat "${mod_dir}/clean_cn_1.txt" "${mod_dir}/clean_cn_2.txt" > "${mod_dir}/merged_cn_raw.txt"
    optimize_smart_self "${mod_dir}/merged_cn_raw.txt" "${mod_dir}/final_cn.txt"

    finalize_output "${mod_dir}/final_cn.txt" "CN_merged.mrs" "none"
    mv "${mod_dir}/final_cn.txt" "CN_merged.txt"
}

# ================= 主程序入口 =================

main() {
    local target=${1:-all}
    case "$target" in
        ads-reject) generate_ads-reject ;;
        ais) generate_ai ;;
        fakeip) generate_fakeip ;;
        ads-drop) generate_ads-drop ;;
        cn) generate_cn ;;
        all)
            echo "⚡️ 启动全局并行处理..."
            generate_ads-reject &
            generate_ai &
            generate_fakeip &
            generate_ads-drop &
            generate_cn &
            
            wait
            echo "🎉 所有任务执行完毕！"
            ;;
        *)
            echo "用法: $0 [ads-reject|ais|fakeip|ads-drop|cn|all]"
            exit 1
            ;;
    esac
}

main "$@"
