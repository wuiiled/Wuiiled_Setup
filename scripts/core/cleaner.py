# -*- coding: utf-8 -*-
"""
Rule cleaning, normalization, prefix-tree deduplication, and regex compaction.
Pure in-memory functions with zero disk/global state dependencies.
"""

import ipaddress
import re
from typing import Dict, Iterable, List, Optional, Set, Tuple

_DOMAIN_LABEL = r'[a-z0-9_]([a-z0-9_-]{0,61}[a-z0-9_])?'
_DOMAIN_MULTI_RE = re.compile(
    rf'^(?=.{{1,253}}$)({_DOMAIN_LABEL}\.)+[a-z0-9]([a-z0-9-]{{0,61}}[a-z0-9])?$',
    re.IGNORECASE,
)
_DOMAIN_OR_TLD_RE = re.compile(
    rf'^(?=.{{1,253}}$)({_DOMAIN_LABEL}\.)*[a-z0-9]([a-z0-9_-]{{0,61}}[a-z0-9])?$',
    re.IGNORECASE,
)
_IPV4_LITERAL_RE = re.compile(r'^\d+\.\d+\.\d+\.\d+$')
_PURE_NUMERIC_RE = re.compile(r'^\d+$')

# Static asset/config extensions that occasionally leak into community lists as fake domains (e.g. init.avif)
_STATIC_ASSET_EXTS = frozenset({
    "avif", "png", "jpg", "jpeg", "gif", "webp", "svg", "ico", "bmp",
    "mp4", "mp3", "m3u8", "apk", "exe", "dll", "json", "yaml", "yml",
    "txt", "conf", "list", "srs", "mrs",
})

_CANCEL_ADG_MODIFIERS = ("$badfilter", "$denyallow=")
_YAML_KEY_RE = re.compile(r'^[a-z0-9_-]+\s*:')
_VALID_FAKEIP_RE = re.compile(r'^(?:\+\.)?[a-z0-9._*-]+$')


def idna_domain(value: str) -> str:
    """Convert non-ASCII domain to punycode (IDNA)."""
    if value.isascii():
        return value
    try:
        return value.encode("idna").decode("ascii").lower()
    except Exception:
        return value


def is_valid_domain(val: str, allow_tld: bool = False) -> bool:
    """Validate whether a string is a syntactically valid ASCII domain/hostname."""
    if not val or _IPV4_LITERAL_RE.match(val) or _PURE_NUMERIC_RE.match(val):
        return False
    if not allow_tld and "." in val and val.rsplit(".", 1)[-1].lower() in _STATIC_ASSET_EXTS:
        return False
    pattern = _DOMAIN_OR_TLD_RE if allow_tld else _DOMAIN_MULTI_RE
    return bool(pattern.match(val))


def domain_ancestors(d: str) -> List[str]:
    """Return all ancestor domains including itself: a.b.com -> [a.b.com, b.com, com]."""
    parts = d.split(".")
    return [".".join(parts[i:]) for i in range(len(parts))]


_domain_ancestors = domain_ancestors  # backward-compatible alias


def normalize_domain_line(line: str) -> Optional[str]:
    """Normalize a raw domain line from various adblock/hosts/domain formats."""
    line = line.strip()
    if not line or line.startswith("!"):
        return None

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

    if not line.isascii():
        line = idna_domain(line)
        if not line.isascii():
            return None

    if not is_valid_domain(line, allow_tld=False):
        return None
    return line


def strip_covered_apex_from_exact_source(domains: Set[str]) -> Set[str]:
    """For exact-match sources (e.g. Pi-hole lists), drop bare 2-label apex
    domains that already have proper subdomains in the same source.
    Prevents `adobe.io` from becoming `+.adobe.io` and blocking all Adobe services
    while preserving all specific telemetry subdomains.
    """
    parent_set = set()
    for d in domains:
        parts = d.split(".")
        if len(parts) >= 3:
            for i in range(1, len(parts) - 1):
                parent_set.add(".".join(parts[i:]))
    return {d for d in domains if not (d.count(".") == 1 and d in parent_set)}


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


