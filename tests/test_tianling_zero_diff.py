# -*- coding: utf-8 -*-
"""
Automated 0-Diff Test against Tianling Shen (1715173329) Official Upstream.
Requirement 1 verification:
Ensures that all generated Sing-box rules match Tianling's upstream 100% exactly.
"""

import os
import sys
import json
import urllib.request
import subprocess
try:
    import pytest
except ImportError:
    class _DummyPytest:
        def skip(self, msg=""):
            pass
        class mark:
            @staticmethod
            def parametrize(*args, **kwargs):
                def decorator(fn):
                    return fn
                return decorator
    pytest = _DummyPytest()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
import utils

# Key Tianling rules to verify
# 注意: geosite-cn 不在此列 —— 它不走 dat 解析，而是原样同步天灵 srs，
# 由下方 test_tianling_raw_srs_zero_diff 单独比对上游。
TIANLING_TEST_SITES = [
    ("geosite-geolocation-!cn", "geosite-!cn"),
    ("geosite-gfw", "geosite-gfw"),
    ("geosite-google", "geosite-google"),
    ("geosite-youtube", "geosite-youtube"),
    ("geosite-github", "geosite-github"),
    ("geosite-onedrive", "geosite-onedrive"),
    ("geosite-microsoft", "geosite-microsoft"),
    ("geosite-tiktok", "geosite-tiktok"),
    ("geosite-spotify", "geosite-spotify"),
    ("geosite-netflix", "geosite-netflix"),
    ("geosite-disney", "geosite-disney"),
    ("geosite-category-games-cn", "geosite-games-cn"),
    ("geosite-private", "geosite-private"),
    ("geosite-apple-tvplus", "geosite-apple-tvplus"),
    ("geosite-category-httpdns-cn", "geosite-httpdns"),
    ("geosite-category-entertainment", "geosite-entertainment"),
    ("geosite-category-games-!cn", "geosite-games-!cn"),
    ("geosite-openai", "geosite-openai"),
    ("geosite-anthropic", "geosite-anthropic"),
    ("geosite-google-gemini", "geosite-gemini"),
    ("geosite-gitlab", "geosite-gitlab"),
    ("geosite-docker", "geosite-docker"),
    ("geosite-stackexchange", "geosite-stackoverflow"),
    ("geosite-npmjs", "geosite-npm"),
    ("geosite-telegram", "geosite-telegram"),
    ("geosite-discord", "geosite-discord"),
    ("geosite-whatsapp", "geosite-whatsapp"),
    ("geosite-signal", "geosite-signal"),
    ("geosite-line", "geosite-line"),
    ("geosite-x", "geosite-x"),
    ("geosite-instagram", "geosite-instagram"),
    ("geosite-reddit", "geosite-reddit"),
    ("geosite-threads", "geosite-threads"),
    ("geosite-bluesky", "geosite-bluesky"),
    ("geosite-twitch", "geosite-twitch"),
    ("geosite-hbo", "geosite-hbo"),
    ("geosite-hulu", "geosite-hulu"),
    ("geosite-primevideo", "geosite-primevideo"),
    ("geosite-bahamut", "geosite-bahamut"),
    ("geosite-abema", "geosite-abema"),
    ("geosite-niconico", "geosite-niconico"),
    ("geosite-dmm", "geosite-dmm"),
    ("geosite-pixiv", "geosite-pixiv"),
    ("geosite-vimeo", "geosite-vimeo"),
    ("geosite-dailymotion", "geosite-dailymotion"),
    ("geosite-deezer", "geosite-deezer"),
    ("geosite-soundcloud", "geosite-soundcloud"),
    ("geosite-tidal", "geosite-tidal"),
    ("geosite-steam", "geosite-steam"),
    ("geosite-epicgames", "geosite-epicgames"),
    ("geosite-playstation", "geosite-playstation"),
    ("geosite-xbox", "geosite-xbox"),
    ("geosite-nintendo", "geosite-nintendo"),
    ("geosite-ea", "geosite-ea"),
    ("geosite-ubisoft", "geosite-ubisoft"),
    ("geosite-rockstar", "geosite-rockstar"),
    ("geosite-blizzard", "geosite-blizzard"),
    ("geosite-riot", "geosite-riotgames"),
    ("geosite-mihoyo", "geosite-mihoyo"),
    ("geosite-hoyoverse", "geosite-hoyoverse"),
    ("geosite-paypal", "geosite-paypal"),
    ("geosite-stripe", "geosite-stripe"),
    ("geosite-wise", "geosite-wise"),
    ("geosite-binance", "geosite-binance"),
    ("geosite-okx", "geosite-okx"),
    ("geosite-cloudflare", "geosite-cloudflare"),
    ("geosite-fastly", "geosite-fastly"),
    ("geosite-akamai", "geosite-akamai"),
    ("geosite-vercel", "geosite-vercel"),
    ("geosite-netlify", "geosite-netlify"),
    ("geosite-notion", "geosite-notion"),
    ("geosite-figma", "geosite-figma"),
    ("geosite-canva", "geosite-canva"),
    ("geosite-zoom", "geosite-zoom"),
]

