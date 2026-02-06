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
DEAD_DOMAINS_FILE = os.path.join(WORK_DIR, "dead_domains.txt")
DEAD_DOMAINS_SET = set() # 内存缓存

def cleanup():
    if os.path.exists(WORK_DIR):
        try:
            shutil.rmtree(WORK_DIR)
        except:
            pass

import atexit
atexit.register(cleanup)

def check_mihomo():
    """检查 mihomo 命令是否存在"""
    return shutil.which("mihomo") is not None

# ================= 资源配置 =================

ALLOW_URLS = [
    "https://raw.githubusercontent.com/Cats-Team/AdRules/refs/heads/script/script/allowlist.txt",
    "https://raw.githubusercontent.com/zoonderkins/blahdns/refs/heads/master/hosts/whitelist.txt",
    "https://raw.githubusercontent.com/AdguardTeam/AdGuardSDNSFilter/master/Filters/exceptions.txt",
    "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/refs/heads/hidden/reject-need-to-remove.txt"
]

# 217heidai 的死域名列表
DEAD_DOMAIN_URL = "https://raw.githubusercontent.com/217heidai/adblockfilters/main/rules/black.txt"

# ================= 核心工具函数 =================

def download_file(url, timeout=20, retries=3):
    """单个文件下载逻辑"""
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
    """并行下载并合并文件"""
    content_list = []
    with ThreadPoolExecutor(max_workers=min(len(urls) + 1, 10)) as executor:
        futures = [executor.submit(download_file, url) for url in urls]
        for f in futures:
            content = f.result()
            if content.strip():
                if not content.endswith('\n'):
                    content += '\n'
                content_list.append(content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        if content_list:
            f.write("".join(content_list))
        else:
            pass

def prepare_dead_domain_list():
    """预加载死域名列表到内存"""
    print("💀 正在下载并加载死域名列表 (217heidai)...")
    content = download_file(DEAD_DOMAIN_URL)
    if content:
        for line in content.splitlines():
            line = line.strip().lower()
            if line and not line.startswith("#"):
                DEAD_DOMAINS_SET.add(line)
        print(f"💀 已加载 {len(DEAD_DOMAINS_SET)} 条死域名记录")
    else:
        print("⚠️ 警告: 死域名列表下载失败，将跳过死域名剔除步骤。")

def apply_dead_domain_filter(input_file, output_file):
    """剔除死域名"""
    if not DEAD_DOMAINS_SET:
        shutil.copyfile(input_file, output_file)
        return

    removed_count = 0
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            original_line = line
            line = line.strip().lower()
            
            # 提取纯域名进行比对
            # 例如: +.example.com -> example.com
            check_domain = line
            if check_domain.startswith("+."):
                check_domain = check_domain[2:]
            elif check_domain.startswith("."):
                check_domain = check_domain[1:]
            
            # 只有当域名完全匹配黑名单时才剔除
            # (不进行后缀匹配，以免误杀子域名)
            if check_domain in DEAD_DOMAINS_SET:
                removed_count += 1
                continue
            
            outfile.write(original_line)
    
    print(f"🧹 已剔除 {removed_count} 条死域名")

def normalize_domain_line(line):
    """单行域名清洗与提取 (借鉴 217heidai 逻辑)"""
    line = line.strip().lower()
    
    if not line or line.startswith("!") or line.startswith("["): return None
    if line.startswith("#"): return None

    # 1. 【直通车】Clash/Mihomo 语法
    if line.startswith("+.") or line.startswith("."):
        check_part = line.lstrip("+.")
        if re.match(r'^[a-z0-9._-]+$', check_part):
            return line

    # 2. 移除 IP
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', line): return None

    # 3. AdBlock 语法清洗
    if "##" in line or "#?#" in line or "#$#" in line or "#@#" in line: return None

    check_pattern = line
    if check_pattern.startswith("@@"): check_pattern = check_pattern[2:]
    if check_pattern.startswith("||"): check_pattern = check_pattern[2:]
    if '$' in check_pattern: check_pattern = check_pattern.split('$')[0]
    
    # 丢弃路径规则
    if '/' in check_pattern: return None
    # 丢弃通配符
    if "*" in check_pattern: return None

    # 提取域名
    pattern = line
    if pattern.startswith("@@"): pattern = pattern[2:]
    if pattern.startswith("||"): pattern = pattern[2:]
    
    end_chars = ['^', '$']
    min_idx = len(pattern)
    found = False
    for char in end_chars:
        idx = pattern.find(char)
        if idx != -1 and idx < min_idx:
            min_idx = idx
            found = True
    
    if found: pattern = pattern[:min_idx]
    
    pattern = re.sub(r'[^a-z0-9.-]', '', pattern)
    pattern = pattern.strip('.')
    
    if '.' not in pattern or len(pattern) < 3: return None
    
    return pattern

def process_normalize_domain(input_file, output_file):
    if not os.path.exists(input_file):
        open(output_file, 'w').close()
        return

    domains = set()
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            res = normalize_domain_line(line)
            if res:
                domains.add(res)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for d in sorted(domains):
            f.write(d + '\n')

def apply_keyword_filter(input_file, output_file):
    """关键词过滤"""
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
    """智能覆盖去重"""
    if not os.path.exists(input_file) or os.path.getsize(input_file) == 0:
        open(output_file, 'w').close()
        return

    lines = []
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    data = []
    for line in lines:
        line = line.strip()
        if not line: continue
        
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
                pass 

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result_lines) + '\n')

