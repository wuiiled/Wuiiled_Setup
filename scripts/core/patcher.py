# -*- coding: utf-8 -*-
"""
Local patch manager for Tianling rulesets.
Reads per-ruleset patch files from rules/patches/ and applies them after upstream fetch.
Patch files are READ-ONLY during the build: entries that upstream already includes are
skipped at runtime and reported in the log (上游已收录), never rewritten on disk.

补丁文件格式 (rules/patches/<规则集名>.txt):
  纯文本        -> domain_suffix (如 example.com)
  full:         -> domain       (如 full:www.example.com)
  keyword:      -> domain_keyword
  regexp:       -> domain_regex
  include:dat:<分类码>      合并 dat 解析出的其他分类 (如 include:dat:category-ai-!cn)
  include:url:<URL>         下载外部列表并清洗后合并
  include:local:<相对路径>  合并本地文件 (相对仓库根)
  以 # 开头为注释

include 合并的清洗规则 (与 04699e9 版本 gen_cn 语义一致):
  裸域名 -> domain_suffix; '+.'/'.' 前缀 -> domain_suffix;
  'domain-suffix,'/'domain,' -> 原语义 (suffix/domain); 'full:' -> domain;
  'keyword:'/'regexp:' -> 对应类型; 空行/#注释/含 skk.moe 水印的行跳过。
include 属于"整表合并", 上游随其自行更新; 解析失败 (下载失败/分类不存在/合并 0 条)
会在 apply_patches 的调用方处中止构建, 防止规则集静默缩水。
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from core.models import RuleSet


PATCH_DIR = "rules/patches"

_INCLUDE_RE = re.compile(r"^include:(dat|url|local):(\S+)\s*$")


def _clean_list_line(line: str) -> Optional[Tuple[str, str]]:
    """
    清洗外部列表的一行, 返回 (rule_type, value); 无法识别/应跳过返回 None。
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if "skk.moe" in line.lower():
        return None
    line = line.split("#")[0].strip()
    if not line:
        return None

    lower = line.lower()
    if lower.startswith("full:"):
        return "domain", line[5:]
    if lower.startswith("keyword:"):
        return "domain_keyword", line[8:]
    if lower.startswith("regexp:"):
        return "domain_regex", line[7:]
    if lower.startswith("domain-suffix,") or lower.startswith("domain,"):
        cleaned = _clean_mihomo_domain(line)
        if cleaned:
            if cleaned.startswith("+."):
                return "domain_suffix", cleaned[2:].lstrip(".")
            return "domain", cleaned
        return None
    if "," in line:
        # 其它带逗号前缀的规则行 (IP-CIDR / PROCESS-NAME 等) 不适用于域名集合
        return None
    if line.lower().startswith("include:"):
        return None
    return "domain_suffix", line.lstrip("+.").lstrip(".").rstrip(".").lower()


def _clean_mihomo_domain(line: str) -> Optional[str]:
    """极简版 mihomo 域名行清洗 (仅处理 domain-suffix,/domain, 前缀)。"""
    parts = line.split(",")
    if len(parts) < 2:
        return None
    val = parts[1].strip()
    if not val:
        return None
    if line.lower().startswith("domain-suffix,"):
        return "+." + val
    return val