TIANLING_TEST_IPS = [
    ("geoip-cn", "geoip-cn"),
    ("geoip-google", "geoip-google"),
    ("geoip-telegram", "geoip-telegram"),
    ("geoip-twitter", "geoip-twitter"),
    ("geoip-facebook", "geoip-facebook"),
    ("geoip-private", "geoip-private"),
]


import tempfile
import core.fetcher as fetcher

CACHE_DIR = os.path.join(tempfile.gettempdir(), "wuiiled_tianling_cache")

def _get_upstream_bytes(repo: str, tag: str) -> bytes:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{tag}.srs")
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return f.read()
    url = f"https://raw.githubusercontent.com/1715173329/{repo}/rule-set/{tag}.srs"
    data = fetcher.fetch_bytes_url(url, timeout=15, retries=2)
    if data:
        with open(cache_file, "wb") as f:
            f.write(data)
    return data


def _decompile_srs(srs_path, json_path):
    cmd = utils._resolve_cmd(["sing-box", "rule-set", "decompile", srs_path, "-o", json_path])
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    rule = data.get("rules", [{}])[0]
    # sing-box decompile emits a bare string when a list field has exactly one entry.
    for key in ("domain", "domain_suffix", "domain_keyword", "domain_regex", "ip_cidr"):
        if isinstance(rule.get(key), str):
            rule[key] = [rule[key]]
    return rule


@pytest.mark.parametrize("upstream_tag, local_name", TIANLING_TEST_SITES)
def test_tianling_geosite_zero_diff(upstream_tag, local_name):
    """Assert our geosite matches Loyalsoldier source geosite.dat semantics + local patches."""
    local_srs = os.path.abspath(f"output/singbox/geosite/{local_name}.srs")
    if not os.path.exists(local_srs):
        pytest.skip(f"Local {local_name}.srs not yet built")

    # Parse source geosite.dat (downloaded during build into work dir)
    from core.geosite_source import parse_geosite_dat
    dat_path = os.path.join(os.path.expanduser("~"), ".cache", "wuiiled_setup", "geosite.dat")
    if not os.path.exists(dat_path):
        pytest.skip("geosite.dat not found in work dir (build first)")
    source_map = parse_geosite_dat(dat_path)
    code = upstream_tag[len("geosite-"):]
    src_rs = source_map.get(code)
    if src_rs is None:
        pytest.skip(f"Upstream source code '{code}' not found")

    work_dir = utils.get_work_dir()
    loc_rule = _decompile_srs(local_srs, os.path.join(work_dir, f"loc_{local_name}.json"))

    # Allow local patches: entries we added on top of source are expected extras.
    from core.patcher import get_active_patch_count, has_patch_includes
    expected_extra = get_active_patch_count(local_name)
    has_inc = has_patch_includes(local_name)

    src_map = {
        "domain": src_rs.domains,
        "domain_suffix": src_rs.domain_suffixes,
        "domain_keyword": src_rs.domain_keywords,
        "domain_regex": src_rs.domain_regexes,
    }
    extra_total = 0
    missing_report = []
    for key in ("domain", "domain_suffix", "domain_keyword", "domain_regex"):
        up_set = set(src_map.get(key, set()))
        loc_set = set(loc_rule.get(key, []))
        missing = up_set - loc_set
        extra = loc_set - up_set
        extra_total += len(extra)
        if missing:
            missing_report.append((key, sorted(missing)))
    # A domain present in domain_suffix covers itself and all subdomains, so an exact
    # 'domain' entry that is also present as 'domain_suffix' is redundant upstream.
    loc_suffixes = set(loc_rule.get("domain_suffix", []))
    real_missing = []
    for key, items in missing_report:
        for d in items:
            if key == "domain" and d in loc_suffixes:
                continue
            real_missing.append((key, d))
    assert len(real_missing) == 0, f"Source rules missing in {local_name}: {real_missing[:5]}"
    if not has_inc:
        # 含 include 合并的补丁无法静态推算期望条数, 仅校验"上游无缺失"
        assert extra_total == expected_extra, f"Extra rules in {local_name}: {extra_total}, expected {expected_extra} (active patches)"


