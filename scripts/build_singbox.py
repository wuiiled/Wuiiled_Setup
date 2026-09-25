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
from typing import Dict, List, Optional, Set

import utils
from core.models import RuleSet
from core.patcher import get_active_patch_count

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def check_singbox() -> bool:
    return utils.check_tool("sing-box")


def synthesize_composites(rules: Dict[str, RuleSet]) -> None:
    """合成 sing-box 专属复合规则 (域名 + IP 同集)。

    必须在并行分发构建器之前、对主 rules 字典一次性完成: 原地替换共享字典
    在多线程迭代下存在竞态 (新增 key 会触发 RuntimeError), 由 main.py 统一
    预合成并为每个构建器传入独立快照来根除。
    """
    composite_specs = [
        ("geosite-custom-direct", "geosite-custom-direct", "geoip-custom-direct"),
        ("geosite-custom-dns", "geosite-custom-dns", "geoip-custom-dns"),
    ]

    for comp_name, domain_key, ip_key in composite_specs:
        comp_domains: Set[str] = set()
        comp_suffixes: Set[str] = set()
        comp_ips: Set[str] = set()
        sources: List[str] = []

        if domain_key in rules:
            comp_domains.update(rules[domain_key].domains)
            comp_suffixes.update(rules[domain_key].domain_suffixes)
            sources += list(rules[domain_key].sources)
        if ip_key in rules:
            comp_ips.update(rules[ip_key].ip_cidrs)
            sources += list(rules[ip_key].sources)

        rules[comp_name] = RuleSet(
            name=comp_name,
            category="geosite",
            description="复合自定义规则 (域名 + IP)",
            domains=comp_domains,
            domain_suffixes=comp_suffixes,
            ip_cidrs=comp_ips,
            source_kind="custom",
            sources=sources,
        )


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

    # 复合规则由 synthesize_composites 预合成 (main.py 在分发前统一调用)
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
        synthesize_composites(rules)
    build_singbox_rules(rules)


if __name__ == '__main__':
    run_all()
