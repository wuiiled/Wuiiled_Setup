# -*- coding: utf-8 -*-
"""
RuleSet Manager: Orchestrates all rule sources (Tianling, Merged, Custom, SKK),
runs the normalization and cleaning pipelines, and yields unified RuleSet objects.
"""

import os
import sys
import re
import ipaddress
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import utils
import providers
from core.models import RuleSet
from core.cleaner import (
    clean_ip_line,
    clean_mihomo_domain_line,
    compact_regexes,
    build_blocklist_b,
    build_whitelist_b,
    absorb_covered_domains
)
from core.fetcher import (
    fetch_text_url,
    read_local_file,
    fetch_tianling_ruleset
)
from core.patcher import apply_patches, load_patch_file
from core.geosite_source import parse_geosite_dat, build_tianling_style_cn

TIANLING_GEOSITES = {
    # 注意: geosite-cn 不在此列 —— 它以天灵配方精编 cn (build_tianling_style_cn) 为基座,
    # 自有列表与手动补丁经 rules/patches/geosite-cn.txt 的 include/规则行声明,
    # 由 apply_rule_patches 统一应用。
    "geosite-geolocation-!cn": "geosite-!cn",
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
    "geosite-category-httpdns-cn": "geosite-httpdns",
    # --- New additions ---
    "geosite-category-entertainment": "geosite-entertainment",
    "geosite-category-games-!cn": "geosite-games-!cn",
    "geosite-category-netdisk-!cn": "geosite-netdisk-!cn",
    # AI & Dev
    "geosite-openai": "geosite-openai",
    "geosite-anthropic": "geosite-anthropic",
    "geosite-google-gemini": "geosite-gemini",
    "geosite-gitlab": "geosite-gitlab",
    "geosite-docker": "geosite-docker",
    "geosite-stackexchange": "geosite-stackoverflow",
    "geosite-npmjs": "geosite-npm",
    # Social & IM
    "geosite-telegram": "geosite-telegram",
    "geosite-discord": "geosite-discord",
    "geosite-whatsapp": "geosite-whatsapp",
    "geosite-signal": "geosite-signal",
    "geosite-line": "geosite-line",
    "geosite-x": "geosite-x",
    "geosite-instagram": "geosite-instagram",
    "geosite-reddit": "geosite-reddit",
    "geosite-threads": "geosite-threads",
    "geosite-bluesky": "geosite-bluesky",
    # Streaming
    "geosite-twitch": "geosite-twitch",
    "geosite-hbo": "geosite-hbo",
    "geosite-hulu": "geosite-hulu",
    "geosite-primevideo": "geosite-primevideo",
    "geosite-bahamut": "geosite-bahamut",
    "geosite-abema": "geosite-abema",
    "geosite-niconico": "geosite-niconico",
    "geosite-dmm": "geosite-dmm",
    "geosite-pixiv": "geosite-pixiv",
    "geosite-vimeo": "geosite-vimeo",
    "geosite-dailymotion": "geosite-dailymotion",
    "geosite-deezer": "geosite-deezer",
    "geosite-soundcloud": "geosite-soundcloud",
    "geosite-tidal": "geosite-tidal",
    # Gaming platforms
    "geosite-steam": "geosite-steam",
    "geosite-epicgames": "geosite-epicgames",
    "geosite-playstation": "geosite-playstation",
    "geosite-xbox": "geosite-xbox",
    "geosite-nintendo": "geosite-nintendo",
    "geosite-ea": "geosite-ea",
    "geosite-ubisoft": "geosite-ubisoft",
    "geosite-rockstar": "geosite-rockstar",
    "geosite-blizzard": "geosite-blizzard",
    "geosite-riot": "geosite-riotgames",
    "geosite-mihoyo": "geosite-mihoyo",
    "geosite-hoyoverse": "geosite-hoyoverse",
    # Finance & Payment
    "geosite-paypal": "geosite-paypal",
    "geosite-stripe": "geosite-stripe",
    "geosite-wise": "geosite-wise",
    "geosite-binance": "geosite-binance",
    "geosite-okx": "geosite-okx",
    # Infrastructure & Tools
    "geosite-cloudflare": "geosite-cloudflare",
    "geosite-fastly": "geosite-fastly",
    "geosite-akamai": "geosite-akamai",
    "geosite-vercel": "geosite-vercel",
    "geosite-netlify": "geosite-netlify",
    "geosite-notion": "geosite-notion",
    "geosite-figma": "geosite-figma",
    "geosite-canva": "geosite-canva",
    "geosite-zoom": "geosite-zoom",
}

