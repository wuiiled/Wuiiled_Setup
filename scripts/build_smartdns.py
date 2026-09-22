# -*- coding: utf-8 -*-
"""
SmartDNS Rule Exporter.
Decoupled: receives canonical RuleSet IR and generates SmartDNS domain-set and ip-set rules.
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


def convert_txt_to_smartdns(src_path: str, dst_path: str, is_ip: bool) -> int:
    """Helper to convert Mihomo text format to SmartDNS syntax."""
    smartdns_lines = []
    with open(src_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                smartdns_lines.append(line)
                continue
            parts = line.split('#')
            rule = parts[0].strip()
            comment = f" #{parts[1]}" if len(parts) > 1 else ""
            if not rule:
                continue
            if is_ip:
                cleaned_ip = utils.clean_ip_line(rule)
                if cleaned_ip and utils.is_valid_ip_or_cidr(cleaned_ip):
                    smartdns_lines.append(cleaned_ip + comment)
            else:
                if utils.is_valid_ip_or_cidr(rule):
                    continue
                if rule.startswith('+.'):
                    converted = rule[2:]
                elif rule.startswith('.'):
                    converted = rule[1:]
                elif rule.startswith('*.'):
                    converted = rule
                elif rule.startswith('-.'):
                    converted = rule
                else:
                    converted = "-." + rule
                smartdns_lines.append(converted + comment)

    rules_count = sum(1 for l in smartdns_lines if l.strip() and not l.strip().startswith('#'))
    if rules_count == 0:
        return False

    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(smartdns_lines) + '\n')
    return True


def build_smartdns_rules(rules: Dict[str, RuleSet], output_dir: str = "output/smartdns"):
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    os.makedirs(geosite_out, exist_ok=True)
    os.makedirs(geoip_out, exist_ok=True)

    print(f"\n📦 [SmartDNS] 正在构建所有规则集并输出至 {output_dir}...")

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

    # ---------------------------------------------------------------
    # OxiDNS two-set ad rules (precise block + separate allow exception)
    # Mihomo/Sing-box keep Option-A parent-domain exemption because their
    # rule-set format cannot express 'block parent but allow child'. OxiDNS
    # CAN via matcher negation + sequence short-circuit, so for smartdns we
    # emit a precise blocklist (re-adding Option-A-released domains) plus a
    # separate allowlist file.
    # ---------------------------------------------------------------
    work_dir = utils.get_work_dir()
    optional_release_path = os.path.join(work_dir, "ads", "optional_release.txt")
    opt_allow_path = os.path.join(work_dir, "ads", "opt_allow.txt")
    if "geosite-ad" in rules:
        ad_rs = rules["geosite-ad"]
        precise_suffixes = set(ad_rs.domain_suffixes)
        if os.path.exists(optional_release_path):
            with open(optional_release_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip().lstrip("+.").lstrip(".")
                    if line:
                        precise_suffixes.add(line)
        precise_path = os.path.join(geosite_out, "geosite-ad.txt")
        with open(precise_path, "w", encoding="utf-8") as f:
            for d in sorted(precise_suffixes):
                if d:
                    f.write(d + chr(10))
        allow_path = os.path.join(geosite_out, "geosite-ad-allow.txt")
        if os.path.exists(opt_allow_path):
            utils.safe_copy(opt_allow_path, allow_path)
        print(f"  [SmartDNS] geosite-ad (OxiDNS two-set) precise={len(precise_suffixes):,}")

    # Aliases
    aliases = {"geosite-emby": "geosite-custom-emby"}
    for alias_name, target_name in aliases.items():
        sub_dir = geoip_out if alias_name.startswith("geoip-") else geosite_out
        src = os.path.join(sub_dir, f"{target_name}.txt")
        dst = os.path.join(sub_dir, f"{alias_name}.txt")
        if os.path.exists(src):
            utils.safe_copy(src, dst)

    print("✅ [SmartDNS] 全部规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_smartdns_rules(rules)


if __name__ == '__main__':
    run_all()
