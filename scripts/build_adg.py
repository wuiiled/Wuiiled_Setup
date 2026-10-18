# -*- coding: utf-8 -*-
"""
AdGuard Home Rule Exporter.
Decoupled: receives canonical RuleSet IR and exports AdGuard filter rules.
"""

import os
from typing import Dict, Optional

import utils
from core.models import RuleSet


def _write_adg_ruleset(rs: Optional[RuleSet], name: str, output_dir: str) -> None:
    lines = []
    if rs:
        lines = [f"||{d.lstrip('.').strip()}^" for d in sorted(rs.domains | rs.domain_suffixes) if d.lstrip('.').strip()]
        if rs.domain_keywords:
            print(f"  [AdGuard] {name} | 跳过 {len(rs.domain_keywords)} 条 keyword 规则 (AdGuard 无对应语义)")
    with open(os.path.join(output_dir, f"{name}.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    print(f"  ✅ [AdGuard] {name:<24} | 规则数: {len(lines):,}")


def build_adg_rules(rules: Dict[str, RuleSet], output_dir: str = "output/adg"):
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n📦 [AdGuard Home] 正在构建所有规则集并输出至 {output_dir}...")

    # 1. geosite-ad: 统一 AdGuard 源文件 (utils 单一渲染), adg 分支直接发布
    ad_src = utils.render_adguard_geosite_ad()
    ad_out_path = os.path.join(output_dir, "geosite-ad.txt")
    utils.safe_copy(ad_src, ad_out_path)
    with open(ad_out_path, encoding="utf-8") as f:
        adg_count = sum(1 for l in f if l.strip())
    print(f"  [AdGuard] {'geosite-ad':<24} | 规则数: {adg_count:,} (黑加白 ||拦截 + @@||放行)")

    # 2. Httpdns & 3. PCDN
    _write_adg_ruleset(rules.get("geosite-httpdns"), "geosite-httpdns", output_dir)
    _write_adg_ruleset(rules.get("geosite-pcdn"), "geosite-pcdn", output_dir)

    print("✅ [AdGuard Home] 全部规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_adg_rules(rules)


if __name__ == '__main__':
    run_all()