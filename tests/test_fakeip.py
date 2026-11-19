# -*- coding: utf-8 -*-
"""geosite-fakeip-filter 重构回归测试 (2026-11-19)。

覆盖: normalize_fakeip_line 清洗面 (拦截 "Mijia Cloud" 类异形行) / 通配形态
统一 (*.x/.x → +.x) / sing-box 三字段装配 ([^.]+ 不跨点、^[^.]+$ 单标签豁免) /
compact_regexes 守卫与折叠行为 / 保留通配梯覆盖对账 (stunN 家族回归) /
addon 补充条目存在性守卫 / 双内核二进制编译 (e2e)。
"""
import os
import re
import shutil
import subprocess

import pytest

from core.cleaner import compact_regexes, normalize_fakeip_line
from core.manager import assemble_fakeip_fields

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ADDON_PATH = os.path.join(REPO_ROOT, "rules", "addons", "fake-ip-addon.txt")


# ---------- normalize_fakeip_line ----------

def test_normalize_line_cleanup():
    """YAML 键泛化过滤、异形行/退化行拦截、注释与引号剥离。"""
    # YAML 键 (skk 的 dns:→fake-ip-filter: 嵌套, 及假想的 payload:)
    for junk in ("dns:", "fake-ip-filter:", "payload:"):
        assert normalize_fakeip_line(junk) is None
    # 字符集白名单: 现行产物曾混入 "mijia cloud" (OpenClash 原文 L163)
    assert normalize_fakeip_line("Mijia Cloud") is None
    assert normalize_fakeip_line("foo bar") is None
    assert normalize_fakeip_line("dns://8.8.8.8") is None
    # 退化行
    for junk in (".", "*.", "+.", "+", "", "# comment"):
        assert normalize_fakeip_line(junk) is None
    # 引号/空白/行内注释/尾点
    assert normalize_fakeip_line("  '*.lan'  ") == "+.lan"
    assert normalize_fakeip_line("stun.example.com # inline") == "stun.example.com"
    assert normalize_fakeip_line("time.apple.com.") == "time.apple.com"


def test_normalize_wildcard_unification():
    """`*.x`/`.x` 统一为 `+.x`; 前缀后仍含 `*` 的保持 mihomo 原生语义。"""
    assert normalize_fakeip_line("*.lan") == "+.lan"
    assert normalize_fakeip_line(".local") == "+.local"
    assert normalize_fakeip_line("*.home.arpa") == "+.home.arpa"
    assert normalize_fakeip_line("*.stun.*.*") == "*.stun.*.*"
    assert normalize_fakeip_line("+.stun.*.*") == "+.stun.*.*"
    assert normalize_fakeip_line("localhost.*.weixin.qq.com") == "localhost.*.weixin.qq.com"
    assert normalize_fakeip_line("time.*.apple.com") == "time.*.apple.com"


# ---------- assemble_fakeip_fields (sing-box 三字段装配) ----------

def test_singbox_field_assembly():
    """`*`→单标签正则; 通配→`[^.]+` 不跨点; 后缀入库带点前缀约定。"""
    domains, suffixes, regexes = assemble_fakeip_fields([
        "*", "+.lan", "+.msftconnecttest.com", "+.stun.*.*",
        "time.*.apple.com", "stun.l.google.com",
    ])
    assert regexes == {
        r"^[^.]+$",
        r"^(?:.+\.)?stun\.[^.]+\.[^.]+$",
        r"^time\.[^.]+\.apple\.com$",
    }
    assert suffixes == {".lan", "msftconnecttest.com"}
    assert domains == {"stun.l.google.com"}


# ---------- compact_regexes 守卫与折叠 ----------

def test_compact_regexes_guard_and_folds():
    """`^[^.]+$` 不被守卫丢弃 (旧版 `^.*$` 被丢弃 → 双核不对称), `[^.]+` 形态不再触发跨点折叠。"""
    assert compact_regexes({r"^[^.]+$"}) == [r"^[^.]+$"]
    assert compact_regexes({r"^.*$"}) == []
    folded_in = compact_regexes({r"^(.*\.)?stun\..*\..*$"})
    assert folded_in == [r"^(.*\.)?stun\..*$"]  # 旧形态的跨点放大折叠仍在 (守卫语义)
    kept = compact_regexes({r"^(?:.+\.)?stun\.[^.]+\.[^.]+$"})
    assert kept == [r"^(?:.+\.)?stun\.[^.]+\.[^.]+$"]  # 新形态零失真
    assert compact_regexes({r"^time\.[^.]+\.com$", r"^time\.[^.]+\.gov$"}) == \
        [r"^time\.[^.]+\.(com|gov)$"]


