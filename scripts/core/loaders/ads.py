# -*- coding: utf-8 -*-
"""
Pure in-memory loaders for adblock (geosite-ad / ad-precise / ad-allow) and reject-drop.
"""

from typing import Iterable, Set, Tuple

import providers
from core import fetcher
from core.cleaner import (
    absorb_covered_domains,
    build_blocklist_b,
    build_whitelist_b,
    clean_domain_entry,
    clean_mihomo_domain_line,
    idna_domain,
    normalize_domain_line,
    strip_covered_apex_from_exact_source,
    subtract_whitelist,
)
from core.models import RuleSet


def _normalize_lines(lines: Iterable[str], skip_allow_rules: bool) -> Set[str]:
    out: Set[str] = set()
    for raw in lines:
        line = raw.strip().lower()
        if not line:
            continue
        if skip_allow_rules and line.startswith("@@"):
            continue
        res = normalize_domain_line(line)
        if res:
            out.add(idna_domain(res))
    return out


def _load_exclude_keywords() -> list:
    raw = fetcher.read_local_file("rules/addons/exclude-keyword.txt")
    return [
        k.strip().lower()
        for k in raw.splitlines()
        if k.strip() and not k.strip().startswith("#")
    ]


def load_ads_rules() -> Tuple[RuleSet, RuleSet, RuleSet, Set[str], Set[str]]:
    """Build geosite-ad (Mode A), geosite-ad-precise & geosite-ad-allow (Mode B) in memory."""
    block_feeds = fetcher.fetch_texts_parallel(providers.ADS_BLOCK_URLS)

    clean_ads: Set[str] = set()
    for url, content in block_feeds.items():
        per_source = _normalize_lines(content.splitlines(), skip_allow_rules=True)
        if url in providers.EXACT_SEMANTIC_AD_URLS:
            before = len(per_source)
            per_source = strip_covered_apex_from_exact_source(per_source)
            dropped_apex = before - len(per_source)
            if dropped_apex:
                print(f"  [精准源降噪] {url} 剥离 {dropped_apex} 个已含具体子域的裸根域")
        clean_ads |= per_source

    local_addon = fetcher.read_local_file("rules/addons/reject-addon.txt")
    if local_addon:
        clean_ads |= _normalize_lines(local_addon.splitlines(), skip_allow_rules=True)

    keywords = _load_exclude_keywords()
    if keywords:
        clean_ads = {d for d in clean_ads if not any(kw in d for kw in keywords)}

    # Prefix-tree absorption over bare suffix pool (fixes Bug B1)
    _, opt_ads, absorbed = absorb_covered_domains(set(), clean_ads)
    if absorbed:
        print(f"  [去广告去重] 前缀树吸收 {absorbed:,} 条冗余子域 -> 保留 {len(opt_ads):,} 条")

    allow_feeds = fetcher.fetch_texts_parallel(providers.ALLOW_URLS)
    allow_exact_feeds = fetcher.fetch_texts_parallel(providers.ALLOW_EXACT_URLS)

    raw_allow_lines = []
    for content in allow_feeds.values():
        raw_allow_lines.extend(content.splitlines())
    for rel in ("rules/addons/exclude-keyword.txt", "rules/Custom_Direct_DOMAIN.txt"):
        txt = fetcher.read_local_file(rel)
        if txt:
            for ln in txt.splitlines():
                s = ln.strip()
                if s and not s.startswith("#"):
                    raw_allow_lines.append(s)

    _, opt_allow, _ = absorb_covered_domains(
        set(), _normalize_lines(raw_allow_lines, skip_allow_rules=False)
    )
    raw_exact_lines = []
    for content in allow_exact_feeds.values():
        raw_exact_lines.extend(content.splitlines())
    _, opt_allow_exact, _ = absorb_covered_domains(
        set(), _normalize_lines(raw_exact_lines, skip_allow_rules=False)
    )

    # Mode A (conservative single-list subtraction)
    final_ads = subtract_whitelist(opt_ads, opt_allow, opt_allow_exact)

    # Mode B (precise blocklist B + allowlist B)
    bl_b = build_blocklist_b(opt_ads, opt_allow, opt_allow_exact)
    wl_b = build_whitelist_b(opt_allow, opt_ads, bl_b)
    print(f"  [黑加白] 黑名单B={len(bl_b):,} 白名单B={len(wl_b):,}")
    print(f"  ✅ [原创广告]   {'geosite-ad':<26} | 规则数: {len(final_ads):,}")

    derived_sources = [
        providers.ADS_BLOCK_SOURCE_NAMES.get(u, u)
        for u in providers.ADS_BLOCK_URLS
    ] + ["本地 reject-addon"]

    rs_ad = RuleSet(
        name="geosite-ad",
        category="geosite",
        description="终极去广告与防追踪规则",
        domain_suffixes=final_ads,
        source_kind="self",
        sources=derived_sources,
    )
    rs_precise = RuleSet(
        name="geosite-ad-precise",
        category="geosite",
        description="去广告黑名单精确版 (双集合黑名单B)",
        domain_suffixes=bl_b,
        source_kind="self",
        sources=["上游黑名单 ∪ 上游白名单 (黑加白差集)"],
    )
    rs_allow = RuleSet(
        name="geosite-ad-allow",
        category="geosite",
        description="去广告防误杀白名单 (双集合白名单B)",
        domain_suffixes=wl_b,
        source_kind="self",
        sources=["上游黑名单 ∪ 上游白名单 (黑加白差集)"],
    )
    return rs_ad, rs_precise, rs_allow, opt_allow, opt_allow_exact