def clean_domain_entry(line: str) -> Optional[Tuple[str, str]]:
    """Canonical domain-line cleaner used across custom/SKK/IPTV/PCDN/drop loaders."""
    line = line.strip().lower()
    if not line or line.startswith(('#', '!', '@@')):
        return None
    line = line.split('#', 1)[0].strip()
    if not line:
        return None

    typed: Optional[str] = None
    for pfx in ("domain-suffix,", "host-suffix,", "domain,", "host,"):
        if line.startswith(pfx):
            typed = "domain_suffix" if pfx.endswith("suffix,") else "domain"
            line = line[len(pfx):].split(",", 1)[0].strip()
            break
    if typed is None:
        if line.startswith(("domain-keyword,", "domain-regex,", "ip-cidr,",
                            "ip-cidr6,", "ip6-cidr,", "ip-asn,", "process-name,",
                            "user-agent,", "url-regex,")):
            return None
        if "," in line:
            return None

    is_suffix = (typed == "domain_suffix") if typed is not None \
        else line.startswith(('+.', '.'))
    body = line[2:] if line.startswith('+.') else \
        (line[1:] if line.startswith('.') else line)
    body = body.strip().lstrip('.').rstrip('.').lstrip('+')
    if (not body or '*' in body or '/' in body or ':' in body or ' ' in body
            or is_valid_ip_or_cidr(body)):
        return None
    d = idna_domain(body)
    if not is_valid_domain(d, allow_tld=is_suffix):
        return None
    return ("domain_suffix" if is_suffix else "domain", d)


def collapse_cidrs(cidrs: Iterable[str]) -> Set[str]:
    """Collapse overlapping/adjacent IPv4 and IPv6 CIDRs independently."""
    v4_nets, v6_nets = [], []
    for c in cidrs:
        try:
            net = ipaddress.ip_network(str(c).strip(), strict=False)
            (v4_nets if net.version == 4 else v6_nets).append(net)
        except ValueError:
            pass
    return {str(n) for n in ipaddress.collapse_addresses(v4_nets)} | {
        str(n) for n in ipaddress.collapse_addresses(v6_nets)
    }


def glob_wildcard_to_regex(pattern: str) -> Optional[str]:
    """Convert Mihomo DOMAIN-WILDCARD glob to anchored sing-box domain_regex."""
    p = pattern.strip().lower()
    if not p or set(p) == {"*"}:
        return None
    out = ["^"]
    for ch in p:
        if ch == "*":
            out.append(".*")
        elif ch == "?":
            out.append(".")
        else:
            out.append(re.escape(ch))
    out.append("$")
    return "".join(out)


def wildcard_prefix_to_mihomo(pattern: str) -> Optional[str]:
    """Convert strict `*.domain` glob to Mihomo dot-wildcard `.domain`."""
    p = pattern.strip().lower()
    if not p.startswith("*.") or "?" in p or "*" in p[1:]:
        return None
    dom = p[2:].strip(".")
    if not dom or not is_valid_domain(dom, allow_tld=True):
        return None
    return "." + dom


