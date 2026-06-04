#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
from utils import download_file
import utils
import providers

def run_all():
    os.makedirs("output/adg", exist_ok=True)

    # 1. 转换 ADs_merged (包含拦截与放行规则)
    opt_ads_path = os.path.join(utils.get_work_dir(), "ads", "opt_ads.txt")
    opt_allow_path = os.path.join(utils.get_work_dir(), "ads", "opt_allow.txt")
    
    adg_lines = []
    
    # 添加拦截规则 (从未经过白名单过滤的 opt_ads 读取)
    if os.path.exists(opt_ads_path):
        for line in open(opt_ads_path, 'r', encoding='utf-8').read().splitlines():
            domain = line.strip()
            if not domain or domain.startswith('#'): continue
            if domain.startswith("+."): domain = domain[2:]
            elif domain.startswith("."): domain = domain[1:]
            adg_lines.append(f"||{domain}^")
            
    # 添加放行/白名单规则 (从 opt_allow 读取，并加上 @@|| 前缀)
    if os.path.exists(opt_allow_path):
        for line in open(opt_allow_path, 'r', encoding='utf-8').read().splitlines():
            domain = line.strip()
            if not domain or domain.startswith('#'): continue
            if domain.startswith("+."): domain = domain[2:]
            elif domain.startswith("."): domain = domain[1:]
            adg_lines.append(f"@@||{domain}^")
            
    # 写入 AdGuard Home 合并规则文件
    with open("output/adg/ADs_merged_adg.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(adg_lines) + '\n')
    print(f"✅ [AdGuard] {'ADs_merged_adg':<24} | 规则数: {len(adg_lines):,} (包含白名单例外规则)")

    # 2. Httpdns
    content = download_file(providers.ADG_URLS["Httpdns"])
    lines = []
    for line in content.splitlines():
        if not line.strip(): continue
        line = re.sub(r'^\+\.', '||', line)
        if not line.startswith('#'): line = line + '^'
        lines.append(line)
    with open("output/adg/Httpdns_adg.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"✅ [AdGuard] {'Httpdns_adg':<24} | 规则数: {len(lines):,}")

    # 3. PCDN
    content = download_file(providers.ADG_URLS["PCDN"])
    lines = []
    for line in content.splitlines():
        if 'DOMAIN-REGEX,' in line or line.startswith('#') or not line.strip(): continue
        line = re.sub(r'^(DOMAIN-SUFFIX,|DOMAIN,|\+\.)', '||', line)
        line = line + '^'
        lines.append(line)
    with open("output/adg/PCDN_adg.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"✅ [AdGuard] {'PCDN_adg':<24} | 规则数: {len(lines):,}")