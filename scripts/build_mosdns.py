# -*- coding: utf-8 -*-
"""
MosDNS-X Rule Exporter.
Decoupled: receives canonical RuleSet IR and generates domain: and full: MosDNS rules.
"""

import os
import sys
from typing import Dict, Optional

import utils
from core.models import RuleSet

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def build_mosdns_rules(rules: Dict[str, RuleSet], output_dir: str = "output/mosdns-x"):
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    os.makedirs(geosite_out, exist_ok=True)
    os.makedirs(geoip_out, exist_ok=True)

    print(f"\n📦 [MosDNS] 正在构建所有规则集并输出至 {output_dir}...")

    for name, rs in rules.items():
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        out_path = os.path.join(sub_dir, f"{name}.txt")

        mos_lines = []
        if rs.is_geoip:
            for cidr in sorted(rs.ip_cidrs):
                mos_lines.append(cidr)
        else:
            for s in sorted(rs.domain_suffixes):
                clean_s = s.lstrip('.')
                if clean_s:
                    mos_lines.append(f"domain:{clean_s}")
            for d in sorted(rs.domains):
                clean_d = d.strip()
                if clean_d and clean_d not in rs.domain_suffixes:
                    mos_lines.append(f"full:{clean_d}")
            for k in sorted(rs.domain_keywords):
                mos_lines.append(f"keyword:{k}")
            for r in sorted(rs.domain_regexes):
                mos_lines.append(f"regexp:{r}")

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(mos_lines) + ("\n" if mos_lines else ""))

    print("✅ [MosDNS] 全部规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_mosdns_rules(rules)


if __name__ == '__main__':
    run_all()