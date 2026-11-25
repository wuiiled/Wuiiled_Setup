# -*- coding: utf-8 -*-
"""
Pure in-memory loaders for composite RuleSets (AI, Fake-IP, GFW-IP, PCDN, IPTV, Stream).
"""

import ipaddress
import re
from typing import Dict, Iterable, Set, Tuple

import providers
from core import fetcher
from core.cleaner import (
    absorb_covered_domains,
    clean_domain_entry,
    clean_ip_line,
    collapse_cidrs,
    compact_regexes,
    dedup_fakeip_lines,
    normalize_fakeip_line,
    parse_ai_rule_line,
)
from core.models import RuleSet


def load_ai_rules(min_domains: int = 0) -> Tuple[RuleSet, RuleSet]:
    """Build geosite-ai and geoip-ai from providers.AI_URLS."""
    feeds = fetcher.fetch_texts_parallel(providers.AI_URLS)

    domains: Set[str] = set()
    domain_suffixes: Set[str] = set()
    domain_keywords: Set[str] = set()
    process_names: Set[str] = set()
    domain_wildcards: Set[str] = set()
    ip_cidrs: Set[str] = set()
    ip_asns: Set[str] = set()
    dropped_counts: Dict[str, int] = {}
    ignored_asns = {str(a).upper().removeprefix("AS") for a in getattr(providers, "AI_IGNORED_ASNS", set())}

    for content in feeds.values():
        for line in content.splitlines():
            parsed = parse_ai_rule_line(line)
            if not parsed:
                continue
            rtype, val = parsed
            if rtype == "domain":
                domains.add(val)
            elif rtype == "domain_suffix":
                domain_suffixes.add(val)
            elif rtype == "domain_keyword":
                domain_keywords.add(val)
            elif rtype == "process_name":
                process_names.add(val)
            elif rtype == "domain_wildcard":
                domain_wildcards.add(val)
            elif rtype == "ip_cidr":
                ip_cidrs.add(val)
            elif rtype == "ip_asn":
                if val not in ignored_asns:
                    ip_asns.add(val)
            elif rtype == "dropped":
                dropped_counts[val] = dropped_counts.get(val, 0) + 1

    if dropped_counts:
        total_dropped = sum(dropped_counts.values())
        detail = ", ".join(f"{k} x{v}" for k, v in sorted(dropped_counts.items()))
        print(f"  ⚠️ [AI] 丢弃 {total_dropped} 条不支持类型规则 ({detail})")

    if ip_asns:
        asn_cidrs, failed_asns = fetcher.resolve_asn_to_cidrs(ip_asns)
        if failed_asns:
            published = fetcher.fetch_published_geoip_ai_cidrs()
            if published:
                print(
                    f"  ⚠️ [AI ASN]     {len(failed_asns)} 个 ASN 双源且缓存均不可用 "
                    f"({', '.join('AS' + a for a in failed_asns)}), 回退上一版已发布网段 {len(published):,} 条"
                )
                asn_cidrs.update(published)
            else:
                raise RuntimeError(
                    f"AI 规则集 IP-ASN 解析失败 (无上一版可用: {', '.join('AS' + a for a in failed_asns)})"
                )
        if not asn_cidrs:
            raise RuntimeError(f"AI 规则集 IP-ASN 转换异常 (待解析: {sorted(ip_asns)} -> 0 条 CIDR)")
        print(
            f"  🔄 [AI ASN]     解析 {len(ip_asns)} 个 IP-ASN "
            f"({', '.join('AS' + a for a in sorted(ip_asns))}) -> {len(asn_cidrs):,} 条 CIDR"
        )
        ip_cidrs.update(asn_cidrs)

    if ip_cidrs:
        ip_cidrs = collapse_cidrs(ip_cidrs)

    domains, domain_suffixes, _ = absorb_covered_domains(domains, domain_suffixes)

    if min_domains > 0 and (len(domains) + len(domain_suffixes)) < min_domains:
        raise RuntimeError(
            f"geosite-ai 域名条数异常偏低 ({len(domains) + len(domain_suffixes)} < {min_domains})"
        )

    geosite_rs = RuleSet(
        name="geosite-ai",
        category="geosite",
        description="全球主流 AI 域名合集",
        domains=domains,
        domain_suffixes=domain_suffixes,
        domain_keywords=domain_keywords,
        process_names=process_names,
        domain_wildcards=domain_wildcards,
        source_kind="self",
        sources=[
            "MetaCubeX/meta-rules-dat",
            "ruleset.skk.moe",
            "DustinWin/ruleset_geodata",
            "MagicRule",
            "dler-io/Rules",
        ],
    )
    geoip_rs = RuleSet(
        name="geoip-ai",
        category="geoip",
        description="全球主流 AI 服务 IP 与 ASN 网段合集",
        ip_cidrs=ip_cidrs,
        source_kind="self",
        sources=["MagicRule", "dler-io/Rules"],
    )
    print(f"  ✅ [原创 AI]    {'geosite-ai':<26} | 规则数: {geosite_rs.total_count:,}")
    print(f"  ✅ [原创 AI]    {'geoip-ai':<26} | 规则数: {geoip_rs.total_count:,}")
    return geosite_rs, geoip_rs


