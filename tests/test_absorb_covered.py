# -*- coding: utf-8 -*-
"""absorb_covered_domains: 覆盖吸收纯函数测试。"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from core.cleaner import absorb_covered_domains


def test_suffix_absorbed_by_ancestor():
    dom, suf, removed = absorb_covered_domains(set(), {"example.com", "sub.example.com"})
    assert suf == {"example.com"}
    assert dom == set()
    assert removed == 1


def test_suffix_chain_absorbed_by_tld():
    dom, suf, removed = absorb_covered_domains(set(), {"cn", "a.b.cn", "b.cn", "example.cn"})
    # cn 覆盖 a.b.cn / b.cn / example.cn 全部
    assert suf == {"cn"}
    assert removed == 3


def test_bare_form_preferred_over_dotted():
    dom, suf, removed = absorb_covered_domains(set(), {".anquan", "anquan"})
    # 同标签: 裸形式 (覆盖自身+子域) 保留, 前导点形式吸收
    assert suf == {"anquan"}
    assert removed == 1


def test_dotted_alone_is_kept():
    dom, suf, removed = absorb_covered_domains(set(), {".anquan"})
    assert suf == {".anquan"}
    assert removed == 0


def test_domain_covered_by_self_suffix():
    dom, suf, removed = absorb_covered_domains({"example.com"}, {"example.com"})
    assert dom == set()
    assert suf == {"example.com"}
    assert removed == 1


def test_domain_covered_by_ancestor_suffix():
    dom, suf, removed = absorb_covered_domains({"www.example.com", "other.com"}, {"example.com"})
    assert dom == {"other.com"}
    assert suf == {"example.com"}
    assert removed == 1


def test_disjoint_sets_untouched():
    dom = {"a.com", "www.a.com"}
    suf = {"b.com"}
    dom2, suf2, removed = absorb_covered_domains(dom, suf)
    assert dom2 == dom
    assert suf2 == suf
    assert removed == 0


def test_case_and_dot_normalization():
    # 大小写/前后缀点号差异按宽松规范化比较, 保留条目维持原字面
    dom, suf, removed = absorb_covered_domains({"WWW.Example.com"}, {"example.com.", "Example.com"})
    # 两个同标签后缀: 后者覆盖前者, 去重后保留一个
    assert len(suf) == 1
    assert removed >= 1
    assert dom == set()


def test_regex_keyword_unaffected_by_design():
    # 函数只接收 domains/suffixes, keyword/regex 不传入即不受影响
    dom, suf, removed = absorb_covered_domains(set(), {"example.com"})
    assert suf == {"example.com"}
