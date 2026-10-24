# -*- coding: utf-8 -*-
"""
Robust network fetcher with concurrency, retries, SSL verification,
local repo file loader, MagicRule two-hop SPA & GitHub blob URL resolver,
ASN-to-CIDR converter, and Tianling authoritative rule-set synchronizer.
"""

import json
import os
import re
import ssl
import time
import hashlib
import threading
import ipaddress
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Set, Tuple

import utils
from core.models import RuleSet

_SSL_CONTEXT = ssl.create_default_context()
UA = "Mozilla/5.0 (compatible; WuiiledSetupRuleEngine/2.0)"

_GITHUB_BLOB_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)$")
_MAGICRULE_SPA_RE = re.compile(r"^(https?://[^/]+)/#/c/([^/]+)/r/([0-9a-fA-F-]+)")
_MAGICRULE_FALLBACKS = {
    "24dbbb36-e5c5-4800-8fde-4af469213846": (
        "https://magicrule.pages.dev/data/_shared/artifacts/GlobalAI_rules_7591fffa97b1e679.list"
    ),
}


def _is_html_payload(text: str) -> bool:
    """Detect Cloudflare Pages / SPA HTML fallback responses (200 OK with index.html)."""
    head = text.lstrip()[:256].lower()
    return head.startswith(("<!doctype html", "<html", "<head", "<meta", "<script"))


