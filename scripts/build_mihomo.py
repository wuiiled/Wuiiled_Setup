# -*- coding: utf-8 -*-
"""
Mihomo (Clash Meta) Rule-set Exporter.
Fully decoupled: receives canonical RuleSet IR and exports .txt and .mrs files.
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
        # mihomo 的 domain behavior (txt/mrs) 只有 domain/+.suffix/*.wildcard 三种表达，
        # 无法承载 keyword/regex 规则：直接编译会把这类行当字面域名塞进 trie（垃圾条目）。
        # 参照 sing-geosite 系转换产物对 mihomo 形态的统一处理，剥离之；
        # keyword/regex 语义仍完整保留在 singbox 分支的 .srs (domain_regex/domain_keyword) 中。
        pattern_lines = [l for l in lines if l.startswith(("DOMAIN-KEYWORD,", "DOMAIN-REGEX,"))]
        if pattern_lines:
            lines = [l for l in lines if not l.startswith(("DOMAIN-KEYWORD,", "DOMAIN-REGEX,"))]
            print(f"  [Mihomo] {name:<26} | 剥离 {len(pattern_lines)} 条 keyword/regex 规则 (domain 格式不支持, 已保留于 singbox .srs)")
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
    # 黑加白模式 (mihomo): emit precise blocklist B + allow exception B as SEPARATE
    # rule-sets.  geosite-ad stays as Option A (backward-compat).  Users opt in via
    # config: RULE-SET,geosite-ad-allow,DIRECT placed BEFORE RULE-SET,geosite-ad-precise,REJECT.
    # ---------------------------------------------------------------
    work_dir = utils.get_work_dir()
    blocklist_b_path = os.path.join(work_dir, "ads", "blocklist_b.txt")
    whitelist_b_path = os.path.join(work_dir, "ads", "whitelist_b.txt")
    bl_b, wl_b = [], []
    if os.path.exists(blocklist_b_path):
        with open(blocklist_b_path, "r", encoding="utf-8") as f:
            bl_b = sorted({l.strip() for l in f if l.strip() and not l.startswith("#")})
        p_txt = os.path.join(geosite_out, "geosite-ad-precise.txt")
        with open(p_txt, "w", encoding="utf-8") as f:
            for d in bl_b:
                f.write("+." + d + "\n")
        if has_m:
            utils.compile_ruleset(
                ["mihomo", "convert-ruleset", "domain", "text", p_txt, os.path.join(geosite_out, "geosite-ad-precise.mrs")],
                "geosite-ad-precise.mrs"
            )
    if os.path.exists(whitelist_b_path):
        with open(whitelist_b_path, "r", encoding="utf-8") as f:
            wl_b = sorted({l.strip() for l in f if l.strip() and not l.startswith("#")})
        a_txt = os.path.join(geosite_out, "geosite-ad-allow.txt")
        with open(a_txt, "w", encoding="utf-8") as f:
            for d in wl_b:
                f.write("+." + d + "\n")
        if has_m:
            utils.compile_ruleset(
                ["mihomo", "convert-ruleset", "domain", "text", a_txt, os.path.join(geosite_out, "geosite-ad-allow.mrs")],
                "geosite-ad-allow.mrs"
            )

    if bl_b or wl_b:
        print(f"  [Mihomo] 黑加白 precise={len(bl_b):,} allow={len(wl_b):,}")

    # 兼容别名机制已退役: 全部规则集统一使用标准名称 (geosite-custom-emby 等)

    print("✅ [Mihomo] 全部规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_mihomo_rules(rules)


if __name__ == '__main__':
    run_all()