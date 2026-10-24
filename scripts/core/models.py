# -*- coding: utf-8 -*-
"""
Canonical RuleSet intermediate data model.
Decouples data sourcing from platform-specific exporters.
"""

from typing import Set, List, Optional, Dict, Any
from core.cleaner import glob_wildcard_to_regex, wildcard_prefix_to_mihomo


def _strip_host_cidr(cidr: str) -> str:
    """Strip /32 from IPv4 or /128 from IPv6 host addresses."""
    if "." in cidr and cidr.endswith("/32"):
        return cidr[:-3]
    if ":" in cidr and cidr.endswith("/128"):
        return cidr[:-4]
    return cidr


class RuleSet:
    def __init__(
        self,
        name: str,
        category: str = "geosite",  # "geosite" or "geoip"
        description: str = "",
        domains: Optional[Set[str]] = None,
        domain_suffixes: Optional[Set[str]] = None,
        domain_keywords: Optional[Set[str]] = None,
        domain_regexes: Optional[Set[str]] = None,
        ip_cidrs: Optional[Set[str]] = None,
        process_names: Optional[Set[str]] = None,
        domain_wildcards: Optional[Set[str]] = None,
        raw_srs: Optional[bytes] = None,
        raw_lines: Optional[List[str]] = None,
        source_kind: str = "",  # dat | recipe | self | skk | custom | geoip-srs
        sources: Optional[List[str]] = None,
        dat_code: str = "",
        flatten_cidr_host: bool = False,
    ):
        self.name = name
        self.category = category.lower()
        self.description = description
        self.domains: Set[str] = domains or set()
        self.domain_suffixes: Set[str] = domain_suffixes or set()
        self.domain_keywords: Set[str] = domain_keywords or set()
        self.domain_regexes: Set[str] = domain_regexes or set()
        self.ip_cidrs: Set[str] = ip_cidrs or set()
        self.process_names: Set[str] = process_names or set()
        self.domain_wildcards: Set[str] = domain_wildcards or set()
        self.raw_srs: Optional[bytes] = raw_srs
        self.raw_lines: Optional[List[str]] = raw_lines
        # 来源画像: 由各 loader 填写, 经 manifest 驱动 README "说明" 列渲染,
        # 保证介绍永远反映真实构建路径而非手工文案。
        self.source_kind: str = source_kind
        self.sources: List[str] = list(sources or [])
        self.dat_code: str = dat_code
        # True 时 mihomo 输出剥掉单主机 CIDR 的 /32、/128 前缀
        # (如 geoip-gfw 靶心表按裸 IP 表达), 替代旧的按集合名硬编码特判。
        self.flatten_cidr_host: bool = flatten_cidr_host

    def copy(self) -> "RuleSet":
        return RuleSet(
            name=self.name,
            category=self.category,
            description=self.description,
            domains=set(self.domains),
            domain_suffixes=set(self.domain_suffixes),
            domain_keywords=set(self.domain_keywords),
            domain_regexes=set(self.domain_regexes),
            ip_cidrs=set(self.ip_cidrs),
            process_names=set(self.process_names),
            domain_wildcards=set(self.domain_wildcards),
            raw_srs=self.raw_srs,
            raw_lines=list(self.raw_lines) if self.raw_lines is not None else None,
            source_kind=self.source_kind,
            sources=list(self.sources),
            dat_code=self.dat_code,
            flatten_cidr_host=self.flatten_cidr_host,
        )

    @property
    def is_geoip(self) -> bool:
        return self.category == "geoip" or bool(self.ip_cidrs and not (self.domains or self.domain_suffixes or self.domain_keywords or self.domain_regexes or self.process_names or self.domain_wildcards))

    @property
    def total_count(self) -> int:
        return (
            len(self.domains)
            + len(self.domain_suffixes)
            + len(self.domain_keywords)
            + len(self.domain_regexes)
            + len(self.ip_cidrs)
            + len(self.process_names)
            + len(self.domain_wildcards)
        )

    def to_singbox_dict(self, version: int = 5) -> Dict[str, Any]:
        """
        Convert RuleSet to Sing-box rule-set JSON structure.
        IMPORTANT (sing-box headless rule semantics):
        Within a single rule object, `(domain || domain_suffix || domain_keyword || domain_regex || ip_cidr)`
        is ANDed with `process_name`. To achieve OR semantics between network indicators and process names,
        `process_name` MUST be emitted as a separate rule entry in the `rules` list.
        """
        rules_list: List[Dict[str, Any]] = []
        net_rule: Dict[str, Any] = {}
        if self.domains:
            net_rule["domain"] = sorted(list(self.domains))
        if self.domain_suffixes:
            net_rule["domain_suffix"] = sorted(list(self.domain_suffixes))
        if self.domain_keywords:
            net_rule["domain_keyword"] = sorted(list(self.domain_keywords))
        # DOMAIN-WILDCARD (mihomo classical glob 语义) 无损转为等价正则并入
        wc_regexes = {r for r in (glob_wildcard_to_regex(w) for w in self.domain_wildcards) if r}
        all_regexes = set(self.domain_regexes) | wc_regexes
        if all_regexes:
            net_rule["domain_regex"] = sorted(list(all_regexes))
        if self.ip_cidrs:
            net_rule["ip_cidr"] = sorted(list(self.ip_cidrs))
        if net_rule:
            rules_list.append(net_rule)

        if self.process_names:
            rules_list.append({"process_name": sorted(list(self.process_names))})

        if not rules_list:
            rules_list.append({})

        return {
            "version": version,
            "rules": rules_list
        }

    def to_mihomo_lines(self) -> List[str]:
        """
        Convert RuleSet to lines for Mihomo payload text file.
        For domain:
          - domain_suffix: +.example.com
          - domain: example.com
          - keyword: DOMAIN-KEYWORD,foo
          - regex: DOMAIN-REGEX,pat
        For ipcidr:
          - ip_cidr: 1.2.3.0/24
        """
        if self.raw_lines is not None:
            return list(self.raw_lines)

        lines = []
        if self.is_geoip:
            for cidr in sorted(self.ip_cidrs):
                if self.flatten_cidr_host:
                    lines.append(_strip_host_cidr(cidr))
                else:
                    lines.append(cidr)
        else:
            for d in sorted(self.domains):
                lines.append(d)
            for s in sorted(self.domain_suffixes):
                clean_s = s.lstrip('.')
                if clean_s:
                    lines.append(f"+.{clean_s}")
            for k in sorted(self.domain_keywords):
                lines.append(f"DOMAIN-KEYWORD,{k}")
            for r in sorted(self.domain_regexes):
                lines.append(f"DOMAIN-REGEX,{r}")
            for w in sorted(self.domain_wildcards):
                # 仅 `*.字面域名` 形态与 domain 行为严格等价 (glob `*` 跨点 = 任意深度子域);
                # 含 ?/中段 * 的形态语义不等价, 由 build_mihomo 统计丢弃并提示 (保留于 singbox .srs)
                converted = wildcard_prefix_to_mihomo(w)
                if converted:
                    lines.append(converted)
        return lines

    def to_oxidns_lines(self, domain_prefix: str = "domain:", flatten_host_cidr: bool = False) -> List[str]:
        """
        Generate line list for OxiDNS (mosdns-x / smartdns) text files.
        For domain:
          - domain_suffix: {domain_prefix}{suffix} (default "domain:foo.com", or "foo.com" for smartdns)
          - domain: full:{domain} (if not already covered by exact suffix)
          - keyword: keyword:{kw}
          - regex: regexp:{regex}
        For geoip:
          - ip_cidr: CIDR (optionally stripping /32 or /128 host suffix)
        """
        lines: List[str] = []
        if self.is_geoip:
            for cidr in sorted(self.ip_cidrs):
                if flatten_host_cidr:
                    lines.append(_strip_host_cidr(cidr))
                else:
                    lines.append(cidr)
        else:
            for s in sorted(self.domain_suffixes):
                clean_s = s.lstrip('.')
                if clean_s:
                    lines.append(f"{domain_prefix}{clean_s}")
            for d in sorted(self.domains):
                clean_d = d.strip()
                if clean_d and clean_d not in self.domain_suffixes:
                    lines.append(f"full:{clean_d}")
            for k in sorted(self.domain_keywords):
                lines.append(f"keyword:{k}")
            for r in sorted(self.domain_regexes):
                lines.append(f"regexp:{r}")
            for w in sorted(self.domain_wildcards):
                # glob 通配语义 (跨点 * / 单字符 ?) 在 DNS 引擎侧以 regexp 等价表达
                rx = glob_wildcard_to_regex(w)
                if rx:
                    lines.append(f"regexp:{rx}")
        return lines
