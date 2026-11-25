# -*- coding: utf-8 -*-
"""守卫与归一测试: 产物不变量校验、基线底线守卫、IDNA 归一、AdGuard IR 渲染。"""
import pytest

import providers
import utils
from core.models import RuleSet


def _full_tree(tmp_path):
    """构造满足全部不变量的最小 output 树。"""
    ox = sorted(set(providers.OXIDNS_RULESETS) | providers.OXIDNS_EXTRA_RULESETS)
    for branch in ("smartdns", "mosdns-x"):
        for name in ox:
            sub = "geoip" if name.startswith("geoip-") else "geosite"
            p = tmp_path / branch / sub
            p.mkdir(parents=True, exist_ok=True)
            (p / f"{name}.txt").write_text("example.org\n", encoding="utf-8")
    for name in ("geosite-cn", "geosite-ad", "geosite-ad-precise", "geosite-ad-allow", "geosite-!cn"):
        p = tmp_path / "mihomo" / "geosite"
        p.mkdir(parents=True, exist_ok=True)
        (p / f"{name}.txt").write_text("example.org\n", encoding="utf-8")
    for name in ("geoip-cn", "geoip-gfw"):
        p = tmp_path / "mihomo" / "geoip"
        p.mkdir(parents=True, exist_ok=True)
        (p / f"{name}.txt").write_text("203.0.113.0/24\n", encoding="utf-8")
    for name in ("geosite-ad", "geosite-httpdns", "geosite-pcdn"):
        p = tmp_path / "adg"
        p.mkdir(parents=True, exist_ok=True)
        (p / f"{name}.txt").write_text("||example.org^\n", encoding="utf-8")
    for sub, name in (("geosite", "geosite-cn"), ("geosite", "geosite-ad"),
                      ("geosite", "geosite-!cn"), ("geoip", "geoip-cn")):
        p = tmp_path / "singbox" / sub
        p.mkdir(parents=True, exist_ok=True)
        (p / f"{name}.srs").write_bytes(b"SRS")


def test_validate_output_invariants_pass(tmp_path):
    _full_tree(tmp_path)
    utils.validate_output_invariants(str(tmp_path), require_binaries=False)
    utils.validate_output_invariants(str(tmp_path), require_binaries=True)


def test_validate_output_invariants_fails_on_empty_set(tmp_path):
    _full_tree(tmp_path)
    victim = None
    for sub in ("geosite", "geoip"):
        p = tmp_path / "smartdns" / sub
        if p.is_dir() and any(p.iterdir()):
            victim = next(p.iterdir())
            break
    victim.write_text("", encoding="utf-8")
    with pytest.raises(RuntimeError, match="缺失或为空"):
        utils.validate_output_invariants(str(tmp_path), require_binaries=False)


def test_validate_output_invariants_min_counts_circuit_breaker(tmp_path):
    _full_tree(tmp_path)
    with pytest.raises(RuntimeError, match="条数异常偏低"):
        utils.validate_output_invariants(
            str(tmp_path), require_binaries=False, min_counts={"geosite-ad": 500}
        )


def test_idna_normalize_converts_unicode_domain():
    rs = RuleSet(name="geosite-custom-emby", category="geosite",
                 domain_suffixes={"帝acg.xyz"})
    utils.idna_normalize_rules({"geosite-custom-emby": rs})
    assert len(rs.domain_suffixes) == 1
    entry = next(iter(rs.domain_suffixes))
    assert entry.isascii() and entry.endswith(".xyz")


def test_idna_normalize_leaves_ascii_and_keywords():
    rs = RuleSet(name="geosite-cn", category="geosite",
                 domains={"exact.example"},
                 domain_suffixes={".single", "suffix.example"},
                 domain_keywords={"somebrand"},
                 domain_regexes={r"^ad[0-9]+\.example$"})
    before = (set(rs.domains), set(rs.domain_suffixes),
              set(rs.domain_keywords), set(rs.domain_regexes))
    assert utils.idna_normalize_rules({"geosite-cn": rs}) == 0
    assert before == (rs.domains, rs.domain_suffixes, rs.domain_keywords, rs.domain_regexes)


def test_render_adguard_lines_from_ir():
    rules = {
        "geosite-ad-precise": RuleSet(
            name="geosite-ad-precise", category="geosite",
            domain_suffixes={"doubleclick.net", "ads.example.com"},
        ),
        "geosite-ad-allow": RuleSet(
            name="geosite-ad-allow", category="geosite",
            domain_suffixes={"fls.doubleclick.net"},
        ),
    }
    lines = utils.render_adguard_lines(rules)
    assert lines == ["||ads.example.com^", "||doubleclick.net^", "@@||fls.doubleclick.net^"]


def test_render_adguard_lines_missing_precise_raises():
    with pytest.raises(RuntimeError, match="geosite-ad-precise"):
        utils.render_adguard_lines({})


def test_include_local_resolves():
    from core.patcher import _resolve_include
    rs = _resolve_include("local", "rules/addons/reject-addon.txt", None)
    assert rs is not None and rs.total_count > 0


def test_include_local_missing_returns_none():
    from core.patcher import _resolve_include
    assert _resolve_include("local", "rules/patches/__.nonexistent.__", None) is None


def test_read_local_file_path_traversal():
    from core.fetcher import read_local_file
    assert read_local_file("../../something_sensitive.txt") == ""
    assert read_local_file("../../../etc/passwd") == ""
    assert read_local_file("C:\\Windows\\win.ini") == ""
    assert read_local_file("D:\\confidential.txt") == ""
    assert read_local_file("/etc/passwd") == ""


def test_assert_no_compile_failures():
    utils._COMPILE_FAILURES.clear()
    try:
        utils.assert_no_compile_failures()
        utils._COMPILE_FAILURES.append("geosite-test.srs")
        with pytest.raises(RuntimeError, match="编译产物完整性校验失败"):
            utils.assert_no_compile_failures()
    finally:
        utils._COMPILE_FAILURES.clear()
