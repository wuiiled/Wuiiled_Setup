# -*- coding: utf-8 -*-
"""
RuleSet Manager: Slim orchestrator over loaders/* and unified patch pipeline.
"""

import os
from typing import Dict, Optional

from core.cleaner import absorb_covered_domains
from core.loaders.ads import load_ads_rules, load_reject_drop_rules
from core.loaders.composite import (
    assemble_fakeip_fields,  # noqa: F401 - re-exported for tests
    load_ai_rules,
    load_fakeip_rules,
    load_gfwip_rules,
    load_iptv_rules,
    load_pcdn_rules,
    load_stream_rules,
)
from core.loaders.external import load_custom_rules, load_skk_rules
from core.loaders.geo import TIANLING_GEOIPS, TIANLING_GEOSITES, load_geo_rules  # noqa: F401
from core.models import RuleSet
from core.patcher import apply_patches, load_patch_file

# Kept for isolated unit tests (tests/test_games_merge.py) when calling apply_rule_patches(rules) directly.
_DAT_SOURCE_MAP: Dict[str, RuleSet] = {}


def _include_label(kind: str, value: str) -> str:
    if kind == "dat":
        return f"dat 分类 {value}"
    if kind == "local":
        return f"本地 {os.path.basename(value)}"
    base = os.path.basename(value.split("?")[0])
    base = base.rsplit(".", 1)[0] if "." in base else base
    return f"SKK {base}" if "skk.moe" in value else base


def apply_rule_patches(
    all_rules: Dict[str, RuleSet],
    dat_map: Optional[Dict[str, RuleSet]] = None,
) -> None:
    """Apply rules/patches/*.txt (manual rules, include, exclude) uniformly."""
    resolved_dat_map = _DAT_SOURCE_MAP if dat_map is None else dat_map
    print("\n🚀 [5/5] 应用本地补丁与列表合并 (rules/patches/)...")
    applied = 0
    failed_includes = []

    for name, rs in all_rules.items():
        if not load_patch_file(name):
            continue
        base_snapshot = set(rs.domains) | set(rs.domain_suffixes)
        rs, plain_n, upstream_included, includes = apply_patches(rs, dat_map=resolved_dat_map)
        applied += 1
        for kind, target, merged in includes:
            if merged < 0:
                failed_includes.append((name, kind, target))
        inc_labels = [_include_label(k, v) for k, v, _n in includes if k in ("dat", "url", "local")]
        if inc_labels:
            rs.sources = list(rs.sources) + inc_labels
        absorbed = 0
        has_includes = any(k in ("dat", "url", "local") and n >= 0 for k, _t, n in includes)
        if has_includes and rs.category == "geosite":
            kept_dom, kept_suf, absorbed = absorb_covered_domains(
                rs.domains, rs.domain_suffixes, protect=base_snapshot
            )
            rs.domains, rs.domain_suffixes = kept_dom, kept_suf
        applied_str = f" | 覆盖吸收: -{absorbed:,}" if absorbed else ""
        inc_str = (
            " | ".join(
                f"{k}:{t} ({'失败' if n < 0 else (f'-{n:,}' if k.startswith('exclude') else f'+{n:,}')})"
                for k, t, n in includes
            )
            if includes
            else "-"
        )
        extra = f" | 上游已收录: {len(upstream_included)}" if upstream_included else ""
        print(f"  📝 [补丁] {name:<26} | 手动补丁: {plain_n} | include: {inc_str}{applied_str}{extra}")

    print(f"  ✅ 共应用 {applied} 个规则集的本地补丁")
    if failed_includes:
        detail = "; ".join(f"{n} <- {k}:{t}" for n, k, t in failed_includes)
        raise RuntimeError(
            "include/exclude 指令解析失败 (下载失败/来源不存在/合并 0 条), "
            f"为防止规则集静默缩水中止构建: {detail}"
        )


def load_all_rules() -> Dict[str, RuleSet]:
    """Master pipeline: load, clean, and patch all canonical RuleSet IR objects."""
    print("\n🚀 [1/5] 拉取权威规则 (Loyalsoldier geosite.dat + Country.mmdb 原生解析 + 天灵配方 cn)...")
    all_rules, dat_map = load_geo_rules()

    print("\n🚀 [2/5] 构建原创复合提纯规则 (Ad / AI / Fake-IP / Drop / GFW-IP / PCDN / IPTV / Stream)...")
    ads, ads_precise, ads_allow, allow_suffix, allow_exact = load_ads_rules()
    ai_site, ai_ip = load_ai_rules(min_domains=300)
    fakeip = load_fakeip_rules()
    drop = load_reject_drop_rules(allow_suffix, allow_exact)
    gfwip = load_gfwip_rules()
    pcdn = load_pcdn_rules()
    iptv_site, iptv_ip = load_iptv_rules()
    stream_site, stream_ip = load_stream_rules(dat_map)

    for r in (
        ads, ads_precise, ads_allow,
        ai_site, ai_ip, fakeip, drop, gfwip, pcdn,
        iptv_site, iptv_ip, stream_site, stream_ip,
    ):
        all_rules[r.name] = r

    print("\n🚀 [3/5] 加载本地自定义规则 (Custom_*)...")
    all_rules.update(load_custom_rules())

    print("\n🚀 [4/5] 加载知名上游规则 (SKK 互联网大厂与流媒体)...")
    all_rules.update(load_skk_rules())

    apply_rule_patches(all_rules, dat_map=dat_map)

    print(f"\n✨ 全网规则集加载完毕，共就绪 {len(all_rules)} 个标准规则集！")
    return all_rules
