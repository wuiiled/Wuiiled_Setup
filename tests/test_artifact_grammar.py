# -*- coding: utf-8 -*-
"""产物语法门禁测试: 用合成最小 IR 跑全部五个导出器, 再以
scripts/lint_artifacts.py 的同一套校验逐文件断言行文法。

不需要网络与编译器 (WUIILED_ALLOW_MISSING_COMPILERS=1, conftest 已设)。
"""
import importlib

import providers
from conftest import seed_blackwhite_files
from core.models import RuleSet
from lint_artifacts import lint

BUILDERS = [
    ("build_singbox", "build_singbox_rules", "singbox"),
    ("build_mihomo", "build_mihomo_rules", "mihomo"),
    ("build_smartdns", "build_smartdns_rules", "smartdns"),
    ("build_mosdns", "build_mosdns_rules", "mosdns-x"),
    ("build_adg", "build_adg_rules", "adg"),
]


def _seed_blackwhite():
    seed_blackwhite_files()


def _synthetic_rules():
    """覆盖 OxiDNS 白名单 + adg 三集 + 带 keyword/regex 的 cn 的最小 IR。"""
    names = (set(providers.OXIDNS_RULESETS)
             | providers.OXIDNS_EXTRA_RULESETS)
    rules = {}
    for name in names:
        if name.startswith("geoip-"):
            rules[name] = RuleSet(name=name, category="geoip",
                                  ip_cidrs={"203.0.113.0/24", "2001:db8::/32"})
        else:
            rules[name] = RuleSet(name=name, category="geosite",
                                  domain_suffixes={"example.org"})
    rules["geosite-cn"] = RuleSet(
        name="geosite-cn", category="geosite",
        domains={"exact.example"},
        domain_suffixes={"suffix.example", ".single"},
        domain_keywords={"somebrand"},
        domain_regexes={r"^ad[0-9]+\.example$"},
    )
    rules["geosite-httpdns"] = RuleSet(name="geosite-httpdns", category="geosite",
                                       domain_suffixes={"httpdns.example"})
    rules["geosite-pcdn"] = RuleSet(name="geosite-pcdn", category="geosite",
                                    domain_suffixes={"pcdn.example"})
    rules["geosite-fakeip-filter"] = RuleSet(
        name="geosite-fakeip-filter", category="geosite",
        raw_lines=["+.mijia.example", "mijia cloud"],
    )
    return rules


def test_all_branch_outputs_pass_grammar_gate(tmp_path):
    _seed_blackwhite()
    rules = _synthetic_rules()
    for modname, func, branch in BUILDERS:
        mod = importlib.import_module(modname)
        # 导出器 output_dir 的末段即分支名 (output/singbox|...|adg), 与 lint 布局对齐
        getattr(mod, func)(dict(rules), str(tmp_path / branch))

    issues = lint(str(tmp_path))
    assert not issues, "\n".join(issues[:20])


def test_gate_rejects_legacy_smartdns_prefix(tmp_path):
    """文法门禁必须能拦住 `-.` 类死条目 (2026-09-26 事故的回归测试)。"""
    _seed_blackwhite()
    rules = _synthetic_rules()
    build_smartdns = importlib.import_module("build_smartdns")
    build_smartdns.build_smartdns_rules(dict(rules), str(tmp_path / "smartdns"))
    out = tmp_path / "smartdns" / "geosite" / "geosite-cn.txt"
    good = out.read_text(encoding="utf-8")
    out.write_text(good + "-.dead.example\n", encoding="utf-8")
    issues = lint(str(tmp_path))
    assert any("smartdns" in x and ("非法行" in x or "残留 smartdns 前缀" in x) for x in issues), issues
