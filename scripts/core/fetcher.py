# -*- coding: utf-8 -*-
"""
Robust network fetcher with concurrency, retries, SSL verification,
local repo file loader, and Tianling authoritative rule-set synchronizer.
"""

import os
import ssl
import json
import time
import urllib.request
import subprocess
from typing import List, Optional

import utils
from core.models import RuleSet

_SSL_CONTEXT = ssl.create_default_context()
UA = "Mozilla/5.0 (compatible; WuiiledSetupRuleEngine/2.0)"


def _get_target_urls(url: str) -> List[str]:
    """Return deduped candidate URLs (origin + ghfast mirror for github)."""
    urls = [url]
    if ("raw.githubusercontent.com" in url or "github.com" in url) and "ghfast.top" not in url:
        mirror = f"https://ghfast.top/{url}"
        if mirror not in urls:
            urls.append(mirror)
    return urls


def fetch_text_url(url: str, timeout: int = 15, retries: int = 3) -> str:
    """Fetch text content from a remote URL with retries and mirror fallback."""
    candidates = _get_target_urls(url)
    for target in candidates:
        req = urllib.request.Request(target, headers={'User-Agent': UA})
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
                    return resp.read().decode('utf-8', errors='ignore')
            except Exception:
                if attempt < retries - 1:
                    time.sleep(0.5 * (attempt + 1))
    print(f"⚠️ 下载失败 (所有镜像源均失败): {url}")
    return ""


def fetch_bytes_url(url: str, timeout: int = 15, retries: int = 3) -> bytes:
    """Fetch binary content from a remote URL with retries and mirror fallback."""
    candidates = _get_target_urls(url)
    for target in candidates:
        req = urllib.request.Request(target, headers={'User-Agent': UA})
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
                    return resp.read()
            except Exception:
                if attempt < retries - 1:
                    time.sleep(0.5 * (attempt + 1))
    print(f"⚠️ 下载二进制失败 (所有镜像源均失败): {url}")
    return b""


def read_local_file(rel_path: str) -> str:
    """Safely read a file relative to the repository root."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    full_path = os.path.join(repo_root, rel_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def fetch_tianling_ruleset(tag: str, category: str = "geosite", out_name: Optional[str] = None) -> Optional[RuleSet]:
    """
    Fetch authoritative .srs from Tianling Shen (1715173329) repository:
      - sing-geosite / rule-set branch
      - sing-geoip / rule-set branch
    Decompiles .srs using sing-box to extract exact domain, domain_suffix, regex, keyword, and ip_cidr.
    Returns a RuleSet containing raw_srs and exact parsed elements.
    """
    rule_name = out_name or tag
    repo = "sing-geoip" if category == "geoip" else "sing-geosite"
    url = f"https://raw.githubusercontent.com/1715173329/{repo}/rule-set/{tag}.srs"

    srs_bytes = fetch_bytes_url(url)
    if not srs_bytes:
        print(f"❌ 无法从天灵官方仓库获取 {tag}.srs: {url}")
        return None

    # Decompile .srs to inspect exact definitions
    temp_dir = utils.get_work_dir()
    temp_srs = os.path.join(temp_dir, f"{tag}.srs")
    temp_json = os.path.join(temp_dir, f"{tag}.json")

    with open(temp_srs, "wb") as f:
        f.write(srs_bytes)

    try:
        cmd = utils._resolve_cmd(["sing-box", "rule-set", "decompile", temp_srs, "-o", temp_json])
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        with open(temp_json, "r", encoding="utf-8") as jf:
            decompiled = json.load(jf)

        rules = decompiled.get("rules", [])
        domains = set()
        domain_suffixes = set()
        domain_keywords = set()
        domain_regexes = set()
        ip_cidrs = set()

        for r in rules:
            domains.update(r.get("domain", []))
            domain_suffixes.update(r.get("domain_suffix", []))
            domain_keywords.update(r.get("domain_keyword", []))
            domain_regexes.update(r.get("domain_regex", []))
            ip_cidrs.update(r.get("ip_cidr", []))

        return RuleSet(
            name=rule_name,
            category=category,
            description=f"天灵官方权威提纯 ({tag})",
            domains=domains,
            domain_suffixes=domain_suffixes,
            domain_keywords=domain_keywords,
            domain_regexes=domain_regexes,
            ip_cidrs=ip_cidrs,
            raw_srs=srs_bytes
        )
    except Exception as e:
        print(f"⚠️ 天灵规则 {tag} 反编译提取失败: {e}")
        return None
    finally:
        for p in (temp_srs, temp_json):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
