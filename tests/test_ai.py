# -*- coding: utf-8 -*-
"""
AI 规则集 (geosite-ai / geoip-ai) 全链路单元测试:
- parse_ai_rule_line 对 Surge / Clash YAML / Mihomo / AdBlock 各语法识别与不支持类型过滤
- MagicRule 两跳动态索引解析 (/data/index/Surge.json -> manifest.json -> artifacts[key=='rules'])
- Cloudflare Pages SPA HTML 兜底响应 (200 OK + <!doctype html>) 拒绝防护
- GitHub /blob/ URL 自动转 Raw
- IP-ASN -> IP-CIDR 转换 (ipverse 主源 + RIPEstat 回退 + 网段聚合 + 全失败守卫)
- Sing-box 复合规则合成: process_name 独立为第二条 rule (OR 语义, 避免与域名/IP 产生 AND 误杀)
- Mihomo 导出 geosite-ai (仅 domain + domain_suffix) 与 geoip-ai (ip_cidr) 并通过 lint_artifacts 门禁
"""
import json
import pytest
from unittest.mock import patch

import providers
import build_singbox
import build_mihomo
import build_smartdns
import build_mosdns
import build_adg
from core.cleaner import parse_ai_rule_line
from core.fetcher import (
    _get_target_urls,
    _is_html_payload,
    _resolve_magicrule_candidates,
    fetch_single_asn_cidrs,
    resolve_asn_to_cidrs,
)
from core.manager import load_ai_rules
from core.models import RuleSet
from core.patcher import apply_patches
from lint_artifacts import lint


def test_providers_ai_urls_registered():
    assert "https://magicrule.pages.dev/#/c/Surge/r/24dbbb36-e5c5-4800-8fde-4af469213846" in providers.AI_URLS
    assert "https://github.com/dler-io/Rules/blob/main/Clash/Provider/AI%20Suite.yaml" in providers.AI_URLS


def test_github_blob_url_rewritten_to_raw():
    targets = _get_target_urls("https://github.com/dler-io/Rules/blob/main/Clash/Provider/AI%20Suite.yaml")
    assert targets[0] == "https://raw.githubusercontent.com/dler-io/Rules/main/Clash/Provider/AI%20Suite.yaml"
    assert any("ghfast.top" in t for t in targets)


def test_html_fallback_rejected():
    assert _is_html_payload("<!DOCTYPE html>\n<html><head></head><body></body></html>")
    assert _is_html_payload("  <html><body>SPA</body></html>")
    assert not _is_html_payload("DOMAIN-SUFFIX,openai.com\n")
    assert not _is_html_payload('{"id": "24dbbb36-e5c5-4800-8fde-4af469213846"}')


def test_magicrule_two_hop_index_and_manifest_resolution():
    mock_index = [
        {
            "id": "24dbbb36-e5c5-4800-8fde-4af469213846",
            "name": "GlobalAI",
            "manifest": "/data/Surge/24dbbb36-e5c5-4800-8fde-4af469213846/manifest.json",
        }
    ]
    mock_manifest = {
        "id": "24dbbb36-e5c5-4800-8fde-4af469213846",
        "artifacts": [
            {"key": "domain-set", "url": "/data/_shared/artifacts/GlobalAI_domain-set_new111.list"},
            {"key": "rules", "url": "/data/_shared/artifacts/GlobalAI_rules_new999.list"},
            {"key": "rule-set", "url": "/data/_shared/artifacts/GlobalAI_rule-set_new222.list"},
        ],
    }

    def fake_fetch(url, timeout=15, retries=3):
        if url == "https://magicrule.pages.dev/data/index/Surge.json":
            return json.dumps(mock_index)
        if url == "https://magicrule.pages.dev/data/Surge/24dbbb36-e5c5-4800-8fde-4af469213846/manifest.json":
            return json.dumps(mock_manifest)
        return ""

    with patch("core.fetcher._fetch_raw_text", side_effect=fake_fetch):
        cands = _resolve_magicrule_candidates(
            "https://magicrule.pages.dev/#/c/Surge/r/24dbbb36-e5c5-4800-8fde-4af469213846"
        )
    assert cands[0] == "https://magicrule.pages.dev/data/_shared/artifacts/GlobalAI_rules_new999.list"


