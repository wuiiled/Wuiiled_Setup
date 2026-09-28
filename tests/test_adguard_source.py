# -*- coding: utf-8 -*-
"""统一 AdGuard 源文件契约测试: geosite-ad 的 AdGuard 源由 utils 单一渲染,
adg 分支 (直接发布) 与 singbox 分支 (转 adguard 型 srs) 必须消费字节相同的
同一份产物 —— 渲染实现只允许存在一份, 两分支不得各自为政。"""
import importlib
import os

import utils
from core.models import RuleSet


def _seed_blackwhite():
    ads = os.path.join(utils.get_work_dir(), "ads")
    os.makedirs(ads, exist_ok=True)
    with open(os.path.join(ads, "blocklist_b.txt"), "w", encoding="utf-8") as f:
        f.write("doubleclick.net\nads.example.com\n")
    with open(os.path.join(ads, "whitelist_b.txt"), "w", encoding="utf-8") as f:
        f.write("fls.doubleclick.net\n")
    return utils.render_adguard_geosite_ad()


def test_render_semantics():
    src = _seed_blackwhite()
    assert open(src, encoding="utf-8").read() == \
        "||doubleclick.net^\n||ads.example.com^\n@@||fls.doubleclick.net^\n"


def test_adg_branch_consumes_canonical_source(tmp_path):
    src = _seed_blackwhite()
    build_adg = importlib.import_module("build_adg")
    build_adg.build_adg_rules(
        {"geosite-httpdns": RuleSet(name="geosite-httpdns", category="geosite")},
        str(tmp_path / "adg"),
    )
    assert (tmp_path / "adg" / "geosite-ad.txt").read_text(encoding="utf-8") == \
        open(src, encoding="utf-8").read()


def test_singbox_branch_consumes_canonical_source(tmp_path):
    src = _seed_blackwhite()
    build_singbox = importlib.import_module("build_singbox")
    gdir = tmp_path / "singbox" / "geosite"
    gdir.mkdir(parents=True)
    # has_sb=False: 不触发编译器 (CI test 环境无 sing-box)
    build_singbox._build_adguard_srs("geosite-ad", str(gdir), has_sb=False)
    assert (gdir / "geosite-ad.txt").read_text(encoding="utf-8") == \
        open(src, encoding="utf-8").read()
    assert not (gdir / "geosite-ad.srs").exists()  # 无编译器时不产出 srs
