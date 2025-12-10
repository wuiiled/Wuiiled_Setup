#!/bin/bash
# 函数：生成 ADs_merged.txt
generate_ads_merged() {
    # 最终输出文件
    OUTPUT_FILE="ADs_merged.txt"

    # 临时工作目录
    WORK_DIR=$(mktemp -d)
    trap "rm -rf ${WORK_DIR}" EXIT

    # 拦截规则源 (Blocklist URLs)
    BLOCK_URLS=(
        "https://raw.githubusercontent.com/pmkol/easymosdns/rules/ad_domain_list.txt"
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/rules/Custom_Reject.txt"
        "https://adrules.top/adrules_domainset.txt"
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt"
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_3.txt"
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_4.txt"
        "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-Surge-RULE-SET.list"
        "https://raw.githubusercontent.com/ForestL18/rules-dat/mihomo/geo/classical/pcdn.list"
        "https://raw.githubusercontent.com/ForestL18/rules-dat/refs/heads/mihomo/geo/classical/reject.list"
        "https://a.dove.isdumb.one/pihole.txt"
    )

    # 白名单源 (Allowlist URLs)
    ALLOW_URLS=(
        "https://raw.githubusercontent.com/Cats-Team/AdRules/refs/heads/script/script/allowlist.txt"
        "https://raw.githubusercontent.com/mawenjian/china-cdn-domain-whitelist/refs/heads/master/china-cdn-domain-whitelist.txt"
        "https://raw.githubusercontent.com/zoonderkins/blahdns/refs/heads/master/hosts/whitelist.txt"
    )

    # ================= 功能函数 =================

    download_files() {
        local output_file=$1
        shift
        local urls=("$@")
        
        for url in "${urls[@]}"; do
            echo "⬇️  正在下载: $url"
            curl -sL --connect-timeout 15 --retry 3 "$url" >> "$output_file"
            echo "" >> "$output_file"
        done
    }

    # 核心清洗函数 (包含 IP 过滤)
    normalize_domain() {
        # 1. 转小写 + 移除 Windows 换行符
        tr 'A-Z' 'a-z' | tr -d '\r' \
        | sed 's/[\$#].*//g' \
        | sed -E 's/^(0\.0\.0\.0|127\.0\.0\.1)[[:space:]]+//g' \
        | sed 's/||//g; s/\^//g' \
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
    # 清洗逻辑详解：
    # grep -vE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' : 【新功能】使用正则剔除 IPv4 地址 (如 192.168.1.1)
    # grep -v "*"           : 剔除包含通配符的行
    # grep -v "[^a-z0-9.-]" : 剔除包含乱码/特殊符号的行
    # grep -E '^[a-z0-9]'   : 开头必须是字母或数字
    # grep -E '[a-z0-9]$'   : 结尾必须是字母或数字
    # awk '/\./'            : 必须包含点 (排除纯单词)

    process_blocklist() {
        local input_file=$1
        local output_block=$2
        local output_allow_extra=$3

        echo "🧹 正在处理拦截规则..."
        
        # 提取 @@ 规则 (AdBlock 白名单) -> 清洗后存入临时白名单
        grep "^@@" "$input_file" | sed 's/^@@//g' | normalize_domain > "$output_allow_extra"

        # 提取正常规则 -> 清洗后存入拦截列表
        grep -v "^@@" "$input_file" | normalize_domain | sort -u > "$output_block"
    }

    optimize_list() {
        local input_file=$1
        local output_file=$2

        echo "🧠 正在智能去重 (主域名覆盖子域名)..."
        cat "$input_file" \
        | rev | sort | awk 'NR==1 {prev=$0; print; next} {if (index($0, prev ".") != 1) {print; prev=$0}}' | rev | sort > "$output_file"
    }

    advanced_whitelist_filter() {
        local block_file=$1
        local allow_file=$2
        local final_file=$3

        echo "🛡️  正在应用白名单过滤..."

        # 准备白名单：反转 + 加标记
        cat "$allow_file" | rev | sed 's/$/!/' > "${WORK_DIR}/allow_rev_tagged.txt"
        # 准备黑名单：反转
        cat "$block_file" | rev > "${WORK_DIR}/block_rev.txt"

        # 排序并过滤
        cat "${WORK_DIR}/allow_rev_tagged.txt" "${WORK_DIR}/block_rev.txt" \
        | sort \
        | awk '
            /\!$/ { root = substr($0, 1, length($0)-1); next; }
            {
                if ($0 == root) next;
                if (root != "" && index($0, root ".") == 1) next;
                print;
            }
        ' \
        | rev > "$final_file"
    }

    add_final_prefix() {
        local input_file=$1
        local output_file=$2
        
        echo "✨ 正在添加最终前缀 (+.)..."
        sed 's/^/+./' "$input_file" > "$output_file"
    }

    # ================= 主程序流程 =================

    echo "=== 脚本开始运行 ==="

    # 1. 下载
    download_files "${WORK_DIR}/raw_block_all.txt" "${BLOCK_URLS[@]}"
    download_files "${WORK_DIR}/raw_allow_all.txt" "${ALLOW_URLS[@]}"

    # 2. 清洗黑名单 (分离 @@)
    # 注意：process_blocklist 内部调用了 normalize_domain，会自动去除 IP
    process_blocklist "${WORK_DIR}/raw_block_all.txt" "${WORK_DIR}/clean_block.txt" "${WORK_DIR}/raw_allow_extra.txt"

    # 3. 清洗并合并白名单
    # 【满足要求1】：白名单先经过 normalize_domain (去 IP、去修饰符) 成为纯域名后，才会被用于后续过滤
    cat "${WORK_DIR}/raw_allow_all.txt" "${WORK_DIR}/raw_allow_extra.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_allow.txt"

    # 4. 自我优化去重 (此时全是纯域名，IP已被剔除)
    optimize_list "${WORK_DIR}/clean_block.txt" "${WORK_DIR}/opt_block.txt"
    optimize_list "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/opt_allow.txt"

    # 5. 白名单过滤 (使用清洗过的白名单 过滤 清洗过的黑名单)
    advanced_whitelist_filter "${WORK_DIR}/opt_block.txt" "${WORK_DIR}/opt_allow.txt" "${WORK_DIR}/final_pure.txt"

    # 6. 添加前缀 (+.) 并输出
    add_final_prefix "${WORK_DIR}/final_pure.txt" "$OUTPUT_FILE"

    # 统计
    COUNT=$(wc -l < "$OUTPUT_FILE")
    echo "✅ 任务完成！"
    echo "📂 输出文件: $OUTPUT_FILE"
    echo "📊 最终规则行数: $COUNT"

    # Surge compatible
    #sed -i 's/+./DOMAIN-SUFFIX,/g' ADs_merged.txt

    mihomo convert-ruleset domain text ADs_merged.txt ADs_merged.mrs

    # 添加计数和时间戳
    count=$(wc -l <ADs_merged.txt)
    current_date=$(date +"%Y-%m-%d %H:%M:%S")
    temp_file=$(mktemp)
    echo "# Count: $count, Updated: $current_date" >"$temp_file"
    cat ADs_merged.txt >>"$temp_file"
    mv "$temp_file" ADs_merged.txt
  }

# 函数：生成 AIs_merged.txt
generate_ais_merged() {
  # 下载并合并规则
  #curl -skL https://github.com/ForestL18/rules-dat/raw/mihomo/geo/domain/ai-domain.list >>ai.txt
  #echo "" >>ai.txt
  curl -skL https://github.com/MetaCubeX/meta-rules-dat/raw/meta/geo/geosite/category-ai-!cn.list >>ai.txt
  echo "" >>ai.txt
  curl -skL https://ruleset.skk.moe/List/non_ip/ai.conf | sed 's/^DOMAIN,//g' | sed 's/^DOMAIN-SUFFIX,//g' | sed '/^#/d' >>ai.txt
  echo "" >>ai.txt
  curl -skL https://github.com/DustinWin/ruleset_geodata/raw/mihomo-ruleset/ai.list >>ai.txt
  echo "" >>ai.txt
  curl -skL https://raw.githubusercontent.com/ConnersHua/RuleGo/refs/heads/master/Surge/Ruleset/Extra/AI.list | sed 's/^DOMAIN,//g' | sed 's/^DOMAIN-SUFFIX,//g' | sed '/^#/d' >>ai.txt

  # 移除注释和空行
  cat ai.txt | sed '/^#/d' >combined_raw.txt

  # 标准化域名
  sed -E 's/^[\+\*\.]+//g' combined_raw.txt | grep -v '^$' >normalized.txt

  # 排序并去重
  sort normalized.txt | uniq >unique_domains.txt

  # 关键词文件过滤
  grep -v -f "scripts/exclude-keyword.txt" unique_domains.txt >filtered_domains.txt

  # 处理域名：添加 +. 前缀（DOMAIN-KEYWORD, 和 DOMAIN, 除外）
  awk '{
      if ($0 ~ /^DOMAIN-KEYWORD,/ || $0 ~ /^DOMAIN,/) {
          print $0
      } else {
          print "+." $0
      }
  }' filtered_domains.txt >AIs_merged.txt

  mihomo convert-ruleset domain text AIs_merged.txt AIs_merged.mrs

  # Surge compatible
  sed -i 's/+./DOMAIN-SUFFIX,/g' AIs_merged.txt

  # 添加计数和时间戳
  count=$(wc -l <AIs_merged.txt)
  current_date=$(date +"%Y-%m-%d %H:%M:%S")
  temp_file=$(mktemp)
  echo "# Count: $count, Updated: $current_date" >"$temp_file"
  cat AIs_merged.txt >>"$temp_file"
  mv "$temp_file" AIs_merged.txt
}

