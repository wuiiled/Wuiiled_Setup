# -*- coding: utf-8 -*-
"""
Native source loaders for Loyalsoldier geosite.dat (protobuf) and Country.mmdb (MaxMind DB).
"""

import os
from typing import Dict, Tuple

from core import fetcher
from core.geoip_source import build_geoip_rulesets
from core.geosite_source import build_tianling_style_cn, parse_geosite_dat
from core.models import RuleSet

TIANLING_GEOSITES = {
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
    "geosite-category-entertainment": "geosite-entertainment",
    "geosite-category-games-!cn": "geosite-games-!cn",
    "geosite-category-netdisk-!cn": "geosite-netdisk-!cn",
    "geosite-openai": "geosite-openai",
    "geosite-anthropic": "geosite-anthropic",
    "geosite-google-gemini": "geosite-gemini",
    "geosite-gitlab": "geosite-gitlab",
    "geosite-docker": "geosite-docker",
    "geosite-stackexchange": "geosite-stackoverflow",
    "geosite-npmjs": "geosite-npm",
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
    "geosite-paypal": "geosite-paypal",
    "geosite-stripe": "geosite-stripe",
    "geosite-wise": "geosite-wise",
    "geosite-binance": "geosite-binance",
    "geosite-okx": "geosite-okx",
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
    "geoip-private": "geoip-private",
}


def load_geo_rules() -> Tuple[Dict[str, RuleSet], Dict[str, RuleSet]]:
    """Load GeoSite rulesets from geosite.dat and GeoIP rulesets from Country.mmdb."""
    results: Dict[str, RuleSet] = {}
    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "wuiiled_setup")
    os.makedirs(cache_dir, exist_ok=True)

    dat_url = "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat"
    dat_path = os.path.join(cache_dir, "geosite.dat")
    print("\n🌐 [源头] 检查/下载 Loyalsoldier geosite.dat ...")
    dat_bytes = fetcher.fetch_bytes_cached(dat_url, timeout=60, retries=3)
    with open(dat_path, "wb") as f:
        f.write(dat_bytes)
    print(f"🌐 [源头] geosite.dat 就绪: {len(dat_bytes):,} bytes")

    source_map = parse_geosite_dat(dat_path)
    print(f"🌐 [源头] 解析出 {len(source_map)} 个上游分类")

    for upstream_tag, out_name in TIANLING_GEOSITES.items():
        code = upstream_tag[len("geosite-"):]
        src_rs = source_map.get(code)
        if src_rs is None:
            raise RuntimeError(
                f"geosite.dat 上游分类 '{code}' 不存在, 规则集 {out_name} 将静默缺失, 拒绝继续"
            )
        rs = src_rs.copy()
        rs.name = out_name
        rs.category = "geosite"
        rs.description = f"Loyalsoldier 权威提纯 ({code})"
        rs.source_kind = "dat"
        rs.sources = ["Loyalsoldier/v2ray-rules-dat"]
        rs.dat_code = code
        print(f"  ✅ [源头 GeoSite] {out_name:<26} | 规则数: {rs.total_count:,}")
        results[out_name] = rs

    recipe_cn = build_tianling_style_cn(source_map)
    recipe_cn.source_kind = "recipe"
    recipe_cn.sources = ["天灵配方精编 cn (geolocation-cn + category-*@cn + category-*-cn + .cn)"]
    print(f"  🧬 [天灵配方] geosite-cn                    | 配方合成: {recipe_cn.total_count:,} 条")
    results["geosite-cn"] = recipe_cn

    mmdb_url = "https://github.com/Loyalsoldier/geoip/releases/latest/download/Country.mmdb"
    print("\n🌐 [源头] 检查/下载 Loyalsoldier Country.mmdb ...")
    mmdb_bytes = fetcher.fetch_bytes_cached(mmdb_url, timeout=60, retries=3)
    print(f"🌐 [源头] Country.mmdb 就绪: {len(mmdb_bytes):,} bytes")

    geoips = build_geoip_rulesets(mmdb_bytes, TIANLING_GEOIPS)
    for out_name, rs in geoips.items():
        print(f"  ✅ [源头 GeoIP]   {out_name:<26} | 规则数: {rs.total_count:,}")
        results[out_name] = rs

    return results, source_map
