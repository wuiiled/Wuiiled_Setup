#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for build_smartdns.convert_txt_to_smartdns"""
import pytest
import tempfile
import os
from build_smartdns import convert_txt_to_smartdns


class TestConvertTxtToSmartdns:
    """Test convert_txt_to_smartdns: Mihomo txt → SmartDNS domain-set/ip-set."""

    def _run(self, lines, is_ip=False):
        """Helper: convert lines, return (success, output_lines)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tf:
            tf.write('\n'.join(lines) + '\n')
            src_path = tf.name
        dst_path = src_path + '.out'
        result = convert_txt_to_smartdns(src_path, dst_path, is_ip)
        output_lines = []
        if os.path.exists(dst_path):
            with open(dst_path, 'r', encoding='utf-8') as f:
                output_lines = [l.strip() for l in f if l.strip()]
            os.unlink(dst_path)
        os.unlink(src_path)
        return result, output_lines

    def test_domain_to_smartdns(self):
        """Plain domain should get -.- prefix for exact match."""
        result, lines = self._run(["example.com"], is_ip=False)
        assert result is True
        assert "-.example.com" in lines

    def test_wildcard_domain(self):
        """+.domain should have prefix stripped (suffix match)."""
        result, lines = self._run(["+.example.com"], is_ip=False)
        assert result is True
        assert "example.com" in lines

    def test_dot_prefix_domain(self):
        """.domain should have prefix stripped."""
        result, lines = self._run([".example.com"], is_ip=False)
        assert result is True
        assert "example.com" in lines

    def test_ip_mode(self):
        """IP/CIDR in IP mode should be kept as-is."""
        result, lines = self._run(["10.0.0.0/8"], is_ip=True)
        assert result is True
        assert "10.0.0.0/8" in lines

    def test_domain_in_ip_mode_filtered(self):
        """Domain in IP mode should be filtered out → empty → False."""
        result, lines = self._run(["example.com"], is_ip=True)
        assert result is False

    def test_ip_in_domain_mode_filtered(self):
        """IP in domain mode should be filtered out → empty → False."""
        result, lines = self._run(["10.0.0.0/8"], is_ip=False)
        assert result is False

    def test_comment_preserved(self):
        """Comment lines should be preserved in output."""
        result, lines = self._run(["# comment", "example.com"], is_ip=False)
        assert result is True
        assert "# comment" in lines

    def test_inline_comment_stripped(self):
        """Inline comments should be stripped from rule, kept as suffix."""
        result, lines = self._run(["example.com # note"], is_ip=False)
        assert result is True
        # The converted line should contain the domain
        assert any("example.com" in l for l in lines)
