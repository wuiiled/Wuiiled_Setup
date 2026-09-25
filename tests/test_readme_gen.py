# -*- coding: utf-8 -*-
"""
README 生成一致性测试: 保证"介绍"永远等于"实际包含的内容"。
- PLATFORM_MARKERS 的包含性判断语义 (后缀覆盖/精确成员, 无误报);
- manifest 说明列渲染按来源类型输出;
- RULE_METADATA 无死键、无硬编码条数/"子类"等会漂移的宣称;
- 0-Diff 徽章只出现在 singbox 分支。
"""
import json
import os

import pytest

from core.models import RuleSet
from core.readme_gen import (
    CATEGORY_DEFS,
    PLATFORM_MARKERS,
    RULE_METADATA,
    _manifest_note,
    _render_note,
    build_manifest,
    compute_markers,
    generate_branch_readme,
    marker_in_ruleset,
    write_manifest,
)


def _rs(name="geosite-test", kind="dat", domains=None, suffixes=None, category="geosite", code="test", sources=None):
    rs = RuleSet(
        name=name, category=category,
        domains=set(domains or []), domain_suffixes=set(suffixes or []),
        source_kind=kind, sources=sources or [], dat_code=code,
    )
    return rs


# ---------- marker 包含性语义 ----------

def test_marker_matches_exact_domain_member():
    rs = _rs(domains=["openai.com"])
    assert marker_in_ruleset("openai.com", rs)


def test_marker_matches_subdomain_of_member_suffix():
    rs = _rs(suffixes=["bilibili.com"])
    assert marker_in_ruleset("bilibili.com", rs)
    assert marker_in_ruleset("www.bilibili.com", rs)


def test_marker_no_false_positive_on_lookalike():
    rs = _rs(suffixes=["bilibili.com"])
    assert not marker_in_ruleset("xxbilibili.com", rs)
    assert not marker_in_ruleset("bilibili.com.evil.example", rs)
    assert not marker_in_ruleset("netflix.com", rs)


def test_marker_matches_leading_dot_suffix():
    rs = _rs(suffixes=[".youtube"])
    assert marker_in_ruleset("youtube", rs)
    assert marker_in_ruleset("www.youtube", rs)
    assert not marker_in_ruleset("notyoutube", rs)


def test_compute_markers_only_reports_present_platforms():
    # category-media 真实构成: 新闻媒体, 不含 Netflix/YouTube 等流媒体
    media = _rs(suffixes=["aljazeera.net", "afp.com", "9news.com.au"])
    got = compute_markers(media)
    assert "半岛电视台" in got and "法新社" in got
    assert "Netflix" not in got and "YouTube" not in got

    # category-porn/entertainment 类: 命中流媒体才宣称
    ent = _rs(suffixes=["youtube.com", "netflix.com", "twitch.tv"])
    got2 = compute_markers(ent)
    assert {"YouTube", "Netflix", "Twitch"} <= set(got2)


def test_compute_markers_skips_geoip():
    rs = _rs(name="geoip-cn", category="geoip", suffixes=["google.com"])
    assert compute_markers(rs) == []


# ---------- manifest 说明列渲染 ----------

def test_manifest_note_dat_with_markers():
    note = _manifest_note({"kind": "dat", "dat_code": "category-porn",
                           "markers": ["Dropbox"], "sources": ["Loyalsoldier/v2ray-rules-dat"]})
    assert note == "dat 分类 category-porn · 含 Dropbox"


def test_manifest_note_dat_marker_cap():
    markers = [f"P{i}" for i in range(9)]
    note = _manifest_note({"kind": "dat", "dat_code": "x", "markers": markers, "sources": []})
    assert note.startswith("dat 分类 x · 含 P0 / P1 / P2 / P3 / P4 / P5 等 9 项")


def test_manifest_note_recipe_self_skk_custom():
    assert _manifest_note({"kind": "recipe", "sources": ["天灵配方精编 cn", "cn-additional-list"]}) \
        == "配方合成: 天灵配方精编 cn ∪ cn-additional-list"
    assert _manifest_note({"kind": "self", "sources": ["OpenClash", "ShellCrash"]}) \
        == "上游: OpenClash · ShellCrash"
    assert _manifest_note({"kind": "skk", "sources": ["ruleset.skk.moe"]}) \
        == "上游: ruleset.skk.moe"
    assert _manifest_note({"kind": "custom", "sources": ["rules/Custom_Emby.txt"]}) \
        == "用户本地规则: rules/Custom_Emby.txt"


def test_build_manifest_carries_source_profile():
    rs = _rs(name="geosite-steam", domains=["steampowered.com"], code="steam",
             sources=["Loyalsoldier/v2ray-rules-dat"])
    m = build_manifest({"geosite-steam": rs})
    assert m["geosite-steam"]["kind"] == "dat"
    assert m["geosite-steam"]["dat_code"] == "steam"
    assert "Steam" in m["geosite-steam"]["markers"]
    assert m["geosite-steam"]["count"] == 1


