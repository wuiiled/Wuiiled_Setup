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

    # 专门用于清洗域名的函数
    normalize_domain() {
        # 1. dos2unix
        # 2. 移除行尾注释 ($ 或 # 后面的内容)
        # 3. 移除行首的 0.0.0.0 或 127.0.0.1 (针对 Hosts 格式)
        # 4. 移除 DOMAIN-SUFFIX, DOMAIN-KEYWORD, DOMAIN, 等前缀
        # 5. 移除 || 和 ^ (AdGuard 格式)
        # 6. 如果有逗号分隔 (Surge格式)，只取第一部分
        # 7. 转小写
        # 8. 移除开头结尾空格
        # 9. 只保留包含点的行 (过滤纯单词)
        
        tr -d '\r' \
        | sed 's/[\$#].*//g' \
        | sed -E 's/^(0\.0\.0\.0|127\.0\.0\.1)[[:space:]]+//g' \
        | sed 's/DOMAIN-SUFFIX,//g; s/DOMAIN-KEYWORD,//g; s/DOMAIN,//g' \
        | sed 's/||//g; s/\^//g' \
        | awk -F, '{print $1}' \
        | tr 'A-Z' 'a-z' \
        | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
        | awk '/\./ {print $0}'
    }

    process_blocklist() {
        local input_file=$1
        local output_block=$2
        local output_allow_extra=$3

        echo "🧹 正在处理拦截规则 (分离 @@ 白名单 和 Hosts 格式)..."

        # 1. 提取 @@ 开头的行 (AdBlock 白名单)，清洗后存入额外白名单文件
        grep "^@@" "$input_file" | sed 's/^@@//g' | normalize_domain > "$output_allow_extra"

        # 2. 提取非 @@ 开头的行，进行清洗
        grep -v "^@@" "$input_file" | grep -v "DOMAIN-KEYWORD" | normalize_domain | sort -u > "$output_block"
    }

    optimize_list() {
        local input_file=$1
        local output_file=$2

        echo "🧠 正在去重 (主域名自动覆盖子域名)..."
        # 反转 -> 排序 -> awk去重 -> 反转回
        cat "$input_file" \
        | rev | sort | awk 'NR==1 {prev=$0; print; next} {if (index($0, prev ".") != 1) {print; prev=$0}}' | rev | sort > "$output_file"
    }

    advanced_whitelist_filter() {
        local block_file=$1
        local allow_file=$2
        local final_file=$3

        echo "🛡️  正在执行高级白名单过滤 (如果白名单包含主域名，则移除拦截列表中的子域名)..."

        # 算法说明：
        # 我们利用 ASCII 排序特性。
        # 1. 准备白名单：反转字符串，并在末尾加 '!' (ASCII 33, 比 '.' 46 小)。
        # 2. 准备黑名单：反转字符串。
        # 3. 混合排序。
        # 4. 遍历：因为 '!' 排在 '.' 前面，如果白名单是 "moc.diub!"，它会排在黑名单 "moc.diub.da" 前面。
        #    awk 只要记录当前的白名单根，就能过滤掉后面匹配的黑名单项。

        # 准备白名单：反转并加标记 !
        cat "$allow_file" | rev | sed 's/$/!/' > "${WORK_DIR}/allow_rev_tagged.txt"

        # 准备黑名单：反转
        cat "$block_file" | rev > "${WORK_DIR}/block_rev.txt"

        # 合并、排序、过滤
        cat "${WORK_DIR}/allow_rev_tagged.txt" "${WORK_DIR}/block_rev.txt" \
        | sort \
        | awk '
            # 如果行以 ! 结尾，说明是白名单规则
            /\!$/ {
                # 去掉 ! 保存为当前白名单根
                root = substr($0, 1, length($0)-1);
                next; 
            }
            # 处理黑名单行
            {
                # 检查1: 是否完全相等 (黑名单 example.com vs 白名单 example.com)
                if ($0 == root) next;
                
                # 检查2: 是否是子域名 (黑名单 a.example.com 匹配 root + ".")
                # index 返回匹配位置，必须是 1 (即开头匹配)
                if (root != "" && index($0, root ".") == 1) next;

                # 如果没被白名单命中，打印出来
                print;
            }
        ' \
        | rev > "$final_file" # 反转回来
    }

    # ================= 主程序流程 =================

    echo "=== 脚本开始运行 ==="

    # 1. 下载原始文件
    download_files "${WORK_DIR}/raw_block_all.txt" "${BLOCK_URLS[@]}"
    download_files "${WORK_DIR}/raw_allow_all.txt" "${ALLOW_URLS[@]}"

    # 2. 处理拦截规则 (清洗 + 分离出 @@ 规则)
    #    分离出的规则会追加到 raw_allow_extra.txt
    process_blocklist "${WORK_DIR}/raw_block_all.txt" "${WORK_DIR}/clean_block.txt" "${WORK_DIR}/raw_allow_extra.txt"

    # 3. 合并所有白名单 (原始白名单 + 从拦截列表中提取的 @@ 规则)
    cat "${WORK_DIR}/raw_allow_all.txt" "${WORK_DIR}/raw_allow_extra.txt" | normalize_domain | sort -u > "${WORK_DIR}/clean_allow.txt"

    # 4. 优化列表 (自我去重：如果有了 google.com，去掉 ad.google.com)
    #    先对自己优化，减少数据量
    optimize_list "${WORK_DIR}/clean_block.txt" "${WORK_DIR}/opt_block.txt"
    optimize_list "${WORK_DIR}/clean_allow.txt" "${WORK_DIR}/opt_allow.txt"

    # 5. 最终过滤：应用白名单剔除黑名单 (包含子域名逻辑)
    advanced_whitelist_filter "${WORK_DIR}/opt_block.txt" "${WORK_DIR}/opt_allow.txt" "$OUTPUT_FILE"

    # 6. 最终排序
    sort -o "$OUTPUT_FILE" "$OUTPUT_FILE"

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
