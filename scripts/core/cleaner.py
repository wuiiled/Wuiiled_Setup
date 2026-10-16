# -*- coding: utf-8 -*-
"""
Rule cleaning, normalization, prefix-tree optimization, and regex compaction.
Extracted and purified from utils.py to ensure testability and high cohesion.
"""

import re
import ipaddress
from typing import Set, List, Optional, Tuple, Dict

_DOMAIN_LABEL = r'[a-z0-9_]([a-z0-9_-]{0,61}[a-z0-9_])?'
# Multi-label domain (requires at least one dot, used for adblock/hosts cleaning)
_DOMAIN_MULTI_RE = re.compile(
    rf'^(?=.{{1,253}}$)({_DOMAIN_LABEL}\.)+[a-z0-9]([a-z0-9-]{{0,61}}[a-z0-9])?$',
    re.IGNORECASE,
)
# Single-label TLD or multi-label domain (used for artifact linting where bare TLDs like 'cn', 'google', 'lan' exist)
_DOMAIN_OR_TLD_RE = re.compile(
    rf'^(?=.{{1,253}}$)({_DOMAIN_LABEL}\.)*[a-z0-9]([a-z0-9_-]{{0,61}}[a-z0-9])?$',
    re.IGNORECASE,
)
_IPV4_LITERAL_RE = re.compile(r'^\d+\.\d+\.\d+\.\d+$')
_PURE_NUMERIC_RE = re.compile(r'^\d+$')

# Only reject modifiers that invert or cancel rule semantics ($badfilter, $denyallow)
_CANCEL_ADG_MODIFIERS = ("$badfilter", "$denyallow=")


def idna_domain(value: str) -> str:
    """非 ASCII 域名转 punycode (IDNA)。"""
    if value.isascii():
        return value
    try:
        return value.encode("idna").decode("ascii").lower()
    except Exception:
        return value


def is_valid_domain(val: str, allow_tld: bool = False) -> bool:
    """Validate whether a string is a syntactically valid ASCII domain/hostname.
    - allow_tld=False: requires at least one dot (for raw adlist/hosts line normalization)
    - allow_tld=True: allows single-label TLDs like 'cn', 'google', 'lan', 'xn--fiqs8s' (for artifact linting)
    """
    if not val or _IPV4_LITERAL_RE.match(val) or _PURE_NUMERIC_RE.match(val):
        return False
    pattern = _DOMAIN_OR_TLD_RE if allow_tld else _DOMAIN_MULTI_RE
    return bool(pattern.match(val))


def normalize_domain_line(line: str) -> Optional[str]:
    """Normalize a raw domain line from various adblock/hosts/domain formats."""
    line = line.strip()
    if not line or line.startswith("!"):
        return None

    # Reject AdGuard rules with rule-canceling modifiers ($badfilter / $denyallow=) before stripping $
    lower_raw = line.split("#", 1)[0].lower()
    if "$" in lower_raw and any(mod in lower_raw for mod in _CANCEL_ADG_MODIFIERS):
        return None

    line = re.sub(r'[\#\$].*', '', line)
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
        or _IPV4_LITERAL_RE.match(line)
        or '/' in line
        or ' ' in line
        or ':' in line
    ):
        return None

    # Convert non-ASCII IDN domains to punycode before validating labels
    if not line.isascii():
        line = idna_domain(line)
        if not line.isascii():
            return None

    if not is_valid_domain(line, allow_tld=False):
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
    line = line.strip(" '\t\"")
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

    if ',' in line or is_valid_ip_or_cidr(line):
        return None

    return line


