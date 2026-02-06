#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import tempfile
import time
import re
import urllib.request
import urllib.error
import subprocess
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, wait
from datetime import datetime

# ================= 全局配置 =================

WORK_DIR = tempfile.mkdtemp(prefix="wuiiled_convert_")

# 强制模拟 Bash 的 C 语言区域设置排序行为
os.environ["LC_ALL"] = "C"

def cleanup():
    if os.path.exists(WORK_DIR):
        try:
            shutil.rmtree(WORK_DIR)
        except:
            pass

import atexit
atexit.register(cleanup)

def check_mihomo():
    return shutil.which("mihomo") is not None

# ================= 资源配置 =================

ALLOW_URLS = [
    "https://raw.githubusercontent.com/Cats-Team/AdRules/refs/heads/script/script/allowlist.txt",
    "https://raw.githubusercontent.com/zoonderkins/blahdns/refs/heads/master/hosts/whitelist.txt",
    "https://raw.githubusercontent.com/AdguardTeam/AdGuardSDNSFilter/master/Filters/exceptions.txt",
    "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/refs/heads/hidden/reject-need-to-remove.txt"
]

# ================= 核心工具函数 =================

def download_file(url, timeout=20, retries=3):
    ua = "Mozilla/5.0 (compatible; MihomoRuleConverter/1.0)"
    req = urllib.request.Request(url, headers={'User-Agent': ua})
    
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception:
            if attempt == retries - 1:
                return ""
            time.sleep(1)
    return ""

def download_files_parallel(output_file, urls):
    content_list = []
    # 保持下载顺序一致性
    with ThreadPoolExecutor(max_workers=min(len(urls) + 1, 10)) as executor:
        # 提交任务
        futures_map = {executor.submit(download_file, url): url for url in urls}
        # 按照 url 列表的原始顺序收集结果
        results = []
        for url in urls:
            for future, f_url in futures_map.items():
                if f_url == url:
                    content = future.result()
                    if content.strip():
                        if not content.endswith('\n'):
                            content += '\n'
                        results.append(content)
                    break
    
    with open(output_file, 'w', encoding='utf-8') as f:
        if results:
            f.write("".join(results))
        else:
            pass

