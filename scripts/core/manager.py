# -*- coding: utf-8 -*-
"""
RuleSet Manager: Orchestrates all rule sources (Tianling, Merged, Custom, SKK),
runs the normalization and cleaning pipelines, and yields unified RuleSet objects.
"""

import os
import re
import ipaddress
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Set, Optional

import utils
import providers
from core.models import RuleSet
from core.cleaner import (
    normalize_domain_line,
    clean_ip_line,
    is_valid_ip_or_cidr,
    clean_mihomo_domain_line,
    compact_regexes,
    build_blocklist_b,
    build_whitelist_b
)
from core.fetcher import (
    fetch_text_url,
    fetch_parallel_texts,
    read_local_file,
    fetch_tianling_ruleset
)

TIANLING_GEOSITES = {
    "geosite-cn": "geosite-cn",
    "geosite-geolocation-!cn": "geosite-geolocation-!cn",
    "geosite-gfw": "geosite-gfw",
    "geosite-google": "geosite-google",
    "geosite-youtube": "geosite-youtube",
    "geosite-github": "geosite-github",
    "geosite-onedrive": "geosite-onedrive",
    "geosite-microsoft": "geosite-microsoft",
    "geosite-tiktok": "geosite-tiktok",
    "geosite-spotify": "geosite-spotify",
    "geosite-netflix": "geosite-netflix",
    "geosite-disney": "geosite-disney",
    "geosite-category-porn": "geosite-porn",
    "geosite-category-media": "geosite-media",
    "geosite-category-communication": "geosite-communication",
    "geosite-category-social-media-!cn": "geosite-social-media",
    "geosite-category-games": "geosite-games",
    "geosite-category-games-cn": "geosite-games-cn",
    "geosite-private": "geosite-private",
    "geosite-apple-tvplus": "geosite-apple-tvplus",
    "geosite-category-httpdns-cn": "geosite-httpdns"
}

TIANLING_GEOIPS = {
    "geoip-cn": "geoip-cn",
    "geoip-google": "geoip-google",
    "geoip-telegram": "geoip-telegram",
    "geoip-twitter": "geoip-twitter",
    "geoip-facebook": "geoip-facebook",
    "geoip-private": "geoip-private"
}


def load_tianling_rules() -> Dict[str, RuleSet]:
    """Fetch all 21 GeoSites and 6 GeoIPs from Tianling Shen's official repository."""
    results: Dict[str, RuleSet] = {}

    def _fetch_one_site(tag, out_name):
        rs = fetch_tianling_ruleset(tag, category="geosite", out_name=out_name)
        if rs:
            print(f"  ✅ [天灵 GeoSite] {out_name:<26} | 规则数: {rs.total_count:,}")
            return out_name, rs
        return None

    def _fetch_one_ip(tag, out_name):
        rs = fetch_tianling_ruleset(tag, category="geoip", out_name=out_name)
        if rs:
            print(f"  ✅ [天灵 GeoIP]   {out_name:<26} | 规则数: {rs.total_count:,}")
            return out_name, rs
        return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        f_sites = [executor.submit(_fetch_one_site, tag, out) for tag, out in TIANLING_GEOSITES.items()]
        f_ips = [executor.submit(_fetch_one_ip, tag, out) for tag, out in TIANLING_GEOIPS.items()]

        for f in f_sites:
            res = f.result()
            if res:
                results[res[0]] = res[1]

        for f in f_ips:
            res = f.result()
            if res:
                results[res[0]] = res[1]

    return results