def _join_base_url(base_url: str, path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    return f"{base_url.rstrip('/')}/{path_or_url.lstrip('/')}"


def _get_target_urls(url: str) -> List[str]:
    """Return deduped candidate URLs (rewriting github blob -> raw + ghfast mirror)."""
    m_blob = _GITHUB_BLOB_RE.match(url)
    if m_blob:
        owner, repo, branch, path = m_blob.groups()
        primary = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    else:
        primary = url

    urls = [primary]
    if ("raw.githubusercontent.com" in primary or "github.com" in primary) and "ghfast.top" not in primary:
        mirror = f"https://ghfast.top/{primary}"
        if mirror not in urls:
            urls.append(mirror)
    return urls


def _fetch_raw_text(url: str, timeout: int = 15, retries: int = 3) -> str:
    """Low-level text fetcher with retries, mirror fallback, and SPA HTML fallback rejection."""
    candidates = _get_target_urls(url)
    for target in candidates:
        req = urllib.request.Request(target, headers={'User-Agent': UA})
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
                    text = resp.read().decode('utf-8', errors='ignore')
                if _is_html_payload(text):
                    break
                return text
            except Exception:
                if attempt < retries - 1:
                    time.sleep(0.5 * (attempt + 1))
    return ""


def _extract_artifact_url_from_obj(obj: dict, base_url: str) -> Optional[str]:
    """
    Extract the 'rules' artifact URL from a manifest or index entry dict.
    Supports both list-of-dicts format (`artifacts: [{"key": "rules", "url": "..."}, ...]`)
    and dict format (`artifacts: {"rules": "..."}`).
    """
    artifacts = obj.get("artifacts")
    if isinstance(artifacts, list):
        by_key = {}
        for entry in artifacts:
            if isinstance(entry, dict):
                k = str(entry.get("key") or entry.get("name") or entry.get("type") or "").lower()
                u = entry.get("url") or entry.get("path") or ""
                if k and u:
                    by_key[k] = u
        for pref in ("rules", "rule-set", "rule_set", "domain-set", "domain_set"):
            if pref in by_key:
                return _join_base_url(base_url, by_key[pref])
        for entry in artifacts:
            if isinstance(entry, dict) and (entry.get("url") or entry.get("path")):
                return _join_base_url(base_url, entry.get("url") or entry.get("path"))
    elif isinstance(artifacts, dict):
        for pref in ("rules", "rule_set", "rule-set", "domain_set", "domain-set"):
            if artifacts.get(pref):
                return _join_base_url(base_url, artifacts[pref])
    for field in ("url", "rules_url"):
        if obj.get(field):
            return _join_base_url(base_url, obj[field])
    return None


def _find_magicrule_entry(data, rule_id: str) -> Optional[dict]:
    """Find the rule entry matching rule_id inside `/data/index/<Client>.json`."""
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if data.get("id") == rule_id:
            return data
        if rule_id in data and isinstance(data[rule_id], dict):
            return data[rule_id]
        for v in data.values():
            if isinstance(v, list):
                items.extend(v)
    for item in items:
        if isinstance(item, dict) and item.get("id") == rule_id:
            return item
    return None


def _resolve_magicrule_candidates(url: str, timeout: int = 15, retries: int = 3) -> List[str]:
    """
    Two-hop dynamic resolver for MagicRule SPA URLs (`#/c/<Client>/r/<UUID>`):
      Hop 1: Fetch `<base>/data/index/<Client>.json` -> locate entry by `id == <UUID>` -> get `manifest` URL.
      Hop 2: Fetch `<manifest_url>` -> extract `artifacts` item with `key == "rules"` -> return artifact `.list` URL.
      Fallback: Known artifact URL if index/manifest endpoints are temporarily unreachable.
    """
    m = _MAGICRULE_SPA_RE.match(url)
    if not m:
        return [url]
    base_url, client, rule_id = m.groups()
    candidates: List[str] = []

    index_url = f"{base_url}/data/index/{client}.json"
    raw_index = _fetch_raw_text(index_url, timeout=timeout, retries=retries)
    if raw_index:
        try:
            index_data = json.loads(raw_index)
            entry = _find_magicrule_entry(index_data, rule_id)
            if entry:
                direct_art = _extract_artifact_url_from_obj(entry, base_url)
                if direct_art:
                    candidates.append(direct_art)
                manifest_ref = entry.get("manifest") or entry.get("manifest_url") or entry.get("manifestUrl")
                if manifest_ref:
                    manifest_url = _join_base_url(base_url, manifest_ref)
                    raw_manifest = _fetch_raw_text(manifest_url, timeout=timeout, retries=retries)
                    if raw_manifest:
                        manifest_data = json.loads(raw_manifest)
                        if isinstance(manifest_data, dict):
                            art_url = _extract_artifact_url_from_obj(manifest_data, base_url)
                            if art_url and art_url not in candidates:
                                candidates.append(art_url)
        except Exception as e:
            print(f"⚠️ MagicRule 动态索引解析异常 ({url}): {e}")

    fallback = _MAGICRULE_FALLBACKS.get(rule_id)
    if fallback and fallback not in candidates:
        candidates.append(fallback)
    return candidates


def fetch_text_url(url: str, timeout: int = 15, retries: int = 3) -> str:
    """Fetch text content from a remote URL with SPA resolution, retries, and mirror fallback."""
    if _MAGICRULE_SPA_RE.match(url):
        for cand in _resolve_magicrule_candidates(url, timeout=timeout, retries=retries):
            content = _fetch_raw_text(cand, timeout=timeout, retries=retries)
            if content.strip():
                return content
        print(f"⚠️ 下载失败 (MagicRule 动态索引与回退源均失败): {url}")
        return ""

    content = _fetch_raw_text(url, timeout=timeout, retries=retries)
    if not content:
        print(f"⚠️ 下载失败 (所有镜像源均失败): {url}")
    return content


def fetch_single_asn_cidrs(asn: str, timeout: int = 15, retries: int = 3) -> Tuple[Set[str], bool]:
    """
    Resolve a single ASN (e.g. '399358' or 'AS399358') into announced IPv4/IPv6 CIDRs.
    1. Primary: ipverse/as-ip-blocks aggregated.json (GitHub Raw + ghfast mirror)
    2. Fallback: RIPEstat Announced Prefixes Data API
    Returns (cidrs, authoritative):
      - authoritative=True  表示至少一源返回了有效数据 (空前缀 = 该 ASN 合法无宣告)
      - authoritative=False 表示双源均未返回有效数据 (网络失败/解析失败), 调用方应中止构建
    """
    clean_asn = re.sub(r"^as", "", str(asn).strip(), flags=re.IGNORECASE).strip()
    if not clean_asn.isdigit():
        return set(), False

    cidrs: Set[str] = set()
    authoritative = False

    # 1. Try ipverse/as-ip-blocks (fast, aggregated, supports GitHub mirror)
    ipverse_url = f"https://raw.githubusercontent.com/ipverse/as-ip-blocks/master/as/{clean_asn}/aggregated.json"
    raw_ipverse = _fetch_raw_text(ipverse_url, timeout=timeout, retries=retries)
    if raw_ipverse:
        try:
            data = json.loads(raw_ipverse)
            authoritative = True
            prefixes = data.get("prefixes") or {}
            for key in ("ipv4", "ipv6"):
                for p in prefixes.get(key) or []:
                    try:
                        cidrs.add(str(ipaddress.ip_network(str(p).strip(), strict=False)))
                    except ValueError:
                        pass
        except Exception:
            pass

    # 2. Fallback to RIPEstat global BGP announced-prefixes API if ipverse returned nothing
    if not cidrs:
        ripe_url = f"https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{clean_asn}"
        raw_ripe = _fetch_raw_text(ripe_url, timeout=timeout, retries=retries)
        if raw_ripe:
            try:
                data = json.loads(raw_ripe)
                authoritative = True
                items = (data.get("data") or {}).get("prefixes") or []
                for item in items:
                    p = item.get("prefix") if isinstance(item, dict) else None
                    if p:
                        try:
                            cidrs.add(str(ipaddress.ip_network(str(p).strip(), strict=False)))
                        except ValueError:
                            pass
            except Exception:
                pass

    if not cidrs and not authoritative:
        print(f"⚠️ ASN 双源均未返回有效数据: AS{clean_asn}")
    if authoritative:
        _source_cache_save(f"asn-cidrs:{clean_asn}", json.dumps(sorted(cidrs)).encode("utf-8"))
        return cidrs, True

    # 双源均无有效数据: 回退该 ASN 上一次完整拉取的网段缓存
    cached = _fresh_cache_or_none(f"asn-cidrs:{clean_asn}", label=f"AS{clean_asn} ")
    if cached is not None:
        try:
            stale_cidrs = set(json.loads(cached.decode("utf-8")))
            print(f"⚠️ AS{clean_asn} 双源失败, 使用缓存网段 {len(stale_cidrs):,} 条")
            return stale_cidrs, True
        except Exception:
            pass
    return cidrs, False


def resolve_asn_to_cidrs(asns: Set[str], timeout: int = 15, retries: int = 3) -> Tuple[Set[str], List[str]]:
    """
    Concurrently resolve a set of ASNs into deduplicated, collapsed IPv4/IPv6 CIDRs.
    Returns (collapsed_cidrs, failed_asns); failed_asns 非空表示这些 ASN 双源解析
    均未获得有效数据, 调用方必须中止构建以防相关网段静默缺失导致流量漏出。
    """
    if not asns:
        return set(), []
    sorted_asns = sorted(asns)
    raw_cidrs: Set[str] = set()
    failed_asns: List[str] = []
    with ThreadPoolExecutor(max_workers=min(len(sorted_asns), 8)) as executor:
        futures = {executor.submit(fetch_single_asn_cidrs, a, timeout, retries): a for a in sorted_asns}
        for fut, asn in futures.items():
            try:
                cidrs, authoritative = fut.result()
                raw_cidrs.update(cidrs)
                if not authoritative:
                    failed_asns.append(asn)
            except Exception as e:
                print(f"⚠️ ASN 并发解析异常 (AS{asn}): {e}")
                failed_asns.append(asn)

    v4_nets = []
    v6_nets = []
    for c in raw_cidrs:
        try:
            net = ipaddress.ip_network(c, strict=False)
            if net.version == 4:
                v4_nets.append(net)
            else:
                v6_nets.append(net)
        except ValueError:
            pass
    collapsed = {str(n) for n in ipaddress.collapse_addresses(v4_nets)} | {
        str(n) for n in ipaddress.collapse_addresses(v6_nets)
    }
    return collapsed, failed_asns


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


# ----------------------------------------------------------------------
# 逐源"上一次完整拉取"缓存: 任意源拉取失败时回退用上一次成功拉取的内容
# 继续合成, 无缓存或缓存超龄则抛错中止构建 —— 拒绝发布缺失任意源的不完整规则。
# CI 侧通过 actions/cache 持久化 ~/.cache/wuiiled_setup 实现跨次构建回退。
# ----------------------------------------------------------------------
SOURCE_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "wuiiled_setup", "sources")


