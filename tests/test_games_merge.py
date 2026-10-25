# -*- coding: utf-8 -*-
"""
Games 三集合重新定义测试 (2026-10-26):
- geosite-games-!cn = 境外 games + platforms-download 海外节点 (剔除 @cn)
- geosite-games-cn  = 国内 games + platforms-download @cn 节点 + 加速器域名
- geosite-games     = games-cn ∪ games-!cn (全量 platforms-download + 加速器)
覆盖 patcher 的 include/exclude 指令与 manager 的吸收豁免逻辑。
"""
import pytest
from core.models import RuleSet
from core.patcher import apply_patches, has_patch_includes, load_patch_file
import core.manager as manager


def _mk(name, domains=(), suffixes=()):
    return RuleSet(name=name, category="geosite",
                   domains=set(domains), domain_suffixes=set(suffixes))


def _mock_dat_map():
    return {
        # platforms-download 主视图: 海外节点 + @cn 中国区节点 (主视图含全部)
        "category-game-platforms-download": _mk("pd",
            domains={"cache1-ams1.steamcontent.com", "download.epicgames.com",
                     "st.dl.eccdnx.com", "cdn-qc.content.steamchina.com"}),
        # @cn 属性视图: 仅中国区下载节点
        "category-game-platforms-download@cn": _mk("pd@cn",
            domains={"st.dl.eccdnx.com", "cdn-qc.content.steamchina.com"}),
        # 加速器
        "category-game-accelerator-cn": _mk("acc",
            suffixes={"uu.163.com", "leigod.com", "xunyou.com"}),
    }


def _base_rules():
    return {
        "geosite-games-!cn": _mk("geosite-games-!cn",
            suffixes={"steampowered.com", "epicgames.com"}),
        "geosite-games-cn": _mk("geosite-games-cn",
            suffixes={"tencent-games.com-ish", "mihoyo.com"}),
        "geosite-games": None,  # 由测试单独构造
    }


def test_patch_files_declared():
    # 三个补丁文件存在且含 include 指令 (0-Diff 期望值分支依赖)
    for n in ("geosite-games", "geosite-games-cn", "geosite-games-!cn"):
        assert load_patch_file(n), f"{n} 补丁文件缺失"
        assert has_patch_includes(n), f"{n} 补丁无 include 指令"


def test_games_notcn_gets_intl_download_nodes():
    rs = _mk("geosite-games-!cn", suffixes={"steampowered.com"})
    rs, _p, _u, stats = apply_patches(rs, dat_map=_mock_dat_map())
    all_d = rs.domains | rs.domain_suffixes
    assert "cache1-ams1.steamcontent.com" in rs.domains      # 海外 Steam cache 并入
    assert "download.epicgames.com" in rs.domains            # Epic 海外下载并入
    assert "st.dl.eccdnx.com" not in rs.domains              # @cn 中国区节点被剔除
    assert "cdn-qc.content.steamchina.com" not in rs.domains
    assert not (rs.domain_suffixes & {"uu.163.com"})         # 加速器不在 !cn
    # exclude 计数为正的移除数
    ex = [s for s in stats if s[0] == "exclude:dat"]
    assert ex and ex[0][2] == 2  # 剔除 2 条 @cn 节点


def test_games_cn_gets_cn_nodes_and_accelerators():
    rs = _mk("geosite-games-cn", suffixes={"mihoyo.com"})
    rs, _p, _u, stats = apply_patches(rs, dat_map=_mock_dat_map())
    assert "st.dl.eccdnx.com" in rs.domains                  # @cn 中国区下载节点并入
    assert "cdn-qc.content.steamchina.com" in rs.domains
    assert rs.domain_suffixes >= {"uu.163.com", "leigod.com"}  # 加速器并入
    assert "cache1-ams1.steamcontent.com" not in rs.domains  # 海外节点不在 cn


def test_games_full_is_union():
    rs = _mk("geosite-games", suffixes={"steampowered.com", "mihoyo.com"})
    rs, _p, _u, _stats = apply_patches(rs, dat_map=_mock_dat_map())
    # 完整 platforms-download (CN + 海外) + 加速器全部并入
    assert rs.domains >= {"cache1-ams1.steamcontent.com", "st.dl.eccdnx.com",
                          "download.epicgames.com", "cdn-qc.content.steamchina.com"}
    assert rs.domain_suffixes >= {"uu.163.com", "xunyou.com"}


def test_exclude_failure_on_missing_dat_category():
    # dat_map 缺失 exclude 目标 (@cn 视图) -> 计 -1, 由 manager 侧中止构建
    rs = _mk("geosite-games-!cn", suffixes={"steampowered.com"})
    bad_map = _mock_dat_map()
    del bad_map["category-game-platforms-download@cn"]
    rs, _p, _u, stats = apply_patches(rs, dat_map=bad_map)
    assert any(k == "exclude:dat" and n == -1 for k, _t, n in stats)


def test_absorb_protects_base_entries():
    # 吸收仅作用于 include 增量: 基座条目参与涵盖判定但绝不被删 (0-Diff 同构)
    from core.cleaner import absorb_covered_domains
    base_suffix = "steamcontent.com"           # 基座后缀 (上游 dat)
    added_full = "cache1-ams1.steamcontent.com"  # include 增量 (被基座涵盖)
    dom, suf, removed = absorb_covered_domains(
        domains={added_full}, suffixes={base_suffix, "b.com"},
        protect={base_suffix})
    assert dom == set() and base_suffix in suf      # 增量被吸收, 基座保留
    # 无 protect 时基座内部冗余照常吸收 (自研 loader 的既有语义不变)
    dom2, suf2, _ = absorb_covered_domains(set(), {"a.b.com", "b.com"})
    assert suf2 == {"b.com"}


def test_apply_rule_patches_keeps_base_intact():
    # manager 集成: games-!cn 场景, 基座 (上游条目) 在含 include 的吸收后零丢失
    rules = {
        "geosite-games-!cn": _mk("geosite-games-!cn",
            domains={"base-full.example.com"},
            suffixes={"steampowered.com", "steamcontent.com"}),
    }
    manager._DAT_SOURCE_MAP = _mock_dat_map()
    try:
        manager.apply_rule_patches(rules)
    finally:
        manager._DAT_SOURCE_MAP = {}
    rs = rules["geosite-games-!cn"]
    assert "steampowered.com" in rs.domain_suffixes     # 基座后缀零丢失
    assert "base-full.example.com" in rs.domains        # 基座精确域零丢失
    # include 增量中被基座涵盖的条目被吸收 (cache1-ams1.steamcontent.com ⊂ steamcontent.com)
    assert "cache1-ams1.steamcontent.com" not in rs.domains
    # 不被涵盖的增量保留
    assert "download.epicgames.com" in rs.domains