def assemble_fakeip_fields(lines: Iterable[str]) -> Tuple[Set[str], Set[str], Set[str]]:
    """Assemble cleaned fakeip-filter lines into sing-box (domains, domain_suffixes, domain_regexes)."""
    domains: Set[str] = set()
    domain_suffixes: Set[str] = set()
    domain_regexes: Set[str] = set()
    for line in lines:
        if line == "*":
            domain_regexes.add(r"^[^.]+$")
        elif line.startswith("+."):
            suffix = line[2:]
            if not suffix:
                continue
            if "*" in suffix:
                escaped = re.escape(suffix).replace(r"\*", r"[^.]+")
                domain_regexes.add(f"^(?:.+\\.)?{escaped}$")
            else:
                domain_suffixes.add("." + suffix if "." not in suffix else suffix)
        elif "*" in line:
            escaped = re.escape(line).replace(r"\*", r"[^.]+")
            domain_regexes.add(f"^{escaped}$")
        else:
            domains.add(line)
    return domains, domain_suffixes, domain_regexes


def load_fakeip_rules() -> RuleSet:
    """Build geosite-fakeip-filter in memory with normalization and regex compaction."""
    feeds = fetcher.fetch_texts_parallel(providers.FAKE_IP_URLS)

    unique_lines: Set[str] = set()
    for content in feeds.values():
        for raw in content.splitlines():
            norm = normalize_fakeip_line(raw)
            if norm:
                unique_lines.add(norm)

    local_addon = fetcher.read_local_file("rules/addons/fake-ip-addon.txt")
    if local_addon:
        for raw in local_addon.splitlines():
            norm = normalize_fakeip_line(raw)
            if norm:
                unique_lines.add(norm)

    raw_mihomo_lines = dedup_fakeip_lines(sorted(unique_lines))
    domains, domain_suffixes, domain_regexes = assemble_fakeip_fields(raw_mihomo_lines)
    compacted_regexes = compact_regexes(domain_regexes)

    print(
        f"  ✅ [Fake-IP]    {'geosite-fakeip-filter':<26} | "
        f"singbox={len(domains) + len(domain_suffixes) + len(compacted_regexes):,} mihomo={len(raw_mihomo_lines):,}"
    )
    return RuleSet(
        name="geosite-fakeip-filter",
        category="geosite",
        description="Fake-IP 过滤名单",
        domains=domains,
        domain_suffixes=domain_suffixes,
        domain_regexes=set(compacted_regexes),
        raw_lines=raw_mihomo_lines,
        source_kind="self",
        sources=["OpenClash", "ShellCrash", "ruleset.skk.moe", "本地 fake-ip-addon"],
    )


def load_gfwip_rules() -> RuleSet:
    """Build geoip-gfw from active pmkol/easymosdns GFW IP list."""
    feeds = fetcher.fetch_texts_parallel(providers.GFW_IP_URLS)
    lines: Set[str] = set()
    for content in feeds.values():
        for line in content.splitlines():
            cleaned = clean_ip_line(line)
            if cleaned:
                try:
                    lines.add(str(ipaddress.ip_network(cleaned, strict=False)))
                except ValueError:
                    pass

    print(f"  ✅ [GFW IP]     {'geoip-gfw':<26} | 规则数: {len(lines):,}")
    return RuleSet(
        name="geoip-gfw",
        category="geoip",
        description="GFW 投毒 IP 与网段拦截",
        ip_cidrs=lines,
        source_kind="self",
        sources=["pmkol/easymosdns"],
        flatten_cidr_host=True,
    )


def load_pcdn_rules() -> RuleSet:
    """Build geosite-pcdn from wuiiled/PCDN-mihomo-list."""
    feeds = fetcher.fetch_texts_parallel(providers.PCDN_URLS)
    domains: Set[str] = set()
    domain_suffixes: Set[str] = set()
    for content in feeds.values():
        for line in content.splitlines():
            parsed = clean_domain_entry(line)
            if parsed:
                bucket, value = parsed
                if bucket == "domain_suffix":
                    domain_suffixes.add(value)
                else:
                    domains.add(value)

    print(f"  ✅ [PCDN]       {'geosite-pcdn':<26} | 规则数: {len(domains) + len(domain_suffixes):,}")
    return RuleSet(
        name="geosite-pcdn",
        category="geosite",
        description="PCDN 边缘上传业务拦截",
        domains=domains,
        domain_suffixes=domain_suffixes,
        source_kind="self",
        sources=["wuiiled/PCDN-mihomo-list"],
    )


