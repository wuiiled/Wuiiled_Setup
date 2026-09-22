# -*- coding: utf-8 -*-
"""
Mihomo (Clash Meta) Rule-set Exporter.
Fully decoupled: receives canonical RuleSet IR and exports .txt and .mrs files.
"""

import os
import sys
import shutil
from glob import glob
from typing import Dict, Optional

import utils
from core.models import RuleSet

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def check_mihomo() -> bool:
    return utils.check_mihomo()


def build_mihomo_rules(rules: Dict[str, RuleSet], output_dir: str = "output/mihomo"):
    """
    Export all RuleSets to Mihomo format (.txt and .mrs).
    """
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    os.makedirs(geosite_out, exist_ok=True)
    os.makedirs(geoip_out, exist_ok=True)

    has_m = check_mihomo()
    print(f"\n📦 [Mihomo] 正在构建所有规则集并输出至 {output_dir}...")

    # 1. Export text payloads
    for name, rs in rules.items():
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        txt_path = os.path.join(sub_dir, f"{name}.txt")
        mrs_path = os.path.join(sub_dir, f"{name}.mrs")

        lines = rs.to_mihomo_lines()
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))

        # Compile to .mrs if compiler available
        if has_m:
            rule_type = "ipcidr" if rs.is_geoip else "domain"
            utils.compile_ruleset(
                ["mihomo", "convert-ruleset", rule_type, "text", txt_path, mrs_path],
                f"{name}.mrs"
            )

    # ---------------------------------------------------------------
    # geosite-ad precise blocklist + allow exception (mirrors smartdns/OxiDNS).
    # Mihomo cannot express 'block parent but allow child' inside a single .mrs,
    # but it CAN at the config level: users place a RULE-SET,geosite-ad-allow,DIRECT
    # rule BEFORE RULE-SET,geosite-ad,REJECT so whitelisted domains short-circuit.
    # Therefore mihomo also ships the precise blocklist (re-adding Option-A-released
    # domains) plus a separate allow rule-set.
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
        # Overwrite precise blocklist txt (+ mrs)
        ad_txt = os.path.join(geosite_out, "geosite-ad.txt")
        with open(ad_txt, "w", encoding="utf-8") as f:
            for d in sorted(precise_suffixes):
                if d:
                    f.write("+." + d + chr(10))
        if has_m:
            utils.compile_ruleset(
                ["mihomo", "convert-ruleset", "domain", "text", ad_txt, os.path.join(geosite_out, "geosite-ad.mrs")],
                "geosite-ad.mrs"
            )
        # Allow rule-set: bare domains emitted with '+. ' suffix semantics so that
        # whitelisted parents also cover their subdomains.
        if os.path.exists(opt_allow_path):
            allow_txt = os.path.join(geosite_out, "geosite-ad-allow.txt")
            with open(opt_allow_path, "r", encoding="utf-8") as fin, open(allow_txt, "w", encoding="utf-8") as fout:
                for line in fin:
                    d = line.strip().lstrip("+.").lstrip(".")
                    if d and not d.startswith("#"):
                        fout.write("+." + d + chr(10))
            if has_m:
                utils.compile_ruleset(
                    ["mihomo", "convert-ruleset", "domain", "text", allow_txt, os.path.join(geosite_out, "geosite-ad-allow.mrs")],
                    "geosite-ad-allow.mrs"
                )
        print(f"  [Mihomo] geosite-ad precise={len(precise_suffixes):,} (+ allow rule-set)")

    # 2. Aliases (e.g. geosite-emby -> geosite-custom-emby)
    aliases = {
        "geosite-emby": "geosite-custom-emby",
    }
    for alias_name, target_name in aliases.items():
        sub_dir = geoip_out if alias_name.startswith("geoip-") else geosite_out
        src_txt = os.path.join(sub_dir, f"{target_name}.txt")
        src_mrs = os.path.join(sub_dir, f"{target_name}.mrs")
        dst_txt = os.path.join(sub_dir, f"{alias_name}.txt")
        dst_mrs = os.path.join(sub_dir, f"{alias_name}.mrs")
        if os.path.exists(src_txt):
            utils.safe_copy(src_txt, dst_txt)
        if os.path.exists(src_mrs):
            utils.safe_copy(src_mrs, dst_mrs)

    print("✅ [Mihomo] 全部规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_mihomo_rules(rules)


if __name__ == '__main__':
    run_all()