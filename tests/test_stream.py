# -*- coding: utf-8 -*-
"""
Stream 总集 (dat 分类 × sve1r × skk) 规则集测试:
- Mihomo 分支: geosite-stream (域名) 与 geoip-stream (裸 CIDR, 无 no-resolve) 严格分离
- Sing-box 分支: geosite-stream 复合为全量集合 (域名+keyword+wildcard+IP),
  且与 IPTV 不同 —— geoip-stream 仍独立导出 (仅 ip_cidr)
"""
import pytest
from core.models import RuleSet
import build_singbox
import build_mihomo


def _mock_stream_rules():
    site = RuleSet(
        name="geosite-stream",
        category="geosite",
        domains={"d1v5ir2lpwr8os.cloudfront.net"},
        domain_suffixes={"netflix.com", "iq.com"},
        domain_keywords={"avoddashs"},
        domain_wildcards={"netflixdnstest*.com"},
        source_kind="self",
        sources=["Loyalsoldier dat", "sve1r/Rules-For-Quantumult-X"],
    )
    ip = RuleSet(
        name="geoip-stream",
        category="geoip",
        ip_cidrs={"23.246.18.0/23", "2607:fb10::/32"},
        source_kind="self",
        sources=["sve1r/Rules-For-Quantumult-X", "ruleset.skk.moe"],
    )
    return {"geosite-stream": site, "geoip-stream": ip}


def test_stream_mihomo_separation():
    rules = _mock_stream_rules()
    site_lines = rules["geosite-stream"].to_mihomo_lines()
    ip_lines = rules["geoip-stream"].to_mihomo_lines()

    # 域名集合: 后缀 +.xxx / 裸域名 / DOMAIN-KEYWORD 行 (exporter 侧对 mrs 剥离 keyword)
    assert "+.netflix.com" in site_lines
    assert "d1v5ir2lpwr8os.cloudfront.net" in site_lines
    assert "DOMAIN-KEYWORD,avoddashs" in site_lines
    assert not any("/" in l for l in site_lines)  # 域名集合绝不含 CIDR

    # IP 集合: 裸 CIDR 形态, 绝不带 no-resolve
    assert "23.246.18.0/23" in ip_lines
    assert "2607:fb10::/32" in ip_lines
    assert all("no-resolve" not in l for l in ip_lines)
    assert all("," not in l for l in ip_lines)


def test_stream_singbox_composite_full():
    rules = _mock_stream_rules()
    build_singbox.synthesize_composites(rules)

    comp = rules["geosite-stream"]
    # 全量复合: 域名 + keyword + wildcard(转 regex) + IP 同集
    assert comp.domain_suffixes == {"netflix.com", "iq.com"}
    assert comp.domain_keywords == {"avoddashs"}
    assert comp.ip_cidrs == {"23.246.18.0/23", "2607:fb10::/32"}

    sb_dict = comp.to_singbox_dict(version=5)
    r0 = sb_dict["rules"][0]
    assert "netflix.com" in r0["domain_suffix"]
    assert "avoddashs" in r0["domain_keyword"]
    assert r0.get("domain_regex")  # host-wildcard 无损转为 regex
    assert "23.246.18.0/23" in r0["ip_cidr"]
    assert "2607:fb10::/32" in r0["ip_cidr"]


def test_stream_singbox_keeps_standalone_geoip(tmp_path):
    rules = _mock_stream_rules()
    build_singbox.synthesize_composites(rules)

    sb_dir = str(tmp_path / "singbox")
    build_singbox.build_singbox_rules(rules, output_dir=sb_dir)

    # 全量复合 geosite-stream 存在
    assert (tmp_path / "singbox" / "geosite" / "geosite-stream.json").exists()
    # 独立 geoip-stream 也必须导出 (与 IPTV 的跳过策略相反), 且仅含 ip_cidr
    geoip_json = tmp_path / "singbox" / "geoip" / "geoip-stream.json"
    assert geoip_json.exists()
    import json
    data = json.loads(geoip_json.read_text(encoding="utf-8"))
    assert set(data["rules"][0].keys()) == {"ip_cidr"}


def test_stream_mihomo_exports_both(tmp_path):
    from conftest import seed_blackwhite_files
    seed_blackwhite_files()
    rules = _mock_stream_rules()
    m_dir = str(tmp_path / "mihomo")
    build_mihomo.build_mihomo_rules(rules, output_dir=m_dir)

    site_file = tmp_path / "mihomo" / "geosite" / "geosite-stream.txt"
    ip_file = tmp_path / "mihomo" / "geoip" / "geoip-stream.txt"
    assert site_file.exists()
    assert ip_file.exists()

    site_content = site_file.read_text(encoding="utf-8")
    ip_content = ip_file.read_text(encoding="utf-8")
    assert "+.netflix.com" in site_content
    assert "d1v5ir2lpwr8os.cloudfront.net" in site_content
    # domain 行为 mrs 无法承载 keyword, exporter 剥离 (语义保留在 singbox .srs)
    assert "DOMAIN-KEYWORD" not in site_content
    assert "23.246.18.0/23" in ip_content
    assert "no-resolve" not in ip_content
    assert "23.246.18.0" not in site_content  # IP 不泄漏进域名集合
