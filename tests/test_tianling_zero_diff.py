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
TIANLING_TEST_SITES = [
    ("geosite-cn", "geosite-cn"),
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

_SCRATCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "brain", "c1999305-4f56-4424-9370-d2d9b412f6f4", "scratch", "tianling_check"))
CACHE_DIR = _SCRATCH_DIR if os.path.exists(_SCRATCH_DIR) else os.path.join(tempfile.gettempdir(), "wuiiled_tianling_cache")

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
    return data.get("rules", [{}])[0]


@pytest.mark.parametrize("upstream_tag, local_name", TIANLING_TEST_SITES)
def test_tianling_geosite_zero_diff(upstream_tag, local_name):
    """Assert 0 difference between our generated geosite and Tianling's upstream."""
    local_srs = os.path.abspath(f"output/singbox/geosite/{local_name}.srs")
    if not os.path.exists(local_srs):
        pytest.skip(f"Local {local_name}.srs not yet built")

    upstream_bytes = _get_upstream_bytes("sing-geosite", upstream_tag)
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

    for key in ("domain", "domain_suffix", "domain_keyword", "domain_regex"):
        up_set = set(up_rule.get(key, []))
        loc_set = set(loc_rule.get(key, []))
        diff = up_set ^ loc_set
        assert len(diff) == 0, f"Difference found in {local_name} for key '{key}': diff count = {len(diff)}"


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

