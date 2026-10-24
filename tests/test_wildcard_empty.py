# -*- coding: utf-8 -*-
"""
WILDCARD 承载纠正与空集跳过导出的测试:
- glob (mihomo classical DOMAIN-WILDCARD 语义: `*` 跨点、`?` 单字符) -> srs domain_regex 无损转换
- `*.字面域名` 形态 -> mihomo domain 行为 `.字面域名` 行 (glob 跨点 `*` = 任意深度子域, 不含自身)
- 含 ? / 中段 * 的形态对 mihomo 语义不等价 -> 不输出, 由 build_mihomo 打印统计
- SKK 加载器捕获 DOMAIN-WILDCARD 行 (原先直接跳过)
- 空集合跳过 singbox/mihomo 导出 (避免 rules:[{}] 全匹配与空 mrs)
"""
from unittest.mock import patch

import pytest

import build_singbox
import build_mihomo
from core.cleaner import glob_wildcard_to_regex, wildcard_prefix_to_mihomo
from core.models import RuleSet


def test_glob_wildcard_to_regex_semantics():
    # `*` 跨任意字符(含点), `?` 恰一个字符, 其余字面转义, 全串锚定
    assert glob_wildcard_to_regex("*.example.com") == r"^.*\.example\.com$"
    assert glob_wildcard_to_regex("qhimgs?.com") == r"^qhimgs.\.com$"
    assert glob_wildcard_to_regex("a.*.b") == r"^a\..*\.b$"
    assert glob_wildcard_to_regex("") is None
    assert glob_wildcard_to_regex("*") is None

    import re
    assert re.search(glob_wildcard_to_regex("qhimgs?.com"), "qhimgs1.com")
    assert not re.search(glob_wildcard_to_regex("qhimgs?.com"), "qhimgs12.com")
    assert not re.search(glob_wildcard_to_regex("qhimgs?.com"), "qhimgs1.net")
    # glob `*` 跨点: a.b.example.com 命中 *.example.com
    assert re.search(glob_wildcard_to_regex("*.example.com"), "a.b.example.com")
    # 不含自身 (需至少一个点前的内容)
    assert not re.search(glob_wildcard_to_regex("*.example.com"), "example.com")


def test_wildcard_prefix_to_mihomo_only_label_aligned():
    # `*.字面域名` -> `.字面域名` (glob 跨点 `*` = 任意深度子域且不含自身, 与 domain 行为 `.x` 严格等价)
    assert wildcard_prefix_to_mihomo("*.example.com") == ".example.com"
    # 含 ? / 中段 * / 裸 * 语义不等价 -> None
    assert wildcard_prefix_to_mihomo("qhimgs?.com") is None
    assert wildcard_prefix_to_mihomo("a.*.b") is None
    assert wildcard_prefix_to_mihomo("*.a.*.b") is None


def test_skk_loader_captures_domain_wildcard():
    from core.manager import load_skk_rules
    sample = (
        "# header\n"
        "DOMAIN-SUFFIX,qq.com\n"
        "DOMAIN-WILDCARD,qhimgs?.com\n"
        "DOMAIN,7h15.ru1353t.1s.m4d3.by.5ukk4w.skk.moe\n"
    )
    with patch("core.manager.fetch_text_cached", return_value=sample):
        rules = load_skk_rules()
    dom = rules["geosite-domestic"]
    assert dom.domain_wildcards == {"qhimgs?.com"}
    assert "qq.com" in dom.domain_suffixes
    assert not any("skk.moe" in d for d in dom.domains | dom.domain_suffixes)


def test_empty_ruleset_skipped_on_export(tmp_path):
    rules = {
        "geosite-empty-test": RuleSet(name="geosite-empty-test", category="geosite"),
        "geosite-real-test": RuleSet(
            name="geosite-real-test", category="geosite", domain_suffixes={"ok.example"}),
    }
    sb_dir = tmp_path / "singbox"
    mh_dir = tmp_path / "mihomo"
    build_singbox.build_singbox_rules(dict(rules), output_dir=str(sb_dir))
    build_mihomo.build_mihomo_rules(dict(rules), output_dir=str(mh_dir))

    assert (sb_dir / "geosite" / "geosite-real-test.json").exists()
    assert not (sb_dir / "geosite" / "geosite-empty-test.json").exists()
    assert (mh_dir / "geosite" / "geosite-real-test.txt").exists()
    assert not (mh_dir / "geosite" / "geosite-empty-test.txt").exists()
    # 空集也不会再产出 rules:[{}] 的 srs 源 JSON
    import json
    d = json.loads((sb_dir / "geosite" / "geosite-real-test.json").read_text(encoding="utf-8"))
    assert d["rules"] and all(r for r in d["rules"])


def test_raw_lines_set_not_skipped(tmp_path):
    # raw_lines 集合 (如 reject-drop) total_count 可能为 0, 但 raw_lines 有内容, 不应跳过
    rs = RuleSet(name="geosite-rawlines-test", category="geosite", raw_lines=["+.keep.example"])
    sb_dir = tmp_path / "sb"
    build_singbox.build_singbox_rules({"geosite-rawlines-test": rs}, output_dir=str(sb_dir))
    # raw_srs 为空且桶为空 -> total_count==0: 此类集合仅靠 raw_lines 表达, 仍跳过 srs
    # (json 由 to_singbox_dict 生成, 无法承载 raw_lines; 与旧行为一致)
    assert not (sb_dir / "geosite" / "geosite-rawlines-test.json").exists()
    mh_dir = tmp_path / "mh"
    build_mihomo.build_mihomo_rules({"geosite-rawlines-test": rs}, output_dir=str(mh_dir))
    assert (mh_dir / "geosite" / "geosite-rawlines-test.txt").exists()
