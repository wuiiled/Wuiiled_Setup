# -*- coding: utf-8 -*-
"""
Sing-box Rule-set Exporter.
Synthesizes sing-box composite rules on a local copy without mutating shared IR.
"""

import json
import os
from typing import Dict, List, Optional, Set

import utils
from core.models import RuleSet
from core.patcher import get_active_patch_count, has_patch_includes

ADGUARD_SOURCE_SETS = {"geosite-ad"}
_SKIPPED_STANDALONE = {
    "geoip-custom-direct",
    "geoip-custom-dns",
    "geoip-iptv-!cn",
    "geoip-ai",
    "geosite-ad-precise",
    "geosite-ad-allow",
}


def check_singbox() -> bool:
    return utils.check_tool("sing-box")


def synthesize_composites(rules: Dict[str, RuleSet]) -> None:
    """Synthesize sing-box composite rules (domain + keyword + regex + process + IP)."""
    composite_specs = [
        ("geosite-custom-direct", "geosite-custom-direct", "geoip-custom-direct"),
        ("geosite-custom-dns", "geosite-custom-dns", "geoip-custom-dns"),
        ("geosite-iptv-!cn", "geosite-iptv-!cn", "geoip-iptv-!cn"),
        ("geosite-ai", "geosite-ai", "geoip-ai"),
        ("geosite-stream", "geosite-stream", "geoip-stream"),
    ]

    for comp_name, domain_key, ip_key in composite_specs:
        if domain_key not in rules and ip_key not in rules:
            continue
        comp_domains: Set[str] = set()
        comp_suffixes: Set[str] = set()
        comp_keywords: Set[str] = set()
        comp_regexes: Set[str] = set()
        comp_processes: Set[str] = set()
        comp_wildcards: Set[str] = set()
        comp_ips: Set[str] = set()
        sources: List[str] = []
        desc = "复合自定义规则 (域名 + IP)"
        source_kind = "custom"

        if domain_key in rules:
            dom_rs = rules[domain_key]
            comp_domains.update(dom_rs.domains)
            comp_suffixes.update(dom_rs.domain_suffixes)
            comp_keywords.update(dom_rs.domain_keywords)
            comp_regexes.update(dom_rs.domain_regexes)
            comp_processes.update(dom_rs.process_names)
            comp_wildcards.update(dom_rs.domain_wildcards)
            sources += list(dom_rs.sources)
            if dom_rs.description:
                desc = dom_rs.description
            if dom_rs.source_kind:
                source_kind = dom_rs.source_kind
        if ip_key in rules:
            comp_ips.update(rules[ip_key].ip_cidrs)
            for s in rules[ip_key].sources:
                if s not in sources:
                    sources.append(s)

        rules[comp_name] = RuleSet(
            name=comp_name,
            category="geosite",
            description=desc,
            domains=comp_domains,
            domain_suffixes=comp_suffixes,
            domain_keywords=comp_keywords,
            domain_regexes=comp_regexes,
            process_names=comp_processes,
            domain_wildcards=comp_wildcards,
            ip_cidrs=comp_ips,
            source_kind=source_kind,
            sources=sources,
        )


def _build_adguard_srs(rules: Dict[str, RuleSet], name: str, sub_dir: str, has_sb: bool) -> None:
    lines = utils.render_adguard_lines(rules)
    txt_path = os.path.join(sub_dir, f"{name}.txt")
    srs_path = os.path.join(sub_dir, f"{name}.srs")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    print(f"  [Sing-box] {name:<26} | AdGuard 语法 {len(lines):,} 行 (||拦截 + @@||放行)")

    if has_sb:
        utils.compile_ruleset(
            ["sing-box", "rule-set", "convert", "--type", "adguard", "-o", srs_path, txt_path],
            f"{name}.srs",
        )


def build_singbox_rules(rules: Dict[str, RuleSet], output_dir: str = "output/singbox") -> None:
    """Export all RuleSets to Sing-box format (.srs and .json)."""
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    os.makedirs(geosite_out, exist_ok=True)
    os.makedirs(geoip_out, exist_ok=True)

    # Synthesize composites on a local copy so other builders & manifest stay isolated
    local_rules = {k: v for k, v in rules.items() if k not in _SKIPPED_STANDALONE}
    synthesize_composites(local_rules)

    has_sb = check_singbox()
    print(f"\n📦 [Sing-box] 正在构建所有规则集并输出至 {output_dir}...")

    for name, rs in local_rules.items():
        if name in _SKIPPED_STANDALONE:
            continue
        if rs.total_count == 0 and not rs.raw_srs:
            print(f"  ⚠️ [Sing-box] {name:<26} | 空集合, 跳过导出 (避免 rules:[{{}}] 全匹配语义)")
            continue

        sub_dir = geoip_out if rs.is_geoip else geosite_out
        srs_path = os.path.join(sub_dir, f"{name}.srs")
        json_path = os.path.join(sub_dir, f"{name}.json")

        if name in ADGUARD_SOURCE_SETS:
            _build_adguard_srs(rules, name, sub_dir, has_sb)
            continue

        if rs.raw_srs and get_active_patch_count(name) == 0 and not has_patch_includes(name):
            with open(srs_path, "wb") as f:
                f.write(rs.raw_srs)
            if has_sb:
                try:
                    utils.decompile_srs(srs_path, json_path)
                except Exception as e:
                    print(f"⚠️ 反编译 {name}.srs 失败: {e}")
        else:
            json_dict = rs.to_singbox_dict(version=5)
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(json_dict, jf, indent=2, ensure_ascii=False)

            if has_sb:
                utils.compile_ruleset(
                    ["sing-box", "rule-set", "compile", json_path, "-o", srs_path],
                    f"{name}.srs",
                )

    print("✅ [Sing-box] 全部规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None) -> None:
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_singbox_rules(rules)


if __name__ == "__main__":
    run_all()