TIANLING_GEOIPS = {
    "geoip-cn": "geoip-cn",
    "geoip-google": "geoip-google",
    "geoip-telegram": "geoip-telegram",
    "geoip-twitter": "geoip-twitter",
    "geoip-facebook": "geoip-facebook",
    "geoip-private": "geoip-private"
}

# 以天灵 sing-geosite 预编译 srs 原样同步的集合（不经 dat 重解析）。
# geosite-cn 以天灵配方为基座，自有列表与手动补丁统一走 rules/patches/ 补丁通道。
# 此机制保留给未来需要原样直通的其他集合。
TIANLING_RAW_SRS: Dict[str, str] = {}

# dat 解析结果 (含属性视图, 已应用 filterTags) 的模块级缓存,
# 供统一补丁通道解析 include:dat: 指令使用。
_DAT_SOURCE_MAP: Dict[str, RuleSet] = {}


def _fetch_one_ip(tag, out_name):
    rs = fetch_tianling_ruleset(tag, category="geoip", out_name=out_name)
    if rs:
        rs.source_kind = "geoip-srs"
        rs.sources = ["1715173329/sing-geoip"]
        print(f"  ✅ [天灵 GeoIP]   {out_name:<26} | 规则数: {rs.total_count:,}")
        return out_name, rs
    return None


def _include_label(kind: str, value: str) -> str:
    """把 include 指令转成 manifest/README 说明列里的简短来源名。"""
    if kind == "dat":
        return f"dat 分类 {value}"
    if kind == "local":
        return f"本地 {os.path.basename(value)}"
    base = os.path.basename(value.split("?")[0])
    base = base.rsplit(".", 1)[0] if "." in base else base
    return f"SKK {base}" if "skk.moe" in value else base


def apply_rule_patches(all_rules: Dict[str, RuleSet]) -> None:
    """
    统一补丁通道: 对 rules/patches/<规则集名>.txt 存在的规则集应用:
      - 手动补丁规则行 (上游已收录的行在运行期跳过并日志标注, 补丁文件保持只读);
      - include 指令 (dat 分类 / 外部 URL / 本地文件 的整表合并)。
    所有集合 (dat 派生 / 自研 / 自定义 / SKK) 共用同一条通道, 逻辑单一稳定。
    include 解析失败 (下载失败/分类不存在/合并 0 条) 时中止构建, 防止规则集静默缩水。
    """
    print("\n🚀 [5/5] 应用本地补丁与列表合并 (rules/patches/)...")
    applied = 0
    failed_includes = []
    for name, rs in all_rules.items():
        if not load_patch_file(name):
            continue
        rs, plain_n, upstream_included, includes = apply_patches(rs, dat_map=_DAT_SOURCE_MAP)
        applied += 1
        for kind, target, merged in includes:
            if merged == 0:
                failed_includes.append((name, kind, target))
        # include 整表合并也是真实来源, 记入来源画像供 manifest/README 渲染
        inc_labels = [_include_label(k, v) for k, v, _n in includes if k in ("dat", "url", "local")]
        if inc_labels:
            rs.sources = list(rs.sources) + inc_labels
        # 含 include 整表合并的集合做覆盖吸收 (删除被更短后缀涵盖的条目);
        # 纯 dat 派生集合不吸收, 保持与天灵 0-Diff 同构。
        absorbed = 0
        if any(n > 0 for _k, _t, n in includes) and rs.category == "geosite":
            kept_dom, kept_suf, absorbed = absorb_covered_domains(rs.domains, rs.domain_suffixes)
            rs.domains, rs.domain_suffixes = kept_dom, kept_suf
        applied_str = f" | 覆盖吸收: -{absorbed:,}" if absorbed else ""
        inc_str = " | ".join(f"{k}:{t} (+{n:,})" for k, t, n in includes) if includes else "-"
        extra = f" | 上游已收录: {len(upstream_included)}" if upstream_included else ""
        print(f"  📝 [补丁] {name:<26} | 手动补丁: {plain_n} | include: {inc_str}{applied_str}{extra}")
    print(f"  ✅ 共应用 {applied} 个规则集的本地补丁")
    if failed_includes:
        detail = "; ".join(f"{n} <- include:{k}:{t}" for n, k, t in failed_includes)
        raise RuntimeError(
            "include 指令解析失败 (下载失败/来源不存在/合并 0 条), "
            f"为防止规则集静默缩水中止构建: {detail}"
        )


