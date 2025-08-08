#!/bin/bash
# 函数：生成 ADs_merged.txt
generate_ads_merged() {
  # 下载并合并规则
  curl -skL https://raw.githubusercontent.com/pmkol/easymosdns/rules/ad_domain_list.txt >>rules.txt
  echo "" >>rules.txt
  curl -skL https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/rules/Custom_Reject.list >>rules.txt
  echo "" >>rules.txt
  #curl -skL https://adrules.top/adrules_domainset.txt | sed 's/+\.//g' >>rules.txt
  #curl -skL https://github.com/Loyalsoldier/v2ray-rules-dat/raw/release/reject-list.txt >>rules.txt
  #curl -sSL https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=1&mimetype=plaintext | perl -ne '/^127\.0\.0\.1\s([-_0-9a-zA-Z]+(\.[-_0-9a-zA-Z]+){1,64})$/ && print "$1\n"' >> rules.txt
  #curl -sSL https://someonewhocares.org/hosts/hosts | perl -ne '/^127\.0\.0\.1\s([-_0-9a-zA-Z]+(\.[-_0-9a-zA-Z]+){1,64})/ && print "$1\n"' | sed '1d' >> rules.txt
  curl -skL https://adguardteam.github.io/HostlistsRegistry/assets/filter_3.txt | sed 's/^||//g' | sed 's/\^$//g' >> rules.txt
  echo "" >>rules.txt
  curl -skL https://adguardteam.github.io/HostlistsRegistry/assets/filter_4.txt | perl -ne '/^0\.0\.0\.0\s([-_0-9a-zA-Z]+(\.[-_0-9a-zA-Z]+){1,64})/ && print "$1\n"' | sed '1d' >> rules.txt
  echo "" >>rules.txt
  curl -skL https://github.com/TG-Twilight/AWAvenue-Ads-Rule/raw/main/Filters/AWAvenue-Ads-Rule-Surge-RULE-SET.list | sed 's/^DOMAIN,//g' >>rules.txt
  echo "" >>rules.txt
  curl -skL https://github.com/limbopro/Adblock4limbo/raw/main/rule/Surge/Adblock4limbo_surge.list | sed 's/^DOMAIN,//g' | sed 's/^DOMAIN-SUFFIX,//g' | sed 's/,reject$//g' >>rules.txt
  #curl -skL https://ruleset.skk.moe/Clash/domainset/reject.txt | sed 's/+\.//g' >>rules.txt
  # adobe验证规则
  echo "" >>rules.txt
  curl -skL https://a.dove.isdumb.one/pihole.txt >>rules.txt

  # 移除注释和空行
  cat rules.txt | sed '/^[#!]/d' >combined_raw.txt

  # 标准化域名
  sed -E 's/^[\+\*\.]+//g' combined_raw.txt | grep -v '^$' | tr '[:upper:]' '[:lower:]' | sed 's/[[:space:]]*$//' > normalized.txt

  # 排序并去重
  sort normalized.txt | uniq >unique_domains.txt
  
  # 关键词文件过滤
  grep -v -f "scripts/exclude-keyword.txt" unique_domains.txt | grep -v '^DOMAIN-KEYWORD' | grep -v '^DOMAIN' >filtered_domains.txt

  # 处理域名：添加 +. 前缀（DOMAIN-KEYWORD 除外）
  awk '{
      if ($0 ~ /^DOMAIN-KEYWORD/) {
          print $0
      } else {
          print "+." $0
      }
  }' filtered_domains.txt >ADs_merged.txt

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
  curl -skL https://github.com/ForestL18/rules-dat/raw/mihomo/geo/domain/ai-domain.list >>ai.txt
  echo "" >>ai.txt
  curl -skL https://github.com/MetaCubeX/meta-rules-dat/raw/meta/geo/geosite/category-ai-!cn.list >>ai.txt
  echo "" >>ai.txt
  curl -skL https://ruleset.skk.moe/List/non_ip/ai.conf | sed 's/^DOMAIN,//g' | sed 's/^DOMAIN-SUFFIX,//g' | sed '/^#/d' >>ai.txt
  echo "" >>ai.txt
  curl -skL https://github.com/DustinWin/ruleset_geodata/raw/mihomo-ruleset/ai.list >>ai.txt

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
  curl -skL https://raw.githubusercontent.com/DustinWin/ruleset_geodata/refs/heads/mihomo-ruleset/fakeip-filter.list >>Fake_IP_Fliter.txt
  echo "" >>Fake_IP_Fliter.txt
  curl -skL https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/fake-ip-addon.txt >>Fake_IP_Fliter.txt

  # 移除注释和空行
  cat Fake_IP_Fliter.txt | sed '/^[#!]/d' >Fake_IP_Fliter_combined_raw.txt

  # 标准化域名
  sed -E 's/^[\+\*\.]+//g' Fake_IP_Fliter_combined_raw.txt | grep -v '^$' | tr '[:upper:]' '[:lower:]' | sed 's/[[:space:]]*$//' > Fake_IP_Fliter_normalized.txt

  # 排序并去重
  sort Fake_IP_Fliter_normalized.txt | uniq >Fake_IP_Fliter_domains.txt

  # 处理域名：添加 +. 前缀（DOMAIN-KEYWORD 除外）
  awk '{
      if ($0 ~ /^DOMAIN-KEYWORD/) {
          print $0
      } else {
          print "+." $0
      }
  }' Fake_IP_Fliter_domains.txt >Fake_IP_Fliter_merged.txt

  mihomo convert-ruleset domain text Fake_IP_Fliter_merged.txt Fake_IP_Fliter_merged.mrs

  # Surge compatible
  sed -i 's/+./DOMAIN-SUFFIX,/g' Fake_IP_Fliter_merged.txt

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
