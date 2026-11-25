# -*- coding: utf-8 -*-
"""
Output invariant & minimum baseline-count guards (anti-shrinkage circuit breaker).
"""

import os
from typing import Dict, Optional

import providers

# Minimum rule counts for real production builds (protects against upstream silent shrinkage).
DEFAULT_MIN_COUNTS: Dict[str, int] = {
    "geosite-cn": 1000,
    "geosite-!cn": 5000,
    "geosite-ad": 50000,
    "geosite-ad-precise": 50000,
    "geosite-ai": 200,
    "geosite-stream": 500,
    "geoip-cn": 2000,
    "geoip-gfw": 100,
}


def _count_nonempty_lines(path: str) -> int:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return sum(1 for line in f if line.strip() and not line.strip().startswith("#"))


def validate_output_invariants(
    output_base: str = "output",
    require_binaries: bool = True,
    min_counts: Optional[Dict[str, int]] = None,
) -> None:
    """Verify critical rule outputs exist, are non-empty, and meet optional minimum floors."""
    problems = []
    ox_names = sorted(set(providers.OXIDNS_RULESETS) | providers.OXIDNS_EXTRA_RULESETS)

    for branch in ("smartdns", "mosdns-x"):
        for name in ox_names:
            sub = "geoip" if name.startswith("geoip-") else "geosite"
            p = os.path.join(output_base, branch, sub, f"{name}.txt")
            n = _count_nonempty_lines(p)
            if n == 0:
                problems.append(f"{branch}/{sub}/{name}.txt 缺失或为空")
            elif min_counts and name in min_counts and n < min_counts[name]:
                problems.append(f"{branch}/{sub}/{name}.txt 条数异常偏低 ({n} < {min_counts[name]})")

    for name in ("geosite-cn", "geosite-ad", "geosite-ad-precise", "geosite-ad-allow", "geosite-!cn"):
        p = os.path.join(output_base, "mihomo", "geosite", f"{name}.txt")
        n = _count_nonempty_lines(p)
        if n == 0:
            problems.append(f"mihomo/geosite/{name}.txt 缺失或为空")
        elif min_counts and name in min_counts and n < min_counts[name]:
            problems.append(f"mihomo/geosite/{name}.txt 条数异常偏低 ({n} < {min_counts[name]})")

    for name in ("geoip-cn", "geoip-gfw"):
        p = os.path.join(output_base, "mihomo", "geoip", f"{name}.txt")
        n = _count_nonempty_lines(p)
        if n == 0:
            problems.append(f"mihomo/geoip/{name}.txt 缺失或为空")
        elif min_counts and name in min_counts and n < min_counts[name]:
            problems.append(f"mihomo/geoip/{name}.txt 条数异常偏低 ({n} < {min_counts[name]})")

    for name in ("geosite-ad", "geosite-httpdns", "geosite-pcdn"):
        p = os.path.join(output_base, "adg", f"{name}.txt")
        n = _count_nonempty_lines(p)
        if n == 0:
            problems.append(f"adg/{name}.txt 缺失或为空")
        elif min_counts and name in min_counts and n < min_counts[name]:
            problems.append(f"adg/{name}.txt 条数异常偏低 ({n} < {min_counts[name]})")

    if require_binaries:
        for name in ("geosite-cn", "geosite-ad", "geosite-!cn", "geoip-cn"):
            sub = "geoip" if name.startswith("geoip-") else "geosite"
            p = os.path.join(output_base, "singbox", sub, f"{name}.srs")
            if not os.path.exists(p) or os.path.getsize(p) == 0:
                problems.append(f"singbox/{sub}/{name}.srs 缺失或为空")

    if problems:
        raise RuntimeError(
            "关键产物不变量校验失败 (拒绝发布, 防止空集或缩水破坏线上 provider):\n  - "
            + "\n  - ".join(problems)
        )
    print(f"  ✅ [守卫] 关键产物不变量校验通过 ({len(ox_names)}x2 DNS 集 + mihomo/adg/singbox 关键集)")
