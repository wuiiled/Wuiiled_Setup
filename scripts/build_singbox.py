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


# 以 AdGuard 语法为源、经 `rule-set convert --type adguard` 编译的集合 (sing-box >= 1.10)。
# geosite-ad 在 singbox 分支与 adg 分支同源: 黑名单B + @@||白名单B^ 混合,
# 例外语义编译进 srs (负向条件); adguard 型 srs 不可反编译, 源码即 txt。
ADGUARD_SOURCE_SETS = {"geosite-ad"}


def _build_adguard_srs(name: str, sub_dir: str, has_sb: bool) -> None:
    """消费统一 AdGuard 源文件 (utils 单一渲染, 与 adg 分支同源):
    复制为分支内源码 txt, 并经 --type adguard 转换为 adguard 型 srs。"""
    src = utils.render_adguard_geosite_ad()
    txt_path = os.path.join(sub_dir, f"{name}.txt")
    srs_path = os.path.join(sub_dir, f"{name}.srs")
    utils.safe_copy(src, txt_path)
    line_count = sum(1 for l in open(txt_path, encoding="utf-8") if l.strip())
    print(f"  [Sing-box] {name:<26} | AdGuard 语法 {line_count:,} 行 (||拦截 + @@||放行)")
    if has_sb:
        utils.compile_ruleset(
            ["sing-box", "rule-set", "convert", "--type", "adguard", "-o", srs_path, txt_path],
            f"{name}.srs"
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

        if name in ADGUARD_SOURCE_SETS:
            # AdGuard 源集合: txt 为源码, srs 经 --type adguard 转换 (无 JSON)
            _build_adguard_srs(name, sub_dir, has_sb)
            continue

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