def normalize_domain_line(line):
    """
    单行域名清洗 - 严格对齐 Bash 逻辑
    """
    line = line.strip()
    
    # 1. Bash: s/[\$#].*//g (去行内注释和选项)
    line = re.sub(r'[\$#].*', '', line)
    
    # 2. Bash: s/^(0\.0\.0\.0|127\.0\.0\.1)[[:space:]]+//g (去IP前缀)
    line = re.sub(r'^(0\.0\.0\.0|127\.0\.0\.1)\s+', '', line)

    # 3. Bash: s/^!.*// (去整行感叹号注释)
    if line.startswith("!"): return None

    # 4. Bash: s/^@@// (去白名单标记)
    if line.startswith("@@"):
        line = line[2:]

    # 5. Bash: s/\|\|//; s/\^//; s/\|// (去 AdBlock 修饰符)
    line = line.replace("||", "").replace("^", "").replace("|", "")

    # 6. Bash: s/^domain-keyword,//; s/^domain-suffix,//; s/^domain,// (去Clash前缀)
    line = re.sub(r'^(domain-keyword|domain-suffix|domain),', '', line)

    # 7. Bash: s/^([^,]+).*/\1/ (取逗号前部分)
    if ',' in line:
        line = line.split(',')[0]

    # 8. Bash: s/^\+\.//; s/^\.//; s/\.$// (去点)
    line = re.sub(r'^(\+\.|\.)', '', line)
    line = line.rstrip('.')

    # 9. Bash AWK 逻辑检查
    # /\./ (必须有点)
    if '.' not in line: return None
    # !/\*/ (不能有星号)
    if '*' in line: return None
    # /^[a-z0-9_]/ (必须以字母数字开头)
    if not re.match(r'^[a-z0-9_]', line): return None
    # !/^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/ (不能是纯IP)
    if re.match(r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$', line): return None

    # 额外安全：丢弃含 / 的路径规则
    if '/' in line: return None

    return line

def process_normalize_domain(input_file, output_file, skip_allow_rules=False):
    """
    文件标准化处理
    skip_allow_rules=True 对应 Bash 的 grep -vE '^\s*@@'
    """
    if not os.path.exists(input_file):
        open(output_file, 'w').close()
        return

    domains = set()
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip().lower()
            if not line: continue
            
            # Bash: grep -vE '^\s*@@'
            if skip_allow_rules and line.startswith("@@"):
                continue

            res = normalize_domain_line(line)
            if res:
                domains.add(res)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Bash: sort -u
        for d in sorted(domains):
            f.write(d + '\n')

def apply_keyword_filter(input_file, output_file):
    keyword_file = "scripts/exclude-keyword.txt"
    keywords = []
    if os.path.exists(keyword_file) and os.path.getsize(keyword_file) > 0:
        with open(keyword_file, 'r', encoding='utf-8') as kf:
            keywords = [k.strip().lower() for k in kf if k.strip() and not k.strip().startswith("#")]

    if not keywords:
        shutil.copyfile(input_file, output_file)
        return

    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            if not any(kw in line for kw in keywords):
                outfile.write(line)

def optimize_smart_self(input_file, output_file):
    """智能去重"""
    if not os.path.exists(input_file) or os.path.getsize(input_file) == 0:
        open(output_file, 'w').close()
        return

    lines = []
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"): continue
        
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
        
        if parts:
            data.append({
                'parts': parts,
                'is_wildcard': is_wildcard,
                'original': line
            })

    # 排序：反转域名列表, 然后是通配符优先
    data.sort(key=lambda x: (x['parts'], not x['is_wildcard']))

    result_lines = []
    last_root = None

    for item in data:
        curr = item['parts']
        is_covered = False
        
        if last_root is not None:
            if len(curr) >= len(last_root):
                if curr[:len(last_root)] == last_root:
                    is_covered = True
        
        if not is_covered:
            result_lines.append(item['original'])
            if item['is_wildcard']:
                last_root = curr
            else:
                last_root = None

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result_lines) + '\n')

def apply_advanced_whitelist_filter(block_in, allow_in, final_out):
    """
    双向白名单过滤 (AWK 逻辑复刻)
    """
    combined_data = []

    # Type 1: Allow
    if os.path.exists(allow_in):
        with open(allow_in, 'r', encoding='utf-8') as f:
            for line in f:
                key = line.strip()
                if not key: continue
                reversed_key = key[::-1]
                combined_data.append({'key': reversed_key, 'type': 1, 'original': None})

    # Type 0: Block
    if os.path.exists(block_in):
        with open(block_in, 'r', encoding='utf-8') as f:
            for line in f:
                original = line.strip()
                if not original: continue
                pure = original
                if pure.startswith("+."): pure = pure[2:]
                elif pure.startswith("."): pure = pure[1:]
                reversed_key = pure[::-1]
                combined_data.append({'key': reversed_key, 'type': 0, 'original': original})

    # 【关键】模仿 Bash sort: Block(0) 排在 Allow(1) 前面
    combined_data.sort(key=lambda x: (x['key'], x['type']))

    active_white_root = ""
    buffered_key = ""
    buffered_line = ""
    final_lines = []

    for item in combined_data:
        key = item['key']
        typ = item['type']
        original = item['original']

        if active_white_root:
             target = active_white_root + "."
             if key.startswith(target):
                 continue
        
        is_child_or_equal = False
        if buffered_key:
            if key == buffered_key or key.startswith(buffered_key + "."):
                is_child_or_equal = True
        
        if is_child_or_equal:
            if typ == 1:
                buffered_key = ""
                buffered_line = ""
                active_white_root = key
        else:
            if buffered_line:
                final_lines.append(buffered_line)
            
            if typ == 1:
                active_white_root = key
                buffered_key = ""
                buffered_line = ""
            else:
                buffered_key = key
                buffered_line = original
                active_white_root = ""
    
    if buffered_line:
        final_lines.append(buffered_line)

    with open(final_out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_lines) + '\n')

