# -*- coding: utf-8 -*-
"""
IPTV (Gary + Cathy) 规则集测试:
- 数据模型正确性 (geosite-iptv!cn 为 geosite, geoip-iptv!cn 为 geoip)
- Mihomo 分支区分域名与 IP
- Sing-box 分支复合统一为单一 geosite-iptv!cn (同时包含域名与 IP), 排除独立 geoip-iptv!cn
"""
import pytest
from core.models import RuleSet
import build_singbox
import build_mihomo


def _mock_iptv_rules():
    site = RuleSet(
        name="geosite-iptv!cn",
        category="geosite",
        domain_suffixes={"4kgood.org", "ch1.live", "cdn.qd.je"},
        source_kind="self",
        sources=["marcuccilli/gary", "marcuccilli/Cathy"],
    )
    ip = RuleSet(
        name="geoip-iptv!cn",
        category="geoip",
        ip_cidrs={"89.187.181.220/32", "92.119.88.156/32"},
        source_kind="self",
        sources=["marcuccilli/gary", "marcuccilli/Cathy"],
    )
    return {"geosite-iptv!cn": site, "geoip-iptv!cn": ip}


def test_iptv_mihomo_separation():
    rules = _mock_iptv_rules()
    site_lines = rules["geosite-iptv!cn"].to_mihomo_lines()
    ip_lines = rules["geoip-iptv!cn"].to_mihomo_lines()

    # mihomo 域名规则必须全部为域名形态 (+.xxx)
    assert all(l.startswith("+.") for l in site_lines)
    assert "+.4kgood.org" in site_lines
    assert "+.ch1.live" in site_lines

    # mihomo IP 规则必须全部为 CIDR 形态
    assert all("/" in l for l in ip_lines)
    assert "89.187.181.220/32" in ip_lines
    assert "92.119.88.156/32" in ip_lines


def test_iptv_singbox_composite_synthesis():
    rules = _mock_iptv_rules()
    build_singbox.synthesize_composites(rules)

    comp = rules["geosite-iptv!cn"]
    # 复合后同时具备 domain_suffix 与 ip_cidr
    assert comp.domain_suffixes == {"4kgood.org", "ch1.live", "cdn.qd.je"}
    assert comp.ip_cidrs == {"89.187.181.220/32", "92.119.88.156/32"}

    # singbox json 序列化包含双方
    sb_dict = comp.to_singbox_dict(version=5)
    r0 = sb_dict["rules"][0]
    assert "domain_suffix" in r0 and len(r0["domain_suffix"]) == 3
    assert "ip_cidr" in r0 and len(r0["ip_cidr"]) == 2


def test_iptv_singbox_skips_standalone_geoip(tmp_path):
    rules = _mock_iptv_rules()
    build_singbox.synthesize_composites(rules)

    sb_dir = str(tmp_path / "singbox")
    build_singbox.build_singbox_rules(rules, output_dir=sb_dir)

    # 复合 geosite-iptv!cn 存在
    assert (tmp_path / "singbox" / "geosite" / "geosite-iptv!cn.json").exists()
    # 独立的 geoip-iptv!cn 被严格跳过 (不生成)
    assert not (tmp_path / "singbox" / "geoip" / "geoip-iptv!cn.json").exists()
    assert not (tmp_path / "singbox" / "geoip" / "geoip-iptv!cn.srs").exists()


def test_iptv_mihomo_exports_both(tmp_path):
    from conftest import seed_blackwhite_files
    seed_blackwhite_files()
    rules = _mock_iptv_rules()
    m_dir = str(tmp_path / "mihomo")
    build_mihomo.build_mihomo_rules(rules, output_dir=m_dir)

    # mihomo 分支两个文件均必须存在且独立
    site_file = tmp_path / "mihomo" / "geosite" / "geosite-iptv!cn.txt"
    ip_file = tmp_path / "mihomo" / "geoip" / "geoip-iptv!cn.txt"
    assert site_file.exists()
    assert ip_file.exists()

    site_content = site_file.read_text(encoding="utf-8")
    ip_content = ip_file.read_text(encoding="utf-8")
    assert "+.4kgood.org" in site_content
    assert "89.187.181.220/32" in ip_content
    assert "89.187.181.220" not in site_content