def test_parse_ai_rule_line_types_and_filtering():
    assert parse_ai_rule_line("DOMAIN,apple-relay.apple.com") == ("domain", "apple-relay.apple.com")
    assert parse_ai_rule_line("  - DOMAIN,chat.openai.com.cdn.cloudflare.net") == (
        "domain", "chat.openai.com.cdn.cloudflare.net"
    )
    assert parse_ai_rule_line("  - DOMAIN-SUFFIX,openai.com") == ("domain_suffix", "openai.com")
    assert parse_ai_rule_line("DOMAIN-KEYWORD,chatgpt") == ("domain_keyword", "chatgpt")
    assert parse_ai_rule_line("PROCESS-NAME,Claude.exe") == ("process_name", "Claude.exe")
    assert parse_ai_rule_line("IP-CIDR,160.79.104.0/21,no-resolve") == ("ip_cidr", "160.79.104.0/21")
    assert parse_ai_rule_line("IP-CIDR6,2607:6bc0::/32,no-resolve") == ("ip_cidr", "2607:6bc0::/32")
    assert parse_ai_rule_line("IP-ASN,399358,no-resolve") == ("ip_asn", "399358")
    assert parse_ai_rule_line("- IP-ASN,AS401518,no-resolve") == ("ip_asn", "401518")

    assert parse_ai_rule_line("+.anthropic.com") == ("domain_suffix", "anthropic.com")
    assert parse_ai_rule_line("||claude.ai^") == ("domain_suffix", "claude.ai")
    assert parse_ai_rule_line("api.github.com") == ("domain", "api.github.com")

    # 明确不支持但可识别的类型 -> ("dropped", 类型) 供上层统计 (区别于垃圾行 None)
    assert parse_ai_rule_line(r"URL-REGEX,https://www\.google\.com/.*continue=https://gemini\.google\.com.+") == (
        "dropped", "URL-REGEX")
    assert parse_ai_rule_line("USER-AGENT,ChatGPT*") == ("dropped", "USER-AGENT")
    assert parse_ai_rule_line("PROCESS-PATH,/Applications/Claude.app") == ("dropped", "PROCESS-PATH")
    # DOMAIN-WILDCARD (mihomo classical glob 语义): 保留原文进入通配桶
    assert parse_ai_rule_line("DOMAIN-WILDCARD,*.openai-edge.com") == ("domain_wildcard", "*.openai-edge.com")
    assert parse_ai_rule_line("DOMAIN-WILDCARD,qhimgs?.com") == ("domain_wildcard", "qhimgs?.com")
    assert parse_ai_rule_line("DOMAIN,7h15.ru1353t.1s.m4d3.by.5ukk4w.skk.moe") is None
    assert parse_ai_rule_line("<!DOCTYPE html>") is None
    assert parse_ai_rule_line("payload:") is None
    assert parse_ai_rule_line("# comment") is None


def test_asn_to_cidr_ipverse_and_ripestat_fallback():
    ipverse_resp = json.dumps({
        "asn": 399358,
        "prefixes": {
            "ipv4": ["160.79.104.0/22", "160.79.108.0/22"],
            "ipv6": ["2607:6bc0::/32"],
        },
    })
    ripe_resp = json.dumps({
        "data": {
            "prefixes": [
                {"prefix": "23.98.142.176/28"},
                {"prefix": "2604:f20::/32"},
            ]
        }
    })

    def fake_fetch(url, timeout=15, retries=3):
        if "ipverse" in url and "/399358/" in url:
            return ipverse_resp
        if "ipverse" in url and "/401518/" in url:
            return ""
        if "stat.ripe.net" in url and "AS401518" in url:
            return ripe_resp
        return ""

    with patch("core.fetcher._fetch_raw_text", side_effect=fake_fetch):
        c_399358, ok_399358 = fetch_single_asn_cidrs("399358")
        assert ok_399358 and "2607:6bc0::/32" in c_399358

        c_401518, ok_401518 = fetch_single_asn_cidrs("401518")
        assert ok_401518 and c_401518 == {"23.98.142.176/28", "2604:f20::/32"}

        merged, failed = resolve_asn_to_cidrs({"399358", "401518"})
        assert failed == []
        assert "160.79.104.0/21" in merged
        assert "2607:6bc0::/32" in merged
        assert "23.98.142.176/28" in merged
        assert "2604:f20::/32" in merged