def load_ads_rules() -> RuleSet:
    """Build geosite-ad with full pipeline (clean, keyword filter, Trie optimize, whitelist filter)."""
    work_dir = utils.get_work_dir()
    mod_dir = os.path.join(work_dir, "ads")
    os.makedirs(mod_dir, exist_ok=True)

    raw_ads_path = os.path.join(mod_dir, "raw_ads.txt")
    clean_ads_path = os.path.join(mod_dir, "clean_ads.txt")
    filter_ads_path = os.path.join(mod_dir, "filter_ads.txt")
    raw_allow_path = os.path.join(mod_dir, "raw_allow.txt")
    clean_allow_path = os.path.join(mod_dir, "clean_allow.txt")
    opt_ads_path = os.path.join(mod_dir, "opt_ads.txt")
    opt_allow_path = os.path.join(mod_dir, "opt_allow.txt")
    final_ads_path = os.path.join(mod_dir, "final_ads.txt")

    # 1. Download online ad sources
    online_urls = [u for u in providers.ADS_BLOCK_URLS if not u.endswith("Reject-addon.txt")]
    utils.download_files_parallel(raw_ads_path, online_urls)

    # 2. Append local addon
    local_addon = read_local_file("rules/addons/reject-addon.txt")
    if local_addon:
        with open(raw_ads_path, "a", encoding="utf-8") as f:
            f.write("\n" + local_addon + "\n")

    # 3. Clean and keyword filter
    utils.process_normalize_domain(raw_ads_path, clean_ads_path, skip_allow_rules=True)
    utils.apply_keyword_filter(clean_ads_path, filter_ads_path)

    # 4. Prepare allowlist
    utils.download_files_parallel(raw_allow_path, providers.ALLOW_URLS)
    local_exclude = read_local_file("rules/addons/exclude-keyword.txt")
    local_custom_direct = read_local_file("rules/Custom_Direct_DOMAIN.txt")

    with open(raw_allow_path, "a", encoding="utf-8") as f:
        if local_exclude:
            for line in local_exclude.splitlines():
                l = line.strip()
                if l and not l.startswith('#'):
                    f.write(l + "\n")
        if local_custom_direct:
            for line in local_custom_direct.splitlines():
                l = line.strip()
                if l and not l.startswith('#'):
                    f.write(l + "\n")

    # 5. Normalize allowlist, optimize both, and apply advanced whitelist subtraction
    utils.process_normalize_domain(raw_allow_path, clean_allow_path, skip_allow_rules=False)
    utils.optimize_smart_self(filter_ads_path, opt_ads_path)
    utils.optimize_smart_self(clean_allow_path, opt_allow_path)
    utils.apply_advanced_whitelist_filter(opt_ads_path, opt_allow_path, final_ads_path)

    # Persist shared optimized allowlist so downstream consumers (reject-drop)
    # reuse it instead of reading a nonexistent path.
    shared_allow_path = os.path.join(work_dir, "shared", "opt_allow.txt")
    os.makedirs(os.path.dirname(shared_allow_path), exist_ok=True)
    if os.path.exists(opt_allow_path):
        with open(opt_allow_path, "r", encoding="utf-8") as src, open(
            shared_allow_path, "w", encoding="utf-8"
        ) as dst:
            dst.write(src.read())

    # 黑加白模式: compute precise blocklist B + allow exception list B via pure
    # functions, persist for platform exporters (smartdns/mihomo/adg).
    # 黑名单A (Option A, final_ads.txt) remains the backward-compatible default.
    blocklist_b_path = os.path.join(mod_dir, "blocklist_b.txt")
    whitelist_b_path = os.path.join(mod_dir, "whitelist_b.txt")
    try:
        with open(opt_ads_path, "r", encoding="utf-8") as f:
            raw_block = {l.strip() for l in f if l.strip() and not l.startswith("#")}
        with open(opt_allow_path, "r", encoding="utf-8") as f:
            raw_allow = {l.strip() for l in f if l.strip() and not l.startswith("#")}
        bl_b = build_blocklist_b(raw_block, raw_allow)
        wl_b = build_whitelist_b(raw_allow, raw_block, bl_b)
        with open(blocklist_b_path, "w", encoding="utf-8") as f:
            f.write(chr(10).join(sorted(bl_b)) + chr(10))
        with open(whitelist_b_path, "w", encoding="utf-8") as f:
            f.write(chr(10).join(sorted(wl_b)) + chr(10))
        print(f"  [黑加白] 黑名单B={len(bl_b):,} 白名单B={len(wl_b):,}")
    except OSError:
        pass

    domain_suffixes = set()
    if os.path.exists(final_ads_path):
        with open(final_ads_path, "r", encoding="utf-8") as f:
            for line in f:
                d = line.strip()
                if d:
                    domain_suffixes.add(d)

    print(f"  ✅ [原创广告]   {'geosite-ad':<26} | 规则数: {len(domain_suffixes):,}")
    return RuleSet(
        name="geosite-ad",
        category="geosite",
        description="终极去广告与防追踪规则",
        domain_suffixes=domain_suffixes
    )