def finalize_output(src, dst, mode):
    if not os.path.exists(src) or os.path.getsize(src) == 0:
        print(f"⚠️  警告: {dst} 源文件为空，跳过生成。")
        return

    # Bash: sort -u
    lines = []
    with open(src, 'r', encoding='utf-8') as f:
        lines = list(set(f.read().splitlines()))
    lines.sort()

    if mode == "add_prefix":
        lines = ["+." + line if not line.startswith("+.") else line for line in lines]

    count = len(lines)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"# Count: {count}\n# Updated: {date_str}\n"

    with open(src, 'w', encoding='utf-8') as f:
        f.write(header + "\n".join(lines) + "\n")
    
    if dst and check_mihomo():
        print(f"🔄 转换 {dst}...")
        try:
            subprocess.run(["mihomo", "convert-ruleset", "domain", "text", src, dst], check=True)
        except subprocess.CalledProcessError:
            print(f"❌ 转换失败: {dst}")
    
    print(f"📊 完成: {dst} (行数: {count})")

# ================= 模块定义 =================

def generate_ads_reject():
    mod_dir = os.path.join(WORK_DIR, "ads")
    os.makedirs(mod_dir, exist_ok=True)
    print("=== 🚀 [ADS] 启动 ===")

    BLOCK_URLS = [
        "https://raw.githubusercontent.com/pmkol/easymosdns/rules/ad_domain_list.txt",
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/Reject-addon.txt",
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt",
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_3.txt",
        "https://adguardteam.github.io/HostlistsRegistry/assets/filter_4.txt",
        "https://raw.githubusercontent.com/ForestL18/rules-dat/mihomo/geo/classical/pcdn.list",
        "https://raw.githubusercontent.com/ForestL18/rules-dat/refs/heads/mihomo/geo/classical/reject.list",
        "https://a.dove.isdumb.one/pihole.txt",
        "https://raw.githubusercontent.com/limbopro/Adblock4limbo/main/rule/Surge/Adblock4limbo_surge.list",
        "https://raw.githubusercontent.com/Cats-Team/AdRules/main/adrules_domainset.txt",
        "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/refs/heads/release/reject-list.txt",
        "https://ruleset.skk.moe/Clash/domainset/reject.txt"
    ]

    raw_ads = os.path.join(mod_dir, "raw_ads.txt")
    raw_allow = os.path.join(mod_dir, "raw_allow.txt")
    
    download_files_parallel(raw_ads, BLOCK_URLS)
    download_files_parallel(raw_allow, ALLOW_URLS)

    clean_ads = os.path.join(mod_dir, "clean_ads.txt")
    # Bash: grep -vE '^\s*@@' -> skip_allow_rules=True
    process_normalize_domain(raw_ads, clean_ads, skip_allow_rules=True)

    filter_ads = os.path.join(mod_dir, "filter_ads.txt")
    apply_keyword_filter(clean_ads, filter_ads)

    merged_allow_raw = os.path.join(mod_dir, "merged_allow_raw.txt")
    allow_content = []
    if os.path.exists(raw_allow):
        with open(raw_allow, 'r', encoding='utf-8') as f:
            allow_content.append(f.read())
    
    local_allow = "scripts/exclude-keyword.txt"
    if os.path.exists(local_allow):
        with open(local_allow, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if line and not line.startswith('#'):
                    allow_content.append(line + "\n")
    
    with open(merged_allow_raw, 'w', encoding='utf-8') as f:
        f.write("".join(allow_content))

    clean_allow = os.path.join(mod_dir, "clean_allow.txt")
    # Bash: normalize_domain (不跳过@@) -> skip_allow_rules=False
    process_normalize_domain(merged_allow_raw, clean_allow, skip_allow_rules=False)

    opt_ads = os.path.join(mod_dir, "opt_ads.txt")
    opt_allow = os.path.join(mod_dir, "opt_allow.txt")
    optimize_smart_self(filter_ads, opt_ads)
    optimize_smart_self(clean_allow, opt_allow)

    final_ads = os.path.join(mod_dir, "final_ads.txt")
    apply_advanced_whitelist_filter(opt_ads, opt_allow, final_ads)

    finalize_output(final_ads, "ADs_merged.mrs", "add_prefix")
    if os.path.exists(final_ads):
        shutil.move(final_ads, "ADs_merged.txt")

def generate_ai():
    mod_dir = os.path.join(WORK_DIR, "ai")
    os.makedirs(mod_dir, exist_ok=True)
    print("=== 🚀 [AI] 启动 ===")

    AI_URLS = [
        "https://github.com/MetaCubeX/meta-rules-dat/raw/meta/geo/geosite/category-ai-!cn.list",
        "https://ruleset.skk.moe/List/non_ip/ai.conf",
        "https://github.com/DustinWin/ruleset_geodata/raw/mihomo-ruleset/ai.list",
        "https://raw.githubusercontent.com/ConnersHua/RuleGo/refs/heads/master/Surge/Ruleset/Extra/AI.list"
    ]
    
    raw_ai = os.path.join(mod_dir, "raw_ai.txt")
    download_files_parallel(raw_ai, AI_URLS)
    clean_ai = os.path.join(mod_dir, "clean_ai.txt")
    process_normalize_domain(raw_ai, clean_ai, skip_allow_rules=False)
    opt_ai = os.path.join(mod_dir, "opt_ai.txt")
    optimize_smart_self(clean_ai, opt_ai)
    finalize_output(opt_ai, "AIs_merged.mrs", "add_prefix")
    if os.path.exists(opt_ai):
        shutil.move(opt_ai, "AIs_merged.txt")

def generate_fakeip():
    mod_dir = os.path.join(WORK_DIR, "fakeip")
    os.makedirs(mod_dir, exist_ok=True)
    print("=== 🚀 [FakeIP] 启动 ===")

    FAKE_IP_URLS = [
        "https://raw.githubusercontent.com/vernesong/OpenClash/refs/heads/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list",
        "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list",
        "https://raw.githubusercontent.com/DustinWin/ruleset_geodata/refs/heads/mihomo-ruleset/fakeip-filter.list",
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/fake-ip-addon.txt",
        "https://ruleset.skk.moe/Internal/clash_fake_ip_filter.yaml"
    ]

    raw_fakeip_dl = os.path.join(mod_dir, "raw_fakeip_dl.txt")
    download_files_parallel(raw_fakeip_dl, FAKE_IP_URLS)
    
    clean_fakeip = os.path.join(mod_dir, "clean_fakeip.txt")
    
    unique_lines = set()
    if os.path.exists(raw_fakeip_dl):
        with open(raw_fakeip_dl, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.lower()
                # 严格按照 Bash 的 grep -vE '^\s*(dns:|fake-ip-filter:)'
                if re.match(r'^\s*(dns:|fake-ip-filter:)', line): continue
                line = re.sub(r'^\s*-\s*', '', line)
                line = line.replace('"', '').replace("'", '').replace('\\', '').strip()
                if not line or line.startswith('#'): continue
                unique_lines.add(line)
    
    with open(clean_fakeip, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(unique_lines)) + '\n')

    final_fakeip = os.path.join(mod_dir, "final_fakeip.txt")
    optimize_smart_self(clean_fakeip, final_fakeip)
    
    finalize_output(final_fakeip, "Fake_IP_Filter_merged.mrs", "none")
    if os.path.exists(final_fakeip):
        shutil.move(final_fakeip, "Fake_IP_Filter_merged.txt")

def generate_ads_drop():
    mod_dir = os.path.join(WORK_DIR, "drop")
    os.makedirs(mod_dir, exist_ok=True)
    print("=== 🚀 [Drop] 启动 ===")

    BLOCK_URLS = [
        "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt",
        "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/rules/Custom_Reject-drop.txt"
    ]
    raw_rd = os.path.join(mod_dir, "raw_rd.txt")
    download_files_parallel(raw_rd, BLOCK_URLS)

    clean_rd = os.path.join(mod_dir, "clean_rd.txt")
    rd_lines = set()
    if os.path.exists(raw_rd):
        with open(raw_rd, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if not line or line.startswith('#') or "skk.moe" in line: continue
                
                # s/^domain-suffix,/+./; s/^domain,//
                if line.startswith("domain-suffix,"):
                    line = "+." + line.split(',')[1].strip()
                elif line.startswith("domain,"):
                    line = line.split(',')[1].strip()
                
                if line == "+.": continue
                
                rd_lines.add(line)
    
    with open(clean_rd, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(rd_lines)) + '\n')

    raw_allow_temp = os.path.join(mod_dir, "raw_allow_temp.txt")
    download_files_parallel(raw_allow_temp, ALLOW_URLS)
    
    merged_allow_raw = os.path.join(mod_dir, "merged_allow_raw.txt")
    allow_content = []
    if os.path.exists(raw_allow_temp):
        with open(raw_allow_temp, 'r', encoding='utf-8') as f:
            allow_content.append(f.read())
    local_allow = "scripts/exclude-keyword.txt"
    if os.path.exists(local_allow):
        with open(local_allow, 'r', encoding='utf-8') as f:
             for line in f:
                line = line.strip().lower()
                if line and not line.startswith('#'):
                    allow_content.append(line + "\n")
    with open(merged_allow_raw, 'w', encoding='utf-8') as f:
        f.write("".join(allow_content))
    
    clean_rd_allow = os.path.join(mod_dir, "clean_rd_allow.txt")
    process_normalize_domain(merged_allow_raw, clean_rd_allow, skip_allow_rules=False)

    final_rd = os.path.join(mod_dir, "final_rd.txt")
    apply_advanced_whitelist_filter(clean_rd, clean_rd_allow, final_rd)
    finalize_output(final_rd, "Reject_Drop_merged.mrs", "none")
    if os.path.exists(final_rd):
        shutil.move(final_rd, "Reject_Drop_merged.txt")

def generate_cn():
    mod_dir = os.path.join(WORK_DIR, "cn")
    os.makedirs(mod_dir, exist_ok=True)
    print("=== 🚀 [CN] 启动 ===")

    CN_URLS_1 = ["https://static-file-global.353355.xyz/rules/cn-additional-list.txt"]
    CN_URLS_2 = ["https://ruleset.skk.moe/Clash/non_ip/domestic.txt"]

    raw_cn_1 = os.path.join(mod_dir, "raw_cn_1.txt")
    raw_cn_2 = os.path.join(mod_dir, "raw_cn_2.txt")
    download_files_parallel(raw_cn_1, CN_URLS_1)
    download_files_parallel(raw_cn_2, CN_URLS_2)

    merged_cn = os.path.join(mod_dir, "merged_cn_raw.txt")
    with open(merged_cn, 'w', encoding='utf-8') as f:
        if os.path.exists(raw_cn_1):
            with open(raw_cn_1, 'r', encoding='utf-8') as f1:
                for line in f1:
                    line = line.strip().lower()
                    if not line or line.startswith('#'): continue
                    f.write("+." + line + "\n")
        
        if os.path.exists(raw_cn_2):
            with open(raw_cn_2, 'r', encoding='utf-8') as f2:
                for line in f2:
                    line = line.strip().lower()
                    if not line or line.startswith('#') or "skk.moe" in line: continue
                    
                    if line.startswith("domain-suffix,"):
                        line = "+." + line.split(',')[1].strip()
                    elif line.startswith("domain,"):
                        line = line.split(',')[1].strip()
                    else:
                        continue 
                    
                    f.write(line + "\n")

    final_cn = os.path.join(mod_dir, "final_cn.txt")
    optimize_smart_self(merged_cn, final_cn)
    finalize_output(final_cn, "CN_merged.mrs", "none")
    if os.path.exists(final_cn):
        shutil.move(final_cn, "CN_merged.txt")

def main():
    target = "all"
    if len(sys.argv) > 1:
        target = sys.argv[1]

    tasks = {
        "ads-reject": generate_ads_reject,
        "ais": generate_ai,
        "fakeip": generate_fakeip,
        "ads-drop": generate_ads_drop,
        "cn": generate_cn
    }

    if target == "all":
        print("⚡️ 启动全局并行处理...")
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(func) for func in tasks.values()]
            wait(futures)
        print("🎉 所有任务执行完毕！")
    elif target in tasks:
        tasks[target]()
    else:
        print("用法: python3 scripts/convert.py [ads-reject|ais|fakeip|ads-drop|cn|all]")
        sys.exit(1)

if __name__ == "__main__":
    main()