def load_tianling_rules() -> Dict[str, RuleSet]:
    """Build GeoSites directly from Loyalsoldier geosite.dat (source protobuf).
    GeoIPs still come from Tianling sing-geoip (no equivalent public dat source wired yet).
    """
    results: Dict[str, RuleSet] = {}

    # Download latest geosite.dat from Loyalsoldier release
    import core.fetcher as fetcher
    dat_url = "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat"
    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "wuiiled_setup")
    os.makedirs(cache_dir, exist_ok=True)
    dat_path = os.path.join(cache_dir, "geosite.dat")
    print(f"\n🌐 [源头] 检查/下载 Loyalsoldier geosite.dat ...")
    data = fetcher.fetch_bytes_url(dat_url, timeout=60, retries=3)
    if data:
        with open(dat_path, "wb") as f:
            f.write(data)
        print(f"🌐 [源头] geosite.dat 下载成功: {len(data):,} bytes")
    elif os.path.exists(dat_path) and os.path.getsize(dat_path) > 0:
        print(f"⚠️ [源头] 下载失败，自动回退使用本地缓存 geosite.dat ({os.path.getsize(dat_path):,} bytes)")
    else:
        raise RuntimeError("无法下载 Loyalsoldier geosite.dat 且本地缓存不存在")

    source_map = parse_geosite_dat(dat_path)
    print(f"🌐 [源头] 解析出 {len(source_map)} 个上游分类")
    global _DAT_SOURCE_MAP
    _DAT_SOURCE_MAP = source_map

    for upstream_tag, out_name in TIANLING_GEOSITES.items():
        # upstream_tag like 'geosite-openai' or 'geosite-category-porn' -> dat code 'openai'/'category-porn'
        code = upstream_tag[len("geosite-"):]
        rs = source_map.get(code)
        if rs is None:
            print(f"  ❌ [源头 GeoSite] {out_name:<26} | 上游分类 '{code}' 不存在")
            continue
        rs.name = out_name
        rs.category = "geosite"
        rs.description = f"Loyalsoldier 权威提纯 ({code})"
        rs.source_kind = "dat"
        rs.sources = ["Loyalsoldier/v2ray-rules-dat"]
        rs.dat_code = code
        print(f"  ✅ [源头 GeoSite] {out_name:<26} | 规则数: {rs.total_count:,}")
        results[out_name] = rs

    # geosite-cn: 以天灵配方精编 cn 为基座 (geolocation-cn + category-*@cn + category-*-cn + .cn)。
    # 自有上游列表 (cn-additional-list / SKK domestic) 与手动补丁统一声明在
    # rules/patches/geosite-cn.txt, 由 apply_rule_patches 统一应用。
    recipe_cn = build_tianling_style_cn(source_map)
    recipe_cn.source_kind = "recipe"
    recipe_cn.sources = ["天灵配方精编 cn (geolocation-cn + category-*@cn + category-*-cn + .cn)"]
    print(f"  🧬 [天灵配方] geosite-cn                    | 配方合成: {recipe_cn.total_count:,} 条 (geolocation-cn + category-*@cn + category-*-cn)")
    results["geosite-cn"] = recipe_cn

    # 天灵原样同步集合 (TIANLING_RAW_SRS): 直接拉取其预编译 srs，不经 dat 重解析
    for tag, out_name in TIANLING_RAW_SRS.items():
        rs = fetch_tianling_ruleset(tag, category="geosite", out_name=out_name)
        if rs is None:
            print(f"  ❌ [天灵原样] {out_name:<26} | 无法获取 {tag}.srs")
            continue
        print(f"  ✅ [天灵原样] {out_name:<26} | 规则数: {rs.total_count:,}")
        results[out_name] = rs

    # GeoIP unchanged: still from Tianling sing-geoip srs
    with ThreadPoolExecutor(max_workers=8) as executor:
        f_ips = [executor.submit(_fetch_one_ip, tag, out) for tag, out in TIANLING_GEOIPS.items()]
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
            f.write("\n".join(sorted(bl_b)) + "\n")
        with open(whitelist_b_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(wl_b)) + "\n")
        print(f"  [黑加白] 黑名单B={len(bl_b):,} 白名单B={len(wl_b):,}")
    except OSError as e:
        # 黑加白产物是 mihomo/adg 下游的输入, 写失败必须显式失败而非静默缺失
        raise RuntimeError(f"黑加白 blocklist/whitelist B 写盘失败: {e}") from e

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
        domain_suffixes=domain_suffixes,
        source_kind="self",
        sources=[
            "pmkol/easymosdns", "AdGuard Hostlists (1/3/4)", "Dan Pollock",
            "isdumb/Pi-hole", "Cats-Team/AdRules", "AWAvenue", "OISD Small",
            "本地 reject-addon",
        ],
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
        domain_suffixes=domain_suffixes,
        source_kind="self",
        sources=["MetaCubeX/meta-rules-dat", "ruleset.skk.moe", "DustinWin/ruleset_geodata"],
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
        raw_lines=raw_mihomo_lines,
        source_kind="self",
        sources=["OpenClash", "ShellCrash", "DustinWin", "ruleset.skk.moe", "本地 fake-ip-addon"],
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
        raw_lines=raw_rd_lines,
        source_kind="self",
        sources=["ruleset.skk.moe", "本地 Custom_Reject-drop"],
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
        ip_cidrs=lines,
        source_kind="self",
        sources=["clowwindy/ChinaDNS", "pmkol/easymosdns", "自有 IPv6 靶心表"],
        flatten_cidr_host=True,
    )


