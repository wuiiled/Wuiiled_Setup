# -*- coding: utf-8 -*-
"""
MosDNS-X Rule Exporter.
Decoupled: receives canonical RuleSet IR and generates domain: and full: MosDNS rules.
"""

import os
from typing import Dict, Optional

import utils
from core.models import RuleSet


def build_mosdns_rules(rules: Dict[str, RuleSet], output_dir: str = "output/mosdns-x"):
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    os.makedirs(geosite_out, exist_ok=True)
    os.makedirs(geoip_out, exist_ok=True)

    rules = utils.select_oxidns_rules(rules)
    print(f"\n📦 [MosDNS] 正在构建 {len(rules)} 个 OxiDNS 订阅规则并输出至 {output_dir}...")

    for name, rs in rules.items():
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        out_path = os.path.join(sub_dir, f"{name}.txt")
        mos_lines = utils.format_oxidns_lines(rs, domain_prefix="domain:", flatten_host_cidr=False)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(mos_lines) + ("\n" if mos_lines else ""))

    utils.publish_oxidns_compat(output_dir, rules)
    print("✅ [MosDNS] OxiDNS 订阅规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_mosdns_rules(rules)


if __name__ == '__main__':
    run_all()
