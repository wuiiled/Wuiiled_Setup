# -*- coding: utf-8 -*-
"""
Sing-box Rule-set Exporter.
Fully decoupled: receives canonical RuleSet IR and exports .srs and .json files.
Guarantees 100% Zero-Diff alignment with Tianling Shen for all Tianling rulesets.
"""

import os
import json
from typing import Dict, List, Optional, Set

import utils
from core.models import RuleSet
from core.patcher import get_active_patch_count, has_patch_includes

ADGUARD_SOURCE_SETS = {"geosite-ad"}


def check_singbox() -> bool:
    return utils.check_tool("sing-box")


def synthesize_composites(rules: Dict[str, RuleSet]) -> None:
    """合成 sing-box 专属复合规则 (域名 + keyword + regex + 进程名 + IP 同集)。"""
    composite_specs = [
        ("geosite-custom-direct", "geosite-custom-direct", "geoip-custom-direct"),
        ("geosite-custom-dns", "geosite-custom-dns", "geoip-custom-dns"),
        ("geosite-iptv-!cn", "geosite-iptv-!cn", "geoip-iptv-!cn"),
        ("geosite-ai", "geosite-ai", "geoip-ai"),
        # stream: 全量复合集 (域名+keyword+wildcard+IP) 落 geosite-stream.srs;
        # geoip-stream 不在下方跳过列表, 仍独立导出 ip-only 的 geoip-stream.srs
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


def _build_adguard_srs(name: str, sub_dir: str, has_sb: bool) -> None:
    """消费统一 AdGuard 源文件 (utils 单一渲染，与 adg 分支同源)。"""
    src = utils.render_adguard_geosite_ad()
    txt_path = os.path.join(sub_dir, f"{name}.txt")
    srs_path = os.path.join(sub_dir, f"{name}.srs")
    utils.safe_copy(src, txt_path)
    with open(txt_path, encoding="utf-8") as f:
        line_count = sum(1 for l in f if l.strip())
    print(f"  [Sing-box] {name:<26} | AdGuard 语法 {line_count:,} 行 (||拦截 + @@||放行)")

    if has_sb:
        utils.compile_ruleset(
            ["sing-box", "rule-set", "convert", "--type", "adguard", "-o", srs_path, txt_path],
            f"{name}.srs"
        )


def build_singbox_rules(rules: Dict[str, RuleSet], output_dir: str = "output/singbox"):
    """Export all RuleSets to Sing-box format (.srs and .json)."""
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    os.makedirs(geosite_out, exist_ok=True)
    os.makedirs(geoip_out, exist_ok=True)

    has_sb = check_singbox()
    print(f"\n📦 [Sing-box] 正在构建所有规则集并输出至 {output_dir}...")

    for name, rs in rules.items():
        if name in ("geoip-custom-direct", "geoip-custom-dns", "geoip-iptv-!cn", "geoip-ai"):
            continue
        # 空集合跳过导出: 无条件 headless rule (rules:[{}]) 等于匹配所有流量,
        # 且 sing-box compile 空集语义危险; 跳过后订阅端保留上一版 (关键集合
        # 另有 validate_output_invariants 非空守卫兜底)
        if rs.total_count == 0 and not rs.raw_srs:
            print(f"  ⚠️ [Sing-box] {name:<26} | 空集合, 跳过导出 (避免 rules:[{{}}] 全匹配语义)")
            continue

        sub_dir = geoip_out if rs.is_geoip else geosite_out
        srs_path = os.path.join(sub_dir, f"{name}.srs")
        json_path = os.path.join(sub_dir, f"{name}.json")

        if name in ADGUARD_SOURCE_SETS:
            _build_adguard_srs(name, sub_dir, has_sb)
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
                    f"{name}.srs"
                )

    print("✅ [Sing-box] 全部规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
        synthesize_composites(rules)
    build_singbox_rules(rules)


if __name__ == '__main__':
    run_all()