def parse_ai_rule_line(line: str, bare_as_suffix: bool = False) -> Optional[Tuple[str, str]]:
    """Parse Surge/QuantumultX/Clash YAML/Mihomo rule lines into typed IR tuples."""
    line = line.strip()
    if not line or line.startswith(("#", "!", ";", "//", "<")):
        return None
    if "skk.moe" in line.lower():
        return None

    line = line.split("#", 1)[0].strip()
    if not line:
        return None

    if line.lower() in ("payload:", "rules:"):
        return None
    if line.startswith("-"):
        m = re.match(r"^-\s+(.*)$", line)
        if not m:
            return None
        line = m.group(1).strip().strip("'\"")
        if not line:
            return None

    if "," in line:
        parts = [p.strip() for p in line.split(",")]
        rtype = parts[0].upper()
        val = parts[1] if len(parts) > 1 else ""
        if not val:
            return None

        if rtype in ("DOMAIN", "HOST"):
            d = idna_domain(val.lower().lstrip(".").rstrip("."))
            return ("domain", d) if is_valid_domain(d, allow_tld=False) else None
        if rtype in ("DOMAIN-SUFFIX", "HOST-SUFFIX"):
            s = idna_domain(val.lower().lstrip("+.").lstrip(".").rstrip("."))
            return ("domain_suffix", s) if is_valid_domain(s, allow_tld=True) else None
        if rtype in ("DOMAIN-KEYWORD", "HOST-KEYWORD"):
            kw = val.lower().strip()
            return ("domain_keyword", kw) if kw else None
        if rtype in ("IP-CIDR", "IP-CIDR6", "IP6-CIDR"):
            cleaned = clean_ip_line(line)
            if cleaned:
                try:
                    return ("ip_cidr", str(ipaddress.ip_network(cleaned, strict=False)))
                except ValueError:
                    return None
            return None
        if rtype == "IP-ASN":
            asn = re.sub(r"^as", "", val.strip(), flags=re.IGNORECASE).strip()
            return ("ip_asn", asn) if asn.isdigit() else None
        if rtype == "PROCESS-NAME":
            proc = val.strip()
            return ("process_name", proc) if proc else None
        if rtype in ("DOMAIN-WILDCARD", "HOST-WILDCARD"):
            wc = val.strip().lower()
            return ("domain_wildcard", wc) if wc and ("*" in wc or "?" in wc) else None
        return ("dropped", rtype)

    lower = line.lower()
    if lower.startswith("full:"):
        d = idna_domain(line[5:].strip().lower().lstrip(".").rstrip("."))
        return ("domain", d) if is_valid_domain(d, allow_tld=False) else None
    if lower.startswith("domain:"):
        s = idna_domain(line[7:].strip().lower().lstrip("+.").lstrip(".").rstrip("."))
        return ("domain_suffix", s) if is_valid_domain(s, allow_tld=True) else None
    if lower.startswith("keyword:"):
        kw = line[8:].strip().lower()
        return ("domain_keyword", kw) if kw else None
    if lower.startswith("regexp:"):
        return None

    if line.startswith("||") and "^" in line:
        dom = normalize_domain_line(line)
        return ("domain_suffix", dom) if dom else None

    if line.startswith("+.") or line.startswith("."):
        s = idna_domain(line.lstrip("+.").lstrip(".").rstrip(".").lower())
        return ("domain_suffix", s) if is_valid_domain(s, allow_tld=True) else None

    if is_valid_ip_or_cidr(line):
        try:
            return ("ip_cidr", str(ipaddress.ip_network(line, strict=False)))
        except ValueError:
            return None

    d = idna_domain(line.lower().lstrip("+.").lstrip(".").rstrip("."))
    if is_valid_domain(d, allow_tld=bare_as_suffix):
        return ("domain_suffix" if bare_as_suffix else "domain", d)
    return None


parse_mixed_rule_line = parse_ai_rule_line


def normalize_fakeip_line(raw: str) -> Optional[str]:
    """Normalize a single fakeip-filter line; reject comments, YAML keys, and malformed lines."""
    line = raw.split('#', 1)[0].strip().lower()
    if not line or _YAML_KEY_RE.match(line):
        return None
    line = re.sub(r'^-\s*', '', line).strip(" '\"\t\\")
    if not line or line in ('.', '*.', '+.', '+'):
        return None
    line = line.rstrip('.')
    if not line or not _VALID_FAKEIP_RE.match(line):
        return None
    if line.startswith('*.') and '*' not in line[2:]:
        line = '+.' + line[2:]
    elif line.startswith('.') and '*' not in line[1:]:
        line = '+.' + line[1:]
    return line


def dedup_fakeip_lines(lines: Iterable[str]) -> List[str]:
    """Deduplicate Mihomo fakeip-filter lines covered by shorter `+.` / `.` suffixes."""
    data = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        clean = line
        is_wildcard = False
        if clean.startswith("+."):
            clean, is_wildcard = clean[2:], True
        elif clean.startswith("."):
            clean, is_wildcard = clean[1:], True
        parts = clean.split(".")
        parts.reverse()
        if parts:
            data.append((parts, not is_wildcard, line, is_wildcard))
    data.sort(key=lambda x: (x[0], x[1]))
    result: List[str] = []
    last_root = None
    for parts, _not_wc, orig, is_wc in data:
        if last_root is not None and len(parts) >= len(last_root) and parts[:len(last_root)] == last_root:
            continue
        result.append(orig)
        last_root = parts if is_wc else None
    return result


