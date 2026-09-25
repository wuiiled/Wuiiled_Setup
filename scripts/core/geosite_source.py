# -*- coding: utf-8 -*-
"""
Parse Loyalsoldier geosite.dat (v2ray GeoSiteList protobuf) directly from source.
Replaces the clumsy decompile-srs round-trip with native protobuf parsing.
"""

import os
import sys

_PROTO_DIR = os.path.join(os.path.dirname(__file__), "proto")
if _PROTO_DIR not in sys.path:
    sys.path.insert(0, _PROTO_DIR)

import common_pb2  # noqa: E402

from typing import Dict
from core.models import RuleSet  # noqa: E402


def _bucket(results: Dict[str, RuleSet], key: str) -> RuleSet:
    rs = results.get(key)
    if rs is None:
        rs = RuleSet(
            name=key,
            category="geosite",
            description=f"Loyalsoldier geosite ({key})",
        )
        results[key] = rs
    return rs


def _add_item(rs: RuleSet, rtype: str, value: str) -> None:
    if rtype == "domain":
        rs.domains.add(value)
    elif rtype == "domain_suffix":
        rs.domain_suffixes.add(value)
    elif rtype == "domain_keyword":
        rs.domain_keywords.add(value)
    elif rtype == "domain_regex":
        rs.domain_regexes.add(value)


def parse_geosite_dat(dat_path: str) -> Dict[str, RuleSet]:
    """
    Parse geosite.dat into a dict of code -> RuleSet.
    code is lowercased country_code (e.g. 'category-porn', 'google', 'cn');
    带 @attr 的属性视图 (如 'apple@cn') 一并展开, 供天灵式 cn 配方使用。
    返回前已按天灵 sing-geosite 的 filterTags 规则做同款变换。
    """
    gl = common_pb2.GeoSiteList()
    with open(dat_path, "rb") as f:
        gl.ParseFromString(f.read())

    results: Dict[str, RuleSet] = {}
    for entry in gl.entry:
        code = entry.country_code.lower()
        main = _bucket(results, code)

        for d in entry.domain:
            v = d.value
            t = d.type
            if t == common_pb2.Domain.Plain:
                rtype, value = "domain_keyword", v
            elif t == common_pb2.Domain.Regex:
                rtype, value = "domain_regex", v
            elif t == common_pb2.Domain.RootDomain:
                # RootDomain matches the domain itself and all subdomains.
                # Emit as suffix; sing-box domain_suffix "example.com" covers both.
                # 单标签根域(如 youtube/adult)保留前导点写法（'.youtube'），
                # 与天灵 sing-geosite 的 srs 产物形态保持一致（sing-box 语义: 前导点=仅子域）。
                clean = v.lstrip('.')
                rtype, value = "domain_suffix", (clean if '.' in clean else '.' + clean)
            elif t == common_pb2.Domain.Full:
                rtype, value = "domain", v
            else:
                continue

            _add_item(main, rtype, value)
            # 属性视图: 与天灵一致, 带 @attr 的域名同时进入主分类与属性子集
            for a in d.attribute:
                _add_item(_bucket(results, f"{code}@{a.key}"), rtype, value)

    filter_tianling_tags(results)
    return results


def filter_tianling_tags(results: Dict[str, RuleSet]) -> None:
    """
    复刻天灵 sing-geosite main.go 的 filterTags:
      1. 属性视图与主分类同名语义 (如 'category-games-cn@cn') 直接删除;
      2. '!cn' 类主分类的 '@cn' 属性视图 (如 'category-games-!cn@cn'):
         这些域名标记为国内可直连, 需从主分类中剔除, 视图本身删除。
    """
    bad_pairs: list = []
    for key in list(results.keys()):
        if key.count("@") != 1:
            continue
        left, attr = key.split("@", 1)
        last = left.split("-")[-1]
        if last == attr:
            del results[key]
        elif "!" + last == attr or last == "!" + attr:
            bad_pairs.append((left, key))
    for left, bad_key in bad_pairs:
        bad = results.pop(bad_key, None)
        main = results.get(left)
        if bad is None or main is None:
            continue
        main.domains -= bad.domains
        main.domain_suffixes -= bad.domain_suffixes
        main.domain_keywords -= bad.domain_keywords
        main.domain_regexes -= bad.domain_regexes


def build_tianling_style_cn(results: Dict[str, RuleSet]) -> RuleSet:
    """
    复刻天灵 sing-geosite main.go 的 mergeTags: 本地合成精编版 cn——
      geolocation-cn
      + 所有 category-*@cn 属性视图 (左侧分类不以 -cn/-!cn 结尾)
      + 所有 category-*-cn 主分类
      + '.cn' 顶级域后缀
    完全弃用 dat 里 dnsmasq-china-list 全量版 cn (111k+)。
    """
    cn = RuleSet(
        name="geosite-cn",
        category="geosite",
        description="天灵配方合成 cn (geolocation-cn + category-*@cn + category-*-cn)",
    )

    def _union(rs: RuleSet) -> None:
        if rs is None:
            return
        cn.domains |= rs.domains
        cn.domain_suffixes |= rs.domain_suffixes
        cn.domain_keywords |= rs.domain_keywords
        cn.domain_regexes |= rs.domain_regexes

    _union(results.get("geolocation-cn"))
    for key, rs in results.items():
        if key.count("@") != 1:
            continue
        left, attr = key.split("@", 1)
        if attr != "cn" or not left.startswith("category-"):
            continue
        if left.endswith("-cn") or left.endswith("-!cn"):
            continue
        _union(rs)
    for key, rs in results.items():
        if "@" in key or not key.startswith("category-") or not key.endswith("-cn"):
            continue
        _union(rs)
    cn.domain_suffixes.add("cn")
    return cn
