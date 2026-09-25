# -*- coding: utf-8 -*-
"""
SmartDNS Rule Exporter.
Decoupled: receives canonical RuleSet IR and generates SmartDNS domain-set and ip-set rules.
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


def build_smartdns_rules(rules: Dict[str, RuleSet], output_dir: str = "output/smartdns"):
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    os.makedirs(geosite_out, exist_ok=True)
    os.makedirs(geoip_out, exist_ok=True)

    # OxiDNS 白名单: smartdns 分支只同步 DNS 服务器实际订阅的规则集
    # (清单与 OxiDNS 配置 downloads 段一致, 见 providers.OXIDNS_RULE_FILES / EXTRA / ALIASES)
    whitelist = set(providers.OXIDNS_RULE_FILES.values()) | providers.OXIDNS_EXTRA_RULESETS
    rules = {name: rs for name, rs in rules.items() if name in whitelist}
    # 黑加白双集合不在主 IR 中, 由 manager 产出的文件按需合成 (线上 OxiDNS 订阅)
    for _name, _bw in utils.load_blackwhite_rulesets().items():
        if _name in whitelist:
            rules[_name] = _bw

    print(f"\n📦 [SmartDNS] 正在构建 {len(rules)} 个 OxiDNS 订阅规则集并输出至 {output_dir}...")

    for name, rs in rules.items():
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        out_path = os.path.join(sub_dir, f"{name}.txt")

        smartdns_lines = []
        if rs.is_geoip:
            for cidr in sorted(rs.ip_cidrs):
                if "." in cidr and cidr.endswith("/32"):
                    smartdns_lines.append(cidr[:-3])
                elif ":" in cidr and cidr.endswith("/128"):
                    smartdns_lines.append(cidr[:-4])
                else:
                    smartdns_lines.append(cidr)
        else:
            for s in sorted(rs.domain_suffixes):
                clean_s = s.lstrip('.')
                if clean_s:
                    smartdns_lines.append(clean_s)
            for d in sorted(rs.domains):
                clean_d = d.strip()
                if clean_d and clean_d not in rs.domain_suffixes:
                    smartdns_lines.append(f"-.{clean_d}")

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(smartdns_lines) + ("\n" if smartdns_lines else ""))

    # OxiDNS 兼容副本: 以 OxiDNS 配置期望的历史文件名在 rules/ 根目录落一份,
    # 保证线上订阅直链 (smartdns/rules/CN_merged.txt 等) 持续可用
    for legacy_name, ruleset_name in providers.OXIDNS_RULE_FILES.items():
        rs = rules.get(ruleset_name)
        if rs is None:
            continue
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        src = os.path.join(sub_dir, f"{ruleset_name}.txt")
        if os.path.exists(src):
            utils.safe_copy(src, os.path.join(output_dir, legacy_name))

    # 线上旧命名订阅的子目录别名副本 (geosite/geosite-geolocation-!cn.txt 等)
    for rel, ruleset_name in providers.OXIDNS_SUBDIR_ALIASES.items():
        rs = rules.get(ruleset_name)
        if rs is None:
            continue
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        src = os.path.join(sub_dir, f"{ruleset_name}.txt")
        dst = os.path.join(output_dir, rel)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            utils.safe_copy(src, dst)

    print("✅ [SmartDNS] OxiDNS 订阅规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_smartdns_rules(rules)


if __name__ == '__main__':
    run_all()
