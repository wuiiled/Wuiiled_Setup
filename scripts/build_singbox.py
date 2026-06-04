#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import subprocess
import re
import ipaddress
from glob import glob
import shutil
import utils

def check_singbox():
    has_sb = shutil.which("sing-box") is not None
    if not has_sb and os.environ.get("GITHUB_ACTIONS") == "true":
        import sys
        print("❌ 错误: 在 GitHub Actions 环境中未找到 'sing-box' 编译器！必须中断任务以防生成残缺规则集。")
        sys.exit(1)
    return has_sb

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
    processed_files = set()
    
    # 查找所有后缀为 _DOMAIN.txt 的文件，并匹配是否有同名的 _IP.txt 文件
    domain_files = [f for f in txt_files if os.path.splitext(os.path.basename(f))[0].endswith("_DOMAIN")]
    
    for domain_path in domain_files:
        base_dir = os.path.dirname(domain_path)
        base_name_domain = os.path.splitext(os.path.basename(domain_path))[0]
        prefix = base_name_domain[:-7]  # 去除 "_DOMAIN" 后缀，获取主规则名 (如 Custom_DNS)
        ip_path = os.path.join(base_dir, f"{prefix}_IP.txt")
        
        if os.path.exists(ip_path):
            print(f"📦 [Sing-box] 检测到配对规则，正在合并: {base_name_domain} + {prefix}_IP -> {prefix}")
            
            # 读取并合并两个文件的规则内容
            merged_lines = []
            for path in [domain_path, ip_path]:
                with open(path, 'r', encoding='utf-8') as f:
                    merged_lines.extend(f.readlines())
            
            # 写入临时文本文件，供 convert_txt_to_json 转换使用
            temp_dir = utils.get_work_dir()
            temp_f_path = os.path.join(temp_dir, f"{prefix}.txt")
            with open(temp_f_path, 'w', encoding='utf-8') as temp_f:
                temp_f.writelines(merged_lines)
                
            try:
                json_path = os.path.join("output/singbox", f"{prefix}.json")
                srs_path = os.path.join("output/singbox", f"{prefix}.srs")
                
                if convert_txt_to_json(temp_f_path, json_path):
                    if has_sb:
                        try:
                            subprocess.run(["sing-box", "rule-set", "compile", json_path, "-o", srs_path], check=True, capture_output=True, text=True)
                        except subprocess.CalledProcessError as e:
                            print(f"⚠️ 警告: 编译 {prefix}.srs 发生异常:\n{e.stderr}")
            finally:
                if os.path.exists(temp_f_path):
                    os.remove(temp_f_path)
            
            processed_files.add(domain_path)
            processed_files.add(ip_path)
            
    # 处理其它无需合并的正常规则文件
    for txt_path in txt_files:
        if txt_path in processed_files:
            continue
            
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
