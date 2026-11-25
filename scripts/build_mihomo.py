# -*- coding: utf-8 -*-
"""
Mihomo (Clash Meta) Rule-set Exporter.
Exports canonical RuleSet IR (including geosite-ad-precise & geosite-ad-allow) to .txt and .mrs.
"""

import os
from typing import Dict, Optional

import utils
from core.cleaner import wildcard_prefix_to_mihomo
from core.models import RuleSet


def check_mihomo() -> bool:
    return utils.check_tool("mihomo")


def build_mihomo_rules(rules: Dict[str, RuleSet], output_dir: str = "output/mihomo") -> None:
    """Export all RuleSets to Mihomo format (.txt and .mrs)."""
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    os.makedirs(geosite_out, exist_ok=True)
    os.makedirs(geoip_out, exist_ok=True)

    has_m = check_mihomo()
    print(f"\n📦 [Mihomo] 正在构建所有规则集并输出至 {output_dir}...")

    for name, rs in rules.items():
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        txt_path = os.path.join(sub_dir, f"{name}.txt")
        mrs_path = os.path.join(sub_dir, f"{name}.mrs")

        if rs.total_count == 0 and rs.raw_lines is None:
            print(f"  ⚠️ [Mihomo] {name:<26} | 空集合, 跳过导出")
            continue

        lines = rs.to_mihomo_lines()
        pattern_lines = [l for l in lines if l.startswith(("DOMAIN-KEYWORD,", "DOMAIN-REGEX,"))]
        if pattern_lines:
            lines = [l for l in lines if not l.startswith(("DOMAIN-KEYWORD,", "DOMAIN-REGEX,"))]
            print(f"  [Mihomo] {name:<26} | 剥离 {len(pattern_lines)} 条 keyword/regex 规则 (已保留于 singbox .srs)")
        if rs.process_names:
            print(f"  [Mihomo] {name:<26} | 丢弃 {len(rs.process_names)} 条 process_name 规则 (已保留于 singbox .srs)")
        unconvertible_wc = sum(1 for w in rs.domain_wildcards if not wildcard_prefix_to_mihomo(w))
        if unconvertible_wc:
            print(f"  [Mihomo] {name:<26} | 丢弃 {unconvertible_wc} 条 glob 通配规则 (已保留于 singbox .srs)")

        if not lines:
            print(f"  ⚠️ [Mihomo] {name:<26} | 剥离后无剩余条目, 跳过导出")
            continue

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        if has_m:
            rule_type = "ipcidr" if rs.is_geoip else "domain"
            utils.compile_ruleset(
                ["mihomo", "convert-ruleset", rule_type, "text", txt_path, mrs_path],
                f"{name}.mrs",
            )

    prec, allow = rules.get("geosite-ad-precise"), rules.get("geosite-ad-allow")
    if prec or allow:
        print(
            f"  [Mihomo] 黑加白 precise={len(prec.domain_suffixes) if prec else 0:,} "
            f"allow={len(allow.domain_suffixes) if allow else 0:,}"
        )

    print("✅ [Mihomo] 全部规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None) -> None:
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_mihomo_rules(rules)


if __name__ == "__main__":
    run_all()