def _source_cache_paths(url: str) -> Tuple[str, str]:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return (
        os.path.join(SOURCE_CACHE_DIR, key + ".body"),
        os.path.join(SOURCE_CACHE_DIR, key + ".meta.json"),
    )


def _source_cache_load(url: str) -> Optional[Tuple[bytes, float]]:
    """读取缓存, 返回 (内容, 缓存年龄天数); 缺失/损坏返回 None。"""
    body_p, meta_p = _source_cache_paths(url)
    try:
        with open(meta_p, encoding="utf-8") as f:
            meta = json.load(f)
        if meta.get("url") != url:
            return None
        with open(body_p, "rb") as f:
            data = f.read()
    except Exception:
        return None
    age_days = max(0.0, (time.time() - float(meta.get("fetched_at", 0))) / 86400)
    return data, age_days


def _source_cache_save(url: str, data: bytes) -> None:
    os.makedirs(SOURCE_CACHE_DIR, exist_ok=True)
    body_p, meta_p = _source_cache_paths(url)
    suffix = f".{os.getpid()}.{threading.get_ident()}.tmp"
    with open(body_p + suffix, "wb") as f:
        f.write(data)
    os.replace(body_p + suffix, body_p)
    with open(meta_p + suffix, "w", encoding="utf-8") as f:
        json.dump({"url": url, "fetched_at": time.time()}, f)
    os.replace(meta_p + suffix, meta_p)