# ---------- 元数据一致性 (防死键 / 防漂移宣称) ----------

def _known_universe():
    from core.manager import TIANLING_GEOIPS, TIANLING_GEOSITES
    import providers
    universe = set(TIANLING_GEOSITES.values()) | {"geosite-cn"} | set(TIANLING_GEOIPS.values())
    universe |= {"geosite-ad", "geosite-ai", "geosite-fakeip-filter", "geosite-reject-drop", "geoip-gfw"}
    universe |= set(providers.MIHOMO_SKK.keys()) | set(providers.CUSTOM_RULES.keys())
    universe |= {  # 构建层产物 (不在 all_rules 中; 兼容别名机制已退役, 无别名集合)
        "geosite-ad-precise", "geosite-ad-allow", "geosite-pcdn",
    }
    return universe


def test_no_alias_names_registered():
    """别名机制已整体退役: 任何旧别名都不应再出现在 metadata/分类/构建层宇宙中。"""
    retired = {"geosite-emby", "geosite-game", "geosite-microsoftcdn",
               "geosite-appleservice", "geosite-applecn", "geosite-applecdn"}
    assert not (set(RULE_METADATA) & retired)
    for _cat, _title, names in CATEGORY_DEFS:
        assert not (set(names) & retired)


def test_metadata_has_no_dead_keys():
    universe = _known_universe()
    dead = set(RULE_METADATA) - universe
    assert not dead, f"RULE_METADATA 死键 (任何分支都不会构建): {sorted(dead)}"


def test_universe_sets_all_have_metadata():
    universe = _known_universe()
    missing = universe - set(RULE_METADATA)
    assert not missing, f"已构建集合缺少人工描述: {sorted(missing)}"


def test_category_defs_names_all_in_metadata():
    for _cat, _title, names in CATEGORY_DEFS:
        for n in names:
            assert n in RULE_METADATA, f"CATEGORY_DEFS 引用了无描述的集合: {n}"


def test_netdisk_registered():
    from core.manager import TIANLING_GEOSITES
    assert TIANLING_GEOSITES.get("geosite-category-netdisk-!cn") == "geosite-netdisk-!cn"
    flat = {n for _c, _t, names in CATEGORY_DEFS for n in names}
    assert "geosite-netdisk-!cn" in flat
    assert "geosite-pcdn" in flat  # adg 分支不再掉入"其他规则集"


def test_metadata_free_of_stale_claims():
    import re
    stale = re.compile(r"子类|\d[\d,，.]*\s*\+?\s*(条|域名)|BT/PT")
    for name, meta in RULE_METADATA.items():
        for field in ("desc", "note"):
            text = meta.get(field, "")
            assert not stale.search(text), f"{name}.{field} 含硬编码条数/子类等会漂移的宣称: {text}"


# ---------- 0-Diff 徽章只在 singbox / 渲染冒烟 ----------

@pytest.fixture()
def branch_outputs(tmp_path):
    """构造最小可用 output 树: singbox + mihomo 各一个集合。"""
    out = tmp_path / "output"
    write_manifest({"geosite-steam": _rs(name="geosite-steam", domains=["steampowered.com"],
                                         suffixes=["steamcommunity.com"], code="steam",
                                         sources=["Loyalsoldier/v2ray-rules-dat"])}, str(out))
    for branch, ext in (("singbox", "json"), ("mihomo", "txt")):
        gdir = out / branch / "geosite"  # output/<branch>/geosite (CI 再整体移入 rules/)
        gdir.mkdir(parents=True)
        if ext == "json":
            (gdir / "geosite-steam.json").write_text(
                json.dumps({"version": 5, "rules": [{"domain": ["steampowered.com"],
                                                     "domain_suffix": ["steamcommunity.com"]}]}),
                encoding="utf-8")
            (gdir / "geosite-steam.srs").write_bytes(b"srs")
        else:
            (gdir / "geosite-steam.txt").write_text("steampowered.com\n+.steamcommunity.com\n", encoding="utf-8")
            (gdir / "geosite-steam.mrs").write_bytes(b"mrs")
    return out


def test_zero_diff_badge_only_on_singbox(branch_outputs):
    generate_branch_readme("singbox", str(branch_outputs))
    generate_branch_readme("mihomo", str(branch_outputs))
    sb = (branch_outputs / "singbox" / "README.md").read_text(encoding="utf-8")
    mh = (branch_outputs / "mihomo" / "README.md").read_text(encoding="utf-8")
    assert "0--Diff" in sb
    assert "0--Diff" not in mh


def test_rendered_note_reflects_verified_markers(branch_outputs):
    generate_branch_readme("mihomo", str(branch_outputs))
    mh = (branch_outputs / "mihomo" / "README.md").read_text(encoding="utf-8")
    assert "dat 分类 steam" in mh
    assert "含 Steam" in mh
    # 未宣称任何未验证平台
    for plat in PLATFORM_MARKERS:
        if plat != "Steam":
            assert f"含 {plat}" not in mh