# ---------- 通配梯覆盖对账 (stunN 家族回归) ----------

def test_wildcard_ladder_coverage():
    """`+.stun.*.*` 锚点是字面 `stun` 标签: 覆盖 stun.<1>.<1> 形态, 覆盖不到
    stunN 编号变体与 4 标签裸 stun 主机 —— 后者必须由 exact 条目兜底。"""
    _, _, regexes = assemble_fakeip_fields(["+.stun.*.*", "+.stun.*.*.*"])
    ladder = [re.compile(r) for r in regexes]
    covered = lambda d: any(r.match(d) for r in ladder)  # noqa: E731
    assert covered("stun.cloudflare.com")
    assert covered("stun.twilio.com")
    assert covered("a.stun.playstation.net")
    assert covered("stun.l.google.com")       # 4 标签被 +.stun.*.*.* 整体对齐覆盖
    assert not covered("stun1.l.google.com")  # 锚点 stun1 ≠ stun → 唯一缺口, addon exact 兜底 (本次重构 P1 回归点)


def test_addon_stun_family_guard():
    """addon 必须保留 stun1-4.l.google.com 与高通 GPS 辅助定位家族 (防再被误删)。"""
    with open(ADDON_PATH, encoding="utf-8") as f:
        entries = {normalize_fakeip_line(x) for x in f}
    entries.discard(None)
    for d in ("stun1.l.google.com", "stun2.l.google.com",
              "stun3.l.google.com", "stun4.l.google.com"):
        assert d in entries, f"addon 缺 {d} (WebRTC 主力 STUN 回归)"
    for p in ("+.qcomgeo2.com", "+.izatcloud.net", "+.xtracloud.net"):
        assert p in entries, f"addon 缺 {p} (高通 GPS 辅助定位)"
    domains, suffixes, _ = assemble_fakeip_fields(sorted(entries))
    assert "stun1.l.google.com" in domains
    assert {"qcomgeo2.com", "izatcloud.net", "xtracloud.net"} <= suffixes


# ---------- 双内核二进制编译 (e2e: 需构建产物 + 编译器) ----------

@pytest.mark.e2e
class TestBinaryCompile:

    @pytest.fixture(autouse=True)
    def _require_products(self):
        self.json_path = os.path.join(REPO_ROOT, "output", "singbox", "geosite", "geosite-fakeip-filter.json")
        self.txt_path = os.path.join(REPO_ROOT, "output", "mihomo", "geosite", "geosite-fakeip-filter.txt")
        if not (os.path.exists(self.json_path) and os.path.exists(self.txt_path)):
            pytest.skip("需要构建产物 output/")
        self.sb = shutil.which("sing-box")
        self.mh = shutil.which("mihomo")
        if not self.sb or not self.mh:
            pytest.skip("PATH 无 sing-box/mihomo 编译器")

    def test_singbox_srs_compile_and_semantics(self, tmp_path):
        srs = tmp_path / "fakeip.srs"
        subprocess.run([self.sb, "rule-set", "compile", self.json_path, "-o", str(srs)], check=True)
        assert srs.stat().st_size > 0
        import utils
        data = utils.decompile_srs(str(srs), str(tmp_path / "fakeip_decomp.json"))
        rule = data.get("rules", [{}])[0]
        for key in ("domain", "domain_suffix", "domain_regex"):
            if isinstance(rule.get(key), str):
                rule[key] = [rule[key]]
        regexes = set(rule.get("domain_regex") or [])
        assert r"^[^.]+$" in regexes                    # 单标签豁免存活
        assert r"^(.*\.)?stun\..*$" not in regexes      # 旧跨点过宽形态绝迹
        assert any("stun" in r and r"[^.]+" in r for r in regexes)
        assert "stun.l.google.com" in set(rule.get("domain") or [])
        assert "stun1.l.google.com" in set(rule.get("domain") or [])

    def test_mihomo_mrs_compile(self, tmp_path):
        mrs = tmp_path / "fakeip.mrs"
        subprocess.run([self.mh, "convert-ruleset", "domain", "text", self.txt_path, str(mrs)], check=True)
        assert mrs.stat().st_size > 0
