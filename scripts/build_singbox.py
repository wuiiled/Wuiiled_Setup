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
    # 使用 set 自动去重，优化规则体积和性能
    domains = set()
    domain_suffixes = set()
    domain_regexes = set()
    ip_cidrs = set()

    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            
            line = line.split('#')[0].strip()
            if not line: continue

            if '/' in line and any(c.isdigit() for c in line):
                ip_cidrs.add(line)
            elif line.startswith('+.'):
                suffix = line[2:]
                if not suffix: continue  # 拦截极端的空规则，防止污染全局流量
                if '*' in suffix:
                    regex = suffix.replace('.', r'\.').replace('*', '.*')
                    # +. 代表包含子域名的后缀匹配，正则前需要放宽条件
                    domain_regexes.add(f"^(.*\\.)?{regex}$")
                else:
                    domain_suffixes.add(suffix)
            elif line.startswith('.'):
                suffix = line[1:]
                if not suffix: continue  # 同上拦截
                if '*' in suffix:
                    regex = suffix.replace('.', r'\.').replace('*', '.*')
                    domain_regexes.add(f"^(.*\\.)?{regex}$")
                else:
                    domain_suffixes.add(suffix)
            elif '*' in line:
                if line == '*':
                    # 极端的单星号匹配全部
                    domain_regexes.add(".*")
                elif line.startswith('*.') and line.count('*') == 1:
                    # 常见的如 *.xboxlive.com，转换为 suffix 性能远超正则
                    suffix = line[2:]
                    if suffix: domain_suffixes.add(suffix)
                else:
                    # 处理复杂的多个星号，例如 *-127-*-*-*.nip.io 等
                    regex = line.replace('.', r'\.').replace('*', '.*')
                    domain_regexes.add(f"^{regex}$")
            else:
                domains.add(line)

    rule_dict = {}
    # 将 set 转回排序后的 list，保持 JSON 结构与顺序的稳定
    if domains: rule_dict["domain"] = sorted(list(domains))
    if domain_suffixes: rule_dict["domain_suffix"] = sorted(list(domain_suffixes))
    if domain_regexes: rule_dict["domain_regex"] = sorted(list(domain_regexes))
    if ip_cidrs: rule_dict["ip_cidr"] = sorted(list(ip_cidrs))

    total_rules = len(domains) + len(domain_suffixes) + len(ip_cidrs) + len(domain_regexes)
    base_name = os.path.splitext(os.path.basename(txt_path))[0]
    
    if total_rules == 0: 
        print(f"⚠️ [Sing-box] {base_name:<23} | ⚠️ 规则为空被跳过")
        return False

    print(f"✅ [Sing-box] {base_name:<23} | 规则总数: {total_rules:,} (正则: {len(domain_regexes):,}, 后缀: {len(domain_suffixes):,}, 域名: {len(domains):,}, IP: {len(ip_cidrs):,})")

    json_data = {
        "version": 4,
        "rules": [rule_dict]
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        # ensure_ascii=False 可以让 JSON 内的字符保持原样
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

if __name__ == '__main__':
    run_all()
