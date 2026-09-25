# -*- coding: utf-8 -*-
"""
Sing-box Rule-set Exporter.
Fully decoupled: receives canonical RuleSet IR and exports .srs and .json files.
Guarantees 100% Zero-Diff alignment with Tianling Shen for all Tianling rulesets.
"""

import os
import sys
import json
import subprocess
import shutil
from typing import Dict, Optional

import utils
from core.models import RuleSet
from core.patcher import get_active_patch_count

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def check_singbox() -> bool:
    has_sb = shutil.which("sing-box") is not None
    if not has_sb and sys.platform == "win32" and shutil.which("wsl"):
        has_sb = True
    if not has_sb and os.environ.get("GITHUB_ACTIONS") == "true":
        print("❌ 错误: 在 GitHub Actions 环境中未找到 'sing-box' 编译器！")
        sys.exit(1)
    return has_sb


def convert_txt_to_json(txt_path: str, json_path: str) -> bool:
    """Helper to convert Mihomo text format to Sing-box JSON format."""
    import ipaddress
    import re
    domains = set()
    domain_suffixes = set()
    domain_regexes = set()
    ip_cidrs = set()

    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            line = line.split('#')[0].strip()
            if not line: continue

            try:
                net = ipaddress.ip_network(line, strict=False)
                ip_cidrs.add(str(net))
                continue
            except ValueError:
                pass

            if ' ' in line or ':' in line:
                continue

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
                    pass
                elif line.startswith('*.') and line.count('*') == 1:
                    suffix = line[2:]
                    if suffix:
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
    if domain_regexes: rule_dict["domain_regex"] = sorted(list(domain_regexes))

    total = len(domains) + len(domain_suffixes) + len(ip_cidrs) + len(domain_regexes)
    if total == 0:
        return False

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({"version": 5, "rules": [rule_dict]}, f, indent=2, ensure_ascii=False)
    return True


def build_singbox_rules(rules: Dict[str, RuleSet], output_dir: str = "output/singbox"):
    """
    Export all RuleSets to Sing-box format (.srs and .json).
    """
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    os.makedirs(geosite_out, exist_ok=True)
    os.makedirs(geoip_out, exist_ok=True)

    has_sb = check_singbox()
    print(f"\n📦 [Sing-box] 正在构建所有规则集并输出至 {output_dir}...")

    # 1. Handle composite custom rules (domains + IPs together)
    composite_specs = [
        ("geosite-custom-direct", "geosite-custom-direct", "geoip-custom-direct"),
        ("geosite-custom-dns", "geosite-custom-dns", "geoip-custom-dns"),
    ]

    for comp_name, domain_key, ip_key in composite_specs:
        comp_domains = set()
        comp_suffixes = set()
        comp_ips = set()

        if domain_key in rules:
            comp_domains.update(rules[domain_key].domains)
            comp_suffixes.update(rules[domain_key].domain_suffixes)
        if ip_key in rules:
            comp_ips.update(rules[ip_key].ip_cidrs)

        comp_rs = RuleSet(
            name=comp_name,
            category="geosite",
            description="复合自定义规则 (域名 + IP)",
            domains=comp_domains,
            domain_suffixes=comp_suffixes,
            ip_cidrs=comp_ips
        )
        rules[comp_name] = comp_rs

    # 2. Build each ruleset
    for name, rs in rules.items():
        # Do not output raw geoip-custom-* into singbox if already merged into geosite-custom-*
        if name in ("geoip-custom-direct", "geoip-custom-dns"):
            continue

        sub_dir = geoip_out if rs.is_geoip else geosite_out
        srs_path = os.path.join(sub_dir, f"{name}.srs")
        json_path = os.path.join(sub_dir, f"{name}.json")

        if rs.raw_srs and get_active_patch_count(name) == 0:
            # Authoritative Tianling rule (no local patches): write raw SRS directly (100% binary match!)
            with open(srs_path, "wb") as f:
                f.write(rs.raw_srs)
            if has_sb:
                try:
                    cmd = utils._resolve_cmd(["sing-box", "rule-set", "decompile", srs_path, "-o", json_path])
                    subprocess.run(cmd, check=True, capture_output=True, text=True)
                except Exception as e:
                    print(f"⚠️ 反编译 {name}.srs 失败: {e}")
        else:
            # Generated rule: export json, compile to srs
            json_dict = rs.to_singbox_dict(version=5)
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(json_dict, jf, indent=2, ensure_ascii=False)

            if has_sb:
                utils.compile_ruleset(
                    ["sing-box", "rule-set", "compile", json_path, "-o", srs_path],
                    f"{name}.srs"
                )

    # 兼容别名机制已退役: 全部规则集统一使用标准名称 (geosite-games / geosite-apple-cdn 等)
    print("✅ [Sing-box] 全部规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_singbox_rules(rules)


if __name__ == '__main__':
    run_all()
