#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量 0-Diff 验证工具: 将本地生成的 sing-box 规则与天灵 sing-geosite 上游逐条语义比对。
修复:
1. 仅当本地补丁 (patches) 新增了父后缀、导致 sing-box 编译时吸收了上游子域时，才豁免被该补丁覆盖的 missing 条目
   (绝不用全量 loc_suffixes 豁免，防止掩盖真正的解析器退化 Bug);
2. 补丁条目统一经过 IDNA 归一。
"""

import argparse
import os
import sys
import json

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import utils
from core.cleaner import _domain_ancestors
from core.manager import TIANLING_GEOSITES
from core.patcher import load_patch_file

UPSTREAM_REPO = "sing-geosite"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "wuiiled_setup", "tianling_diff")
FIELDS = ("domain", "domain_suffix", "domain_keyword", "domain_regex")


def fetch_upstream_srs(tag: str, no_cache: bool = False) -> str:
    """实时拉取天灵官方上游最新 srs; 失败/离线时降级复用已有缓存保底。"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{tag}.srs")
    import urllib.request
    url = f"https://raw.githubusercontent.com/1715173329/{UPSTREAM_REPO}/rule-set/{tag}.srs"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Wuiiled-Diff/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        with open(cache_file, "wb") as f:
            f.write(data)
        return cache_file
    except Exception as e:
        bypass = no_cache or os.environ.get("WUIILED_NO_CACHE") == "1"
        if not bypass and os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
            print(f"  ⚠️ 下载上游 {tag}.srs 失败 ({e})，降级复用已有缓存")
            return cache_file
        print(f"  ⚠️ 下载上游 {tag}.srs 失败: {e}")
        return ""


def load_rule_fields(srs_path: str = "", json_path: str = "") -> dict:
    """读取规则字段: 优先给反编译好的 json，否则用 sing-box 反编译 srs。"""
    work_dir = utils.get_work_dir()
    if not json_path:
        json_path = os.path.join(work_dir, f"diff_{os.path.basename(srs_path)}.json")
        utils.decompile_srs(srs_path, json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    fields = {}
    for r in data.get("rules", []):
        for key in FIELDS:
            v = r.get(key)
            if isinstance(v, str):
                v = [v]
            if v:
                fields.setdefault(key, set()).update(v)
    return fields


def active_patch_entries(local_name: str) -> set:
    """当前仍生效的手动补丁条目 (含 IDNA 归一，用于从 local-only 差异中扣除)。"""
    entries = set()
    for kind, rtype, value, _raw in load_patch_file(local_name):
        if kind == "rule":
            entries.add(utils._idna_domain(value.lower().lstrip(".")))
    return entries


def active_patch_suffixes(local_name: str) -> set:
    """当前仍生效的 domain_suffix 补丁 (仅后缀补丁在编译期会吸收上游同名/子域名)。"""
    return {
        utils._idna_domain(value.lower().lstrip("."))
        for kind, rtype, value, _raw in load_patch_file(local_name)
        if kind == "rule" and rtype == "domain_suffix"
    }


def _is_covered_by_patch_suffixes(item: str, patches: set) -> bool:
    """检查上游条目是否被本地补丁 (patches) 中的父后缀所覆盖。"""
    clean = item.lstrip(".")
    return any(anc in patches for anc in _domain_ancestors(clean))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output/singbox")
    parser.add_argument("--fail-on-diff", action="store_true")
    parser.add_argument("--strict-extra", action="store_true",
                        help="额外 (本地比天灵镜像多) 也视为失败; 默认仅 missing 致命")
    parser.add_argument("--no-cache", action="store_true",
                        help="强制绕过本地缓存, 重新从天灵上游拉取最新 srs")
    args = parser.parse_args()

    geosite_dir = os.path.join(args.output, "geosite")
    if not os.path.isdir(geosite_dir):
        print(f"❌ 本地产物目录不存在: {geosite_dir} (请先构建)")
        return 1

    total_pairs = 0
    skipped_pairs = 0
    diff_pairs = []
    extra_only_pairs = []
    for upstream_tag, local_name in sorted(TIANLING_GEOSITES.items()):
        local_srs = os.path.join(geosite_dir, f"{local_name}.srs")
        if not os.path.exists(local_srs):
            print(f"  ⏭️  {local_name:<28} 本地未构建, 跳过")
            continue
        up_srs = fetch_upstream_srs(upstream_tag, no_cache=args.no_cache)
        if not up_srs:
            print(f"  ⚠️  {local_name:<28} 上游 srs 下载失败, 本轮跳过")
            skipped_pairs += 1
            continue
        total_pairs += 1

        up_fields = load_rule_fields(srs_path=up_srs)
        loc_fields = load_rule_fields(srs_path=local_srs)
        patches = active_patch_entries(local_name)
        patch_suffixes = active_patch_suffixes(local_name)

        set_diffs = []
        for key in FIELDS:
            up_set = {x.lower() for x in up_fields.get(key, set())}
            loc_set = {x.lower() for x in loc_fields.get(key, set())}
            missing = up_set - loc_set
            if missing and patch_suffixes and key in ("domain", "domain_suffix"):
                missing = {m for m in missing if not _is_covered_by_patch_suffixes(m, patch_suffixes)}
            extra = loc_set - up_set
            if patches:
                extra = {e for e in extra if e.lstrip(".") not in patches}
            if missing:
                set_diffs.append((key, "missing", sorted(missing)))
            if extra:
                set_diffs.append((key, "extra", sorted(extra)))

        missing_diffs = [d for d in set_diffs if d[1] == "missing"]
        extra_only = [d for d in set_diffs if d[1] != "missing"]
        if missing_diffs or (extra_only and args.strict_extra):
            fatal = missing_diffs + extra_only
            diff_pairs.append((local_name, fatal))
            detail = "; ".join(
                f"{k} {kind} {len(items)} 条 如{items[:3]}" for k, kind, items in fatal
            )
            print(f"  ❌ {local_name:<28} {detail}")
        elif extra_only:
            extra_only_pairs.append((local_name, extra_only))
            detail = "; ".join(
                f"{k} {kind} {len(items)} 条 如{items[:3]}" for k, kind, items in extra_only
            )
            print(f"  ⚠️  {local_name:<28} 仅额外 (上游发布滞后, 不拦截): {detail}")
        else:
            print(f"  ✅ {local_name:<28} 0-Diff")

    print(f"\n📊 比对完成: {total_pairs} 个集合, 0-Diff: {total_pairs - len(diff_pairs)}, 缺失差异: {len(diff_pairs)}, 仅额外(上游滞后): {len(extra_only_pairs)}, 跳过(上游下载失败): {skipped_pairs}")
    if diff_pairs and args.fail_on_diff:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