def test_ai_guards_on_asn_failure_and_domain_shrinkage():
    sample_ai_raw = "DOMAIN-SUFFIX,openai.com\nIP-ASN,399358,no-resolve\n"

    def fake_download(out_file, urls):
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(sample_ai_raw)

    # Guard 1: ASN 双源失败且缓存/上一版 geoip-ai 均不可用 (真冷启动) -> 中止构建
    with patch("utils.download_files_parallel", side_effect=fake_download), \
         patch("core.manager.resolve_asn_to_cidrs", return_value=(set(), ["399358"])), \
         patch("core.manager.fetch_published_geoip_ai_cidrs", return_value=set()):
        with pytest.raises(RuntimeError, match="IP-ASN 解析失败"):
            load_ai_rules()

    # Guard 1b: ASN 双源失败但上一版已发布 geoip-ai 可用 -> 回退继续合成, 不中止
    with patch("utils.download_files_parallel", side_effect=fake_download), \
         patch("core.manager.resolve_asn_to_cidrs", return_value=(set(), ["399358"])), \
         patch("core.manager.fetch_published_geoip_ai_cidrs",
               return_value={"160.79.104.0/21", "2001:db8::/32"}):
        g1, ip1 = load_ai_rules()
    assert {"160.79.104.0/21", "2001:db8::/32"} <= ip1.ip_cidrs

    # Guard 2: total-empty CIDR result still raises (belt-and-braces)
    with patch("utils.download_files_parallel", side_effect=fake_download), \
         patch("core.manager.resolve_asn_to_cidrs", return_value=(set(), [])):
        with pytest.raises(RuntimeError, match="IP-ASN 转换异常"):
            load_ai_rules()

    # Guard 3: Minimum domain count guard raises RuntimeError on shrinkage
    with patch("utils.download_files_parallel", side_effect=fake_download), \
         patch("core.manager.resolve_asn_to_cidrs", return_value=({"160.79.104.0/21"}, [])):
        with pytest.raises(RuntimeError, match="域名条数异常偏低"):
            load_ai_rules(min_domains=300)


def test_asn_authoritative_empty_not_failure_but_double_failure_is():
    # RIPEstat 返回合法空集 (该 ASN 无宣告前缀): 不算失败, 不进 failed_asns
    def fake_valid_empty(url, timeout=15, retries=3):
        if "stat.ripe.net" in url:
            return json.dumps({"data": {"prefixes": []}})
        return ""

    with patch("core.fetcher._fetch_raw_text", side_effect=fake_valid_empty):
        cidrs, failed = resolve_asn_to_cidrs({"64512"})
        assert cidrs == set() and failed == []

    # 双源均未返回有效数据且无缓存: 计入 failed_asns, 供 manager 中止构建
    # (AS64512 已有上一步的合法空集缓存, 会按"上一次完整拉取"回退, 故换无缓存的 ASN)
    with patch("core.fetcher._fetch_raw_text", return_value=""):
        cidrs, failed = resolve_asn_to_cidrs({"64598", "399358"})
        assert failed == ["399358", "64598"]


def test_patcher_full_overlap_reports_zero_delta_not_negative():
    rs = RuleSet(name="geosite-ai", category="geosite", domain_suffixes={"openai.com", "claude.ai"})
    dat_map = {"category-ai-!cn": RuleSet(name="category-ai-!cn", category="geosite", domain_suffixes={"openai.com"})}
    _, _, _, stats = apply_patches(rs, dat_map=dat_map)
    assert stats == [("dat", "category-ai-!cn", 0)]