def compact_regexes(regex_set: Set[str]) -> List[str]:
    """Compact Fake-IP exemption regexes safely (only for allow/exemption sets)."""
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


def absorb_covered_domains(domains: Set[str], suffixes: Set[str], protect=frozenset()) -> Tuple[Set[str], Set[str], int]:
    """Remove domain/suffix entries covered by shorter suffixes (respecting protected base entries)."""
    prot = set()
    for x in protect:
        x = x.strip().lower().lstrip(".")
        if x:
            prot.add(x)
            prot.add(x.rstrip("."))

    kept_suffixes: Set[str] = set()
    label_map: Dict[str, str] = {}
    dup_labels = 0
    for s in suffixes:
        key = s.strip().lower().lstrip(".").rstrip(".")
        if not key:
            continue
        if key in label_map:
            dup_labels += 1
            if label_map[key].startswith(".") and not s.strip().startswith("."):
                label_map[key] = s
            continue
        label_map[key] = s

    covered_suffixes = 0
    for key, orig in label_map.items():
        parts = key.split(".")
        covered_by_shorter = any(".".join(parts[i:]) in label_map for i in range(1, len(parts)))
        if covered_by_shorter and key not in prot:
            covered_suffixes += 1
        else:
            kept_suffixes.add(orig)
    removed = dup_labels + covered_suffixes

    kept_domains: Set[str] = set()
    for d in domains:
        key = d.strip().lower().lstrip(".")
        parts = key.split(".")
        covered = key in label_map or any(".".join(parts[i:]) in label_map for i in range(1, len(parts)))
        if not covered or key in prot:
            kept_domains.add(d)
        else:
            removed += 1

    return kept_domains, kept_suffixes, removed


def subtract_whitelist(
    block_domains: Set[str],
    allow_suffix: Set[str],
    allow_exact: Set[str] = frozenset(),
) -> Set[str]:
    """Pure in-memory Mode A whitelist subtraction (suffix bidirectional + exact exact-only)."""
    allow_set = {a for a in (x.strip().lower().lstrip('+').strip('.') for x in allow_suffix) if a}
    allow_parents: Set[str] = set()
    for a in allow_set:
        parts = a.split('.')
        for i in range(1, len(parts)):
            allow_parents.add(".".join(parts[i:]))
    exact_set = {a for a in (x.strip().lower().lstrip('+').strip('.') for x in allow_exact) if a}

    kept = set()
    for raw in block_domains:
        pure = raw.strip().lower().lstrip('+').strip('.')
        if not pure or pure in exact_set:
            continue
        if pure in allow_parents or any(anc in allow_set for anc in domain_ancestors(pure)):
            continue
        kept.add(pure)
    return kept


def build_blocklist_b(raw_block: Set[str], raw_allow: Set[str],
                      raw_allow_exact: Set[str] = frozenset()) -> Set[str]:
    """Precise blocklist B: removes descendants/exact matches of allow_suffix and exact matches of allow_exact."""
    allow_set = {a for a in (x.strip().lower().lstrip('+').strip('.') for x in raw_allow) if a}
    allow_exact = {a for a in (x.strip().lower().lstrip('+').strip('.') for x in raw_allow_exact) if a}
    kept = set()
    for b in raw_block:
        b = b.strip().lower().lstrip('+').strip('.')
        if not b or b in allow_exact:
            continue
        if any(anc in allow_set for anc in domain_ancestors(b)):
            continue
        kept.add(b)
    _, final, _ = absorb_covered_domains(set(), kept)
    return final


def build_whitelist_b(raw_allow: Set[str], raw_block: Set[str], blocklist_b: Set[str]) -> Set[str]:
    """Allow exception list B: entries in raw_allow not directly blocked that sit under a blocklist_b rule."""
    block_set = {b for b in (x.strip().lower().lstrip('+').strip('.') for x in raw_block) if b}
    blk_b_set = {b for b in (x.strip().lower().lstrip('+').strip('.') for x in blocklist_b) if b}
    out = set()
    for a in raw_allow:
        a = a.strip().lower().lstrip('+').strip('.')
        if not a or a in block_set:
            continue
        if any(anc in blk_b_set for anc in domain_ancestors(a)):
            out.add(a)
    return out
