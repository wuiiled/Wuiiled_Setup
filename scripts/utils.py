# -*- coding: utf-8 -*-
"""
Shared exporter helpers and backward-compatible re-exports of compiler/validator utilities.
"""

import os
import shutil
import sys
from typing import Dict, List

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import providers
from core.cleaner import domain_ancestors, idna_domain as _idna_domain, subtract_whitelist
from core.compiler import (  # noqa: F401
    _COMPILE_FAILURES,
    _resolve_cmd,
    assert_no_compile_failures,
    check_tool,
    cleanup,
    compile_ruleset,
    decompile_srs,
    get_work_dir,
)
from core.models import RuleSet
from core.validators import DEFAULT_MIN_COUNTS, validate_output_invariants  # noqa: F401

os.environ["LC_ALL"] = "C"


def safe_copy(src: str, dst: str) -> None:
    """Cross-platform copy safe on case-insensitive filesystems."""
    if os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(dst)):
        return
    shutil.copyfile(src, dst)


def apply_advanced_whitelist_filter(block_in: str, allow_in: str, final_out: str, exact_in: str = None) -> None:
    """File-based Mode A whitelist subtraction helper (delegates matching semantics cleanly)."""
    allow_set = set()
    allow_exact = set()
    if os.path.exists(allow_in):
        with open(allow_in, "r", encoding="utf-8") as f:
            allow_set = {l.strip().lower().lstrip("+").lstrip(".") for l in f if l.strip() and not l.strip().startswith("#")}
    if exact_in and os.path.exists(exact_in):
        with open(exact_in, "r", encoding="utf-8") as f:
            allow_exact = {l.strip().lower().lstrip("+").lstrip(".") for l in f if l.strip() and not l.strip().startswith("#")}

    allow_parents = set()
    for a in allow_set:
        parts = a.split(".")
        for i in range(1, len(parts)):
            allow_parents.add(".".join(parts[i:]))

    final_lines = []
    if os.path.exists(block_in):
        with open(block_in, "r", encoding="utf-8") as f:
            for line in f:
                original = line.strip()
                if not original or original.startswith("#"):
                    continue
                pure = original.lower().lstrip("+").lstrip(".")
                if pure in allow_exact:
                    continue
                if pure in allow_parents or any(anc in allow_set for anc in domain_ancestors(pure)):
                    continue
                final_lines.append(original)

    with open(final_out, "w", encoding="utf-8") as f:
        if final_lines:
            f.write("\n".join(final_lines) + "\n")


def render_adguard_lines(rules: Dict[str, RuleSet]) -> List[str]:
    """Render unified AdGuard filter lines (||blocklist_b^ + @@||whitelist_b^) directly from IR."""
    blk = rules.get("geosite-ad-precise")
    wht = rules.get("geosite-ad-allow")
    if blk is None:
        raise RuntimeError("黑加白精确集 geosite-ad-precise 缺失")
    lines = []
    for d in sorted(blk.domain_suffixes):
        clean = _idna_domain(d.strip().lstrip("+").lstrip("."))
        if clean and not clean.startswith("#"):
            lines.append(f"||{clean}^")
    if wht is not None:
        for d in sorted(wht.domain_suffixes):
            clean = _idna_domain(d.strip().lstrip("+").lstrip("."))
            if clean and not clean.startswith("#"):
                lines.append(f"@@||{clean}^")
    return lines


def select_oxidns_rules(rules: Dict[str, RuleSet]) -> Dict[str, RuleSet]:
    """Filter IR rules to the OxiDNS subscription whitelist (smartdns / mosdns-x)."""
    whitelist = set(providers.OXIDNS_RULESETS) | providers.OXIDNS_EXTRA_RULESETS
    return {name: rs for name, rs in rules.items() if name in whitelist}


def publish_oxidns_compat(output_dir: str, rules: Dict[str, RuleSet]) -> None:
    """Write legacy-named subdir aliases for OxiDNS consumers."""
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    for rel, ruleset_name in providers.OXIDNS_SUBDIR_ALIASES.items():
        rs = rules.get(ruleset_name)
        if rs is None:
            continue
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        src = os.path.join(sub_dir, f"{ruleset_name}.txt")
        dst = os.path.join(output_dir, rel)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            safe_copy(src, dst)


def format_oxidns_lines(rs: RuleSet, domain_prefix: str = "domain:", flatten_host_cidr: bool = False) -> List[str]:
    return rs.to_oxidns_lines(domain_prefix=domain_prefix, flatten_host_cidr=flatten_host_cidr)


def export_oxidns_rules(
    rules: Dict[str, RuleSet],
    output_dir: str,
    domain_prefix: str,
    flatten_host_cidr: bool,
    label: str,
) -> None:
    """Shared exporter for smartdns and mosdns-x branches."""
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    os.makedirs(geosite_out, exist_ok=True)
    os.makedirs(geoip_out, exist_ok=True)

    selected = select_oxidns_rules(rules)
    print(f"\n📦 [{label}] 正在构建 {len(selected)} 个 OxiDNS 订阅规则并输出至 {output_dir}...")
    for name, rs in selected.items():
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        out_path = os.path.join(sub_dir, f"{name}.txt")
        lines = format_oxidns_lines(rs, domain_prefix=domain_prefix, flatten_host_cidr=flatten_host_cidr)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))

    publish_oxidns_compat(output_dir, selected)
    print(f"✅ [{label}] OxiDNS 订阅规则构建完成！")


def idna_normalize_rules(rules: Dict[str, RuleSet]) -> int:
    """Normalize any remaining non-ASCII domain/suffix entries to punycode across all RuleSets."""
    total = 0
    for name, rs in rules.items():
        converted = 0
        new_domains = set()
        for d in rs.domains:
            v = _idna_domain(d)
            converted += (v != d)
            new_domains.add(v)
        new_suffixes = set()
        for s in rs.domain_suffixes:
            v = _idna_domain(s)
            converted += (v != s)
            new_suffixes.add(v)
        if converted:
            rs.domains, rs.domain_suffixes = new_domains, new_suffixes
            total += converted
            print(f"  [IDNA] {name:<26} | {converted} 条非 ASCII 域名已转 punycode")
    if total:
        print(f"  ✅ [IDNA] 共转换 {total} 条")
    return total