def load_iptv_rules() -> Tuple[RuleSet, RuleSet]:
    """Build geosite-iptv-!cn and geoip-iptv-!cn from Gary and Cathy IPTV upstream."""
    feeds = fetcher.fetch_texts_parallel(providers.IPTV_URLS)
    domains: Set[str] = set()
    domain_suffixes: Set[str] = set()
    ip_cidrs: Set[str] = set()

    for content in feeds.values():
        for raw in content.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.upper().startswith(("IP-CIDR,", "IP-CIDR6,", "IP6-CIDR,")):
                cleaned_ip = clean_ip_line(line)
                if cleaned_ip:
                    try:
                        ip_cidrs.add(str(ipaddress.ip_network(cleaned_ip, strict=False)))
                    except ValueError:
                        pass
            else:
                parsed = clean_domain_entry(line)
                if parsed:
                    bucket, value = parsed
                    if bucket == "domain_suffix":
                        domain_suffixes.add(value)
                    else:
                        domains.add(value)

    domains, domain_suffixes, _ = absorb_covered_domains(domains, domain_suffixes)

    geosite_rs = RuleSet(
        name="geosite-iptv-!cn",
        category="geosite",
        description="IPTV 境外直播与流媒体服务 (Gary & Cathy 聚合)",
        domains=domains,
        domain_suffixes=domain_suffixes,
        source_kind="self",
        sources=["marcuccilli/gary", "marcuccilli/Cathy"],
    )
    geoip_rs = RuleSet(
        name="geoip-iptv-!cn",
        category="geoip",
        description="IPTV 境外直播与流媒体 IP 节点 (Gary & Cathy 聚合)",
        ip_cidrs=ip_cidrs,
        source_kind="self",
        sources=["marcuccilli/gary", "marcuccilli/Cathy"],
    )
    print(f"  ✅ [IPTV]       {'geosite-iptv-!cn':<26} | 规则数: {geosite_rs.total_count:,}")
    print(f"  ✅ [IPTV]       {'geoip-iptv-!cn':<26} | 规则数: {geoip_rs.total_count:,}")
    return geosite_rs, geoip_rs


def load_stream_rules(dat_map: Dict[str, RuleSet]) -> Tuple[RuleSet, RuleSet]:
    """Build geosite-stream (dat categories + sve1r) and geoip-stream (sve1r + skk)."""
    feeds = fetcher.fetch_texts_parallel(providers.STREAM_URLS)

    domains: Set[str] = set()
    domain_suffixes: Set[str] = set()
    domain_keywords: Set[str] = set()
    domain_wildcards: Set[str] = set()
    domain_regexes: Set[str] = set()
    ip_cidrs: Set[str] = set()
    dropped_counts: Dict[str, int] = {}

    for content in feeds.values():
        for line in content.splitlines():
            parsed = parse_ai_rule_line(line, bare_as_suffix=True)
            if not parsed:
                continue
            rtype, val = parsed
            if rtype == "domain":
                domains.add(val)
            elif rtype == "domain_suffix":
                domain_suffixes.add(val)
            elif rtype == "domain_keyword":
                domain_keywords.add(val)
            elif rtype == "domain_wildcard":
                domain_wildcards.add(val)
            elif rtype == "ip_cidr":
                ip_cidrs.add(val)
            elif rtype == "dropped":
                dropped_counts[val] = dropped_counts.get(val, 0) + 1

    if dropped_counts:
        total_dropped = sum(dropped_counts.values())
        detail = ", ".join(f"{k} x{v}" for k, v in sorted(dropped_counts.items()))
        print(f"  ⚠️ [Stream] 丢弃 {total_dropped} 条不支持类型规则 ({detail})")

    dat_missing = [c for c in providers.STREAM_DAT_CATEGORIES if c not in dat_map]
    if dat_missing:
        raise RuntimeError(
            f"geosite-stream 的 dat 分类不存在: {', '.join(dat_missing)}, 拒绝静默缩水"
        )
    for code in providers.STREAM_DAT_CATEGORIES:
        src = dat_map[code]
        domains |= src.domains
        domain_suffixes |= src.domain_suffixes
        domain_keywords |= src.domain_keywords
        domain_regexes |= src.domain_regexes
        domain_wildcards |= src.domain_wildcards

    domains, domain_suffixes, _ = absorb_covered_domains(domains, domain_suffixes)
    ip_cidrs = collapse_cidrs(ip_cidrs)

    geosite_rs = RuleSet(
        name="geosite-stream",
        category="geosite",
        description="境外流媒体总集 (dat 分类 × sve1r ForeignMedia, 域名+keyword+wildcard)",
        domains=domains,
        domain_suffixes=domain_suffixes,
        domain_keywords=domain_keywords,
        domain_regexes=domain_regexes,
        domain_wildcards=domain_wildcards,
        source_kind="self",
        sources=[
            f"Loyalsoldier dat ({len(providers.STREAM_DAT_CATEGORIES)} 分类)",
            "sve1r/Rules-For-Quantumult-X",
        ],
    )
    geoip_rs = RuleSet(
        name="geoip-stream",
        category="geoip",
        description="流媒体服务 IP 网段 (sve1r + skk, 主体 Netflix Open Connect)",
        ip_cidrs=ip_cidrs,
        source_kind="self",
        sources=["sve1r/Rules-For-Quantumult-X", "ruleset.skk.moe"],
    )
    print(f"  ✅ [Stream]     {'geosite-stream':<26} | 规则数: {geosite_rs.total_count:,}")
    print(f"  ✅ [Stream]     {'geoip-stream':<26} | 规则数: {geoip_rs.total_count:,}")
    return geosite_rs, geoip_rs
