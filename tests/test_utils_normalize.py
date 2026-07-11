#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for utils.normalize_domain_line"""
import pytest
from utils import normalize_domain_line


class TestNormalizeDomainLine:
    """Test normalize_domain_line: converts various rule formats to plain domain."""

    def test_plain_domain(self):
        assert normalize_domain_line("example.com") == "example.com"

    def test_dollar_comment(self):
        assert normalize_domain_line("example.com$important") == "example.com"

    def test_hash_comment(self):
        assert normalize_domain_line("example.com#comment") == "example.com"

    def test_zero_prefix(self):
        assert normalize_domain_line("0.0.0.0 example.com") == "example.com"

    def test_localhost_prefix(self):
        assert normalize_domain_line("127.0.0.1 example.com") == "example.com"

    def test_adguard_pipe(self):
        assert normalize_domain_line("||example.com^") == "example.com"

    def test_exception_rule(self):
        assert normalize_domain_line("@@||example.com^") == "example.com"

    def test_bang_comment(self):
        assert normalize_domain_line("! comment") is None

    def test_domain_suffix(self):
        assert normalize_domain_line("domain-suffix,example.com") == "example.com"

    def test_domain_prefix(self):
        assert normalize_domain_line("domain,example.com") == "example.com"

    def test_domain_keyword_no_dot_filtered(self):
        """domain-keyword with non-domain value (no dot) should be filtered out."""
        assert normalize_domain_line("domain-keyword,example") is None

    def test_domain_keyword_with_dot(self):
        """domain-keyword with domain value should pass."""
        assert normalize_domain_line("domain-keyword,example.com") == "example.com"

    def test_plus_dot_prefix(self):
        assert normalize_domain_line("+.example.com") == "example.com"

    def test_dot_prefix(self):
        assert normalize_domain_line(".example.com") == "example.com"

    def test_ip_address(self):
        assert normalize_domain_line("192.168.1.1") is None

    def test_wildcard(self):
        assert normalize_domain_line("*.example.com") is None

    def test_no_dot(self):
        assert normalize_domain_line("localhost") is None

    def test_slash(self):
        assert normalize_domain_line("example.com/path") is None

    def test_empty(self):
        assert normalize_domain_line("") is None

    def test_trailing_dot(self):
        assert normalize_domain_line("example.com.") == "example.com"

    def test_comma_separated_takes_first(self):
        assert normalize_domain_line("example.com,extra") == "example.com"
