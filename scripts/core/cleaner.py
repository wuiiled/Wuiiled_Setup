# -*- coding: utf-8 -*-
"""
Rule cleaning, normalization, prefix-tree optimization, and regex compaction.
Extracted and purified from utils.py to ensure testability and high cohesion.
"""

import os
import re
import ipaddress
from typing import Set, List, Optional


def normalize_domain_line(line: str) -> Optional[str]:
    """Normalize a raw domain line from various adblock/hosts/domain formats."""
    line = line.strip()
    line = re.sub(r'[\$#].*', '', line)
    line = re.sub(r'^(0\.0\.0\.0|127\.0\.0\.1)\s+', '', line)
    if line.startswith("!"):
        return None
    if line.startswith("@@"):
        line = line[2:]
    line = line.replace("||", "").replace("^", "").replace("|", "")
    line = re.sub(r'^(domain-keyword|domain-suffix|domain),', '', line, flags=re.IGNORECASE)
    if ',' in line:
        line = line.split(',')[0]
    line = re.sub(r'^(\+\.|\.)', '', line)
    line = line.rstrip('.')
    if (
        '.' not in line
        or '*' in line
        or not re.match(r'^[a-z0-9_]', line)
        or re.match(r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$', line)
        or '/' in line
        or ' ' in line
        or ':' in line
    ):
        return None
    return line


def clean_ip_line(line: str) -> Optional[str]:
    """Clean and validate an IP or CIDR line."""
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    line = re.sub(r'#.*$', '', line).strip()
    line = re.sub(r'^(IP-CIDR|IP-CIDR6|IP6-CIDR),', '', line, flags=re.IGNORECASE).strip()
    if ',' in line:
        line = line.split(',')[0].strip()
    line = line.strip(" '\"")
    return line if is_valid_ip_or_cidr(line) else None


def is_valid_ip_or_cidr(val: str) -> bool:
    try:
        ipaddress.ip_network(val, strict=False)
        return True
    except ValueError:
        return False


def clean_mihomo_domain_line(line: str) -> Optional[str]:
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    line = line.split('#')[0].strip()
    if not line:
        return None

    lower = line.lower()
    if lower.startswith("domain-suffix,"):
        val = line.split(',')[1].strip()
        return "+." + val if val else None
    elif lower.startswith("domain,"):
        val = line.split(',')[1].strip()
        return val if val else None

    # 如果包含逗号，说明是具有其它前缀修饰的行 (如 IP-CIDR, PROCESS-NAME 等)，过滤掉
    if ',' in line:
        return None

    if is_valid_ip_or_cidr(line):
        return None

    return line


def compact_regexes(regex_set: Set[str]) -> List[str]:
    """
    Ultimate regex compactor: safe filtering + intelligent grouping.
    Primarily utilized for Fake-IP lists.
    """
    if not regex_set:
        return []

    regex_set.discard(".*")
    regex_set.discard("^.*$")
    regex_set.discard("^(.*\\.)?.*$")

    step1 = set()
    for r in regex_set:
        while r'\..*\..*' in r:
            r = r.replace(r'\..*\..*', r'\..*')
        while r'-.*-.*' in r:
            r = r.replace(r'-.*-.*', r'-.*')
        step1.add(r)

    step2 = set()
    num_pattern = re.compile(r'^(\^?[a-zA-Z_-]+)(\d*)(\\..*)$')
    groups = {}
    for r in step1:
        m = num_pattern.match(r)
        if m:
            prefix, num, suffix = m.groups()
            key = (prefix, suffix)
            if key not in groups:
                groups[key] = set()
            groups[key].add(num)
        else:
            step2.add(r)

    for (prefix, suffix), nums in groups.items():
        if len(nums) > 1:
            step2.add(f"{prefix}\\d*{suffix}")
        else:
            step2.add(f"{prefix}{nums.pop()}{suffix}")

    step3 = set()
    time_bases = {}
    nip_sslip_bases = set()

    time_prefix_regex = re.compile(r'^(\^time(?:\\d*)?\\..*\\.)([^.]+\$)$')

    for r in step2:
        m = time_prefix_regex.match(r)
        if m:
            base, tld_with_dollar = m.groups()
            tld = tld_with_dollar[:-1]
            if base not in time_bases:
                time_bases[base] = set()
            time_bases[base].add(tld)
        elif r.endswith("nip\\.io$") or r.endswith("sslip\\.io$"):
            base = r.replace("nip\\.io$", "").replace("sslip\\.io$", "")
            nip_sslip_bases.add(base)
        else:
            step3.add(r)

    for base, tlds in time_bases.items():
        if len(tlds) > 1:
            tld_str = "|".join(sorted(list(tlds)))
            step3.add(f"{base}({tld_str})$")
        else:
            step3.add(f"{base}{tlds.pop()}$")

    for base in nip_sslip_bases:
        step3.add(f"{base}(nip|sslip)\\.io$")

    return sorted(list(step3))
