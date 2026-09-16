#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import subprocess
import re
import ipaddress
from glob import glob
import shutil
import utils

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def check_singbox():
    has_sb = shutil.which("sing-box") is not None
    if not has_sb and sys.platform == "win32" and shutil.which("wsl"):
        has_sb = True
    if not has_sb and os.environ.get("GITHUB_ACTIONS") == "true":
        print("❌ 错误: 在 GitHub Actions 环境中未找到 'sing-box' 编译器！必须中断任务以防生成残缺规则集。")
        sys.exit(1)
    if has_sb:
        try:
            cmd = utils._resolve_cmd(["sing-box", "version"])
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"📋 sing-box 版本: {result.stdout.strip().splitlines()[0]}")
        except Exception:
            pass
    return has_sb

def compact_regexes(regex_set):
    """
    终极版正则压缩器：安全过滤 + 智能聚合
    仅在 Fake-IP 列表中被调用
    """
    if not regex_set:
        return []

    regex_set.discard(".*")
    regex_set.discard("^.*$")
    regex_set.discard("^(.*\\.)?.*$")
    
    step1 = set()
    for r in regex_set:
        while r'\..*\..*' in r:
            r = r.replace(r'\..*\..*', r'\..*')
        while r'-.*-.*' in r:
            r = r.replace(r'-.*-.*', r'-.*')
        step1.add(r)
        
    step2 = set()
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
        if len(nums) > 1:
            step2.add(f"{prefix}\\d*{suffix}")
        else:
            step2.add(f"{prefix}{nums.pop()}{suffix}")
            
    step3 = set()
    time_bases = {}
    nip_sslip_bases = set()
    
    time_prefix_regex = re.compile(r'^(\^time(?:\\d*)?\\..*\\.)([^.]+\$)$')
    
    for r in step2:
        m = time_prefix_regex.match(r)
        if m:
            base, tld_with_dollar = m.groups()
            tld = tld_with_dollar[:-1]
            if base not in time_bases:
                time_bases[base] = set()
            time_bases[base].add(tld)
        elif r.endswith("nip\\.io$") or r.endswith("sslip\\.io$"):
            base = r.replace("nip\\.io$", "").replace("sslip\\.io$", "")
            nip_sslip_bases.add(base)
        else:
            step3.add(r)
            
    for base, tlds in time_bases.items():
        if len(tlds) > 1:
            tld_str = "|".join(sorted(list(tlds)))
            step3.add(f"{base}({tld_str})$")
        else:
            step3.add(f"{base}{tlds.pop()}$")
            
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
                    if suffix == 'cn':
                        domain_suffixes.add('cn')
                    elif '.' not in suffix:
                        domain_suffixes.add('.' + suffix)
                    else:
                        domain_suffixes.add(suffix)
            elif line.startswith('.'):
                suffix = line[1:]
                if not suffix: continue
                if '*' in suffix:
                    escaped = re.escape(suffix).replace(r'\*', '.*')
                    domain_regexes.add(f"^(.*\\.)?{escaped}$")
                else:
                    if suffix == 'cn':
                        domain_suffixes.add('cn')
                    elif '.' not in suffix:
                        domain_suffixes.add('.' + suffix)
                    else:
                        domain_suffixes.add(suffix)
            elif '*' in line:
                if line == '*':
                    pass
                elif line.startswith('*.') and line.count('*') == 1:
                    suffix = line[2:]
                    if suffix:
                        if suffix == 'cn':
                            domain_suffixes.add('cn')
                        elif '.' not in suffix:
                            domain_suffixes.add('.' + suffix)
                        else:
                            domain_suffixes.add(suffix)
                else:
                    escaped = re.escape(line).replace(r'\*', '.*')
                    domain_regexes.add(f"^{escaped}$")
            else:
                domains.add(line)

    rule_dict = {}
    
    if domains: rule_dict["domain"] = sorted(list(domains))
    if domain_suffixes: rule_dict["domain_suffix"] = sorted(list(domain_suffixes))
    if ip_cidrs: rule_dict["ip_cidr"] = sorted(list(ip_cidrs))
    
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
        return False

    print(f"✅ [Sing-box] {base_name:<26} | 规则总数: {total_rules:,} (正则: {len(rule_dict.get('domain_regex', [])):,}, 后缀: {len(domain_suffixes):,}, 域名: {len(domains):,}, IP: {len(ip_cidrs):,})")

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
    
    # 1. 优先处理复合规则 (既有域名又有 IP)，合体编译
    paired_configs = [
        ("custom-direct", "geosite-custom-direct.txt", "geoip-custom-direct.txt"),
        ("custom-dns", "geosite-custom-dns.txt", "geoip-custom-dns.txt"),
        ("private", "geosite-private.txt", "geoip-private.txt"),
    ]
    
    for comp_name, site_name, ip_name in paired_configs:
        site_path = os.path.join("output/mihomo", site_name)
        ip_path = os.path.join("output/mihomo", ip_name)
        
        if os.path.exists(site_path) and os.path.exists(ip_path):
            print(f"📦 [Sing-box] 复合规则正在合并: {site_name} + {ip_name} -> {comp_name}.srs")
            merged_lines = []
            for p in [site_path, ip_path]:
                with open(p, 'r', encoding='utf-8') as f:
                    merged_lines.extend(f.readlines())
                    
            temp_dir = utils.get_work_dir()
            temp_f_path = os.path.join(temp_dir, f"{comp_name}.txt")
            with open(temp_f_path, 'w', encoding='utf-8') as temp_f:
                temp_f.writelines(merged_lines)
                
            try:
                json_path = os.path.join("output/singbox", f"{comp_name}.json")
                srs_path = os.path.join("output/singbox", f"{comp_name}.srs")
                if convert_txt_to_json(temp_f_path, json_path):
                    if has_sb:
                        utils.compile_ruleset(
                            ["sing-box", "rule-set", "compile", json_path, "-o", srs_path],
                            f"{comp_name}.srs"
                        )
            finally:
                if os.path.exists(temp_f_path):
                    os.remove(temp_f_path)
                    
    # 2. 编译所有标准规则 (包括单个 geosite- 和 geoip-)
    for txt_path in txt_files:
        base_name = os.path.splitext(os.path.basename(txt_path))[0]
        json_path = os.path.join("output/singbox", f"{base_name}.json")
        srs_path = os.path.join("output/singbox", f"{base_name}.srs")
        
        if convert_txt_to_json(txt_path, json_path):
            if has_sb:
                utils.compile_ruleset(
                    ["sing-box", "rule-set", "compile", json_path, "-o", srs_path],
                    f"{base_name}.srs"
                )

    # 3. 生成向后兼容的别名文件 (平滑过渡保障)
    aliases = {
        "Custom_Direct": "custom-direct",
        "Custom-Direct": "custom-direct",
        "Custom_Direct_DOMAIN": "geosite-custom-direct",
        "Custom_Direct_IP": "geoip-custom-direct",
        "Custom_DNS": "custom-dns",
        "Custom-DNS": "custom-dns",
        "Custom_DNS_DOMAIN": "geosite-custom-dns",
        "Custom_DNS_IP": "geoip-custom-dns",
        "Custom_Emby": "geosite-custom-emby",
        "Custom-Emby": "geosite-custom-emby",
        "Custom_Download": "geosite-custom-download",
        "Custom-Download": "geosite-custom-download",
        "Custom_Proxy": "geosite-custom-proxy",
        "Custom-Proxy": "geosite-custom-proxy",
        "Custom_ADs_merged": "geosite-ad",
        "ADs_merged": "geosite-ad",
        "AIs_merged": "geosite-ai",
        "Fake_IP_Filter_merged": "geosite-fakeip-filter",
        "Reject_Drop_merged": "geosite-reject-drop",
        "download": "geosite-download",
        "microsoft_cdn": "geosite-microsoft-cdn",
        "apple_services": "geosite-apple-services",
        "apple_cn": "geosite-apple-cn",
        "apple_cdn": "geosite-apple-cdn",
        "stream_ip": "geoip-stream",
        "apple_services_ip": "geoip-apple",
        "cnip": "geoip-cn",
        "cn": "geosite-cn",
        "gfw": "geosite-gfw",
        "proxy": "geosite-geolocation-!cn",
        "CN_merged": "geosite-cn",
        "telegram": "geoip-telegram",
        "twitter": "geoip-twitter",
        "facebook": "geoip-facebook",
    }
    
    for old_name, target_name in aliases.items():
        target_srs = os.path.join("output/singbox", f"{target_name}.srs")
        target_json = os.path.join("output/singbox", f"{target_name}.json")
        old_srs = os.path.join("output/singbox", f"{old_name}.srs")
        old_json = os.path.join("output/singbox", f"{old_name}.json")
        
        if os.path.exists(target_srs):
            utils.safe_copy(target_srs, old_srs)
        if os.path.exists(target_json):
            utils.safe_copy(target_json, old_json)

if __name__ == '__main__':
    run_all()