# 函数：生成 Fake_IP_Fliter_merged.txt
generate_Fake_IP_Fliter_merged() {
  # 下载并合并规则
  echo "" >>Fake_IP_Fliter.txt
  curl -skL https://raw.githubusercontent.com/vernesong/OpenClash/refs/heads/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list >>Fake_IP_Fliter.txt
  echo "" >>Fake_IP_Fliter.txt
  curl -skL https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list >>Fake_IP_Fliter.txt
  echo "" >>Fake_IP_Fliter.txt
  curl -skL https://raw.githubusercontent.com/DustinWin/ruleset_geodata/refs/heads/mihomo-ruleset/fakeip-filter.list >>Fake_IP_Fliter.txt
  echo "" >>Fake_IP_Fliter.txt
  curl -skL https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/fake-ip-addon.txt >>Fake_IP_Fliter.txt

  # 移除注释和空行
  #cat Fake_IP_Fliter.txt | sed '/^[#!]/d' >Fake_IP_Fliter_combined_raw.txt

  # 移除注释和空行并标准化域名
  #sed -E 's/^[\+\*\.]+//g' Fake_IP_Fliter_combined_raw.txt | grep -v '^$' | tr '[:upper:]' '[:lower:]' | sed 's/[[:space:]]*$//' > Fake_IP_Fliter_normalized.txt
  tr -d '\r' < Fake_IP_Fliter.txt | sed -E '/^[[:space:]]*(#|$)/d; s/^[[:space:]]+//; s/[[:space:]]+$//' > Fake_IP_Fliter_combined_clean.txt

  # 排序并去重
  sort Fake_IP_Fliter_combined_clean.txt | uniq >Fake_IP_Fliter_merged.txt

  # 处理域名：添加 +. 前缀（DOMAIN-KEYWORD 除外）
  #awk '{
  #    if ($0 ~ /^DOMAIN-KEYWORD/) {
  #        print $0
  #    } else {
  #        print "+." $0
  #    }
  #}' Fake_IP_Fliter_domains.txt >Fake_IP_Fliter_merged.txt

  mihomo convert-ruleset domain text Fake_IP_Fliter_merged.txt Fake_IP_Fliter_merged.mrs

  # Surge compatible
  #sed -i 's/+./DOMAIN-SUFFIX,/g' Fake_IP_Fliter_merged.txt

  # 添加计数和时间戳
  count=$(wc -l <Fake_IP_Fliter_merged.txt)
  current_date=$(date +"%Y-%m-%d %H:%M:%S")
  temp_file=$(mktemp)
  echo "# Count: $count, Updated: $current_date" >"$temp_file"
  cat Fake_IP_Fliter_merged.txt >>"$temp_file"
  mv "$temp_file" Fake_IP_Fliter_merged.txt
}

# 主函数
main() {
  if [ "$1" == "ads" ]; then
    generate_ads_merged
  elif [ "$1" == "ais" ]; then
    generate_ais_merged
  elif [ "$1" == "fakeip" ]; then
    generate_Fake_IP_Fliter_merged
  else
    echo "Usage: $0 [ads|ais|fakeip]"
    exit 1
  fi
}

# 调用主函数
main "$@"
