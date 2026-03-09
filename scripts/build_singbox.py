#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import subprocess
from glob import glob
import shutil

def check_singbox():
    return shutil.which("sing-box") is not None

def convert_txt_to_json(txt_path, json_path):
    domains = []
    domain_suffixes = []
    ip_cidrs = []

    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            
            line = line.split('#')[0].strip()
            if not line: continue

            if '/' in line and any(c.isdigit() for c in line):
                ip_cidrs.append(line)
            elif line.startswith('+.'):
                domain_suffixes.append(line[2:])
            elif line.startswith('.'):
                domain_suffixes.append(line[1:])
            else:
                domains.append(line)

    rule_dict = {}
    if domains: rule_dict["domain"] = domains
    if domain_suffixes: rule_dict["domain_suffix"] = domain_suffixes
    if ip_cidrs: rule_dict["ip_cidr"] = ip_cidrs

    total_rules = len(domains) + len(domain_suffixes) + len(ip_cidrs)
    base_name = os.path.splitext(os.path.basename(txt_path))[0]
    
    if total_rules == 0: 
        print(f"⚠️ [Sing-box] {base_name:<23} | ⚠️ 规则为空被跳过")
        return False

    print(f"✅ [Sing-box] {base_name:<23} | 规则总数: {total_rules:,} (后缀: {len(domain_suffixes):,}, 域名: {len(domains):,}, IP: {len(ip_cidrs):,})")

    json_data = {
        "version": 4,
        "rules": [rule_dict]
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    return True

def run_all():
    os.makedirs("output/singbox", exist_ok=True)
    has_sb = check_singbox()
    
    txt_files = glob("output/mihomo/*.txt")
    for txt_path in txt_files:
        base_name = os.path.splitext(os.path.basename(txt_path))[0]
        json_path = os.path.join("output/singbox", f"{base_name}.json")
        srs_path = os.path.join("output/singbox", f"{base_name}.srs")
        
        if convert_txt_to_json(txt_path, json_path):
            if has_sb:
                try:
                    subprocess.run(["sing-box", "rule-set", "compile", json_path, "-o", srs_path], check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e:
                    print(f"⚠️ 警告: 编译 {base_name}.srs 发生异常:\n{e.stderr}")