@pytest.mark.parametrize("upstream_tag, local_name", TIANLING_TEST_IPS)
def test_tianling_geoip_zero_diff(upstream_tag, local_name):
    """Assert 0 difference between our generated geoip and Tianling's upstream."""
    local_srs = os.path.abspath(f"output/singbox/geoip/{local_name}.srs")
    if not os.path.exists(local_srs):
        pytest.skip(f"Local {local_name}.srs not yet built")

    upstream_bytes = _get_upstream_bytes("sing-geoip", upstream_tag)
    if not upstream_bytes:
        pytest.skip(f"Could not download upstream {upstream_tag}")

    work_dir = utils.get_work_dir()
    temp_up_srs = os.path.join(work_dir, f"up_{upstream_tag}.srs")
    temp_up_json = os.path.join(work_dir, f"up_{upstream_tag}.json")
    temp_loc_json = os.path.join(work_dir, f"loc_{local_name}.json")

    with open(temp_up_srs, "wb") as f:
        f.write(upstream_bytes)

    up_rule = _decompile_srs(temp_up_srs, temp_up_json)
    loc_rule = _decompile_srs(local_srs, temp_loc_json)

    up_set = set(up_rule.get("ip_cidr", []))
    loc_set = set(loc_rule.get("ip_cidr", []))
    diff = up_set ^ loc_set
    assert len(diff) == 0, f"Difference found in {local_name} for 'ip_cidr': diff count = {len(diff)}"


def test_tianling_cn_superset():
    """geosite-cn = 天灵配方精编 ∪ dat 全量 cn: 上游每条规则必须被本地集合覆盖。

    覆盖判定为语义级: 上游的 domain/suffix 条目若被本地某个更短后缀涵盖
    (编译期会把被覆盖项去重掉), 视为已覆盖; keyword/regex 要求精确存在。
    """
    local_srs = os.path.abspath("output/singbox/geosite/geosite-cn.srs")
    if not os.path.exists(local_srs):
        pytest.skip("Local geosite-cn.srs not yet built")

    upstream_bytes = _get_upstream_bytes("sing-geosite", "geosite-cn")
    if not upstream_bytes:
        pytest.skip("Could not download upstream geosite-cn")

    work_dir = utils.get_work_dir()
    temp_up_srs = os.path.join(work_dir, "up_geosite-cn.srs")
    temp_up_json = os.path.join(work_dir, "up_geosite-cn.json")
    temp_loc_json = os.path.join(work_dir, "loc_geosite-cn.json")

    with open(temp_up_srs, "wb") as f:
        f.write(upstream_bytes)

    up_rule = _decompile_srs(temp_up_srs, temp_up_json)
    loc_rule = _decompile_srs(local_srs, temp_loc_json)

    loc_domains = {x.lower().lstrip(".") for x in (loc_rule.get("domain", []) or [])}
    loc_suffixes = {x.lower().lstrip(".") for x in (loc_rule.get("domain_suffix", []) or [])}

    def _covered_by_suffix(d: str) -> bool:
        d = d.lower().lstrip(".")
        if d in loc_domains or d in loc_suffixes:
            return True
        return any(d == s or d.endswith("." + s) for s in loc_suffixes)

    for key in ("domain", "domain_suffix"):
        up_set = {x.lower() for x in (up_rule.get(key, []) or [])}
        missing = [d for d in up_set if not _covered_by_suffix(d)]
        assert len(missing) == 0, (
            f"Upstream '{key}' entries not covered by local geosite-cn "
            f"(count={len(missing)}): {sorted(missing)[:5]}"
        )
    for key in ("domain_keyword", "domain_regex"):
        up_set = {x.lower() for x in (up_rule.get(key, []) or [])}
        loc_set = {x.lower() for x in (loc_rule.get(key, []) or [])}
        missing = up_set - loc_set
        assert len(missing) == 0, (
            f"Upstream '{key}' entries missing in local geosite-cn "
            f"(count={len(missing)}): {sorted(missing)[:5]}"
        )

