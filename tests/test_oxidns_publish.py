# -*- coding: utf-8 -*-
"""OxiDNS 发布契约测试: smartdns / mosdns-x 分支的发布清单必须覆盖线上 OxiDNS
的下载需求 (providers 三张表 == 线上 config downloads 段)。

背景事故 (2026-09-25~26): OxiDNS 白名单把 geosite-ad-precise / geosite-ad-allow /
geoip-gfw 排除、且未提供 geosite-geolocation-!cn 旧命名别名, 导致线上
10.0.0.2 的 4 个下载 URL 404、规则文件停更。本测试防止白名单再次与线上漂移。
"""
import importlib
import os

import pytest

import providers
from core.models import RuleSet

BUILDERS = [
    ("build_smartdns", "build_smartdns_rules"),
    ("build_mosdns", "build_mosdns_rules"),
]


def _published_rules():
    """构造恰好覆盖发布清单 (白名单 + 额外订阅 + 别名目标) 的最小 IR。"""
    names = (set(providers.OXIDNS_RULE_FILES.values())
             | providers.OXIDNS_EXTRA_RULESETS
             | set(providers.OXIDNS_SUBDIR_ALIASES.values()))
    rules = {}
    for name in names:
        if name.startswith("geoip-"):
            rules[name] = RuleSet(name=name, category="geoip", ip_cidrs={"203.0.113.0/24"})
        else:
            rules[name] = RuleSet(name=name, category="geosite", domain_suffixes={"example.org"})
    return rules


@pytest.mark.parametrize("modname,func", BUILDERS)
def test_publish_covers_oxidns_downloads(tmp_path, modname, func):
    mod = importlib.import_module(modname)
    getattr(mod, func)(_published_rules(), str(tmp_path))

    # 1. 线上额外订阅的集合必须发布 (上次事故的 4 个中的 3 个)
    for name in providers.OXIDNS_EXTRA_RULESETS:
        sub = "geoip" if name.startswith("geoip-") else "geosite"
        assert (tmp_path / sub / f"{name}.txt").exists(), f"线上订阅但未发布: {name}"

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
