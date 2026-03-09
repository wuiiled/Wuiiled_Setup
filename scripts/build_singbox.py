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
            
            # 兼容行内注释
            line = line.split('#')[0].strip()
            if not line: continue

            # 判断规则类型
            if '/' in line and any(c.isdigit() for c in line): # 判断为 IP CIDR
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

    # 避免写入空规则导致 sing-box 报错
    if not rule_dict:
        return False

    json_data = {
        "version": 1,
        "rules": [rule_dict]
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    return True

def run_all():
    os.makedirs("output/singbox", exist_ok=True)
    has_sb = check_singbox()
    
    # 直接读取 Mihomo 处理好的全部 txt 文件
    txt_files = glob("output/mihomo/*.txt")
    for txt_path in txt_files:
        base_name = os.path.splitext(os.path.basename(txt_path))[0]
        json_path = os.path.join("output/singbox", f"{base_name}.json")
        srs_path = os.path.join("output/singbox", f"{base_name}.srs")
        
        # 转换 txt 成 sing-box 的 json 格式
        if convert_txt_to_json(txt_path, json_path):
            # 编译 srs
            if has_sb:
                try:
                    subprocess.run(["sing-box", "rule-set", "compile", json_path, "-o", srs_path], check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e:
                    print(f"⚠️ 警告: 编译 {base_name}.srs 发生异常:\n{e.stderr}")