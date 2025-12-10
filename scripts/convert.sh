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
        local urls=("$@")
        local output_file=$1
        # 移除第一个参数(输出文件名)，保留剩下的作为URL数组
        shift
        local url_list=("$@")
        
        for url in "${url_list[@]}"; do
            echo "⬇️  正在下载: $url"
            curl -sL --connect-timeout 10 --retry 3 "$url" >> "$output_file"
            echo "" >> "$output_file" # 确保文件末尾有换行，防止拼接错误
        done
    }

    clean_domains() {
        local input_file=$1
        local output_file=$2

        echo "🧹 正在清洗规则..."
        
        # 解释 sed/grep 管道操作：
        # 1. dos2unix: 移除 Windows 换行符 \r
        # 2. grep -v: 移除包含 DOMAIN-KEYWORD 的行
        # 3. sed 移除注释: 移除行首的 ! 和 #
        # 4. sed 移除修饰符: 移除 || 和 ^
        # 5. sed 移除前缀: 移除 DOMAIN-SUFFIX, 和 DOMAIN,
        # 6. sed 移除行尾注释: 移除行内 $ 或 # 及其后面的内容
        # 7. tr: 转小写 (方便去重)
        # 8. sed 清理: 移除行首行尾空格
        # 9. awk: 过滤只包含点号的合法域名 (排除纯单词)
        
        cat "$input_file" \
        | tr -d '\r' \
        | grep -v "DOMAIN-KEYWORD" \
        | sed 's/^[!#].*//g' \
        | sed 's/||//g; s/\^//g' \
        | sed 's/DOMAIN-SUFFIX,//g; s/DOMAIN,//g' \
        | sed 's/[\$#].*//g' \
        | tr 'A-Z' 'a-z' \
        | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
        | awk '/\./ {print $0}' \
        | sort -u > "$output_file"
    }

    optimize_domains() {
        local input_file=$1
        local output_file=$2

        echo "🧠 正在执行智能去重 (主域名覆盖子域名)..."
        
        # 算法说明：
        # 1. rev: 将域名反转 (google.com -> moc.elgoog)
        # 2. sort: 排序。这样 ad.google.com (moc.elgoog.da) 会紧挨着 google.com (moc.elgoog)
        # 3. awk: 比较当前行是否以"上一行+."开头。如果是，说明是子域名，丢弃。
        # 4. rev: 翻转回来
        
        cat "$input_file" \
        | rev \
        | sort \
        | awk 'NR==1 {prev=$0; print; next} {if (index($0, prev ".") != 1) {print; prev=$0}}' \
        | rev \
        | sort > "$output_file"
    }

    apply_whitelist() {
        local block_file=$1
        local allow_file=$2
        local final_file=$3

        echo "🛡️  正在应用白名单过滤..."
        
        # 使用 awk 读取白名单到数组，然后遍历黑名单进行过滤
        # 比 grep -vf 快得多，且不需要两个文件都严格排序
        
        awk 'NR==FNR {whitelist[$0]=1; next} !whitelist[$0]' "$allow_file" "$block_file" > "$final_file"
    }

    # ================= 主程序流程 =================

    echo "=== 脚本开始运行 ==="

    # 1. 下载并合并拦截规则
    download_files "${WORK_DIR}/raw_block.txt" "${BLOCK_URLS[@]}"

    # 2. 下载并合并白名单规则
    download_files "${WORK_DIR}/raw_allow.txt" "${ALLOW_URLS[@]}"

    # 3. 清洗拦截规则
    clean_domains "${WORK_DIR}/raw_block.txt" "${WORK_DIR}/clean_block.txt"

    # 4. 清洗白名单 (白名单也必须清洗，否则格式对不上无法剔除)
    clean_domains "${WORK_DIR}/raw_allow.txt" "${WORK_DIR}/clean_allow.txt"

    # 5. 智能优化拦截规则 (去除被包含的子域名)
    optimize_domains "${WORK_DIR}/clean_block.txt" "${WORK_DIR}/optimized_block.txt"

    # 6. 应用白名单剔除
    apply_whitelist "${WORK_DIR}/optimized_block.txt" "${WORK_DIR}/clean_allow.txt" "$OUTPUT_FILE"

    # 统计
    COUNT=$(wc -l < "$OUTPUT_FILE")
    echo "✅ 任务完成！"
    echo "📂 输出文件: $OUTPUT_FILE"
    echo "📊 最终规则行数: $COUNT"

    mihomo convert-ruleset domain text ADs_merged.txt ADs_merged.mrs

    # Surge compatible
    sed -i 's/+./DOMAIN-SUFFIX,/g' ADs_merged.txt

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