def _parse_patch_line(line: str):
    """
    Parse one patch line.
    返回 ('rule', rule_type, value) / ('include', kind, target) / (None, None, None)。
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None, None, None

    m = _INCLUDE_RE.match(stripped)
    if m:
        return "include", m.group(1), m.group(2)

    if stripped.startswith("full:"):
        return "rule", "domain", stripped[5:]
    if stripped.startswith("keyword:"):
        return "rule", "domain_keyword", stripped[8:]
    if stripped.startswith("regexp:"):
        return "rule", "domain_regex", stripped[7:]

    # 默认: domain_suffix
    return "rule", "domain_suffix", stripped.lstrip(".")


def load_patch_file(ruleset_name: str) -> List[tuple]:
    """
    Load a patch file for a ruleset.
    返回 ('rule', rule_type, value, raw_line) 与 ('include', kind, target, raw_line) 列表。
    """
    path = os.path.join(PATCH_DIR, f"{ruleset_name}.txt")
    if not os.path.exists(path):
        return []

    results = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            kind, a, b = _parse_patch_line(raw)
            if kind == "rule" and a and b:
                results.append(("rule", a, b, raw.rstrip("\n")))
            elif kind == "include" and b:
                results.append(("include", a, b, raw.rstrip("\n")))
    return results


def has_patch_includes(ruleset_name: str) -> bool:
    """补丁文件中是否含有 include 指令 (用于 0-Diff 测试的期望值判定)。"""
    return any(kind == "include" for kind, *_ in load_patch_file(ruleset_name))


def get_active_patch_count(ruleset_name: str) -> int:
    """统计补丁文件中的普通规则行数 (不含 include, 与 0-Diff 测试期望一致)。"""
    return sum(1 for kind, *_ in load_patch_file(ruleset_name) if kind == "rule")


def _ruleset_contains(rs: RuleSet, rtype: str, value: str) -> bool:
    """Check if a RuleSet already contains a rule."""
    value = value.lower().strip()
    if rtype == "domain":
        return value in rs.domains
    if rtype == "domain_suffix":
        clean = value.lstrip(".")
        return clean in {s.lstrip(".").lower() for s in rs.domain_suffixes}
    if rtype == "domain_keyword":
        return value in rs.domain_keywords
    if rtype == "domain_regex":
        return value in rs.domain_regexes
    return False


def _add_to_ruleset(rs: RuleSet, rtype: str, value: str) -> None:
    """Add a rule to a RuleSet."""
    value = value.strip()
    if rtype == "domain":
        rs.domains.add(value)
    elif rtype == "domain_suffix":
        rs.domain_suffixes.add(value.lstrip("."))
    elif rtype == "domain_keyword":
        rs.domain_keywords.add(value)
    elif rtype == "domain_regex":
        rs.domain_regexes.add(value)


def _merge_ruleset(src: RuleSet, dst: RuleSet) -> None:
    dst.domains |= src.domains
    dst.domain_suffixes |= src.domain_suffixes
    dst.domain_keywords |= src.domain_keywords
    dst.domain_regexes |= src.domain_regexes


def _resolve_include(kind: str, target: str, dat_map: Optional[Dict[str, RuleSet]]) -> Optional[RuleSet]:
    """解析 include 指令, 返回待合并的 RuleSet (或 None)。"""
    if kind == "dat":
        if dat_map is None:
            print(f"    ⚠️ include:dat:{target} 被跳过 (当前上下文无 dat 源)")
            return None
        rs = dat_map.get(target.lower())
        if rs is None:
            print(f"    ⚠️ include:dat:{target} 被跳过 (dat 中不存在该分类)")
        return rs
    if kind == "url":
        import utils
        content = utils.download_file(target)
        if not content:
            print(f"    ⚠️ include:url 下载失败, 已跳过: {target}")
            return None
        rs = RuleSet(name=f"include:{target}", category="geosite")
        for line in content.splitlines():
            parsed = _clean_list_line(line)
            if parsed:
                _add_to_ruleset(rs, parsed[0], parsed[1])
        return rs
    if kind == "local":
        import utils
        content = utils.read_local_file(target)
        if not content:
            print(f"    ⚠️ include:local 文件不存在或为空, 已跳过: {target}")
            return None
        rs = RuleSet(name=f"include:{target}", category="geosite")
        for line in content.splitlines():
            parsed = _clean_list_line(line)
            if parsed:
                _add_to_ruleset(rs, parsed[0], parsed[1])
        return rs
    print(f"    ⚠️ 未知 include 类型 '{kind}', 已跳过: {target}")
    return None


def apply_patches(rs: RuleSet, dat_map: Optional[Dict[str, RuleSet]] = None):
    """
    Apply local patches to a ruleset.
    Returns (ruleset, active_patch_count, upstream_included_domains, include_stats).
    include_stats: [(kind, target, merged_count), ...]
    """
    entries = load_patch_file(rs.name)
    if not entries:
        return rs, 0, [], []

    active = 0
    upstream_included = []
    include_stats = []

    for kind, a, b, _raw in entries:
        if kind == "rule":
            rtype, value = a, b
            if _ruleset_contains(rs, rtype, value):
                upstream_included.append(value)
                continue
            _add_to_ruleset(rs, rtype, value)
            active += 1
        elif kind == "include":
            src = _resolve_include(a, b, dat_map)
            if src is None:
                include_stats.append((a, b, 0))
                continue
            before = rs.total_count
            _merge_ruleset(src, rs)
            include_stats.append((a, b, rs.total_count - before))

    return rs, active, upstream_included, include_stats
