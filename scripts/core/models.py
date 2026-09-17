# -*- coding: utf-8 -*-
"""
Canonical RuleSet intermediate data model.
Decouples data sourcing from platform-specific exporters.
"""

from typing import Set, List, Optional, Dict, Any


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
        raw_srs: Optional[bytes] = None,
        raw_lines: Optional[List[str]] = None,
    ):
        self.name = name
        self.category = category.lower()
        self.description = description
        self.domains: Set[str] = domains or set()
        self.domain_suffixes: Set[str] = domain_suffixes or set()
        self.domain_keywords: Set[str] = domain_keywords or set()
        self.domain_regexes: Set[str] = domain_regexes or set()
        self.ip_cidrs: Set[str] = ip_cidrs or set()
        self.raw_srs: Optional[bytes] = raw_srs
        self.raw_lines: Optional[List[str]] = raw_lines

    @property
    def is_geoip(self) -> bool:
        return self.category == "geoip" or bool(self.ip_cidrs and not (self.domains or self.domain_suffixes or self.domain_keywords or self.domain_regexes))

    @property
    def total_count(self) -> int:
        return (
            len(self.domains)
            + len(self.domain_suffixes)
            + len(self.domain_keywords)
            + len(self.domain_regexes)
            + len(self.ip_cidrs)
        )

    def to_singbox_dict(self, version: int = 5) -> Dict[str, Any]:
        """Convert RuleSet to Sing-box rule-set JSON structure."""
        rule_dict: Dict[str, Any] = {}
        if self.domains:
            rule_dict["domain"] = sorted(list(self.domains))
        if self.domain_suffixes:
            rule_dict["domain_suffix"] = sorted(list(self.domain_suffixes))
        if self.domain_keywords:
            rule_dict["domain_keyword"] = sorted(list(self.domain_keywords))
        if self.domain_regexes:
            rule_dict["domain_regex"] = sorted(list(self.domain_regexes))
        if self.ip_cidrs:
            rule_dict["ip_cidr"] = sorted(list(self.ip_cidrs))

        return {
            "version": version,
            "rules": [rule_dict]
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
                if self.name == "geoip-gfw":
                    if "." in cidr and cidr.endswith("/32"):
                        lines.append(cidr[:-3])
                    elif ":" in cidr and cidr.endswith("/128"):
                        lines.append(cidr[:-4])
                    else:
                        lines.append(cidr)
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
        return lines

    def to_plain_domains(self) -> List[str]:
        """
        Extract clean plain domains/suffixes for SmartDNS / MosDNS / AdGuard Home.
        """
        results = set()
        for d in self.domains:
            clean = d.strip().lower()
            if clean:
                results.add(clean)
        for s in self.domain_suffixes:
            clean = s.lstrip('.').strip().lower()
            if clean:
                results.add(clean)
        return sorted(list(results))
