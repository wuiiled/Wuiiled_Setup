# -*- coding: utf-8 -*-
"""
Parse Loyalsoldier Country.mmdb directly from source to produce GeoIP RuleSets.
Replicates oschwald/maxminddb-golang `Networks(SkipAliasedNetworks)` used by
1715173329/sing-geoip so outputs remain 100% 0-Diff against Tianling sing-geoip.
"""

import io
import ipaddress
from typing import Dict, Set

import maxminddb
import maxminddb.decoder

from core.models import RuleSet

_DATA_SECTION_SEPARATOR_SIZE = 16

# MaxMind aliased IPv6 subtrees skipped by SkipAliasedNetworks (IPv4-mapped, Teredo, 6to4)
_V6_ALIASES = (
    (int(ipaddress.IPv6Address("::ffff:0:0")), 96),
    (int(ipaddress.IPv6Address("2001::")), 32),
    (int(ipaddress.IPv6Address("2002::")), 16),
)


def _is_aliased_v6(ip_int: int, depth: int) -> bool:
    for net_int, pfx in _V6_ALIASES:
        if depth == pfx and (ip_int >> (128 - pfx)) == (net_int >> (128 - pfx)):
            return True
    return False


def parse_geoip_mmdb(mmdb_bytes: bytes) -> Dict[str, Set[str]]:
    """Extract `{country_code_lower: set_of_cidr_strings}` from Country.mmdb bytes."""
    reader = maxminddb.open_database(io.BytesIO(mmdb_bytes), mode=maxminddb.MODE_FD)
    try:
        meta = reader.metadata()
    finally:
        reader.close()

    node_count = meta.node_count
    record_size = meta.record_size
    ip_version = meta.ip_version
    node_byte_size = record_size // 4
    data_section_start = node_count * node_byte_size + _DATA_SECTION_SEPARATOR_SIZE
    decoder = maxminddb.decoder.Decoder(mmdb_bytes, data_section_start)

    def _read_node(node_num: int, bit: int) -> int:
        offset = node_num * node_byte_size
        if record_size == 24:
            return int.from_bytes(mmdb_bytes[offset + bit * 3: offset + bit * 3 + 3], "big")
        if record_size == 28:
            mid = mmdb_bytes[offset + 3]
            if bit == 0:
                return ((mid & 0xF0) << 20) | int.from_bytes(mmdb_bytes[offset: offset + 3], "big")
            return ((mid & 0x0F) << 24) | int.from_bytes(mmdb_bytes[offset + 4: offset + 7], "big")
        if record_size == 32:
            return int.from_bytes(mmdb_bytes[offset + bit * 4: offset + bit * 4 + 4], "big")
        raise ValueError(f"Unsupported MMDB record_size: {record_size}")

    max_depth = 128 if ip_version == 6 else 32
    country_map: Dict[str, Set[str]] = {}
    stack = [(0, 0, 0)]

    while stack:
        node, ip_int, depth = stack.pop()
        if node == node_count:
            continue
        if node > node_count:
            data_offset = node - node_count - _DATA_SECTION_SEPARATOR_SIZE + data_section_start
            rec, _ = decoder.decode(data_offset)
            code = ((rec or {}).get("country") or {}).get("iso_code", "").lower()
            if code:
                if ip_version == 6 and depth >= 96 and (ip_int >> 32) == 0:
                    cidr = str(ipaddress.IPv4Network((ip_int & 0xFFFFFFFF, depth - 96), strict=False))
                elif ip_version == 6:
                    cidr = str(ipaddress.IPv6Network((ip_int, depth), strict=False))
                else:
                    cidr = str(ipaddress.IPv4Network((ip_int, depth), strict=False))
                country_map.setdefault(code, set()).add(cidr)
            continue
        if ip_version == 6 and _is_aliased_v6(ip_int, depth):
            continue
        if depth >= max_depth:
            continue
        shift = max_depth - depth - 1
        stack.append((_read_node(node, 1), ip_int | (1 << shift), depth + 1))
        stack.append((_read_node(node, 0), ip_int, depth + 1))

    return country_map


def build_geoip_rulesets(mmdb_bytes: bytes, tags: Dict[str, str]) -> Dict[str, RuleSet]:
    """Build GeoIP RuleSets for requested `tags` (`{'geoip-cn': 'geoip-cn', ...}`)."""
    country_map = parse_geoip_mmdb(mmdb_bytes)
    out: Dict[str, RuleSet] = {}
    for upstream_tag, out_name in tags.items():
        code = upstream_tag[len("geoip-"):].lower()
        cidrs = country_map.get(code)
        if not cidrs:
            raise RuntimeError(
                f"Country.mmdb 中不存在分类 '{code}', 规则集 {out_name} 将静默缺失, 拒绝继续"
            )
        out[out_name] = RuleSet(
            name=out_name,
            category="geoip",
            description=f"Loyalsoldier 权威 GeoIP ({code})",
            ip_cidrs=set(cidrs),
            source_kind="geoip-mmdb",
            sources=["Loyalsoldier/geoip (Country.mmdb)"],
            dat_code=code,
        )
    return out
