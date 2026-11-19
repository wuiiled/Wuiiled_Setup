# -*- coding: utf-8 -*-
"""geosite-fakeip-filter 核心逻辑回归测试。"""
from core.cleaner import compact_regexes, normalize_fakeip_line
from core.manager import assemble_fakeip_fields


def test_normalize_fakeip_line():
    for junk in ("dns:", "fake-ip-filter:", "payload:", "Mijia Cloud", "dns://8.8.8.8", ".", "*.", "+.", "+", "", "# c"):
        assert normalize_fakeip_line(junk) is None
    assert normalize_fakeip_line("  '*.lan'  ") == "+.lan"
    assert normalize_fakeip_line(".local") == "+.local"
    assert normalize_fakeip_line("stun.example.com # inline") == "stun.example.com"
    assert normalize_fakeip_line("time.apple.com.") == "time.apple.com"
    assert normalize_fakeip_line("*.stun.*.*") == "*.stun.*.*"
    assert normalize_fakeip_line("+.stun.*.*") == "+.stun.*.*"


def test_assemble_fakeip_fields():
    domains, suffixes, regexes = assemble_fakeip_fields([
        "*", "+.lan", "+.msftconnecttest.com", "+.stun.*.*",
        "time.*.apple.com", "stun1.l.google.com",
    ])
    assert domains == {"stun1.l.google.com"}
    assert suffixes == {".lan", "msftconnecttest.com"}
    assert regexes == {
        r"^[^.]+$",
        r"^(?:.+\.)?stun\.[^.]+\.[^.]+$",
        r"^time\.[^.]+\.apple\.com$",
    }


def test_compact_regexes_preserves_single_label_and_non_greedy():
    assert compact_regexes({r"^[^.]+$"}) == [r"^[^.]+$"]
    assert compact_regexes({r"^.*$"}) == []
    assert compact_regexes({r"^(?:.+\.)?stun\.[^.]+\.[^.]+$"}) == [r"^(?:.+\.)?stun\.[^.]+\.[^.]+$"]
    assert compact_regexes({r"^time\.[^.]+\.com$", r"^time\.[^.]+\.gov$"}) == [r"^time\.[^.]+\.(com|gov)$"]
