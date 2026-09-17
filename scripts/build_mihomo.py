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