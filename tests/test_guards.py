# -*- coding: utf-8 -*-
"""守卫与归一测试: 产物不变量校验、IDNA 归一、黑加白缺失硬失败。"""
import pytest

import providers
import utils
from core.models import RuleSet


# ---------- validate_output_invariants ----------

def _full_tree(tmp_path):
    """构造满足全部不变量的最小 output 树。"""
    ox = sorted(set(providers.OXIDNS_RULE_FILES.values()) | providers.OXIDNS_EXTRA_RULESETS)
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
    # 模拟上游整体失败: OxiDNS 白名单中的集合被发布为空
    victim = None
    for sub in ("geosite", "geoip"):
        p = tmp_path / "smartdns" / sub
        if p.is_dir() and any(p.iterdir()):
            victim = next(p.iterdir())
            break
    victim.write_text("", encoding="utf-8")
    with pytest.raises(RuntimeError, match="缺失或为空"):
        utils.validate_output_invariants(str(tmp_path), require_binaries=False)


# ---------- IDNA 归一 ----------

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


# ---------- 黑加白缺失硬失败 ----------

def test_load_blackwhite_missing_raises(tmp_path):
    empty_dir = tmp_path / "ads"
    empty_dir.mkdir()
    with pytest.raises(RuntimeError, match="黑加白中间产物缺失"):
        utils.load_blackwhite_rulesets(work_dir=str(tmp_path))


def test_load_blackwhite_empty_file_warns_and_skips(tmp_path):
    ads = tmp_path / "ads"
    ads.mkdir()
    (ads / "blocklist_b.txt").write_text("doubleclick.net\n", encoding="utf-8")
    (ads / "whitelist_b.txt").write_text("", encoding="utf-8")
    out = utils.load_blackwhite_rulesets(work_dir=str(tmp_path))
    assert "geosite-ad-precise" in out
    assert "geosite-ad-allow" not in out


# ---------- include:local 路径 (2026-09-28 发现其自引入即损坏: 误引 utils.read_local_file) ----------

def test_include_local_resolves():
    from core.patcher import _resolve_include
    rs = _resolve_include("local", "rules/addons/reject-addon.txt", None)
    assert rs is not None and rs.total_count > 0


def test_include_local_missing_returns_none():
    from core.patcher import _resolve_include
    assert _resolve_include("local", "rules/patches/__.nonexistent.__", None) is None