def load_ai_rules() -> RuleSet:
    """Build geosite-ai."""
    work_dir = utils.get_work_dir()
    mod_dir = os.path.join(work_dir, "ai")
    os.makedirs(mod_dir, exist_ok=True)
    raw_ai = os.path.join(mod_dir, "raw_ai.txt")
    clean_ai = os.path.join(mod_dir, "clean_ai.txt")
    opt_ai = os.path.join(mod_dir, "opt_ai.txt")

    utils.download_files_parallel(raw_ai, providers.AI_URLS)
    utils.process_normalize_domain(raw_ai, clean_ai, skip_allow_rules=False)
    utils.optimize_smart_self(clean_ai, opt_ai)

    domain_suffixes = set()
    if os.path.exists(opt_ai):
        with open(opt_ai, "r", encoding="utf-8") as f:
            for line in f:
                d = line.strip()
                if d:
                    domain_suffixes.add(d)

    print(f"  ✅ [原创 AI]    {'geosite-ai':<26} | 规则数: {len(domain_suffixes):,}")
    return RuleSet(
        name="geosite-ai",
        category="geosite",
        description="全球主流 AI 域名合集",
        domain_suffixes=domain_suffixes
    )


def load_fakeip_rules() -> RuleSet:
    """Build geosite-fakeip-filter with regex compaction."""
    work_dir = utils.get_work_dir()
    mod_dir = os.path.join(work_dir, "fakeip")
    os.makedirs(mod_dir, exist_ok=True)
    raw_fakeip_dl = os.path.join(mod_dir, "raw_fakeip_dl.txt")

    online_urls = [u for u in providers.FAKE_IP_URLS if not u.endswith("fake-ip-addon.txt")]
    utils.download_files_parallel(raw_fakeip_dl, online_urls)

    unique_lines = set()
    if os.path.exists(raw_fakeip_dl):
        with open(raw_fakeip_dl, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                line = line.lower()
                if re.match(r'^\s*(dns:|fake-ip-filter:)', line):
                    continue
                line = re.sub(r'^\s*-\s*', '', line).replace('"', '').replace("'", '').replace('\\', '').strip()
                if line and not line.startswith('#'):
                    unique_lines.add(line)

    local_addon = read_local_file("rules/addons/fake-ip-addon.txt")
    if local_addon:
        for line in local_addon.splitlines():
            line = line.strip().lower()
            if line and not line.startswith('#'):
                unique_lines.add(line)

    clean_fakeip = os.path.join(mod_dir, "clean_fakeip.txt")
    final_fakeip = os.path.join(mod_dir, "final_fakeip.txt")
    with open(clean_fakeip, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(unique_lines)) + '\n')
    utils.optimize_smart_self(clean_fakeip, final_fakeip)

    domains = set()
    domain_suffixes = set()
    domain_regexes = set()
    raw_mihomo_lines = []

    if os.path.exists(final_fakeip):
        with open(final_fakeip, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                raw_mihomo_lines.append(line)
                if line.startswith('+.'):
                    suffix = line[2:]
                    if not suffix:
                        continue
                    if '*' in suffix:
                        escaped = re.escape(suffix).replace(r'\*', '.*')
                        domain_regexes.add(f"^(.*\\.)?{escaped}$")
                    else:
                        if suffix == 'cn':
                            domain_suffixes.add('cn')
                        elif '.' not in suffix:
                            domain_suffixes.add('.' + suffix)
                        else:
                            domain_suffixes.add(suffix)
                elif '*' in line:
                    escaped = re.escape(line).replace(r'\*', '.*')
                    domain_regexes.add(f"^{escaped}$")
                else:
                    domains.add(line)

    compacted_regexes = compact_regexes(domain_regexes)

    print(f"  ✅ [Fake-IP]    {'geosite-fakeip-filter':<26} | 规则数: {len(domains)+len(domain_suffixes)+len(compacted_regexes):,}")
    return RuleSet(
        name="geosite-fakeip-filter",
        category="geosite",
        description="Fake-IP 过滤名单",
        domains=domains,
        domain_suffixes=domain_suffixes,
        domain_regexes=set(compacted_regexes),
        raw_lines=raw_mihomo_lines
    )


def load_reject_drop_rules() -> RuleSet:
    """Build geosite-reject-drop."""
    work_dir = utils.get_work_dir()
    mod_dir = os.path.join(work_dir, "drop")
    os.makedirs(mod_dir, exist_ok=True)
    raw_rd = os.path.join(mod_dir, "raw_rd.txt")

    online_urls = [u for u in providers.DROP_URLS if not u.endswith("Custom_Reject-drop.txt")]
    utils.download_files_parallel(raw_rd, online_urls)

    rd_lines = set()
    if os.path.exists(raw_rd):
        with open(raw_rd, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                cleaned = clean_mihomo_domain_line(line)
                if cleaned and "skk.moe" not in line.lower() and cleaned != "+.":
                    rd_lines.add(cleaned)

    local_drop = read_local_file("rules/Custom_Reject-drop.txt")
    if local_drop:
        for line in local_drop.splitlines():
            cleaned = clean_mihomo_domain_line(line)
            if cleaned and cleaned != "+.":
                rd_lines.add(cleaned)

    clean_rd = os.path.join(mod_dir, "clean_rd.txt")
    with open(clean_rd, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(rd_lines)) + '\n')

    # Reuse the shared optimized allowlist produced by load_ads_rules instead of
    # a nonexistent shared/raw_allow.txt (which silently disabled the whitelist).
    clean_rd_allow = os.path.join(work_dir, "shared", "opt_allow.txt")
    final_rd = os.path.join(mod_dir, "final_rd.txt")

    if os.path.exists(clean_rd_allow) and os.path.getsize(clean_rd_allow) > 0:
        utils.apply_advanced_whitelist_filter(clean_rd, clean_rd_allow, final_rd)
    else:
        print("  [Reject-Drop] WARNING: shared allowlist missing/empty, whitelist filter skipped")
        with open(clean_rd, "r", encoding="utf-8") as src, open(final_rd, "w", encoding="utf-8") as dst:
            dst.write(src.read())

    domains = set()
    domain_suffixes = set()
    raw_rd_lines = []
    if os.path.exists(final_rd):
        with open(final_rd, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    raw_rd_lines.append(line)
                    if line.startswith('+.'):
                        suffix = line[2:]
                        if not suffix:
                            continue
                        if '.' not in suffix:
                            domain_suffixes.add('.' + suffix)
                        else:
                            domain_suffixes.add(suffix)
                    else:
                        domains.add(line)

    print(f"  ✅ [Reject-Drop]{'geosite-reject-drop':<26} | 规则数: {len(domains)+len(domain_suffixes):,}")
    return RuleSet(
        name="geosite-reject-drop",
        category="geosite",
        description="高危/垃圾流量直接丢弃规则",
        domains=domains,
        domain_suffixes=domain_suffixes,
        raw_lines=raw_rd_lines
    )


def load_gfwip_rules() -> RuleSet:
    """Build geoip-gfw with IPv4 & IPv6 networks."""
    work_dir = utils.get_work_dir()
    mod_dir = os.path.join(work_dir, "gfwip")
    os.makedirs(mod_dir, exist_ok=True)
    raw_gfwip = os.path.join(mod_dir, "raw_gfwip.txt")
    utils.download_files_parallel(raw_gfwip, providers.GFW_IP_URLS)

    ipv4_nets = set()
    ipv6_nets = set()

    if os.path.exists(raw_gfwip):
        with open(raw_gfwip, 'r', encoding='utf-8') as f:
            for line in f:
                cleaned = clean_ip_line(line)
                if cleaned:
                    try:
                        net = ipaddress.ip_network(cleaned, strict=False)
                        if net.version == 4:
                            ipv4_nets.add(net)
                        else:
                            ipv6_nets.add(net)
                    except ValueError:
                        pass

    for item in providers.GFW_IPV6_LIST:
        cleaned = clean_ip_line(item)
        if cleaned:
            try:
                net = ipaddress.ip_network(cleaned, strict=False)
                if net.version == 6:
                    ipv6_nets.add(net)
                else:
                    ipv4_nets.add(net)
            except ValueError:
                pass

    sorted_ipv4 = sorted(list(ipv4_nets), key=lambda x: (int(x.network_address), x.prefixlen))
    sorted_ipv6 = sorted(list(ipv6_nets), key=lambda x: (int(x.network_address), x.prefixlen))

    lines = set()
    for net in sorted_ipv4:
        lines.add(str(net.network_address) + "/32" if net.prefixlen == 32 else str(net))
    for net in sorted_ipv6:
        lines.add(str(net.network_address) + "/128" if net.prefixlen == 128 else str(net))

    print(f"  ✅ [GFW IP]     {'geoip-gfw':<26} | 规则数: {len(lines):,}")
    return RuleSet(
        name="geoip-gfw",
        category="geoip",
        description="GFW 投毒 IP 与网段拦截",
        ip_cidrs=lines
    )


def load_custom_rules() -> Dict[str, RuleSet]:
    """Load local custom rules from rules/ directory."""
    results: Dict[str, RuleSet] = {}
    for name, rel_path in providers.CUSTOM_RULES.items():
        content = read_local_file(rel_path)
        is_ip = name.startswith("geoip-") or name.lower().endswith(('_ip', '_ip.txt'))

        domains = set()
        domain_suffixes = set()
        ip_cidrs = set()

        for line in content.splitlines():
            if 'PROCESS-NAME' in line:
                continue
            if is_ip:
                cleaned = clean_ip_line(line)
                if cleaned:
                    try:
                        net = ipaddress.ip_network(cleaned, strict=False)
                        ip_cidrs.add(str(net))
                    except ValueError:
                        pass
            else:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('+.'):
                    domain_suffixes.add(line[2:])
                elif line.startswith('.'):
                    domain_suffixes.add(line[1:])
                else:
                    domains.add(line)

        cat = "geoip" if is_ip else "geosite"
        rs = RuleSet(
            name=name,
            category=cat,
            description=f"本地自定义规则 ({name})",
            domains=domains,
            domain_suffixes=domain_suffixes,
            ip_cidrs=ip_cidrs
        )
        print(f"  ✅ [Custom]     {name:<26} | 规则数: {rs.total_count:,}")
        results[name] = rs

    return results


def load_skk_rules() -> Dict[str, RuleSet]:
    """Fetch and parse rules from ruleset.skk.moe."""
    results: Dict[str, RuleSet] = {}
    url_cache = {}

    for name, url in providers.MIHOMO_SKK.items():
        if url not in url_cache:
            url_cache[url] = fetch_text_url(url)
        content = url_cache[url]

        is_ip = name.startswith("geoip-") or name.lower().endswith(('_ip', '_ip.txt'))
        domains = set()
        domain_suffixes = set()
        ip_cidrs = set()

        for line in content.splitlines():
            if 'skk.moe' in line or line.startswith('DOMAIN-WILDCARD,'):
                continue
            if is_ip:
                cleaned = clean_ip_line(line)
                if cleaned:
                    try:
                        net = ipaddress.ip_network(cleaned, strict=False)
                        ip_cidrs.add(str(net))
                    except ValueError:
                        pass
            else:
                cleaned = clean_mihomo_domain_line(line)
                if cleaned and cleaned != '+.':
                    if cleaned.startswith('+.'):
                        domain_suffixes.add(cleaned[2:])
                    elif cleaned.startswith('.'):
                        domain_suffixes.add(cleaned[1:])
                    else:
                        domains.add(cleaned)

        cat = "geoip" if is_ip else "geosite"
        rs = RuleSet(
            name=name,
            category=cat,
            description=f"SKK 规则 ({name})",
            domains=domains,
            domain_suffixes=domain_suffixes,
            ip_cidrs=ip_cidrs
        )
        print(f"  ✅ [SKK]        {name:<26} | 规则数: {rs.total_count:,}")
        results[name] = rs

    return results


def load_all_rules() -> Dict[str, RuleSet]:
    """Master pipeline: Load and normalize all rules across all categories."""
    print("\n🚀 [1/4] 拉取天灵权威官方规则 (21 GeoSites + 6 GeoIPs)...")
    all_rules = load_tianling_rules()

    print("\n🚀 [2/4] 构建原创复合提纯规则 (Ad / AI / Fake-IP / Drop / GFW-IP)...")
    ads = load_ads_rules()
    ai = load_ai_rules()
    fakeip = load_fakeip_rules()
    drop = load_reject_drop_rules()
    gfwip = load_gfwip_rules()

    for r in (ads, ai, fakeip, drop, gfwip):
        all_rules[r.name] = r

    print("\n🚀 [3/4] 加载本地自定义规则 (Custom_*)...")
    customs = load_custom_rules()
    for name, r in customs.items():
        all_rules[name] = r

    print("\n🚀 [4/4] 加载知名上游规则 (SKK 互联网大厂与流媒体)...")
    skks = load_skk_rules()
    for name, r in skks.items():
        all_rules[name] = r

    print(f"\n✨ 全网规则集加载完毕，共就绪 {len(all_rules)} 个标准规则集！")
    return all_rules
