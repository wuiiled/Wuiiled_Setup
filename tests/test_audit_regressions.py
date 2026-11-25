# -*- coding: utf-8 -*-
"""Regression tests covering audit-identified bugs and security hardening."""

import build_singbox
import lint_artifacts
from core import fetcher
from core.cleaner import (
    absorb_covered_domains,
    is_valid_domain,
    normalize_domain_line,
    parse_ai_rule_line,
    strip_covered_apex_from_exact_source,
)
from core.models import RuleSet


def test_absorb_covered_domains_eliminates_bare_subdomains():
    _, kept, removed = absorb_covered_domains(
        set(), {"adobe.io", "a.adobe.io", "b.c.adobe.io", "other.org"}
    )
    assert kept == {"adobe.io", "other.org"}
    assert removed == 2


def test_strip_covered_apex_from_exact_source():
    raw = {"adobe.io", "cc-api-data.adobe.io", "fp.adobestats.io"}
    cleaned = strip_covered_apex_from_exact_source(raw)
    assert cleaned == {"cc-api-data.adobe.io", "fp.adobestats.io"}


def test_static_asset_extensions_rejected():
    assert is_valid_domain("init.avif", allow_tld=False) is False
    assert is_valid_domain("logo.png", allow_tld=False) is False
    assert normalize_domain_line("init.avif") is None
    assert is_valid_domain("example.com", allow_tld=False) is True


def test_lint_rejects_whitespace_in_mihomo_lines(tmp_path):
    for br in ("singbox", "mihomo", "smartdns", "mosdns-x", "adg"):
        (tmp_path / br).mkdir()
    bad_file = tmp_path / "mihomo" / "geosite-test.txt"
    bad_file.write_text("Mijia Cloud\nvalid.example.com\n", encoding="utf-8")
    issues = lint_artifacts.lint(str(tmp_path))
    assert any("Mijia Cloud" in issue for issue in issues)


def test_singbox_synthesize_composites_does_not_mutate_shared_ir(tmp_path):
    site = RuleSet(
        name="geosite-stream", category="geosite",
        domain_suffixes={"netflix.com"}, sources=["Loyalsoldier dat"],
    )
    ip = RuleSet(
        name="geoip-stream", category="geoip",
        ip_cidrs={"23.246.18.0/23"}, sources=["ruleset.skk.moe"],
    )
    shared = {"geosite-stream": site, "geoip-stream": ip}
    build_singbox.build_singbox_rules(shared, output_dir=str(tmp_path / "sb"))
    # Caller's IR must remain uncontaminated by geoip-stream
    assert shared["geosite-stream"].ip_cidrs == set()
    assert shared["geosite-stream"].sources == ["Loyalsoldier dat"]


def test_fetcher_no_unrequested_ghfast_mirror(monkeypatch):
    monkeypatch.delenv("WUIILED_GH_MIRROR", raising=False)
    urls = fetcher._get_target_urls("https://raw.githubusercontent.com/a/b/main/c.txt")
    assert all("ghfast.top" not in u for u in urls)

    monkeypatch.setenv("WUIILED_GH_MIRROR", "https://mirror.example.test")
    urls2 = fetcher._get_target_urls("https://raw.githubusercontent.com/a/b/main/c.txt")
    assert "https://mirror.example.test/https://raw.githubusercontent.com/a/b/main/c.txt" in urls2


def test_oisd_official_has_github_fallback():
    urls = fetcher._get_target_urls("https://small.oisd.nl")
    assert urls == [
        "https://small.oisd.nl",
        "https://raw.githubusercontent.com/sjhgvr/oisd/main/oisd_small.txt",
    ]


def test_parse_ai_rule_line_handles_stream_quantumultx_syntax():
    assert parse_ai_rule_line("HOST-SUFFIX,netflix.com,Stream", bare_as_suffix=True) == ("domain_suffix", "netflix.com")
    assert parse_ai_rule_line("HOST-KEYWORD,avoddashs,Stream", bare_as_suffix=True) == ("domain_keyword", "avoddashs")
    assert parse_ai_rule_line("HOST-WILDCARD,netflixdnstest*.com,Stream", bare_as_suffix=True) == ("domain_wildcard", "netflixdnstest*.com")
    assert parse_ai_rule_line("USER-AGENT,Netflix*,Stream", bare_as_suffix=True) == ("dropped", "USER-AGENT")
    assert parse_ai_rule_line("IP6-CIDR,2607:fb10::/32,no-resolve", bare_as_suffix=True) == ("ip_cidr", "2607:fb10::/32")