def compact_regexes(regex_set: Set[str]) -> List[str]:
    """
    Ultimate regex compactor: safe filtering + intelligent grouping.
    Primarily utilized for Fake-IP lists.
    """
    if not regex_set:
        return []

    candidates = regex_set - {".*", "^.*$", "^(.*\\.)?.*$", "^(\\.)?.*$"}

    step1 = set()
    for r in candidates:
        while r'\..*\..*' in r:
            r = r.replace(r'\..*\..*', r'\..*')
        while r'-.*-.*' in r:
            r = r.replace(r'-.*-.*', r'-.*')
        step1.add(r)

    step2 = set()
    num_pattern = re.compile(r'^(\^?[a-zA-Z_-]+)(\d*)(\\..*)$')
    groups: Dict[Tuple[str, str], Set[str]] = {}
    for r in step1:
        m = num_pattern.match(r)
        if m:
            prefix, num, suffix = m.groups()
            groups.setdefault((prefix, suffix), set()).add(num)
        else:
            step2.add(r)

    for (prefix, suffix), nums in groups.items():
        if len(nums) > 1:
            step2.add(f"{prefix}\\d*{suffix}")
        else:
            step2.add(f"{prefix}{next(iter(nums))}{suffix}")

    step3 = set()
    time_bases: Dict[str, Set[str]] = {}
    nip_sslip_bases = set()
    time_prefix_regex = re.compile(r'^(\^time(?:\d*)?\\..*\\.)([^.]+\$)$')

    for r in step2:
        m = time_prefix_regex.match(r)
        if m:
            base, tld_with_dollar = m.groups()
            time_bases.setdefault(base, set()).add(tld_with_dollar[:-1])
        elif r.endswith("nip\\.io$") or r.endswith("sslip\\.io$"):
            base = r.replace("nip\\.io$", "").replace("sslip\\.io$", "")
            nip_sslip_bases.add(base)
        else:
            step3.add(r)

    for base, tlds in time_bases.items():
        if len(tlds) > 1:
            tld_str = "|".join(sorted(tlds))
            step3.add(f"{base}({tld_str})$")
        else:
            step3.add(f"{base}{next(iter(tlds))}$")

    for base in nip_sslip_bases:
        step3.add(f"{base}(nip|sslip)\\.io$")

    return sorted(step3)


def absorb_covered_domains(domains: Set[str], suffixes: Set[str]) -> Tuple[Set[str], Set[str], int]:
    """
    覆盖吸收: 删除被更短后缀语义涵盖的条目。仅用于 include 合并集 (cn/ai 等)，
    dat 派生集合不做吸收 (保持与天灵 0-Diff 同构)。
    """
    kept_suffixes: Set[str] = set()
    removed = 0
    label_map: Dict[str, str] = {}
    dup_labels = 0
    for s in suffixes:
        key = s.strip().lower().lstrip(".").rstrip(".")
        if not key:
            continue
        if key in label_map:
            dup_labels += 1
            cur = label_map[key]
            if cur.startswith(".") and not s.strip().startswith("."):
                label_map[key] = s
            continue
        label_map[key] = s

    covered_suffixes = 0
    for key, orig in label_map.items():
        parts = key.split(".")
        if any(".".join(parts[i:]) in label_map for i in range(1, len(parts))):
            covered_suffixes += 1
        else:
            kept_suffixes.add(orig)
    removed = dup_labels + covered_suffixes

    kept_domains: Set[str] = set()
    for d in domains:
        key = d.strip().lower().lstrip(".")
        parts = key.split(".")
        covered = key in label_map or any(".".join(parts[i:]) in label_map for i in range(1, len(parts)))
        if not covered:
            kept_domains.add(d)
        else:
            removed += 1

    return kept_domains, kept_suffixes, removed


def _domain_ancestors(d: str) -> List[str]:
    """Return all ancestor domains including itself: a.b.com -> [a.b.com, b.com, com]."""
    parts = d.split(".")
    return [".".join(parts[i:]) for i in range(len(parts))]


def build_blocklist_b(raw_block: Set[str], raw_allow: Set[str]) -> Set[str]:
    """
    Precise blocklist (黑加白模式 黑名单B).
    """
    allow_set = {a for a in (x.strip().lower().lstrip('+').strip('.') for x in raw_allow) if a}
    kept = set()
    for b in raw_block:
        b = b.strip().lower().lstrip('+').strip('.')
        if not b:
            continue
        if any(anc in allow_set for anc in _domain_ancestors(b)):
            continue
        kept.add(b)
    _, final, _ = absorb_covered_domains(set(), kept)
    return final


def build_whitelist_b(raw_allow: Set[str], raw_block: Set[str], blocklist_b: Set[str]) -> Set[str]:
    """
    Allow exception list (黑加白模式 白名单B).
    """
    block_set = {b for b in (x.strip().lower().lstrip('+').strip('.') for x in raw_block) if b}
    blk_b_set = {b for b in (x.strip().lower().lstrip('+').strip('.') for x in blocklist_b) if b}
    out = set()
    for a in raw_allow:
        a = a.strip().lower().lstrip('+').strip('.')
        if not a or a in block_set:
            continue
        if any(anc in blk_b_set for anc in _domain_ancestors(a)):
            out.add(a)
    return out
