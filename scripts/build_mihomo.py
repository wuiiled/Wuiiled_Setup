#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import shutil
import ipaddress
from glob import glob
from concurrent.futures import ThreadPoolExecutor
import utils
import providers
import geodata

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def _merge_allow_list(raw_allow_path, merged_output_path):
    """合并共享白名单、exclude-keyword.txt 以及本地 Custom_Direct_DOMAIN.txt 为统一的白名单文件"""
    allow_content = []
    if os.path.exists(raw_allow_path):
        with open(raw_allow_path, 'r', encoding='utf-8') as f:
            allow_content.append(f.read())
    if os.path.exists(utils.EXCLUDE_FILE):
        with open(utils.EXCLUDE_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    allow_content.append(line + "\n")
    custom_direct = os.path.join(os.path.dirname(__file__), "..", "rules", "Custom_Direct_DOMAIN.txt")
    if os.path.exists(custom_direct):
        with open(custom_direct, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    allow_content.append(line + "\n")
    with open(merged_output_path, 'w', encoding='utf-8') as f:
        f.write("".join(allow_content))

def gen_ads_reject():
    mod_dir = os.path.join(utils.get_work_dir(), "ads")
    os.makedirs(mod_dir, exist_ok=True)
    raw_ads, raw_allow = os.path.join(mod_dir, "raw_ads.txt"), os.path.join(mod_dir, "raw_allow.txt")
    
    utils.download_files_parallel(raw_ads, providers.ADS_BLOCK_URLS)
    
    shared_allow = os.path.join(utils.get_work_dir(), "shared", "raw_allow.txt")
    if os.path.exists(shared_allow):
        shutil.copyfile(shared_allow, raw_allow)
    else:
        with open(raw_allow, 'w', encoding='utf-8') as f: pass

    clean_ads, filter_ads = os.path.join(mod_dir, "clean_ads.txt"), os.path.join(mod_dir, "filter_ads.txt")
    utils.process_normalize_domain(raw_ads, clean_ads, skip_allow_rules=True)
    utils.apply_keyword_filter(clean_ads, filter_ads)

    merged_allow_raw = os.path.join(mod_dir, "merged_allow_raw.txt")
    _merge_allow_list(raw_allow, merged_allow_raw)

    clean_allow, opt_ads, opt_allow, final_ads = [os.path.join(mod_dir, x) for x in ["clean_allow.txt", "opt_ads.txt", "opt_allow.txt", "final_ads.txt"]]
    utils.process_normalize_domain(merged_allow_raw, clean_allow, skip_allow_rules=False)
    utils.optimize_smart_self(filter_ads, opt_ads)
    utils.optimize_smart_self(clean_allow, opt_allow)
    utils.apply_advanced_whitelist_filter(opt_ads, opt_allow, final_ads)
    utils.finalize_output(final_ads, "output/mihomo", "geosite-ad", "add_prefix")

def gen_ai():
    mod_dir = os.path.join(utils.get_work_dir(), "ai")
    os.makedirs(mod_dir, exist_ok=True)
    raw_ai, clean_ai, opt_ai = [os.path.join(mod_dir, x) for x in ["raw_ai.txt", "clean_ai.txt", "opt_ai.txt"]]
    utils.download_files_parallel(raw_ai, providers.AI_URLS)
    utils.process_normalize_domain(raw_ai, clean_ai, skip_allow_rules=False)
    utils.optimize_smart_self(clean_ai, opt_ai)
    utils.finalize_output(opt_ai, "output/mihomo", "geosite-ai", "add_prefix")

def gen_fakeip():
    mod_dir = os.path.join(utils.get_work_dir(), "fakeip")
    os.makedirs(mod_dir, exist_ok=True)
    raw_fakeip_dl = os.path.join(mod_dir, "raw_fakeip_dl.txt")
    utils.download_files_parallel(raw_fakeip_dl, providers.FAKE_IP_URLS)
    unique_lines = set()
    if os.path.exists(raw_fakeip_dl):
        with open(raw_fakeip_dl, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                line = line.lower()
                if re.match(r'^\s*(dns:|fake-ip-filter:)', line): continue
                line = re.sub(r'^\s*-\s*', '', line).replace('"', '').replace("'", '').replace('\\', '').strip()
                if line and not line.startswith('#'): unique_lines.add(line)
    clean_fakeip, final_fakeip = os.path.join(mod_dir, "clean_fakeip.txt"), os.path.join(mod_dir, "final_fakeip.txt")
    with open(clean_fakeip, 'w', encoding='utf-8') as f: f.write('\n'.join(sorted(unique_lines)) + '\n')
    utils.optimize_smart_self(clean_fakeip, final_fakeip)
    utils.finalize_output(final_fakeip, "output/mihomo", "geosite-fakeip-filter", "none")

def gen_ads_drop():
    mod_dir = os.path.join(utils.get_work_dir(), "drop")
    os.makedirs(mod_dir, exist_ok=True)
    raw_rd = os.path.join(mod_dir, "raw_rd.txt")
    utils.download_files_parallel(raw_rd, providers.DROP_URLS)
    rd_lines = set()
    if os.path.exists(raw_rd):
        with open(raw_rd, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                cleaned = utils.clean_mihomo_domain_line(line)
                if cleaned and "skk.moe" not in line.lower() and cleaned != "+.":
                    rd_lines.add(cleaned)
    clean_rd = os.path.join(mod_dir, "clean_rd.txt")
    with open(clean_rd, 'w', encoding='utf-8') as f: f.write('\n'.join(sorted(rd_lines)) + '\n')
    
    raw_allow_temp = os.path.join(utils.get_work_dir(), "shared", "raw_allow.txt")
    merged_allow_raw = os.path.join(mod_dir, "merged_allow_raw.txt")
    _merge_allow_list(raw_allow_temp, merged_allow_raw)
    
    clean_rd_allow, final_rd = os.path.join(mod_dir, "clean_rd_allow.txt"), os.path.join(mod_dir, "final_rd.txt")
    utils.process_normalize_domain(merged_allow_raw, clean_rd_allow, skip_allow_rules=False)
    utils.apply_advanced_whitelist_filter(clean_rd, clean_rd_allow, final_rd)
    utils.finalize_output(final_rd, "output/mihomo", "geosite-reject-drop", "none")

def gen_custom_rules():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(base_dir, ".."))
    
    for name, rel_path in providers.CUSTOM_RULES.items():
        file_path = os.path.join(repo_root, rel_path)
        content = ""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
        lines = []
        is_ip = name.startswith("geoip-") or name.lower().endswith(('_ip', '_ip.txt'))
        for line in content.splitlines():
            if 'PROCESS-NAME' in line: continue
            if is_ip:
                cleaned = utils.clean_ip_line(line)
                if cleaned and utils.is_valid_ip_or_cidr(cleaned):
                    lines.append(cleaned)
            else:
                cleaned_dom = utils.clean_mihomo_domain_line(line)
                if cleaned_dom:
                    lines.append(cleaned_dom)
                    
        lines = sorted(list(set(lines)))
        print(f"✅ [Custom]  {name:<26} | 规则数: {len(lines):,}")
        txt_path = f"output/mihomo/{name}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + ('\n' if lines else ''))

def gen_skk_rules():
    url_cache = {}
    for name, url in providers.MIHOMO_SKK.items():
        if url not in url_cache:
            url_cache[url] = utils.download_file(url)
        content = url_cache[url]
        lines = []
        is_ip = name.startswith("geoip-") or name.lower().endswith(('_ip', '_ip.txt'))
        for line in content.splitlines():
            if 'skk.moe' in line or line.startswith('DOMAIN-WILDCARD,'): continue
            if is_ip:
                cleaned_ip = utils.clean_ip_line(line)
                if cleaned_ip and utils.is_valid_ip_or_cidr(cleaned_ip):
                    lines.append(cleaned_ip)
            else:
                cleaned_dom = utils.clean_mihomo_domain_line(line)
                if cleaned_dom and cleaned_dom != '+.':
                    lines.append(cleaned_dom)
                    
        lines = sorted(list(set(lines)))
        print(f"✅ [SKK]     {name:<26} | 规则数: {len(lines):,}")
        txt_path = f"output/mihomo/{name}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + ('\n' if lines else ''))

def gen_gfwip():
    mod_dir = os.path.join(utils.get_work_dir(), "gfwip")
    os.makedirs(mod_dir, exist_ok=True)
    raw_gfwip = os.path.join(mod_dir, "raw_gfwip.txt")
    utils.download_files_parallel(raw_gfwip, providers.GFW_IP_URLS)

    ipv4_nets = set()
    ipv6_nets = set()

    if os.path.exists(raw_gfwip):
        with open(raw_gfwip, 'r', encoding='utf-8') as f:
            for line in f:
                cleaned = utils.clean_ip_line(line)
                if cleaned:
                    try:
                        net = ipaddress.ip_network(cleaned, strict=False)
                        if net.version == 4: ipv4_nets.add(net)
                        else: ipv6_nets.add(net)
                    except ValueError: pass

    for item in providers.GFW_IPV6_LIST:
        cleaned = utils.clean_ip_line(item)
        if cleaned:
            try:
                net = ipaddress.ip_network(cleaned, strict=False)
                if net.version == 6: ipv6_nets.add(net)
                else: ipv4_nets.add(net)
            except ValueError: pass

    sorted_ipv4 = sorted(list(ipv4_nets), key=lambda x: (int(x.network_address), x.prefixlen))
    sorted_ipv6 = sorted(list(ipv6_nets), key=lambda x: (int(x.network_address), x.prefixlen))

    lines = []
    for net in sorted_ipv4:
        lines.append(str(net.network_address) if net.prefixlen == 32 else str(net))
    for net in sorted_ipv6:
        lines.append(str(net.network_address) if net.prefixlen == 128 else str(net))

    rule_count = len(lines)
    print(f"✅ [Mihomo]  {'geoip-gfw':<26} | 规则数: {rule_count:,} (IPv4: {len(sorted_ipv4):,}, IPv6: {len(sorted_ipv6):,})")

    txt_path = "output/mihomo/geoip-gfw.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

def compile_all_mrs():
    has_m = utils.check_mihomo()
    
    # 批量编译所有 txt 为 mrs
    all_txts = glob("output/mihomo/*.txt")
    for txt_path in all_txts:
        base_name = os.path.splitext(os.path.basename(txt_path))[0]
        mrs_path = os.path.join("output/mihomo", f"{base_name}.mrs")
        
        is_ip = (
            base_name.startswith("geoip-") 
            or base_name.lower().endswith(('_ip', '_ip.txt')) 
            or base_name in ("cnip", "gfwip")
        )
        rule_type = "ipcidr" if is_ip else "domain"
        
        if has_m:
            utils.compile_ruleset(
                ["mihomo", "convert-ruleset", rule_type, "text", txt_path, mrs_path],
                f"{base_name}.mrs"
            )

    # 规范别名支持 (如 geosite-emby)
    for alias_name, target_name in [("geosite-emby", "geosite-custom-emby")]:
        src_txt = os.path.join("output/mihomo", f"{target_name}.txt")
        src_mrs = os.path.join("output/mihomo", f"{target_name}.mrs")
        dst_txt = os.path.join("output/mihomo", f"{alias_name}.txt")
        dst_mrs = os.path.join("output/mihomo", f"{alias_name}.mrs")
        if os.path.exists(src_txt):
            utils.safe_copy(src_txt, dst_txt)
        if os.path.exists(src_mrs):
            utils.safe_copy(src_mrs, dst_mrs)

def run_all():
    os.makedirs("output/mihomo", exist_ok=True)
    work_dir = utils.get_work_dir()
    shared_dir = os.path.join(work_dir, "shared")
    os.makedirs(shared_dir, exist_ok=True)
    shared_allow = os.path.join(shared_dir, "raw_allow.txt")
    utils.download_files_parallel(shared_allow, providers.ALLOW_URLS)

    # 并行执行各个模块与天灵 Geodata 提取
    tasks = [
        gen_ads_reject,
        gen_ai,
        gen_fakeip,
        gen_ads_drop,
        gen_custom_rules,
        gen_skk_rules,
        gen_gfwip,
        geodata.extract_all
    ]
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(t) for t in tasks]
        for future in futures:
            future.result()
            
    print("\n📦 正在编译所有 Mihomo 规则集 (.mrs)...")
    compile_all_mrs()

if __name__ == '__main__':
    run_all()