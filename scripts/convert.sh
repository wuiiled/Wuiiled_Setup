#!/bin/bash
# 函数：生成 ADs_merged.txt
generate_ads_merged() {
  # 下载并合并规则
  curl -skL https://raw.githubusercontent.com/pmkol/easymosdns/rules/ad_domain_list.txt >>rules.txt
  echo "" >>rules.txt
  curl -skL https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/rules/Custom_Reject.txt >>rules.txt
  echo "" >>rules.txt
  #curl -skL https://small.oisd.nl/domainswild2 >>rules.txt
  #echo "" >>rules.txt
  curl -skL https://adrules.top/adrules_domainset.txt | sed 's/+\.//g' >>rules.txt
  echo "" >>rules.txt
  #curl -skL https://github.com/Loyalsoldier/v2ray-rules-dat/raw/release/reject-list.txt >>rules.txt
  #echo "" >>rules.txt
  #curl -sSL https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=1&mimetype=plaintext | perl -ne '/^127\.0\.0\.1\s([-_0-9a-zA-Z]+(\.[-_0-9a-zA-Z]+){1,64})$/ && print "$1\n"' >> rules.txt
  #curl -sSL https://someonewhocares.org/hosts/hosts | perl -ne '/^127\.0\.0\.1\s([-_0-9a-zA-Z]+(\.[-_0-9a-zA-Z]+){1,64})/ && print "$1\n"' | sed '1d' >> rules.txt
  curl -skL https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt | sed 's/[|^]//g' >> rules.txt
  echo "" >>rules.txt
  curl -skL https://adguardteam.github.io/HostlistsRegistry/assets/filter_3.txt | sed 's/^||//g' | sed 's/\^$//g' >> rules.txt
  echo "" >>rules.txt
  curl -skL https://adguardteam.github.io/HostlistsRegistry/assets/filter_4.txt | perl -ne '/^0\.0\.0\.0\s([-_0-9a-zA-Z]+(\.[-_0-9a-zA-Z]+){1,64})/ && print "$1\n"' | sed '1d' >> rules.txt
  echo "" >>rules.txt
  curl -skL https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-Surge-RULE-SET.list | sed -E '/^DOMAIN-KEYWORD,/d; s/^(DOMAIN|DOMAIN-SUFFIX),//g' >>rules.txt
  echo "" >>rules.txt
  #curl -skL https://github.com/limbopro/Adblock4limbo/raw/main/rule/Surge/Adblock4limbo_surge.list | sed 's/^DOMAIN,//g' | sed 's/^DOMAIN-SUFFIX,//g' | sed 's/,reject$//g' >>rules.txt
  #curl -skL https://ruleset.skk.moe/Clash/domainset/reject.txt | sed 's/+\.//g' >>rules.txt
  #echo "" >>rules.txt
  #curl -skL https://ruleset.skk.moe/Clash/domainset/reject_extra.txt | sed 's/+\.//g' >>rules.txt
  #echo "" >>rules.txt
  curl -skL https://raw.githubusercontent.com/ForestL18/rules-dat/mihomo/geo/classical/pcdn.list | sed -E '/^DOMAIN-KEYWORD,/d; s/^(DOMAIN|DOMAIN-SUFFIX),//g' >>rules.txt
  echo "" >>rules.txt
  curl -skL https://raw.githubusercontent.com/ForestL18/rules-dat/refs/heads/mihomo/geo/classical/reject.list | sed -E '/^DOMAIN-KEYWORD,/d; s/^(DOMAIN|DOMAIN-SUFFIX),//g' >>rules.txt
  echo "" >>rules.txt
  # adobe验证规则
  curl -skL https://a.dove.isdumb.one/pihole.txt >>rules.txt
  echo "" >>rules.txt

  # --- BEGIN: 将三份远程白名单加入 exclude.txt（去除空行和#注释并去重） ---
  # 三个远程白名单来源
  whitelist_urls=(
    "https://raw.githubusercontent.com/Cats-Team/AdRules/refs/heads/script/script/allowlist.txt"
    "https://raw.githubusercontent.com/mawenjian/china-cdn-domain-whitelist/refs/heads/master/china-cdn-domain-whitelist.txt"
    "https://raw.githubusercontent.com/zoonderkins/blahdns/refs/heads/master/hosts/whitelist.txt"
  )

  # 下载并清洗（去空行/去注释/去前后空白/小写），将结果与现有 exclude.txt 合并去重写回 exclude.txt
  tmp_whitelist="$(mktemp)"
  curl -fsSL "${whitelist_urls[@]}" 2>/dev/null \
    | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' \
    | sed -E '/^$/d; /^#/d' \
    | tr '[:upper:]' '[:lower:]' \
    | sort -u > "$tmp_whitelist"

  # 如果不存在 exclude.txt，先创建空文件
  : > .tmp_existing_exclude.txt
  [ -f exclude.txt ] && cp exclude.txt .tmp_existing_exclude.txt

  # 合并去重并写回 exclude.txt
  cat .tmp_existing_exclude.txt "$tmp_whitelist" | sort -u > exclude.txt

  # 清理临时文件
  rm -f .tmp_existing_exclude.txt "$tmp_whitelist"
  # --- END: 添加白名单到 exclude.txt ---

  # --- BEGIN: 提取以 @@ 开头的域名并生成 exclude.txt (原脚本逻辑) ---
  # 从 rules.txt 中抽出以 @@ 开头的行，简化为二级域名写入临时排除文件（不会覆盖已生成的 exclude.txt）
  # 提取原始 @@ 条目并做初步清洗
  grep -E '^[[:space:]]*@@' rules.txt \
    | sed 's/^[[:space:]]*@@//' \
    | sed -E 's#^[[:alpha:]]+://##' \
    | sed -E 's#/.*$##' \
    | sed -E 's/[:].*$//' \
    | sed -E 's/^[\*\.\s]+//' \
    | tr '[:upper:]' '[:lower:]' \
    > .tmp_exclude_raw.txt

  if [ -s .tmp_exclude_raw.txt ]; then
    awk -F'.' '
      BEGIN {
        sfx_count = split("co.uk com.cn net.cn org.cn gov.cn ac.uk gov.uk co.jp or.jp", sfx_arr, " ")
      }
      {
        host = $0
        n = NF
        if (n <= 2) {
          print host
          next
        }
        kept = ""
        matched = 0
        for (i = 1; i <= sfx_count; i++) {
          suf = sfx_arr[i]
          suf_regex = "\\." suf "$"
          if (host ~ suf_regex) {
            if (n >= 3) {
              kept = $(n-2) "." $(n-1) "." $n
            } else {
              kept = host
            }
            matched = 1
            break
          }
        }
        if (!matched) {
          kept = $(n-1) "." $n
        }
        print kept
      }
    ' .tmp_exclude_raw.txt | sort -u > .tmp_exclude_from_atat.txt

    # 将提取到的放行域名合并到 exclude.txt 并去重
    cat exclude.txt .tmp_exclude_from_atat.txt | sort -u > .tmp_exclude_combined && mv .tmp_exclude_combined exclude.txt
    rm -f .tmp_exclude_from_atat.txt
  fi

  rm -f .tmp_exclude_raw.txt
  # --- END: 提取 @@ 放行并合并到 exclude.txt ---

  # 移除注释+空行+无法识别规则
  sed -E '/\*/d; s/^[[:space:]]*//; /^[A-Za-z0-9]/!d' rules.txt > combined_raw.txt

  # 标准化域名
  sed -E 's/^[\+\*\.]+//g' combined_raw.txt | grep -v '^$' | tr '[:upper:]' '[:lower:]' | sed 's/[[:space:]]*$//' > normalized.txt

  # 排序并去重
  sort normalized.txt | uniq >unique_domains.txt
  
  # 关键词文件过滤
  #grep -v -f "scripts/exclude-keyword.txt" unique_domains.txt | grep -v '^DOMAIN-KEYWORD' | grep -v '^DOMAIN' >filtered_domains.txt

  # 在原有基础上，额外排除 exclude.txt 中的域名
  grep -v -f "scripts/exclude-keyword.txt" unique_domains.txt \
    | grep -v -f exclude.txt \
    | grep -v '^DOMAIN-KEYWORD' | grep -v '^DOMAIN' >filtered_domains.txt

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