def load_reject_drop_rules(allow_suffix: Set[str], allow_exact: Set[str]) -> RuleSet:
    """Build geosite-reject-drop in memory using shared allowlists."""
    drop_feeds = fetcher.fetch_texts_parallel(providers.DROP_URLS)

    rd_lines: Set[str] = set()
    for content in drop_feeds.values():
        for line in content.splitlines():
            cleaned = clean_mihomo_domain_line(line)
            if cleaned and "skk.moe" not in line.lower() and cleaned != "+.":
                rd_lines.add(cleaned)

    local_drop = fetcher.read_local_file("rules/Custom_Reject-drop.txt")
    if local_drop:
        for line in local_drop.splitlines():
            cleaned = clean_mihomo_domain_line(line)
            if cleaned and cleaned != "+.":
                rd_lines.add(cleaned)

    domains: Set[str] = set()
    domain_suffixes: Set[str] = set()
    raw_rd_lines = []

    allow_parents: Set[str] = set()
    for a in allow_suffix:
        parts = a.split(".")
        for i in range(1, len(parts)):
            allow_parents.add(".".join(parts[i:]))
    from core.cleaner import domain_ancestors

    for raw in sorted(rd_lines):
        parsed = clean_domain_entry(raw)
        if not parsed:
            continue
        bucket, value = parsed
        if value in allow_exact or value in allow_parents or any(anc in allow_suffix for anc in domain_ancestors(value)):
            continue
        raw_rd_lines.append(value if bucket == "domain" else "+." + value)
        if bucket == "domain_suffix":
            domain_suffixes.add(value)
        else:
            domains.add(value)

    print(f"  ✅ [Reject-Drop]{'geosite-reject-drop':<26} | 规则数: {len(domains) + len(domain_suffixes):,}")
    return RuleSet(
        name="geosite-reject-drop",
        category="geosite",
        description="高危/垃圾流量直接丢弃规则",
        domains=domains,
        domain_suffixes=domain_suffixes,
        raw_lines=raw_rd_lines,
        source_kind="self",
        sources=["ruleset.skk.moe", "本地 Custom_Reject-drop"],
    )