def apply_advanced_whitelist_filter(block_in, allow_in, final_out):
    """双向白名单过滤"""
    combined_data = []

    if os.path.exists(allow_in):
        with open(allow_in, 'r', encoding='utf-8') as f:
            for line in f:
                key = line.strip().lower()
                if not key: continue
                if key.startswith("+."): pure = key[2:]
                elif key.startswith("."): pure = key[1:]
                else: pure = key
                reversed_key = pure[::-1]
                combined_data.append({'key': reversed_key, 'type': 1, 'original': None})

    if os.path.exists(block_in):
        with open(block_in, 'r', encoding='utf-8') as f:
            for line in f:
                original = line.strip()
                if not original: continue
                pure = original.lower()
                if pure.startswith("+."): pure = pure[2:]
                elif pure.startswith("."): pure = pure[1:]
                reversed_key = pure[::-1]
                combined_data.append({'key': reversed_key, 'type': 0, 'original': original})

    combined_data.sort(key=lambda x: x['key'])

    active_white_root = ""
    buffered_key = ""
    buffered_line = ""
    final_lines = []

    for item in combined_data:
        key = item['key']
        typ = item['type']
        original = item['original']

        if active_white_root and key.startswith(active_white_root):
            if len(key) == len(active_white_root) or key[len(active_white_root)] == '.':
                continue
        
        is_child_or_equal = False
        if buffered_key:
            if key.startswith(buffered_key):
                 if len(key) == len(buffered_key) or key[len(buffered_key)] == '.':
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
    """输出封装"""
    if not os.path.exists(src) or os.path.getsize(src) == 0:
        print(f"⚠️  警告: {dst} 源文件为空，跳过生成。")
        return

    # 【新步骤】在生成最终文件前，应用死域名过滤
    temp_dead_filtered = src + ".dead_filtered"
    apply_dead_domain_filter(src, temp_dead_filtered)
    shutil.move(temp_dead_filtered, src)

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
    process_normalize_domain(raw_ads, clean_ads)

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
                line = line.strip()
                if line and not line.startswith('#'):
                    allow_content.append(line.lower() + "\n")
    
    with open(merged_allow_raw, 'w', encoding='utf-8') as f:
        f.write("".join(allow_content))

    clean_allow = os.path.join(mod_dir, "clean_allow.txt")
    process_normalize_domain(merged_allow_raw, clean_allow)

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
    process_normalize_domain(raw_ai, clean_ai)
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

    raw_fakeip = os.path.join(mod_dir, "raw_fakeip_dl.txt")
    download_files_parallel(raw_fakeip, FAKE_IP_URLS)
    
    clean_fakeip = os.path.join(mod_dir, "clean_fakeip.txt")
    unique_lines = set()
    if os.path.exists(raw_fakeip):
        with open(raw_fakeip, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.lower()
                if re.match(r'^\s*(dns:|fake-ip-filter:)', line): continue
                line = re.sub(r'^\s*-\s*', '', line)
                line = line.replace('"', '').replace("'", '').replace('\\', '').strip()
                if not line or line.startswith('#'): continue
                
                res = normalize_domain_line(line)
                if res: unique_lines.add(res)
    
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
    process_normalize_domain(raw_rd, clean_rd)

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
                if line.strip() and not line.strip().startswith('#'):
                    allow_content.append(line.lower() + "\n")
    with open(merged_allow_raw, 'w', encoding='utf-8') as f:
        f.write("".join(allow_content))
    
    clean_rd_allow = os.path.join(mod_dir, "clean_rd_allow.txt")
    process_normalize_domain(merged_allow_raw, clean_rd_allow)

    final_rd = os.path.join(mod_dir, "final_rd.txt")
    apply_advanced_whitelist_filter(clean_rd, clean_rd_allow, final_rd)
    finalize_output(final_rd, "Reject_Drop_merged.mrs", "none")
    if os.path.exists(final_rd):
        shutil.move(final_rd, "Reject_Drop_merged.txt")

def generate_cn():
    mod_dir = os.path.join(WORK_DIR, "cn")
    os.makedirs(mod_dir, exist_ok=True)
    print("=== 🚀 [CN] 启动 ===")

    CN_URLS = [
        "https://static-file-global.353355.xyz/rules/cn-additional-list.txt",
        "https://ruleset.skk.moe/Clash/non_ip/domestic.txt"
    ]

    raw_cn = os.path.join(mod_dir, "raw_cn.txt")
    download_files_parallel(raw_cn, CN_URLS)

    final_cn_list = []
    if os.path.exists(raw_cn):
        with open(raw_cn, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if not line or line.startswith('#'): continue
                
                if line.startswith("domain-suffix,"):
                    line = "+." + line.split(',')[1].strip()
                elif line.startswith("domain,"):
                    line = line.split(',')[1].strip()
                
                if re.match(r'^[a-z0-9.-]+$', line):
                     line = "+." + line
                
                res = normalize_domain_line(line)
                if res: final_cn_list.append(res)
    
    temp_cn = os.path.join(mod_dir, "temp_cn.txt")
    with open(temp_cn, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_cn_list))
    
    final_cn = os.path.join(mod_dir, "final_cn.txt")
    optimize_smart_self(temp_cn, final_cn)
    finalize_output(final_cn, "CN_merged.mrs", "none")
    if os.path.exists(final_cn):
        shutil.move(final_cn, "CN_merged.txt")

def main():
    target = "all"
    if len(sys.argv) > 1:
        target = sys.argv[1]

    # 【初始化】优先下载死域名列表，供后续任务共享
    prepare_dead_domain_list()

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