def _source_cache_max_age_days() -> float:
    import providers
    return float(getattr(providers, "SOURCE_CACHE_MAX_AGE_DAYS", 14))


def _fresh_cache_or_none(url: str, label: str = "源") -> Optional[bytes]:
    """读取未超龄的缓存并打印回退提示; 缺失或超龄返回 None。"""
    cached = _source_cache_load(url)
    if cached is None:
        return None
    data, age_days = cached
    if age_days > _source_cache_max_age_days():
        return None
    print(f"⚠️ {label}拉取失败, 回退上一次完整拉取的缓存 ({age_days:.1f} 天前): {url}")
    return data


def fetch_text_cached(url: str, timeout: int = 15, retries: int = 3) -> str:
    """网络优先文本拉取: 成功即刷新缓存; 失败回退上一次完整拉取的缓存;
    无缓存或缓存超龄则抛 RuntimeError, 由调用方中止构建。"""
    content = fetch_text_url(url, timeout=timeout, retries=retries)
    if content.strip():
        _source_cache_save(url, content.encode("utf-8"))
        return content
    cached = _fresh_cache_or_none(url)
    if cached is not None:
        return cached.decode("utf-8", errors="ignore")
    raise RuntimeError(f"源拉取失败且无可用缓存 (拒绝合成缺失该源的不完整规则): {url}")


def fetch_bytes_cached(url: str, timeout: int = 15, retries: int = 3) -> bytes:
    """fetch_text_cached 的二进制版本 (geosite.dat / .srs 等大文件)。"""
    data = fetch_bytes_url(url, timeout=timeout, retries=retries)
    if data:
        _source_cache_save(url, data)
        return data
    cached = _fresh_cache_or_none(url)
    if cached is not None:
        return cached
    raise RuntimeError(f"源拉取失败且无可用缓存 (拒绝合成缺失该源的不完整规则): {url}")


def read_local_file(rel_path: str) -> str:
    """Safely read a file relative to the repository root."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    full_path = os.path.abspath(os.path.join(repo_root, rel_path))
    try:
        inside = os.path.commonpath([repo_root, os.path.realpath(full_path)]) == repo_root
    except ValueError:
        inside = False
    if not inside:
        print(f"⚠️ 拒绝越界路径: {rel_path}")
        return ""
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

    srs_bytes = fetch_bytes_cached(url)
    if not srs_bytes:
        print(f"❌ 无法从天灵官方仓库获取 {tag}.srs: {url}")
        return None

    temp_dir = utils.get_work_dir()
    temp_srs = os.path.join(temp_dir, f"{tag}.srs")
    temp_json = os.path.join(temp_dir, f"{tag}.json")

    with open(temp_srs, "wb") as f:
        f.write(srs_bytes)

    try:
        decompiled = utils.decompile_srs(temp_srs, temp_json)

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
