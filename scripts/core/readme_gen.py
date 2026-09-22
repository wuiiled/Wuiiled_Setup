# -*- coding: utf-8 -*-
"""
Intelligent README Generator for All Distribution Branches.
Generates beautiful, compact, dual-format tables and copy-paste client configurations.
Completely replaces the fragile inline Bash script in GitHub Actions.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple


NL = chr(10)


# Branch display metadata: (emoji, title, format badge text, primary format)
_BRANCH_META = {
    "singbox":  ("📦", "Sing-box",  ".srs / .json",  "binary"),
    "mihomo":   ("📦", "Mihomo (Clash Meta)", ".mrs / .txt", "mrs"),
    "smartdns": ("📦", "SmartDNS",  "domain-set / ip-set", "txt"),
    "mosdns-x": ("📦", "MosDNS-X",  "domain: / full:", "txt"),
    "adg":      ("📦", "AdGuard Home", "AdGuard filter", "txt"),
}


def count_file_rules(file_path: str) -> int:
    """Accurately count rules inside a .json, .txt, or other format file."""
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
            count = 0
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        count += 1
            return count
        except Exception:
            return 0
    return 0


def _total_rules(target_dir: str) -> int:
    """Sum rule counts across geosite/geoip subdirs and root rule files."""
    total = 0
    for sub in ("geosite", "geoip"):
        d = os.path.join(target_dir, sub)
        if os.path.isdir(d):
            seen = set()
            for f in os.listdir(d):
                base = os.path.splitext(f)[0]
                if base in seen:
                    continue
                seen.add(base)
                # prefer .json (singbox), then .txt; skip binaries (.srs/.mrs)
                cand = None
                for ext in (".json", ".txt", ".conf", ".list"):
                    c2 = os.path.join(d, base + ext)
                    if os.path.exists(c2):
                        cand = c2
                        break
                if cand is not None:
                    total += count_file_rules(cand)
    for f in os.listdir(target_dir):
        p = os.path.join(target_dir, f)
        if os.path.isfile(p) and f != "README.md":
            total += count_file_rules(p)
    return total


def generate_branch_readme(target: str, output_base_dir: str, repo: str = "wuiiled/Wuiiled_Setup"):
    """Generate README.md in output/<target>/README.md with unified, compact tables."""
    target_dir = os.path.join(output_base_dir, target)
    if not os.path.exists(target_dir):
        return

    emoji, title, fmt_badge, _ = _BRANCH_META.get(target, ("📦", target, "", "txt"))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = _total_rules(target_dir)

    lines = []
    lines.append('<div align="center">')
    lines.append("")
    lines.append(f"# {emoji} {title} 规则订阅")
    lines.append("")
    lines.append(f'![规则总数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E6%80%BB%E6%95%B0-{total}-blue)')
    lines.append(f'![格式](https://img.shields.io/badge/%E6%A0%BC%E5%BC%8F-{fmt_badge.replace(" ", "%20").replace("/", "%2F")}-informational)')

    lines.append("")
    lines.append('<i>由 <a href="https://github.com/' + repo + '">Wuiiled_Setup</a> 规则自动化引擎实时构建分发</i><br>')
    lines.append(f'<sub>🕐 最后更新：{now_str} (Asia/Shanghai)</sub>')
    lines.append("")
    lines.append("</div>")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 💡 如何使用")
    lines.append("")
    lines.append("在下方表格中 **右键点击** 对应链接，选择 **复制链接地址**，填入客户端订阅即可。")
    lines.append("")

    # Client configuration examples
    if target == "singbox":
        lines.append('<details>')
        lines.append('<summary><b>🛠️ Sing-box 配置示例</b>（点击展开）</summary>')
        lines.append("")
        lines.append("在 `config.json` 的 `route.rule_set` 中配置远程规则集。将下方 `{tag}` 替换为表格中的规则名（推荐优先使用高效的二进制 `.srs`）：")
        lines.append("")
        lines.append("```json")
        lines.append('{\n  "tag": "{tag}",\n  "type": "remote",\n  "format": "binary",\n  "url": "' + f"https://raw.githubusercontent.com/{repo}/singbox/rules/geosite/{{tag}}.srs" + '",\n  "download_detour": "direct"\n}')
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    elif target == "mihomo":
        lines.append('<details>')
        lines.append('<summary><b>🛠️ Mihomo 配置示例</b>（点击展开）</summary>')
        lines.append("")
        lines.append("在配置文件的 `rule-providers` 中配置规则提供者（推荐优先使用高性能的 `.mrs`）：")
        lines.append("")
        lines.append("```yaml")
        lines.append("rule-providers:")
        lines.append("  geosite-ad:")
        lines.append("    type: http")
        lines.append("    behavior: domain")
        lines.append("    format: mrs")
        lines.append(f'    url: "https://raw.githubusercontent.com/{repo}/mihomo/rules/geosite/geosite-ad.mrs"')
        lines.append("    path: ./ruleset/geosite-ad.mrs")
        lines.append("    interval: 86400")
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    elif target == "smartdns":
        lines.append('<details>')
        lines.append('<summary><b>🛠️ SmartDNS 配置示例</b>（点击展开）</summary>')
        lines.append("")
        lines.append("在 `smartdns.conf` 中引入规则集文件：")
        lines.append("")
        lines.append("```conf")
        lines.append("domain-set -name geosite-cn -file /etc/smartdns/rules/geosite-cn.txt")
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    geosite_dir = os.path.join(target_dir, "geosite")
    geoip_dir = os.path.join(target_dir, "geoip")

    def _render_dual_table(category_name: str, sub_dir: str, rel_sub: str):
        if not os.path.exists(sub_dir):
            return
        files = sorted(os.listdir(sub_dir))
        if not files:
            return
        base_names = sorted(list(set(os.path.splitext(f)[0] for f in files)))

        if target == "singbox":
            lines.append(f"## 🌐 {category_name}")
            lines.append("")
            lines.append("| 规则名称 | 条数 | SRS | JSON |")
            lines.append("| :--- | ---: | :---: | :---: |")
            for bname in base_names:
                json_p = os.path.join(sub_dir, f"{bname}.json")
                srs_p = os.path.join(sub_dir, f"{bname}.srs")
                count = count_file_rules(json_p)
                count_str = f"{count:,}" if count > 0 else "-"
                srs_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_sub}/{bname}.srs"
                json_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_sub}/{bname}.json"
                srs_link = f"[📥 SRS]({srs_url})" if os.path.exists(srs_p) else "-"
                json_link = f"[📄 JSON]({json_url})" if os.path.exists(json_p) else "-"
                lines.append(f"| **`{bname}`** | `{count_str}` | {srs_link} | {json_link} |")
            lines.append("")
        elif target == "mihomo":
            lines.append(f"## 🌐 {category_name}")
            lines.append("")
            lines.append("| 规则名称 | 条数 | MRS | TXT |")
            lines.append("| :--- | ---: | :---: | :---: |")
            for bname in base_names:
                txt_p = os.path.join(sub_dir, f"{bname}.txt")
                mrs_p = os.path.join(sub_dir, f"{bname}.mrs")
                count = count_file_rules(txt_p)
                count_str = f"{count:,}" if count > 0 else "-"
                mrs_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_sub}/{bname}.mrs"
                txt_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_sub}/{bname}.txt"
                mrs_link = f"[📥 MRS]({mrs_url})" if os.path.exists(mrs_p) else "-"
                txt_link = f"[📄 TXT]({txt_url})" if os.path.exists(txt_p) else "-"
                lines.append(f"| **`{bname}`** | `{count_str}` | {mrs_link} | {txt_link} |")
            lines.append("")
        else:
            lines.append(f"## 🌐 {category_name}")
            lines.append("")
            lines.append("| 规则文件 | 条数 | 订阅 |")
            lines.append("| :--- | ---: | :---: |")
            # 每个文件本身就是完整规则文件, 直接 O(N) 遍历即可
            for f in files:
                txt_p = os.path.join(sub_dir, f)
                count = count_file_rules(txt_p)
                count_str = f"{count:,}" if count > 0 else "-"
                url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_sub}/{f}"
                lines.append(f"| **`{f}`** | `{count_str}` | [📥 直链]({url}) |")
            lines.append("")

    _render_dual_table("GeoSite 域名规则集", geosite_dir, "geosite")
    _render_dual_table("GeoIP 地址规则集", geoip_dir, "geoip")

    root_files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f)) and f != "README.md"]
    if root_files:
        lines.append("## 📌 独立规则集")
        lines.append("")
        lines.append("| 规则文件 | 条数 | 订阅 |")
        lines.append("| :--- | ---: | :---: |")
        for f in sorted(root_files):
            p = os.path.join(target_dir, f)
            count = count_file_rules(p)
            count_str = f"{count:,}" if count > 0 else "-"
            url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{f}"
            lines.append(f"| **`{f}`** | `{count_str}` | [📥 直链]({url}) |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append('<div align="center">')
    lines.append("")
    lines.append(f'[🏠 返回主仓库](https://github.com/{repo}) · [⭐ Star](https://github.com/{repo})')
    lines.append("")
    lines.append("</div>")

    readme_path = os.path.join(target_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(NL.join(lines) + NL)
    print(f"  📄 [README] 为分支 {target:<10} 成功生成订阅导航")


def generate_all_readmes(output_base_dir: str = "output", repo: str = "wuiiled/Wuiiled_Setup"):
    """Generate README.md for all 5 platform outputs."""
    print("\n📝 正在生成全平台订阅导航文档 (README.md)...")
    for target in ("singbox", "mihomo", "smartdns", "mosdns-x", "adg"):
        generate_branch_readme(target, output_base_dir, repo)
