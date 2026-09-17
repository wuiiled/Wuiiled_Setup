# -*- coding: utf-8 -*-
"""
AdGuard Home Rule Exporter.
Decoupled: receives canonical RuleSet IR and exports AdGuard filter rules.
"""

import os
import sys
from typing import Dict, Optional

import utils
import providers
from core.models import RuleSet

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def build_adg_rules(rules: Dict[str, RuleSet], output_dir: str = "output/adg"):
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n📦 [AdGuard Home] 正在构建所有规则集并输出至 {output_dir}...")

    # 1. geosite-ad / ADs_merged_adg
    work_dir = utils.get_work_dir()
    opt_ads_path = os.path.join(work_dir, "ads", "opt_ads.txt")
    opt_allow_path = os.path.join(work_dir, "ads", "opt_allow.txt")

    adg_lines = []
    if os.path.exists(opt_ads_path):
        with open(opt_ads_path, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                domain = line.strip()
                if not domain or domain.startswith('#'):
                    continue
                if domain.startswith("+."):
                    domain = domain[2:]
                elif domain.startswith("."):
                    domain = domain[1:]
                adg_lines.append(f"||{domain}^")

    if os.path.exists(opt_allow_path):
        with open(opt_allow_path, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                domain = line.strip()
                if not domain or domain.startswith('#'):
                    continue
                if domain.startswith("+."):
                    domain = domain[2:]
                elif domain.startswith("."):
                    domain = domain[1:]
                adg_lines.append(f"@@||{domain}^")

    ad_out_path = os.path.join(output_dir, "geosite-ad.txt")
    legacy_ad_path = os.path.join(output_dir, "ADs_merged_adg.txt")
    for p in (ad_out_path, legacy_ad_path):
        with open(p, 'w', encoding='utf-8') as f:
            f.write('\n'.join(adg_lines) + '\n')
    print(f"  ✅ [AdGuard] {'geosite-ad':<24} | 规则数: {len(adg_lines):,} (含白名单例外)")

    # 2. Httpdns
    httpdns_lines = []
    if "geosite-httpdns" in rules:
        rs = rules["geosite-httpdns"]
        for d in sorted(rs.domains | rs.domain_suffixes):
            clean = d.lstrip('.').strip()
            if clean:
                httpdns_lines.append(f"||{clean}^")
    for fname in ("geosite-httpdns.txt", "Httpdns.txt"):
        with open(os.path.join(output_dir, fname), 'w', encoding='utf-8') as f:
            f.write('\n'.join(httpdns_lines) + ('\n' if httpdns_lines else ''))
    print(f"  ✅ [AdGuard] {'geosite-httpdns':<24} | 规则数: {len(httpdns_lines):,}")

    # 3. PCDN
    pcdn_content = utils.download_file(providers.ADG_URLS.get("PCDN", ""))
    pcdn_lines = []
    for line in pcdn_content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        cleaned = utils.clean_mihomo_domain_line(line)
        if cleaned:
            domain = cleaned.lstrip('+.')
            pcdn_lines.append(f"||{domain}^")
    for fname in ("geosite-pcdn.txt", "PCDN.txt"):
        with open(os.path.join(output_dir, fname), 'w', encoding='utf-8') as f:
            f.write('\n'.join(pcdn_lines) + ('\n' if pcdn_lines else ''))
    print(f"  ✅ [AdGuard] {'geosite-pcdn':<24} | 规则数: {len(pcdn_lines):,}")

    print("✅ [AdGuard Home] 全部规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_adg_rules(rules)


if __name__ == '__main__':
    run_all()