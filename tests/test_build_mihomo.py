#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for build_mihomo.py rules parsing and domain/IP separation."""
import pytest
from utils import clean_mihomo_domain_line, clean_ip_line, is_valid_ip_or_cidr
import providers


class TestSKKRulesParsing:
    """Test parsing of SKK rules: domain rules vs IP rules."""

    def test_apple_services_domain_filters_ip(self):
        """Simulate skk apple_services lines including 17.0.0.0/8, ensure IP is rejected."""
        sample_lines = [
            "DOMAIN-SUFFIX,apple.com",
            "DOMAIN,apple.co",
            "IP-CIDR,17.0.0.0/8,no-resolve",
            "DOMAIN-SUFFIX,icloud.com",
            "17.0.0.0/8"
        ]
        dom_lines = []
        for line in sample_lines:
            cleaned_dom = clean_mihomo_domain_line(line)
            if cleaned_dom and cleaned_dom != '+.':
                dom_lines.append(cleaned_dom)

        assert dom_lines == ["+.apple.com", "apple.co", "+.icloud.com"]
        assert not any("17.0.0.0" in d for d in dom_lines)
        assert not any(is_valid_ip_or_cidr(d) for d in dom_lines)

    def test_apple_services_ip_cleans_no_resolve(self):
        """Simulate skk apple_services.conf, ensure no-resolve stripped and domains ignored."""
        sample_lines = [
            "DOMAIN,7h15.ru1353t.1s.m4d3.by.5ukk4w.skk.moe",
            "IP-CIDR,17.0.0.0/8,no-resolve",
            "IP-CIDR,63.92.224.0/19,no-resolve",
            "IP-CIDR,139.178.128.0/18,no-resolve"
        ]
        ip_lines = []
        for line in sample_lines:
            cleaned_ip = clean_ip_line(line)
            if cleaned_ip and is_valid_ip_or_cidr(cleaned_ip):
                ip_lines.append(cleaned_ip)

        assert ip_lines == ["17.0.0.0/8", "63.92.224.0/19", "139.178.128.0/18"]
        assert not any("no-resolve" in ip for ip in ip_lines)
        assert not any("skk.moe" in ip for ip in ip_lines)

    def test_stream_ip_cleans_no_resolve_ipv4_and_ipv6(self):
        """Simulate skk stream.conf with IPv4 and IPv6."""
        sample_lines = [
            "DOMAIN,7h15.ru1353t.1s.m4d3.by.5ukk4w.skk.moe",
            "IP-CIDR,23.246.18.0/23,no-resolve",
            "IP-CIDR,35.186.224.47/32,no-resolve",
            "IP-CIDR6,2607:fb10::/32,no-resolve",
            "IP-CIDR6,2a00:86c0::/32,no-resolve"
        ]
        ip_lines = []
        for line in sample_lines:
            cleaned_ip = clean_ip_line(line)
            if cleaned_ip and is_valid_ip_or_cidr(cleaned_ip):
                ip_lines.append(cleaned_ip)

        assert ip_lines == [
            "23.246.18.0/23",
            "35.186.224.47/32",
            "2607:fb10::/32",
            "2a00:86c0::/32"
        ]
        assert not any("no-resolve" in ip for ip in ip_lines)

    def test_providers_has_new_skk_ip_entries(self):
        """Verify stream_ip and apple_services_ip exist in providers.MIHOMO_SKK."""
        assert "stream_ip" in providers.MIHOMO_SKK
        assert "apple_services_ip" in providers.MIHOMO_SKK
        assert providers.MIHOMO_SKK["stream_ip"] == "https://ruleset.skk.moe/List/ip/stream.conf"
        assert providers.MIHOMO_SKK["apple_services_ip"] == "https://ruleset.skk.moe/List/ip/apple_services.conf"
