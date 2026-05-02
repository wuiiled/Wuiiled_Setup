#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import subprocess
import re
import ipaddress
from glob import glob
import shutil

def check_singbox():
    return shutil.which("sing-box") is not None

def compact_regexes(regex_set):
    """
    终极版正则压缩器：安全过滤 + 智能聚合
    仅在 Fake-IP 列表中被调用
    """
    if not regex_set:
        return []

    # 1. 绝对防御：剔除全局流量接管黑洞
    regex_set.discard(".*")
    regex_set.discard("^.*$")
    regex_set.discard("^(.*\\.)?.*$")
    
    step1 = set()
    # 2. 折叠冗余的连续通配符
    for r in regex_set:
        while r'\..*\..*' in r:
            r = r.replace(r'\..*\..*', r'\..*')
        while r'-.*-.*' in r:
            r = r.replace(r'-.*-.*', r'-.*')
        step1.add(r)
        
    step2 = set()
    # 3. 数字前缀安全聚合 (如 ntp1, ntp2 -> ntp\d*)
    num_pattern = re.compile(r'^(\^?[a-zA-Z_-]+)(\d*)(\\..*)$')
    groups = {}
    for r in step1:
        m = num_pattern.match(r)
        if m:
            prefix, num, suffix = m.groups()
            key = (prefix, suffix)
            if key not in groups:
                groups[key] = set()
            groups[key].add(num)
        else:
            step2.add(r)
            
    for (prefix, suffix), nums in groups.items():
        # 仅当真正存在多个数字变体时，才启用 \d* 匹配
        if len(nums) > 1:
            step2.add(f"{prefix}\\d*{suffix}")
        else:
            step2.add(f"{prefix}{nums.pop()}{suffix}")
            
    step3 = set()
    # 4. 同源后缀合并 (针对 time 服务与 nip/sslip 回环域)
    time_bases = {}
    nip_sslip_bases = set()
    
    time_prefix_regex = re.compile(r'^(\^time(?:\\d*)?\\..*\\.)([^.]+\$)$')
    
    for r in step2:
        m = time_prefix_regex.match(r)
        if m:
            base, tld_with_dollar = m.groups()
            tld = tld_with_dollar[:-1] # 剥离 $
            if base not in time_bases:
                time_bases[base] = set()
            time_bases[base].add(tld)
        elif r.endswith("nip\\.io$") or r.endswith("sslip\\.io$"):
            base = r.replace("nip\\.io$", "").replace("sslip\\.io$", "")
            nip_sslip_bases.add(base)
        else:
            step3.add(r)
            
    # 执行 time 合并
    for base, tlds in time_bases.items():
        if len(tlds) > 1:
            tld_str = "|".join(sorted(list(tlds)))
            step3.add(f"{base}({tld_str})$")
        else:
            step3.add(f"{base}{tlds.pop()}$")
            
    # 执行回环地址合并
    for base in nip_sslip_bases:
        step3.add(f"{base}(nip|sslip)\\.io$")
        
    return sorted(list(step3))

def convert_txt_to_json(txt_path, json_path):
    domains = set()
    domain_suffixes = set()
    domain_regexes = set()
    ip_cidrs = set()
    
    base_name = os.path.splitext(os.path.basename(txt_path))[0]

    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            
            line = line.split('#')[0].strip()
            if not line: continue

            # 拦截 1: 严格 IP 与 CIDR 提取
            try:
                net = ipaddress.ip_network(line, strict=False)
                ip_cidrs.add(str(net))
                continue
            except ValueError:
                pass

            # 拦截 2: 过滤包含空格或冒号的脏数据
            if ' ' in line or ':' in line:
                continue

            # 拦截 3: 安全转义处理与前缀剥离
            if line.startswith('+.'):
                suffix = line[2:]
                if not suffix: continue 
                if '*' in suffix:
                    escaped = re.escape(suffix).replace(r'\*', '.*')
                    domain_regexes.add(f"^(.*\\.)?{escaped}$")
                else:
                    domain_suffixes.add(suffix)
            elif line.startswith('.'):
                suffix = line[1:]
                if not suffix: continue
                if '*' in suffix:
                    escaped = re.escape(suffix).replace(r'\*', '.*')
                    domain_regexes.add(f"^(.*\\.)?{escaped}$")
                else:
                    domain_suffixes.add(suffix)
            elif '*' in line:
                if line == '*':
                    pass # 抛弃
                elif line.startswith('*.') and line.count('*') == 1:
                    suffix = line[2:]
                    if suffix: domain_suffixes.add(suffix)
                else:
                    escaped = re.escape(line).replace(r'\*', '.*')
                    domain_regexes.add(f"^{escaped}$")
            else:
                domains.add(line)

    rule_dict = {}
    
    if domains: rule_dict["domain"] = sorted(list(domains))
    if domain_suffixes: rule_dict["domain_suffix"] = sorted(list(domain_suffixes))
    if ip_cidrs: rule_dict["ip_cidr"] = sorted(list(ip_cidrs))
    
    # 核心改动：仅对 Fake-IP 列表执行智能正则压缩，其他列表原样输出
    if domain_regexes:
        is_fake_ip = "fake_ip" in base_name.lower() or "fake-ip" in base_name.lower()
        if is_fake_ip:
            optimized_regexes = compact_regexes(domain_regexes)
            if optimized_regexes:
                rule_dict["domain_regex"] = optimized_regexes
        else:
            rule_dict["domain_regex"] = sorted(list(domain_regexes))

    total_rules = len(domains) + len(domain_suffixes) + len(ip_cidrs) + len(rule_dict.get("domain_regex", []))
    
    if total_rules == 0: 
        print(f"⚠️ [Sing-box] {base_name:<23} | ⚠️ 规则为空被跳过")
        return False

    print(f"✅ [Sing-box] {base_name:<23} | 规则总数: {total_rules:,} (正则: {len(rule_dict.get('domain_regex', [])):,}, 后缀: {len(domain_suffixes):,}, 域名: {len(domains):,}, IP: {len(ip_cidrs):,})")

    json_data = {
        "version": 5,
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

if __name__ == '__main__':
    run_all()
