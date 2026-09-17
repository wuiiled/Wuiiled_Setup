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


def count_file_rules(file_path: str) -> int:
    """Accurately count rules inside a .json, .txt, or other format file."""
    if not os.path.exists(file_path):
        return 0
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".json":
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        count += 1
            return count
        except Exception:
            return 0
    return 0


def generate_branch_readme(target: str, output_base_dir: str, repo: str = "wuiiled/Wuiiled_Setup"):
    """
    Generate README.md in output/<target>/README.md with unified, compact tables.
    """
    target_dir = os.path.join(output_base_dir, target)
    if not os.path.exists(target_dir):
        return

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []

    lines.append('<div align="center">')
    lines.append("")
    lines.append(f"# 📦 {target} 规则订阅导航")
    lines.append("")
    lines.append(f"<i>由 Wuiiled_Setup 规则自动化构建引擎实时构建分发</i><br>")
    lines.append(f"<i>最后更新时间：{now_str} (Asia/Shanghai)</i>")
    lines.append("</div>")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 💡 如何使用")
    lines.append("在下方表格中，**右键点击**对应规则链接，选择 **“复制链接地址”** 填入客户端订阅即可。")
    lines.append("")

    # Add client configuration examples
    if target == "singbox":
        lines.append("### 🛠️ Sing-box 客户端配置示例")
        lines.append("在 `config.json` 的 `route.rule_set` 中配置远程规则集（推荐优先使用高效的二进制 `.srs`）：")
        lines.append("```json")
        lines.append('{\n  "tag": "geosite-cn",\n  "type": "remote",\n  "format": "binary",\n  "url": "' + f"https://raw.githubusercontent.com/{repo}/singbox/rules/geosite/geosite-cn.srs" + '",\n  "download_detour": "direct"\n}')
        lines.append("```")
        lines.append("")
    elif target == "mihomo":
        lines.append("### 🛠️ Mihomo (Clash Meta) 客户端配置示例")
        lines.append("在配置文件的 `rule-providers` 中配置规则提供者（推荐优先使用高性能的 `.mrs`）：")
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
    elif target == "smartdns":
        lines.append("### 🛠️ SmartDNS 客户端配置示例")
        lines.append("在 `smartdns.conf` 中引入规则集文件：")
        lines.append("```conf")
        lines.append("domain-set -name geosite-cn -file /etc/smartdns/rules/geosite-cn.txt")
        lines.append("```")
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
            lines.append(f"### 🌐 {category_name} 规则集")
            lines.append("| 🗂️ 规则名称 (Tag) | 🔢 条数 | ⚡️ 二进制订阅 (.srs) | 📄 明文规则 (.json) |")
            lines.append("| :--- | :---: | :---: | :---: |")
            for bname in base_names:
                json_p = os.path.join(sub_dir, f"{bname}.json")
                srs_p = os.path.join(sub_dir, f"{bname}.srs")
                count = count_file_rules(json_p)
                count_str = f"{count:,}" if count > 0 else "-"
                srs_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_sub}/{bname}.srs"
                json_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_sub}/{bname}.json"
                srs_link = f"[👉 复制 SRS 直链]({srs_url})" if os.path.exists(srs_p) else "-"
                json_link = f"[👉 查看 JSON]({json_url})" if os.path.exists(json_p) else "-"
                lines.append(f"| **`{bname}`** | <kbd>{count_str}</kbd> | {srs_link} | {json_link} |")
            lines.append("")

        elif target == "mihomo":
            lines.append(f"### 🌐 {category_name} 规则集")
            lines.append("| 🗂️ 规则名称 (Rule) | 🔢 条数 | ⚡️ 高性能二进制 (.mrs) | 📄 纯文本 (.txt) |")
            lines.append("| :--- | :---: | :---: | :---: |")
            for bname in base_names:
                txt_p = os.path.join(sub_dir, f"{bname}.txt")
                mrs_p = os.path.join(sub_dir, f"{bname}.mrs")
                count = count_file_rules(txt_p)
                count_str = f"{count:,}" if count > 0 else "-"
                mrs_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_sub}/{bname}.mrs"
                txt_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_sub}/{bname}.txt"
                mrs_link = f"[👉 复制 MRS 直链]({mrs_url})" if os.path.exists(mrs_p) else "-"
                txt_link = f"[👉 查看 TXT]({txt_url})" if os.path.exists(txt_p) else "-"
                lines.append(f"| **`{bname}`** | <kbd>{count_str}</kbd> | {mrs_link} | {txt_link} |")
            lines.append("")

        else:
            lines.append(f"### 🌐 {category_name} 规则集")
            lines.append("| 🗂️ 规则名称 (Rule) | 🔢 条数 | 🔗 订阅链接 (右键复制) |")
            lines.append("| :--- | :---: | :---: |")
            for bname in base_names:
                for f in files:
                    if f.startswith(bname + "."):
                        txt_p = os.path.join(sub_dir, f)
                        count = count_file_rules(txt_p)
                        count_str = f"{count:,}" if count > 0 else "-"
                        url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_sub}/{f}"
                        lines.append(f"| **`{f}`** | <kbd>{count_str}</kbd> | [👉 获取直链]({url}) |")
            lines.append("")

    # Render GeoSite table
    _render_dual_table("GeoSite 域名", geosite_dir, "geosite")
    # Render GeoIP table
    _render_dual_table("GeoIP 地址", geoip_dir, "geoip")

    # Render root files (if any for adg)
    root_files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f)) and f != "README.md"]
    if root_files:
        lines.append("### 📌 独立规则集")
        lines.append("| 🗂️ 规则名称 (Rule) | 🔢 条数 | 🔗 订阅链接 (右键复制) |")
        lines.append("| :--- | :---: | :---: |")
        for f in sorted(root_files):
            p = os.path.join(target_dir, f)
            count = count_file_rules(p)
            count_str = f"{count:,}" if count > 0 else "-"
            url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{f}"
            lines.append(f"| **`{f}`** | <kbd>{count_str}</kbd> | [👉 获取直链]({url}) |")
        lines.append("")

    readme_path = os.path.join(target_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  📄 [README] 为分支 {target:<10} 成功生成订阅导航")


def generate_all_readmes(output_base_dir: str = "output", repo: str = "wuiiled/Wuiiled_Setup"):
    """Generate README.md for all 5 platform outputs."""
    print("\n📝 正在生成全平台订阅导航文档 (README.md)...")
    for target in ("singbox", "mihomo", "smartdns", "mosdns-x", "adg"):
        generate_branch_readme(target, output_base_dir, repo)
