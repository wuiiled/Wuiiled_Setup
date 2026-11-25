# -*- coding: utf-8 -*-
"""
Loaders for local custom rules (rules/Custom_*.txt) and SKK upstream rulesets.
"""

import ipaddress
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

import providers
from core import fetcher
from core.cleaner import clean_domain_entry, clean_ip_line
from core.models import RuleSet


def load_custom_rules() -> Dict[str, RuleSet]:
    """Load local custom rules from rules/ directory."""
    results: Dict[str, RuleSet] = {}
    for name, rel_path in providers.CUSTOM_RULES.items():
        content = fetcher.read_local_file(rel_path)
        is_ip = name.startswith("geoip-")

        domains = set()
        domain_suffixes = set()
        ip_cidrs = set()

        for line in content.splitlines():
            if is_ip:
                cleaned = clean_ip_line(line)
                if cleaned:
                    try:
                        ip_cidrs.add(str(ipaddress.ip_network(cleaned, strict=False)))
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

        rs = RuleSet(
            name=name,
            category="geoip" if is_ip else "geosite",
            description=f"本地自定义规则 ({name})",
            domains=domains,
            domain_suffixes=domain_suffixes,
            ip_cidrs=ip_cidrs,
            source_kind="custom",
            sources=[rel_path],
        )
        print(f"  ✅ [Custom]     {name:<26} | 规则数: {rs.total_count:,}")
        results[name] = rs

    return results


def load_skk_rules() -> Dict[str, RuleSet]:
    """Fetch and parse rules from ruleset.skk.moe."""
    results: Dict[str, RuleSet] = {}
    unique_urls = list(set(providers.MIHOMO_SKK.values()))
    with ThreadPoolExecutor(max_workers=min(len(unique_urls), 8)) as executor:
        url_cache = dict(zip(unique_urls, executor.map(fetcher.fetch_text_cached, unique_urls)))

    for name, url in providers.MIHOMO_SKK.items():
        content = url_cache.get(url, "")
        is_ip = name.startswith("geoip-") or name.lower().endswith(("_ip", "_ip.txt"))

        domains = set()
        domain_suffixes = set()
        wildcards = set()
        ip_cidrs = set()

        for line in content.splitlines():
            if "skk.moe" in line:
                continue
            if line.startswith("DOMAIN-WILDCARD,"):
                wc = line.split(",", 1)[1].strip().lower()
                if wc:
                    wildcards.add(wc)
                continue
            if is_ip:
                cleaned = clean_ip_line(line)
                if cleaned:
                    try:
                        ip_cidrs.add(str(ipaddress.ip_network(cleaned, strict=False)))
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

        rs = RuleSet(
            name=name,
            category="geoip" if is_ip else "geosite",
            description=f"SKK 规则 ({name})",
            domains=domains,
            domain_suffixes=domain_suffixes,
            domain_wildcards=wildcards,
            ip_cidrs=ip_cidrs,
            source_kind="skk",
            sources=["ruleset.skk.moe"],
        )
        print(f"  ✅ [SKK]        {name:<26} | 规则数: {rs.total_count:,}")
        results[name] = rs

    return results
