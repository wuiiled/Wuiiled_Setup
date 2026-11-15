# -*- coding: utf-8 -*-
"""白名单双档语义测试: bot 产物 exact 档只精确放行, 后缀档保持历史语义。"""
import pytest

from core.cleaner import build_blocklist_b, build_whitelist_b
from utils import apply_advanced_whitelist_filter


def _write(tmp_path, name, lines):
    p = tmp_path / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


def test_exact_tier_does_not_collateralize(tmp_path):
    """exact 档裸域只救自身规则; 后缀档保持双向连坐(历史语义不变)。"""
    block = _write(tmp_path, "block.txt", [
        "tanx.com",            # exact 档裸域自身 -> 被救
        "a.tanx.com",          # 子域 -> 不被 exact 档救(重新拦截)
        "ads.fwmrm.net",       # 后缀档裸域的子域 -> 被祖先救
        "cloudfront.net",      # 后缀档裸域自身 -> 被救
    ])
    suffix = _write(tmp_path, "allow.txt", ["cloudfront.net"])
    exact = _write(tmp_path, "exact.txt", ["tanx.com"])
    out = str(tmp_path / "final.txt")

    apply_advanced_whitelist_filter(block, suffix, out, exact_in=exact)
    kept = open(out, encoding="utf-8").read().split()
    assert sorted(kept) == ["a.tanx.com", "ads.fwmrm.net"]

    # 不传 exact 档时行为与旧签名逐字节一致(向后兼容)
    out_old = str(tmp_path / "final_old.txt")
    apply_advanced_whitelist_filter(block, suffix, out_old)
    kept_old = open(out_old, encoding="utf-8").read().split()
    assert sorted(kept_old) == ["a.tanx.com", "ads.fwmrm.net", "tanx.com"]


def test_exact_tier_rescues_self_only(tmp_path):
    """exact 档深条目只救等值规则, 不连坐其子域(与后缀档的本质区别)。"""
    block = _write(tmp_path, "block.txt", ["ad.tanx.com", "x.ad.tanx.com"])
    suffix = _write(tmp_path, "allow.txt", [])
    exact = _write(tmp_path, "exact.txt", ["ad.tanx.com"])
    out = str(tmp_path / "final.txt")
    apply_advanced_whitelist_filter(block, suffix, out, exact_in=exact)
    # 自身被救; 子域规则保留(exact ≠ suffix)
    assert open(out, encoding="utf-8").read().split() == ["x.ad.tanx.com"]


def test_blocklist_b_exact_param(tmp_path):
    """黑名单B: exact 档只救等值规则; 白名单B 两档并集共用同一谓词。"""
    block = {"tanx.com", "a.tanx.com", "dun.163.com"}
    bl_b = build_blocklist_b(block, {"ac.dun.163.com"}, {"tanx.com"})
    # tanx.com 自身被 exact 救 -> 出黑名单B; a.tanx.com 保留; dun.163.com
    # 因 allow 的子域条目 ac.dun.163.com 不构成祖先放行 -> 保留(黑加白 B 语义)
    assert bl_b == {"a.tanx.com", "dun.163.com"}

    wl_b = build_whitelist_b({"ac.dun.163.com"} | {"tanx.com"}, block, bl_b)
    # tanx.com 自身 ∈ 黑名单B? 否(被救) -> 不列; ac.dun.163.com 祖先 dun.163.com
    # ∈ 黑名单B -> 列入(需要前置豁免)
    assert wl_b == {"ac.dun.163.com"}
