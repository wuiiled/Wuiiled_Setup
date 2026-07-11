#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for utils.apply_advanced_whitelist_filter"""
import pytest
import tempfile
import os
from utils import apply_advanced_whitelist_filter


class TestApplyAdvancedWhitelistFilter:
    """Test apply_advanced_whitelist_filter: whitelist-based false-positive prevention."""

    def _run(self, block_lines, allow_lines):
        """Helper: run filter with given block and allow lines, return result lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as bf:
            bf.write('\n'.join(block_lines) + '\n')
            block_path = bf.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as af:
            af.write('\n'.join(allow_lines) + '\n')
            allow_path = af.name
        out_path = block_path + '.out'
        apply_advanced_whitelist_filter(block_path, allow_path, out_path)
        with open(out_path, 'r', encoding='utf-8') as f:
            result = [l.strip() for l in f if l.strip()]
        for p in [block_path, allow_path, out_path]:
            if os.path.exists(p):
                os.unlink(p)
        return result

    def test_exact_whitelist(self):
        """Domain in whitelist should be removed from block list."""
        result = self._run(["ads.com", "keep.com"], ["ads.com"])
        assert "keep.com" in result
        assert "ads.com" not in result

    def test_parent_whitelist(self):
        """Parent domain in whitelist should remove subdomain from block list."""
        result = self._run(["a.google.com", "keep.com"], ["google.com"])
        assert "a.google.com" not in result
        assert "keep.com" in result

    def test_option_a_child_protects_parent(self):
        """Option A: if whitelist has a child domain, parent domain in block list should be released."""
        result = self._run(["example.com"], ["sub.example.com"])
        assert "example.com" not in result

    def test_empty_whitelist(self):
        """Empty whitelist should keep all block domains."""
        result = self._run(["ads.com"], [])
        assert "ads.com" in result

    def test_wildcard_allow(self):
        """Wildcard allow entry should match subdomains."""
        result = self._run(["a.example.com", "keep.org"], ["+.example.com"])
        assert "a.example.com" not in result
        assert "keep.org" in result

    def test_comment_lines_skipped(self):
        """Comment lines in block list should be skipped."""
        result = self._run(["# comment", "ads.com"], [])
        assert "ads.com" in result
        assert len(result) == 1

    def test_all_blocks_whitelisted(self):
        """When all blocks are whitelisted, output should be 0 bytes (not '\\n')."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as bf:
            bf.write('ads.com\n')
            block_path = bf.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as af:
            af.write('ads.com\n')
            allow_path = af.name
        out_path = block_path + '.out'
        apply_advanced_whitelist_filter(block_path, allow_path, out_path)
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) == 0
        for p in [block_path, allow_path, out_path]:
            if os.path.exists(p):
                os.unlink(p)
