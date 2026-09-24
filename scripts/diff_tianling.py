#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量 0-Diff 验证工具: 将本地生成的 sing-box 规则与天灵 sing-geosite 上游逐条语义比对。

对 core.manager.TIANLING_GEOSITES 中的每个集合:
  1. 下载天灵 rule-set 分支的预编译 srs (本地缓存)
  2. sing-box 反编译为 JSON
  3. 与本地 output/singbox 产物 (优先直接读构建时生成的 .json) 按
     domain / domain_suffix / domain_keyword / domain_regex 四个字段做集合差
  4. 本地多出的条目会先扣除 rules/patches/ 中仍生效的本地补丁

用法:
  PYTHONPATH=scripts python scripts/diff_tianling.py [--output output/singbox] [--fail-on-diff]
退出码: 有差异且 --fail-on-diff 时为 1, 否则 0。
"""

import argparse
import os
import sys
import json
import subprocess

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import utils
from core.manager import TIANLING_GEOSITES
from core.patcher import load_patch_file

UPSTREAM_REPO = "sing-geosite"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "wuiiled_setup", "tianling_diff")
FIELDS = ("domain", "domain_suffix", "domain_keyword", "domain_regex")


def fetch_upstream_srs(tag: str) -> str:
    """下载(或读取缓存)天灵上游 srs, 返回本地文件路径; 失败返回空串。"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{tag}.srs")
    if os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
        return cache_file
    import urllib.request
    url = f"https://raw.githubusercontent.com/1715173329/{UPSTREAM_REPO}/rule-set/{tag}.srs"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()
        with open(cache_file, "wb") as f:
            f.write(data)
        return cache_file
    except Exception as e:
        print(f"  ⚠️ 下载上游 {tag}.srs 失败: {e}")
        return ""


def load_rule_fields(srs_path: str = "", json_path: str = "") -> dict:
    """读取规则字段: 优先给反编译好的 json, 否则用 sing-box 反编译 srs。"""
    work_dir = utils.get_work_dir()
    if not json_path:
        json_path = os.path.join(work_dir, f"diff_{os.path.basename(srs_path)}.json")
        cmd = utils._resolve_cmd(["sing-box", "rule-set", "decompile", srs_path, "-o", json_path])
        subprocess.run(cmd, check=True, capture_output=True, text=True)
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
    """当前仍生效的手动补丁条目 (用于从 local-only 差异中扣除)。"""
    entries = set()
    for kind, rtype, value, _raw in load_patch_file(local_name):
        if kind == "rule":
            entries.add(value.lower().lstrip("."))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output/singbox")
    parser.add_argument("--fail-on-diff", action="store_true")
    args = parser.parse_args()

    geosite_dir = os.path.join(args.output, "geosite")
    if not os.path.isdir(geosite_dir):
        print(f"❌ 本地产物目录不存在: {geosite_dir} (请先构建)")
        return 1

    total_pairs = 0
    diff_pairs = []
    for upstream_tag, local_name in sorted(TIANLING_GEOSITES.items()):
        local_srs = os.path.join(geosite_dir, f"{local_name}.srs")
        local_json = os.path.join(geosite_dir, f"{local_name}.json")
        if not os.path.exists(local_srs):
            print(f"  ⏭️  {local_name:<28} 本地未构建, 跳过")
            continue
        up_srs = fetch_upstream_srs(upstream_tag)
        if not up_srs:
            diff_pairs.append((local_name, [("下载失败", "", "")]))
            continue
        total_pairs += 1

        up_fields = load_rule_fields(srs_path=up_srs)
        # 必须反编译本地 .srs 而非读构建时的 .json: 后者是编译前源码,
        # sing-box 编译时会做覆盖去重, 用 .json 比对会产生假差异
        loc_fields = load_rule_fields(srs_path=local_srs)
        patches = active_patch_entries(local_name)

        set_diffs = []
        for key in FIELDS:
            up_set = {x.lower() for x in up_fields.get(key, set())}
            loc_set = {x.lower() for x in loc_fields.get(key, set())}
            missing = up_set - loc_set
            extra = loc_set - up_set
            if patches:
                extra = {e for e in extra if e not in patches}
            if missing:
                set_diffs.append((key, "missing", sorted(missing)))
            if extra:
                set_diffs.append((key, "extra", sorted(extra)))

        if set_diffs:
            diff_pairs.append((local_name, set_diffs))
            detail = "; ".join(
                f"{k} {kind} {len(items)} 条 如{items[:3]}" for k, kind, items in set_diffs
            )
            print(f"  ❌ {local_name:<28} {detail}")
        else:
            print(f"  ✅ {local_name:<28} 0-Diff")

    print(f"\n📊 比对完成: {total_pairs} 个集合, 0-Diff: {total_pairs - len(diff_pairs)}, 有差异: {len(diff_pairs)}")
    if diff_pairs and args.fail_on_diff:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