def test_ai_end_to_end_singbox_or_semantics_and_mihomo_lint(tmp_path):
    from conftest import seed_blackwhite_files
    seed_blackwhite_files()

    sample_ai_raw = "\n".join([
        "payload:",
        "  - DOMAIN,apple-relay.cloudflare.com",
        "  - DOMAIN,chat.openai.com",
        "  - DOMAIN-SUFFIX,openai.com",
        "  - DOMAIN-SUFFIX,claude.ai",
        "  - DOMAIN-KEYWORD,chatgpt",
        "  - IP-CIDR,102.37.57.54/32,no-resolve",
        "  - IP-CIDR6,2607:6bc0::/32,no-resolve",
        "IP-ASN,399358,no-resolve",
        "PROCESS-NAME,Claude",
        "PROCESS-NAME,ChatGPT.exe",
        "DOMAIN-WILDCARD,*.wildcard-test.example",
        "DOMAIN-WILDCARD,qhimgs?.com",
        r"URL-REGEX,https://www\.google\.com/.*continue=https://gemini\.google\.com.+",
    ]) + "\n"

    def fake_download_parallel(out_file, urls):
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(sample_ai_raw)

    with patch("utils.download_files_parallel", side_effect=fake_download_parallel), \
         patch("core.manager.resolve_asn_to_cidrs", return_value=({"160.79.104.0/21"}, [])):
        geosite_ai, geoip_ai = load_ai_rules()

    assert "apple-relay.cloudflare.com" in geosite_ai.domains
    assert "chat.openai.com" not in geosite_ai.domains
    assert {"openai.com", "claude.ai"} <= geosite_ai.domain_suffixes
    assert geosite_ai.domain_keywords == {"chatgpt"}
    assert geosite_ai.process_names == {"Claude", "ChatGPT.exe"}
    assert geosite_ai.domain_wildcards == {"*.wildcard-test.example", "qhimgs?.com"}
    assert geosite_ai.ip_cidrs == set()

    assert geoip_ai.is_geoip
    assert geoip_ai.ip_cidrs == {"102.37.57.54/32", "160.79.104.0/21", "2607:6bc0::/32"}

    # Build full synthetic rule dictionary for all 5 branches so lint_artifacts can run
    rules = {"geosite-ai": geosite_ai, "geoip-ai": geoip_ai}
    for name in set(providers.OXIDNS_RULESETS) | providers.OXIDNS_EXTRA_RULESETS:
        if name.startswith("geoip-"):
            rules[name] = RuleSet(name=name, category="geoip", ip_cidrs={"203.0.113.0/24"})
        else:
            rules[name] = RuleSet(name=name, category="geosite", domain_suffixes={"example.org"})
    rules["geosite-httpdns"] = RuleSet(name="geosite-httpdns", category="geosite", domain_suffixes={"httpdns.example"})
    rules["geosite-pcdn"] = RuleSet(name="geosite-pcdn", category="geosite", domain_suffixes={"pcdn.example"})

    build_singbox.synthesize_composites(rules)

    sb_dir = tmp_path / "singbox"
    mh_dir = tmp_path / "mihomo"
    build_singbox.build_singbox_rules(dict(rules), output_dir=str(sb_dir))
    build_mihomo.build_mihomo_rules(dict(rules), output_dir=str(mh_dir))
    build_smartdns.build_smartdns_rules(dict(rules), output_dir=str(tmp_path / "smartdns"))
    build_mosdns.build_mosdns_rules(dict(rules), output_dir=str(tmp_path / "mosdns-x"))
    build_adg.build_adg_rules(dict(rules), output_dir=str(tmp_path / "adg"))

    # Verify P0 fix: Sing-box rules array has 2 separate entries (network rule OR process_name rule)
    sb_json_path = sb_dir / "geosite" / "geosite-ai.json"
    assert sb_json_path.exists()
    assert not (sb_dir / "geoip" / "geoip-ai.json").exists()

    sb_data = json.loads(sb_json_path.read_text(encoding="utf-8"))
    assert len(sb_data["rules"]) == 2
    r_net, r_proc = sb_data["rules"][0], sb_data["rules"][1]
    assert "process_name" not in r_net
    assert r_net["domain"] == ["apple-relay.cloudflare.com"]
    assert set(r_net["domain_suffix"]) == {"openai.com", "claude.ai"}
    assert r_net["domain_keyword"] == ["chatgpt"]
    assert set(r_net["ip_cidr"]) == {"102.37.57.54/32", "160.79.104.0/21", "2607:6bc0::/32"}
    assert r_proc == {"process_name": ["ChatGPT.exe", "Claude"]}
    # DOMAIN-WILDCARD (glob) 无损转 domain_regex
    from core.cleaner import glob_wildcard_to_regex
    assert set(r_net["domain_regex"]) == {
        glob_wildcard_to_regex("*.wildcard-test.example"),
        glob_wildcard_to_regex("qhimgs?.com"),
    }

    # Verify Mihomo separation
    mh_site = (mh_dir / "geosite" / "geosite-ai.txt").read_text(encoding="utf-8").splitlines()
    mh_ip = (mh_dir / "geoip" / "geoip-ai.txt").read_text(encoding="utf-8").splitlines()
    assert set(mh_site) == {"apple-relay.cloudflare.com", "+.claude.ai", "+.openai.com", ".wildcard-test.example"}
    assert not any("KEYWORD" in l or "PROCESS" in l for l in mh_site)
    assert not any("qhimgs" in l for l in mh_site)  # 含 ? 的 glob 形态语义不等价, 不输出
    assert set(mh_ip) == {"102.37.57.54/32", "160.79.104.0/21", "2607:6bc0::/32"}

    # Verify lint_artifacts grammar gate passes with 0 issues
    issues = lint(str(tmp_path))
    assert not issues, "\n".join(issues[:20])
