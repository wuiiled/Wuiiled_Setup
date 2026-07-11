#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for utils.optimize_smart_self"""
import pytest
import tempfile
import os
from utils import optimize_smart_self


class TestOptimizeSmartSelf:
    """Test optimize_smart_self: prefix-tree deduplication."""

    def _run(self, lines):
        """Helper: run optimize_smart_self on given lines, return result lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as inf:
            inf.write('\n'.join(lines) + '\n')
            in_path = inf.name
        out_path = in_path + '.out'
        optimize_smart_self(in_path, out_path)
        with open(out_path, 'r', encoding='utf-8') as f:
            result = [l.strip() for l in f if l.strip()]
        os.unlink(in_path)
        if os.path.exists(out_path):
            os.unlink(out_path)
        return result

    def test_wildcard_covers_subdomain(self):
        """Wildcard parent domain should cover all subdomains."""
        result = self._run(["+.example.com", "a.example.com", "b.example.com"])
        assert result == ["+.example.com"]

    def test_exact_does_not_cover(self):
        """Exact domain should not cover its subdomains."""
        result = self._run(["example.com", "a.example.com"])
        assert "example.com" in result
        assert "a.example.com" in result

    def test_empty_file(self):
        """Empty file should produce empty output."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as inf:
            inf.write('')
            in_path = inf.name
        out_path = in_path + '.out'
        optimize_smart_self(in_path, out_path)
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) == 0
        os.unlink(in_path)
        os.unlink(out_path)

    def test_comments_skipped(self):
        """Comment lines should be skipped."""
        result = self._run(["# comment", "+.example.com"])
        assert result == ["+.example.com"]

    def test_dot_prefix_wildcard(self):
        """.prefix should also be treated as wildcard."""
        result = self._run([".example.com", "a.example.com"])
        assert ".example.com" in result
        assert "a.example.com" not in result

    def test_multiple_wildcards(self):
        """Multiple unrelated wildcards should all be kept."""
        result = self._run(["+.example.com", "+.test.org"])
        assert "+.example.com" in result
        assert "+.test.org" in result

    def test_blank_lines_skipped(self):
        """Blank lines should be skipped."""
        result = self._run(["", "+.example.com", "  "])
        assert result == ["+.example.com"]

    def test_all_comment_lines(self):
        """All-comment input should produce empty output (0 bytes, not 1 byte)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as inf:
            inf.write('# comment1\n# comment2\n')
            in_path = inf.name
        out_path = in_path + '.out'
        optimize_smart_self(in_path, out_path)
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) == 0
        os.unlink(in_path)
        os.unlink(out_path)
