# -*- coding: utf-8 -*-
"""
逐源"上一次完整拉取"缓存全链路测试:
- 拉取成功即写缓存
- 拉取失败回退缓存继续合成 (all-or-nothing 语义的容错半边)
- 无缓存 / 缓存超龄 → 抛错中止构建 (严格半边)
- download_files_parallel: 任一源既失败又无缓存 → 整体拒绝合成
- ASN 双源失败回退该 ASN 上一次完整拉取的网段
- 天灵 .srs 拉取失败回退缓存 (fetch_bytes_cached)
"""
import json
import os
import time
from unittest.mock import patch

import pytest

import utils
import core.fetcher as fetcher


def _seed_cache(url, body, age_days=0.0):
    """直接向 SOURCE_CACHE_DIR 写入一份缓存 (受 conftest 隔离 fixture 保护)。"""
    os.makedirs(fetcher.SOURCE_CACHE_DIR, exist_ok=True)
    body_p, meta_p = fetcher._source_cache_paths(url)
    data = body if isinstance(body, bytes) else body.encode("utf-8")
    with open(body_p, "wb") as f:
        f.write(data)
    with open(meta_p, "w", encoding="utf-8") as f:
        json.dump({"url": url, "fetched_at": time.time() - age_days * 86400}, f)


def test_success_refreshes_cache():
    url = "https://x.example/list.txt"
    with patch.object(fetcher, "fetch_text_url", return_value="a.example\n"):
        out = fetcher.fetch_text_cached(url)
    assert out == "a.example\n"
    body_p, meta_p = fetcher._source_cache_paths(url)
    assert os.path.exists(body_p)
    assert json.load(open(meta_p, encoding="utf-8"))["url"] == url


def test_failure_falls_back_to_fresh_cache():
    url = "https://x.example/list.txt"
    _seed_cache(url, "stale.example\n", age_days=1)
    with patch.object(fetcher, "fetch_text_url", return_value=""):
        out = fetcher.fetch_text_cached(url)
    assert out == "stale.example\n"


def test_failure_without_cache_raises():
    url = "https://x.example/list.txt"
    with patch.object(fetcher, "fetch_text_url", return_value=""):
        with pytest.raises(RuntimeError, match="无可用缓存"):
            fetcher.fetch_text_cached(url)


def test_stale_cache_beyond_max_age_raises():
    url = "https://x.example/list.txt"
    _seed_cache(url, "ancient.example\n", age_days=999)
    with patch.object(fetcher, "fetch_text_url", return_value=""):
        with pytest.raises(RuntimeError, match="无可用缓存"):
            fetcher.fetch_text_cached(url)


def test_bytes_failure_falls_back(tmp_path):
    url = "https://x.example/blob.srs"
    _seed_cache(url, b"\x00\x01BINBODY", age_days=2)
    with patch.object(fetcher, "fetch_bytes_url", return_value=b""):
        out = fetcher.fetch_bytes_cached(url)
    assert out == b"\x00\x01BINBODY"


def test_download_files_parallel_rejects_missing_source(tmp_path):
    out_file = str(tmp_path / "merged.txt")
    # 源 1 正常, 源 2 拉取失败且无缓存 -> 整体拒绝合成
    with patch("utils.download_file", side_effect=["good.example\n", RuntimeError("boom")]):
        with pytest.raises(RuntimeError, match="拒绝合成不完整规则"):
            utils.download_files_parallel(out_file, ["https://a.example/1", "https://a.example/2"])


def test_download_files_parallel_accepts_cached_fallback(tmp_path):
    out_file = str(tmp_path / "merged.txt")
    # 源 2 "失败" 但 download_file (缓存回退) 返回上一次完整拉取内容 -> 照常合成
    with patch("utils.download_file", side_effect=["good.example\n", "cached.example\n"]):
        utils.download_files_parallel(out_file, ["https://a.example/1", "https://a.example/2"])
    content = open(out_file, encoding="utf-8").read()
    assert "good.example" in content and "cached.example" in content


def test_asn_double_failure_falls_back_to_cached_cidrs():
    # 先成功一次 -> 写入 AS 网段缓存
    with patch.object(fetcher, "_fetch_raw_text", return_value=json.dumps(
        {"prefixes": {"ipv4": ["160.79.104.0/21"], "ipv6": []}})):
        cidrs, ok = fetcher.fetch_single_asn_cidrs("399358")
    assert ok and cidrs == {"160.79.104.0/21"}

    # 双源失败 -> 回退缓存, authoritative=True, manager 不中止
    with patch.object(fetcher, "_fetch_raw_text", return_value=""):
        cidrs2, ok2 = fetcher.fetch_single_asn_cidrs("399358")
    assert ok2 and cidrs2 == {"160.79.104.0/21"}


def test_asn_double_failure_without_cache_still_fails():
    # 无缓存时双源失败仍返回 authoritative=False (manager 拦截)
    with patch.object(fetcher, "_fetch_raw_text", return_value=""):
        cidrs, ok = fetcher.fetch_single_asn_cidrs("64599")
    assert not ok and cidrs == set()