def load_pcdn_rules() -> RuleSet:
    """Build geosite-pcdn from wuiiled/PCDN-mihomo-list (统一走 IR, 各平台导出+来源画像)."""
    work_dir = utils.get_work_dir()
    mod_dir = os.path.join(work_dir, "pcdn")
    os.makedirs(mod_dir, exist_ok=True)
    raw_pcdn = os.path.join(mod_dir, "raw_pcdn.txt")
    utils.download_files_parallel(raw_pcdn, providers.PCDN_URLS)

    domains = set()
    domain_suffixes = set()
    if os.path.exists(raw_pcdn):
        with open(raw_pcdn, 'r', encoding='utf-8') as f:
            for line in f:
                cleaned = clean_mihomo_domain_line(line)
                if not cleaned:
                    continue
                if cleaned.startswith('+.'):
                    suffix = cleaned[2:].lstrip('.')
                    if suffix:
                        domain_suffixes.add(suffix)
                elif cleaned.startswith('.'):
                    suffix = cleaned[1:].lstrip('.')
                    if suffix:
                        domain_suffixes.add(suffix)
                else:
                    domains.add(cleaned)

    print(f"  ✅ [PCDN]       {'geosite-pcdn':<26} | 规则数: {len(domains)+len(domain_suffixes):,}")
    return RuleSet(
        name="geosite-pcdn",
        category="geosite",
        description="PCDN 边缘上传业务拦截",
        domains=domains,
        domain_suffixes=domain_suffixes,
        source_kind="self",
        sources=["wuiiled/PCDN-mihomo-list"],
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
            ip_cidrs=ip_cidrs,
            source_kind="skk",
            sources=["ruleset.skk.moe"],
        )
        print(f"  ✅ [SKK]        {name:<26} | 规则数: {rs.total_count:,}")
        results[name] = rs

    return results


def load_all_rules() -> Dict[str, RuleSet]:
    """Master pipeline: Load and normalize all rules across all categories."""
    print("\n🚀 [1/5] 拉取权威规则 (Loyalsoldier dat 原生解析 GeoSites + 天灵配方 cn + GeoIPs)...")
    all_rules = load_tianling_rules()

    print("\n🚀 [2/5] 构建原创复合提纯规则 (Ad / AI / Fake-IP / Drop / GFW-IP / PCDN)...")
    ads = load_ads_rules()
    ai = load_ai_rules()
    fakeip = load_fakeip_rules()
    drop = load_reject_drop_rules()
    gfwip = load_gfwip_rules()
    pcdn = load_pcdn_rules()

    for r in (ads, ai, fakeip, drop, gfwip, pcdn):
        all_rules[r.name] = r

    print("\n🚀 [3/5] 加载本地自定义规则 (Custom_*)...")
    customs = load_custom_rules()
    for name, r in customs.items():
        all_rules[name] = r

    print("\n🚀 [4/5] 加载知名上游规则 (SKK 互联网大厂与流媒体)...")
    skks = load_skk_rules()
    for name, r in skks.items():
        all_rules[name] = r

    # 统一补丁通道: 手动域名补丁 + include 列表/分类合并 (rules/patches/*.txt)
    apply_rule_patches(all_rules)

    print(f"\n✨ 全网规则集加载完毕，共就绪 {len(all_rules)} 个标准规则集！")
    return all_rules
