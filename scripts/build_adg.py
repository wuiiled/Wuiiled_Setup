# -*- coding: utf-8 -*-
"""
AdGuard Home Rule Exporter.
Decoupled: receives canonical RuleSet IR and exports AdGuard filter rules.
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


def build_adg_rules(rules: Dict[str, RuleSet], output_dir: str = "output/adg"):
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n📦 [AdGuard Home] 正在构建所有规则集并输出至 {output_dir}...")

    # 1. geosite-ad: 统一 AdGuard 源文件 (utils 单一渲染), adg 分支直接发布
    #    (singbox 分支以同一文件 --type adguard 转 srs, 两分支同源派生)
    ad_src = utils.render_adguard_geosite_ad()
    ad_out_path = os.path.join(output_dir, "geosite-ad.txt")
    utils.safe_copy(ad_src, ad_out_path)
    adg_count = sum(1 for l in open(ad_out_path, encoding='utf-8') if l.strip())
    print(f"  [AdGuard] {'geosite-ad':<24} | 规则数: {adg_count:,} (黑加白 ||拦截 + @@||放行)")

    # 2. Httpdns
    httpdns_lines = []
    if "geosite-httpdns" in rules:
        rs = rules["geosite-httpdns"]
        for d in sorted(rs.domains | rs.domain_suffixes):
            clean = d.lstrip('.').strip()
            if clean:
                httpdns_lines.append(f"||{clean}^")
        if rs.domain_keywords:
            print(f"  [AdGuard] geosite-httpdns | 跳过 {len(rs.domain_keywords)} 条 keyword 规则 (AdGuard 无对应语义)")
    for fname in ("geosite-httpdns.txt",):
        with open(os.path.join(output_dir, fname), 'w', encoding='utf-8') as f:
            f.write('\n'.join(httpdns_lines) + ('\n' if httpdns_lines else ''))
    print(f"  ✅ [AdGuard] {'geosite-httpdns':<24} | 规则数: {len(httpdns_lines):,}")

    # 3. PCDN: 已由 manager 统一装载为 IR (geosite-pcdn), 此处仅做 AdGuard 格式渲染
    pcdn_lines = []
    pcdn_rs = rules.get("geosite-pcdn")
    if pcdn_rs:
        for d in sorted(pcdn_rs.domains | pcdn_rs.domain_suffixes):
            clean = d.lstrip('.').strip()
            if clean:
                pcdn_lines.append(f"||{clean}^")
    for fname in ("geosite-pcdn.txt",):
        with open(os.path.join(output_dir, fname), 'w', encoding='utf-8') as f:
            f.write('\n'.join(pcdn_lines) + ('\n' if pcdn_lines else ''))
    print(f"  ✅ [AdGuard] {'geosite-pcdn':<24} | 规则数: {len(pcdn_lines):,}")

    print("✅ [AdGuard Home] 全部规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_adg_rules(rules)


if __name__ == '__main__':
    run_all()