#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for build_singbox.convert_txt_to_json"""
import pytest
import json
import tempfile
import os
from build_singbox import convert_txt_to_json


class TestConvertTxtToJson:
    """Test convert_txt_to_json: Mihomo txt → sing-box JSON rule-set."""

    def _run(self, lines, filename="test_rules.txt"):
        """Helper: convert lines to JSON, return (success, parsed_json)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tf:
            tf.write('\n'.join(lines) + '\n')
            txt_path = tf.name
        json_path = txt_path.replace('.txt', '.json')
        result = convert_txt_to_json(txt_path, json_path)
        data = {}
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            os.unlink(json_path)
        os.unlink(txt_path)
        return result, data

    def test_plain_domain(self):
        result, data = self._run(["example.com"])
        assert result is True
        assert "example.com" in data["rules"][0]["domain"]

    def test_domain_suffix(self):
        result, data = self._run(["+.example.com"])
        assert result is True
        assert "example.com" in data["rules"][0]["domain_suffix"]

    def test_ip_cidr(self):
        result, data = self._run(["10.0.0.0/8"])
        assert result is True
        assert "10.0.0.0/8" in data["rules"][0]["ip_cidr"]

    def test_wildcard_to_suffix(self):
        result, data = self._run(["*.example.com"])
        assert result is True
        assert "example.com" in data["rules"][0]["domain_suffix"]

    def test_version_is_5(self):
        result, data = self._run(["example.com"])
        assert data["version"] == 5

    def test_empty_input(self):
        result, data = self._run(["# only comment"])
        assert result is False

    def test_comment_skipped(self):
        result, data = self._run(["# comment", "example.com"])
        assert result is True
        assert len(data["rules"][0]["domain"]) == 1

    def test_dot_prefix_suffix(self):
        result, data = self._run([".example.com"])
        assert result is True
        assert "example.com" in data["rules"][0]["domain_suffix"]

    def test_ipv6_cidr(self):
        result, data = self._run(["fd00::/8"])
        assert result is True
        assert "fd00::/8" in data["rules"][0]["ip_cidr"]

    def test_multiple_domains_sorted(self):
        result, data = self._run(["zeta.com", "alpha.com"])
        assert result is True
        domains = data["rules"][0]["domain"]
        assert domains == sorted(domains)

    def test_inline_comment_stripped(self):
        result, data = self._run(["example.com # comment"])
        assert result is True
        assert "example.com" in data["rules"][0]["domain"]
