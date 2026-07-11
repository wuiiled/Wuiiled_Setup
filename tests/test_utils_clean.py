#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for utils.clean_mihomo_domain_line, clean_ip_line, is_valid_ip_or_cidr"""
import pytest
from utils import clean_mihomo_domain_line, clean_ip_line, is_valid_ip_or_cidr


class TestCleanMihomoDomainLine:
    """Test clean_mihomo_domain_line: parse Clash/Mihomo rule lines to domain format."""

    def test_domain_suffix(self):
        assert clean_mihomo_domain_line("DOMAIN-SUFFIX,example.com") == "+.example.com"

    def test_domain_suffix_lowercase(self):
        assert clean_mihomo_domain_line("domain-suffix,example.com") == "+.example.com"

    def test_domain(self):
        assert clean_mihomo_domain_line("DOMAIN,example.com") == "example.com"

    def test_ip_cidr_filtered(self):
        assert clean_mihomo_domain_line("IP-CIDR,192.168.0.0/16") is None

    def test_process_name_filtered(self):
        assert clean_mihomo_domain_line("PROCESS-NAME,chrome") is None

    def test_comment(self):
        assert clean_mihomo_domain_line("# comment") is None

    def test_plain_domain(self):
        assert clean_mihomo_domain_line("example.com") == "example.com"

    def test_empty(self):
        assert clean_mihomo_domain_line("") is None

    def test_inline_comment_stripped(self):
        assert clean_mihomo_domain_line("example.com # comment") == "example.com"

    def test_plain_ip_filtered(self):
        assert clean_mihomo_domain_line("192.168.1.1") is None


class TestCleanIpLine:
    """Test clean_ip_line: extract IP/CIDR from rule lines."""

    def test_plain_ip(self):
        assert clean_ip_line("192.168.1.1") == "192.168.1.1"

    def test_cidr(self):
        assert clean_ip_line("10.0.0.0/8") == "10.0.0.0/8"

    def test_ip_cidr_prefix(self):
        assert clean_ip_line("IP-CIDR,10.0.0.0/8,no-resolve") == "10.0.0.0/8"

    def test_ipv6(self):
        assert clean_ip_line("::1/128") == "::1/128"

    def test_domain_filtered(self):
        assert clean_ip_line("example.com") is None

    def test_comment(self):
        assert clean_ip_line("# comment") is None

    def test_empty(self):
        assert clean_ip_line("") is None

    def test_ip_cidr6_prefix(self):
        assert clean_ip_line("IP-CIDR6,fd00::/8") == "fd00::/8"


class TestIsValidIpOrCidr:
    """Test is_valid_ip_or_cidr."""

    def test_valid_ip(self):
        assert is_valid_ip_or_cidr("192.168.1.1") is True

    def test_valid_cidr(self):
        assert is_valid_ip_or_cidr("10.0.0.0/8") is True

    def test_valid_ipv6(self):
        assert is_valid_ip_or_cidr("fd00::1") is True

    def test_invalid_domain(self):
        assert is_valid_ip_or_cidr("example.com") is False

    def test_with_prefix(self):
        assert is_valid_ip_or_cidr("IP-CIDR,10.0.0.0/8") is True

    def test_empty(self):
        assert is_valid_ip_or_cidr("") is False
