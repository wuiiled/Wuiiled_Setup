#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import shutil
import utils
import providers

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def run_all():
    os.makedirs("output/mosdns-x", exist_ok=True)

    # 1. 转换 geosite-ad
    base_ads = "output/mihomo/geosite/geosite-ad.txt"
    if not os.path.exists(base_ads):
        base_ads = "output/mihomo/geosite-ad.txt"
    if os.path.exists(base_ads):
        lines = []
        with open(base_ads, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                if not line.strip() or line.startswith('#'): continue
                line = re.sub(r'^(DOMAIN-SUFFIX,|\+\.)', '', line)
                lines.append(line)
        with open("output/mosdns-x/ad_domain_list.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print(f"✅ [MosDNS] {'ad_domain_list':<25} | 规则数: {len(lines):,}")

    # 2. SKK 规则 (从 mihomo 已生成的 txt 读取，不再重复下载)
    for name in providers.MIHOMO_SKK:
        if name in ("download", "geosite-download"): continue
        is_ip = name.startswith("geoip-") or name.lower().endswith(('_ip', '_ip.txt'))
        sub_dir = "geoip" if is_ip else "geosite"
        mihomo_txt = f"output/mihomo/{sub_dir}/{name}.txt"
        if not os.path.exists(mihomo_txt):
            mihomo_txt = f"output/mihomo/{name}.txt"
        if not os.path.exists(mihomo_txt):
            print(f"⚠️ [MosDNS] {name} 源文件不存在，跳过")
            continue
        # IP 规则集直接以纯 IP CIDR 文本输出，与 gfwip 保持一致
        if is_ip:
            shutil.copyfile(mihomo_txt, f"output/mosdns-x/{name}.txt")
            print(f"✅ [MosDNS] {name:<25} | 规则已生成 (IP 规则)")
            continue
        lines = []
        with open(mihomo_txt, 'r', encoding='utf-8') as f:
            for line in f:
                cleaned = line.strip()
                if not cleaned or cleaned.startswith('#') or cleaned == '+.':
                    continue
                if 'skk.moe' in cleaned:
                    continue
                if utils.is_valid_ip_or_cidr(cleaned):
                    continue
                if cleaned.startswith('+.'):
                    lines.append('domain:' + cleaned[2:])
                else:
                    lines.append('full:' + cleaned)
        with open(f"output/mosdns-x/{name}.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print(f"✅ [MosDNS] {name:<25} | 规则数: {len(lines):,}")

    # 3. 复制 geoip-gfw.txt (IP 规则无需额外转换)
    mihomo_gfwip = "output/mihomo/geoip/geoip-gfw.txt"
    if not os.path.exists(mihomo_gfwip):
        mihomo_gfwip = "output/mihomo/geoip-gfw.txt"
    if os.path.exists(mihomo_gfwip):
        shutil.copyfile(mihomo_gfwip, "output/mosdns-x/geoip-gfw.txt")
        print(f"✅ [MosDNS] {'geoip-gfw':<25} | 规则已生成")