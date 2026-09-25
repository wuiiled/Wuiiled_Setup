# -*- coding: utf-8 -*-
"""OxiDNS 发布契约测试: smartdns / mosdns-x 分支的发布清单必须覆盖线上 OxiDNS
的下载需求 (providers 三张表 == 线上 config downloads 段)。

背景事故 (2026-09-25~26): OxiDNS 白名单把 geosite-ad-precise / geosite-ad-allow /
geoip-gfw 排除、且未提供 geosite-geolocation-!cn 旧命名别名, 导致线上
10.0.0.2 的 4 个下载 URL 404、规则文件停更。本测试防止白名单再次与线上漂移。

注意: 黑加白双集合不在主 IR 中, 导出器需从 manager 产出的
work_dir/ads/blocklist_b.txt + whitelist_b.txt 合成——本测试同时锁定该注入路径。
"""
import importlib
import os

import pytest

import providers
import utils
from core.models import RuleSet

BUILDERS = [
    ("build_smartdns", "build_smartdns_rules"),
    ("build_mosdns", "build_mosdns_rules"),
]


def _seed_blackwhite_files():
    """在共享 work_dir 里伪造 manager 产出的黑加白文件 (导出器注入的数据源)。"""
    ads_dir = os.path.join(utils.get_work_dir(), "ads")
    os.makedirs(ads_dir, exist_ok=True)
    with open(os.path.join(ads_dir, "blocklist_b.txt"), "w", encoding="utf-8") as f:
        f.write("ads-bad.example\nblock.me.example\n")
    with open(os.path.join(ads_dir, "whitelist_b.txt"), "w", encoding="utf-8") as f:
        f.write("allow.me.example\n")


def _published_rules():
    """构造主 IR: 恰好覆盖白名单+别名目标, 但不含黑加白双集合 (与真实 all_rules 一致)。"""
    names = (set(providers.OXIDNS_RULE_FILES.values())
             | providers.OXIDNS_EXTRA_RULESETS
             | set(providers.OXIDNS_SUBDIR_ALIASES.values()))
    rules = {}
    for name in names:
        if name in ("geosite-ad-precise", "geosite-ad-allow"):
            continue  # 黑加白走文件注入, 不在主 IR
        if name.startswith("geoip-"):
            rules[name] = RuleSet(name=name, category="geoip", ip_cidrs={"203.0.113.0/24"})
        else:
            rules[name] = RuleSet(name=name, category="geosite", domain_suffixes={"example.org"})
    return rules


@pytest.mark.parametrize("modname,func", BUILDERS)
def test_publish_covers_oxidns_downloads(tmp_path, modname, func):
    _seed_blackwhite_files()
    mod = importlib.import_module(modname)
    getattr(mod, func)(_published_rules(), str(tmp_path))

    # 1. 线上额外订阅的集合必须发布 (上次事故的 4 个中的 3 个);
    #    黑加白双集合由文件注入合成
    for name in providers.OXIDNS_EXTRA_RULESETS:
        sub = "geoip" if name.startswith("geoip-") else "geosite"
        assert (tmp_path / sub / f"{name}.txt").exists(), f"线上订阅但未发布: {name}"
    prec = (tmp_path / "geosite" / "geosite-ad-precise.txt").read_text(encoding="utf-8")
    allow = (tmp_path / "geosite" / "geosite-ad-allow.txt").read_text(encoding="utf-8")
    assert "ads-bad.example" in prec and "block.me.example" in prec
    assert "allow.me.example" in allow

    # 2. 旧命名别名副本必须存在于 geosite/ 子目录 (线上 URL 的确切相对路径)
    for rel in providers.OXIDNS_SUBDIR_ALIASES:
        assert (tmp_path / rel).exists(), f"线上订阅的别名缺失: {rel}"

    # 3. 传统根目录兼容副本保持存在
    for legacy in providers.OXIDNS_RULE_FILES:
        assert (tmp_path / legacy).exists(), f"根目录兼容副本缺失: {legacy}"

    # 4. 白名单之外的集合不得发布 (例如 adg 专属的 geosite-pcdn)
    assert not (tmp_path / "geosite" / "geosite-pcdn.txt").exists()


def test_oxidns_lists_are_consistent():
    """别名目标必须可发布 (在白名单并集内), 且别名 base 不与标准名冲突。"""
    published = (set(providers.OXIDNS_RULE_FILES.values())
                 | providers.OXIDNS_EXTRA_RULESETS)
    for rel, target in providers.OXIDNS_SUBDIR_ALIASES.items():
        assert target in published, f"别名 {rel} 的目标集合 {target} 不在发布清单内"
        assert os.path.splitext(os.path.basename(rel))[0] != target


def test_smartdns_output_format_is_oxidns_syntax(tmp_path):
    """smartdns 分支行文法: 裸=后缀, full:=精确, keyword:/regexp:=原语义。

    消费端 OxiDNS (rule_matcher/domain.rs) 只识别这四种形式;
    SmartDNS 的 -./+. 语法会被 OxiDNS 当字面后缀而成为永不命中的死条目。
    """
    mod = importlib.import_module("build_smartdns")
    rs = RuleSet(
        name="geosite-cn",  # 白名单内, 否则会被发布过滤剔除
        category="geosite",
        domains={"exact.example"},
        domain_suffixes={"suffix.example", ".single"},
        domain_keywords={"somebrand"},
        domain_regexes={r"^ad[0-9]+\.example$"},
    )
    mod.build_smartdns_rules({"geosite-cn": rs}, str(tmp_path))
    lines = (tmp_path / "geosite" / "geosite-cn.txt").read_text(encoding="utf-8").splitlines()
    assert "suffix.example" in lines
    assert "single" in lines
    assert "full:exact.example" in lines
    assert "keyword:somebrand" in lines
    assert r"regexp:^ad[0-9]+\.example$" in lines
    assert not any(l.startswith("-.") or l.startswith("+.") for l in lines), lines
