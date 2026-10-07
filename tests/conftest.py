#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest configuration: add scripts/ to sys.path for imports."""
import os
import sys

# 测试环境无 mihomo/sing-box 编译器: 允许 check_tool 返回 False 而非 sys.exit
os.environ.setdefault("WUIILED_ALLOW_MISSING_COMPILERS", "1")

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))


def seed_blackwhite_files(blocklist="doubleclick.net\nads.example.com\n",
                          whitelist="fls.doubleclick.net\n"):
    """在共享 work_dir 写入 manager.load_ads_rules 产出的黑加白中间产物样例,
    供 AdGuard 源渲染 / 黑加白 IR 注入类测试使用。"""
    import utils
    ads = os.path.join(utils.get_work_dir(), "ads")
    os.makedirs(ads, exist_ok=True)
    with open(os.path.join(ads, "blocklist_b.txt"), "w", encoding="utf-8") as f:
        f.write(blocklist)
    with open(os.path.join(ads, "whitelist_b.txt"), "w", encoding="utf-8") as f:
        f.write(whitelist)
