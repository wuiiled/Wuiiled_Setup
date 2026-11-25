# -*- coding: utf-8 -*-
"""
README Generator for all distribution orphan branches.
Metadata lives in core/catalog.py; source provenance comes from manifest.json.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import providers
from core.catalog import (
    BRANCH_DESC_OVERRIDES,
    BRANCH_META,
    CATEGORY_DEFS,
    PLATFORM_MARKERS,
    RULE_METADATA,
)
from core.cleaner import domain_ancestors


def _rule_desc(target: str, bname: str) -> str:
    override = BRANCH_DESC_OVERRIDES.get((target, bname))
    if override:
        return override
    return RULE_METADATA.get(bname, {}).get("desc", bname)


def _match_marker_sets(marker: str, dom_set: Set[str], suf_set: Set[str]) -> bool:
    m = (marker or "").strip().lower().lstrip(".")
    if not m:
        return False
    return m in dom_set or any(anc in suf_set for anc in domain_ancestors(m))


def marker_in_ruleset(marker: str, rs) -> bool:
    dom_set = {d.lower() for d in rs.domains}
    suf_set = {s.lstrip(".").lower() for s in rs.domain_suffixes if s.lstrip(".")}
    return _match_marker_sets(marker, dom_set, suf_set)


def compute_markers(rs) -> List[str]:
    if getattr(rs, "category", "") == "geoip":
        return []
    dom_set = {d.lower() for d in rs.domains}
    suf_set = {s.lstrip(".").lower() for s in rs.domain_suffixes if s.lstrip(".")}
    hits = []
    for plat, marks in PLATFORM_MARKERS.items():
        n = sum(1 for mk in marks if _match_marker_sets(mk, dom_set, suf_set))
        if n:
            hits.append((n, plat))
    hits.sort(key=lambda t: -t[0])
    return [plat for _n, plat in hits]


def build_manifest(all_rules, exclude: Set[str] = frozenset()) -> Dict[str, dict]:
    """Serialize per-ruleset provenance & verified markers (optionally excluding branch-only extras)."""
    out: Dict[str, dict] = {}
    for name, rs in all_rules.items():
        if name in exclude:
            continue
        out[name] = {
            "kind": getattr(rs, "source_kind", ""),
            "dat_code": getattr(rs, "dat_code", ""),
            "sources": list(getattr(rs, "sources", []) or []),
            "markers": compute_markers(rs),
            "count": rs.total_count,
        }
    return out


def write_manifest(all_rules, output_base_dir: str = "output") -> str:
    os.makedirs(output_base_dir, exist_ok=True)
    path = os.path.join(output_base_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(build_manifest(all_rules), f, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"  🗂️ [manifest] 来源画像已写入 {path}")
    return path


def _load_manifest(output_base_dir: str) -> Dict[str, dict]:
    path = os.path.join(output_base_dir, "manifest.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _manifest_note(entry: dict) -> str:
    kind = entry.get("kind", "")
    sources = entry.get("sources") or []
    if kind == "dat":
        parts = [f"dat 分类 {entry.get('dat_code', '')}"]
        markers = entry.get("markers") or []
        if markers:
            head = markers[:6]
            tail = f" 等 {len(markers)} 项" if len(markers) > 6 else ""
            parts.append("含 " + " / ".join(head) + tail)
        return " · ".join(parts)
    if kind == "recipe":
        return "配方合成: " + " ∪ ".join(sources) if sources else ""
    if kind in ("self", "skk", "geoip-srs", "geoip-mmdb"):
        return "上游: " + " · ".join(sources) if sources else ""
    if kind == "custom":
        return f"用户本地规则: {sources[0]}" if sources else ""
    return ""


_REVERSE_DAT: Optional[Dict[str, str]] = None


def _fallback_dat_code(bname: str) -> str:
    global _REVERSE_DAT
    if _REVERSE_DAT is None:
        try:
            from core.loaders.geo import TIANLING_GEOSITES
            _REVERSE_DAT = {out: up[len("geosite-"):] for up, out in TIANLING_GEOSITES.items()}
        except Exception:
            _REVERSE_DAT = {}
    return _REVERSE_DAT.get(bname, "")


def _render_note(bname: str, manifest: Dict[str, dict]) -> str:
    entry = manifest.get(bname)
    if entry:
        note = _manifest_note(entry)
        if note:
            return note
    meta = RULE_METADATA.get(bname, {})
    if meta.get("note"):
        return meta["note"]
    code = _fallback_dat_code(bname)
    return f"dat 分类 {code}" if code else "-"


def count_file_rules(file_path: str) -> int:
    if not os.path.exists(file_path):
        return 0
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".json":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            total = 0
            for r in data.get("rules", []):
                for val in r.values():
                    if isinstance(val, list):
                        total += len(val)
                    elif isinstance(val, str):
                        total += 1
            return total
        except Exception:
            return 0
    elif ext in (".txt", ".conf", ".list"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return sum(1 for line in f if line.strip() and not line.strip().startswith("#"))
        except Exception:
            return 0
    return 0


def _oxidns_alias_basenames() -> Set[str]:
    return {os.path.splitext(os.path.basename(k))[0] for k in providers.OXIDNS_SUBDIR_ALIASES}


def _total_rules(target_dir: str) -> Tuple[int, int]:
    total_items = 0
    distinct_rules = set()
    alias_names = _oxidns_alias_basenames()

    for sub in ("geosite", "geoip"):
        d = os.path.join(target_dir, sub)
        if os.path.isdir(d):
            seen = set()
            for f in os.listdir(d):
                base = os.path.splitext(f)[0]
                if base in seen or base in alias_names:
                    continue
                seen.add(base)
                distinct_rules.add(base)
                for ext in (".json", ".txt", ".conf", ".list"):
                    cand = os.path.join(d, base + ext)
                    if os.path.exists(cand):
                        total_items += count_file_rules(cand)
                        break

    for f in os.listdir(target_dir):
        p = os.path.join(target_dir, f)
        if os.path.isfile(p) and f != "README.md":
            base = os.path.splitext(f)[0]
            distinct_rules.add(base)
            total_items += count_file_rules(p)

    return total_items, len(distinct_rules)


def _client_example_lines(target: str, repo: str) -> List[str]:
    examples = {
        "singbox": (
            "🛠️ Sing-box 配置示例",
            "在 `config.json` 的 `route.rule_set` 中配置远程规则集。将下方 `{tag}` 替换为表格中的规则名（推荐优先使用高效的二进制 `.srs`）：",
            "json",
            '{\n  "tag": "{tag}",\n  "type": "remote",\n  "format": "binary",\n  "url": "'
            + f"https://raw.githubusercontent.com/{repo}/singbox/rules/geosite/{{tag}}.srs"
            + '",\n  "download_detour": "direct"\n}',
        ),
        "mihomo": (
            "🛠️ Mihomo (Clash Meta) 配置示例",
            "在配置文件的 `rule-providers` 中配置规则提供者（推荐优先使用高性能的 `.mrs`）：",
            "yaml",
            "rule-providers:\n  geosite-ad:\n    type: http\n    behavior: domain\n    format: mrs\n"
            f'    url: "https://raw.githubusercontent.com/{repo}/mihomo/rules/geosite/geosite-ad.mrs"\n'
            "    path: ./ruleset/geosite-ad.mrs\n    interval: 86400",
        ),
        "smartdns": (
            "🛠️ OxiDNS / MosDNS 配置示例",
            "规则文件为 OxiDNS/MosDNS 兼容语法（注意：本分支产出适配 OxiDNS 的裸域名后缀 + `full:` 精确 + `keyword:`/`regexp:` 规则，非传统 SmartDNS 语法）。在 `domain_set` 插件中引用：",
            "yaml",
            '  - tag: provider_cn_domains\n    type: domain_set\n    args:\n      files:\n        - "/etc/oxidns/rules/geosite-cn.txt"',
        ),
        "mosdns-x": (
            "🛠️ MosDNS 配置示例",
            "在 `config.yaml` 的插件配置中引入规则集：",
            "yaml",
            'plugins:\n  - tag: site_cn\n    type: domain_set\n    args:\n      files:\n        - "/etc/mosdns/rules/geosite-cn.txt"',
        ),
    }
    if target == "adg":
        return [
            "<details>",
            "<summary><b>🛠️ AdGuard Home 配置示例</b>（点击展开）</summary>",
            "",
            "在 **过滤器** -> **DNS 封锁清单** 中添加自定义订阅链接，直接粘贴下方表格中的订阅直链。",
            "",
            "</details>",
            "",
        ]
    spec = examples.get(target)
    if not spec:
        return []
    summary, intro, lang, code = spec
    return [
        "<details>",
        f"<summary><b>{summary}</b>（点击展开）</summary>",
        "",
        intro,
        "",
        f"```{lang}",
        code,
        "```",
        "",
        "</details>",
        "",
    ]


def generate_branch_readme(target: str, output_base_dir: str, repo: str = "wuiiled/Wuiiled_Setup") -> None:
    """Generate README.md in output/<target>/README.md."""
    target_dir = os.path.join(output_base_dir, target)
    if not os.path.exists(target_dir):
        return

    emoji, title, fmt_badge = BRANCH_META.get(target, ("📦", target, ""))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_items, total_sets = _total_rules(target_dir)
    manifest = _load_manifest(output_base_dir)

    lines = [
        '<div align="center">',
        "",
        f"# {emoji} {title} 规则订阅",
        "",
        f'![规则总数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E6%80%BB%E6%95%B0-{total_items:,}-blue)',
        f'![规则集数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E9%9B%86%E6%95%B0-{total_sets}-success)',
        f'![格式](https://img.shields.io/badge/%E6%A0%BC%E5%BC%8F-{fmt_badge.replace(" ", "%20").replace("/", "%2F")}-informational)',
    ]
    if target == "singbox":
        lines.append('![0--Diff对齐](https://img.shields.io/badge/0--Diff-%E7%99%BE%E5%88%86%E7%99%BE%E5%AF%B9%E9%BD%90-brightgreen)')
    lines.extend([
        "",
        f'<i>由 <a href="https://github.com/{repo}">Wuiiled_Setup</a> 规则自动化引擎实时构建分发</i><br>',
        f'<sub>🕐 最后更新：{now_str} (Asia/Shanghai)</sub>',
        "",
        "</div>",
        "",
        "---",
        "",
        "## 💡 如何使用",
        "",
        "在下方分类表格中 **右键点击** 对应链接，选择 **复制链接地址**，填入客户端订阅即可。",
        "",
    ])
    lines.extend(_client_example_lines(target, repo))

    geosite_dir = os.path.join(target_dir, "geosite")
    geoip_dir = os.path.join(target_dir, "geoip")
    alias = _oxidns_alias_basenames()
    available_geosites = (
        {os.path.splitext(f)[0] for f in os.listdir(geosite_dir) if os.path.splitext(f)[0] not in alias}
        if os.path.exists(geosite_dir) else set()
    )
    available_geoips = (
        {os.path.splitext(f)[0] for f in os.listdir(geoip_dir)}
        if os.path.exists(geoip_dir) else set()
    )
    root_files = {
        os.path.splitext(f)[0]: f
        for f in os.listdir(target_dir)
        if os.path.isfile(os.path.join(target_dir, f)) and f != "README.md"
    }

    lines.extend(["## 📑 规则分类快速导航", ""])
    nav_links = [
        f"[{cat_title.split(' ')[0]}](#{cat_id})"
        for cat_id, cat_title, rule_names in CATEGORY_DEFS
        if any(r in available_geosites or r in available_geoips or r in root_files for r in rule_names)
    ]
    lines.extend([" · ".join(nav_links), "", "---", ""])

    rendered_rules: Set[str] = set()
    for cat_id, cat_title, rule_names in CATEGORY_DEFS:
        cat_items = []
        for rname in rule_names:
            if rname in available_geosites:
                cat_items.append((rname, "geosite", os.path.join(geosite_dir, rname)))
            elif rname in available_geoips:
                cat_items.append((rname, "geoip", os.path.join(geoip_dir, rname)))
            elif rname in root_files:
                cat_items.append((rname, "root", os.path.join(target_dir, root_files[rname])))
        if not cat_items:
            continue

        lines.extend([f'<span id="{cat_id}"></span>', "", f"### {cat_title}", ""])

        if target == "singbox":
            lines.extend([
                "| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | 源码 (JSON/TXT) |",
                "| :--- | :--- | :--- | ---: | :---: | :---: |",
            ])
            for bname, location, file_prefix in cat_items:
                rendered_rules.add(bname)
                json_p, srs_p, txt_p = file_prefix + ".json", file_prefix + ".srs", file_prefix + ".txt"
                rel_dir = "geosite" if location == "geosite" else "geoip"
                base_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_dir}/{bname}"
                srs_link = f"[📥 SRS]({base_url}.srs)" if os.path.exists(srs_p) else "-"
                if os.path.exists(json_p):
                    count = count_file_rules(json_p)
                    src_link = f"[📄 JSON]({base_url}.json)"
                elif os.path.exists(txt_p):
                    count = count_file_rules(txt_p)
                    src_link = f"[📄 TXT]({base_url}.txt)"
                else:
                    count, src_link = 0, "-"
                note = _render_note(bname, manifest)
                if bname == "geosite-stream":
                    # geosite-stream on singbox is composite (includes geoip-stream CIDRs)
                    note = note + " · 含流媒体 IP (sing-box 复合)" if note and note != "-" else "-"
                count_str = f"{count:,}" if count > 0 else "-"
                lines.append(f"| **`{bname}`** | {_rule_desc(target, bname)} | {note} | `{count_str}` | {srs_link} | {src_link} |")
            lines.append("")

        elif target == "mihomo":
            lines.extend([
                "| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |",
                "| :--- | :--- | :--- | ---: | :---: | :---: |",
            ])
            for bname, location, file_prefix in cat_items:
                rendered_rules.add(bname)
                txt_p, mrs_p = file_prefix + ".txt", file_prefix + ".mrs"
                count = count_file_rules(txt_p)
                count_str = f"{count:,}" if count > 0 else "-"
                rel_dir = "geosite" if location == "geosite" else "geoip"
                base_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_dir}/{bname}"
                mrs_link = f"[📥 MRS]({base_url}.mrs)" if os.path.exists(mrs_p) else "-"
                txt_link = f"[📄 TXT]({base_url}.txt)" if os.path.exists(txt_p) else "-"
                lines.append(f"| **`{bname}`** | {_rule_desc(target, bname)} | {_render_note(bname, manifest)} | `{count_str}` | {mrs_link} | {txt_link} |")
            lines.append("")

        else:
            lines.extend([
                "| 规则名称 | 描述 | 条数 | 订阅链接 |",
                "| :--- | :--- | ---: | :---: |",
            ])
            for bname, location, file_prefix in cat_items:
                rendered_rules.add(bname)
                txt_p = file_prefix if location == "root" else file_prefix + ".txt"
                count = count_file_rules(txt_p)
                count_str = f"{count:,}" if count > 0 else "-"
                if location == "root":
                    url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{os.path.basename(txt_p)}"
                else:
                    rel_dir = "geosite" if location == "geosite" else "geoip"
                    url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_dir}/{bname}.txt"
                lines.append(f"| **`{bname}`** | {_rule_desc(target, bname)} | `{count_str}` | [📥 直链]({url}) |")
            lines.append("")

    remaining_geosites = sorted(available_geosites - rendered_rules)
    remaining_geoips = sorted(available_geoips - rendered_rules)
    remaining_roots = sorted(set(root_files.keys()) - rendered_rules)
    if remaining_geosites or remaining_geoips or remaining_roots:
        lines.extend(["### 📌 其他规则集", "", "| 规则文件 | 条数 | 订阅 |", "| :--- | ---: | :---: |"])
        ext = ".srs" if target == "singbox" else (".mrs" if target == "mihomo" else ".txt")
        for sub, bnames in (("geosite", remaining_geosites), ("geoip", remaining_geoips)):
            sub_dir = geosite_dir if sub == "geosite" else geoip_dir
            for bname in bnames:
                p = os.path.join(sub_dir, f"{bname}.txt")
                if not os.path.exists(p):
                    p = os.path.join(sub_dir, f"{bname}.json")
                count = count_file_rules(p)
                url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{sub}/{bname}{ext}"
                lines.append(f"| **`{bname}`** | `{count:,}` | [📥 直链]({url}) |" if count > 0 else f"| **`{bname}`** | `-` | [📥 直链]({url}) |")
        for bname in remaining_roots:
            count = count_file_rules(os.path.join(target_dir, root_files[bname]))
            url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{root_files[bname]}"
            lines.append(f"| **`{root_files[bname]}`** | `{count:,}` | [📥 直链]({url}) |" if count > 0 else f"| **`{root_files[bname]}`** | `-` | [📥 直链]({url}) |")
        lines.append("")

    lines.extend([
        "---", "",
        '<div align="center">', "",
        f'[🏠 返回主仓库](https://github.com/{repo}) · [⭐ Star 支持](https://github.com/{repo})',
        "", "</div>",
    ])
    with open(os.path.join(target_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  📄 [README] 为分支 {target:<10} 成功生成订阅导航 (包含 {total_sets} 个规则集, 共 {total_items:,} 条规则)")


def generate_all_readmes(output_base_dir: str = "output", repo: str = "wuiiled/Wuiiled_Setup") -> None:
    print("\n📝 正在生成全平台订阅导航文档 (README.md)...")
    for target in providers.TARGET_BRANCHES:
        generate_branch_readme(target, output_base_dir, repo)
