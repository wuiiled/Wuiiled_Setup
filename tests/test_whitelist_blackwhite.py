# -*- coding: utf-8 -*-
"""Tests for 黑加白模式 (blocklist B + whitelist B) pure functions.

Locked semantics (validated against the three canonical examples):
- 黑名单B: remove upstream-block entries sharing an exact name or ancestor with the
  upstream allowlist (direction-1 only), then absorb redundant subdomains under a kept parent.
- 白名单B: upstream-allow entries that would be hit by 黑名单B (exact name or ancestor in
  blocklist B) AND do NOT themselves appear in the upstream blocklist.
"""
from core.cleaner import build_blocklist_b, build_whitelist_b


class TestBlocklistB:
    def test_example1(self):
        allow = {"ads.aaa.com", "publishers.aaa.com"}
        block = {"aaa.com", "ocdn.aaa.com", "ads.aaa.com"}
        assert build_blocklist_b(block, allow) == {"aaa.com"}

    def test_example2_allow_contains_parent(self):
        allow = {"aaa.com", "ads.aaa.com", "publishers.aaa.com"}
        block = {"aaa.com", "ocdn.aaa.com", "ads.aaa.com"}
        assert build_blocklist_b(block, allow) == set()

    def test_example3_upper_parent_kept(self):
        allow = {"ads.a.a.com", "publishers.a.a.com", "b.a.com"}
        block = {"a.a.com", "ocdn.a.a.com", "ads.a.a.com", "a.com"}
        assert build_blocklist_b(block, allow) == {"a.com"}


class TestWhitelistB:
    def test_example1(self):
        allow = {"ads.aaa.com", "publishers.aaa.com"}
        block = {"aaa.com", "ocdn.aaa.com", "ads.aaa.com"}
        b = build_blocklist_b(block, allow)
        # ads.aaa.com appears in upstream block -> excluded; publishers.aaa.com kept
        assert build_whitelist_b(allow, block, b) == {"publishers.aaa.com"}

    def test_example2_empty_blocklist_b(self):
        allow = {"aaa.com", "ads.aaa.com", "publishers.aaa.com"}
        block = {"aaa.com", "ocdn.aaa.com", "ads.aaa.com"}
        b = build_blocklist_b(block, allow)
        assert build_whitelist_b(allow, block, b) == set()

    def test_example3(self):
        allow = {"ads.a.a.com", "publishers.a.a.com", "b.a.com"}
        block = {"a.a.com", "ocdn.a.a.com", "ads.a.a.com", "a.com"}
        b = build_blocklist_b(block, allow)
        # a.a.com & ads.a.a.com are in upstream block -> excluded
        # publishers.a.a.com & b.a.com hit by a.com (blocklist B) -> kept
        assert build_whitelist_b(allow, block, b) == {"publishers.a.a.com", "b.a.com"}
