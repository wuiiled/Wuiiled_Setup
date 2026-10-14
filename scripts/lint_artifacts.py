#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产物语法门禁: 校验 output/<branch> 下每个规则文件的行语法与该分支消费端解析器一致。
- 域名校验复用 core.cleaner.is_valid_domain (geosite 允许单标签 TLD 如 cn/lan/xn--fiqs8s,
  adg/singbox 广告过滤要求带点号域名，同时支持 _dmarc 等下划线前缀并拒绝纯数字 IPv4 混入域名);
- IP 校验复用 core.cleaner.is_valid_ip_or_cidr (支持 IPv4-mapped IPv6，拦截 999.999.999.999/99 与纯十六进制词)。
"""
import glob
import json
import os
import re
import sys

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.cleaner import is_valid_domain, is_valid_ip_or_cidr


def lint(output_base="output"):
    issues = []
    seen_any = False

    def add(rel, ln, msg):
        issues.append(f"{rel}:{ln}: {msg}")

    for branch in ("singbox", "mihomo", "smartdns", "mosdns-x", "adg"):
        branch_dir = os.path.join(output_base, branch)
        root = os.path.join(branch_dir, "rules") if os.path.isdir(os.path.join(branch_dir, "rules")) else branch_dir
        if not os.path.isdir(root):
            add(f"{branch}", 0, "分支产物目录缺失")
            continue
        files = glob.glob(root + "/**/*", recursive=True)
        for f in sorted(files):
            if not os.path.isfile(f):
                continue
            rel = os.path.relpath(f, output_base).replace("\\", "/")
            norm = f.replace("\\", "/")
            if f.endswith((".srs", ".mrs")):
                if os.path.getsize(f) == 0:
                    add(rel, 0, "空二进制文件")
                continue
            if f.endswith(".json"):
                seen_any = True
                if os.path.getsize(f) == 0:
                    add(rel, 0, "空文件")
                    continue
                try:
                    with open(f, encoding="utf-8") as jf:
                        json.load(jf)
                except Exception as e:
                    add(rel, 0, f"JSON 解析失败: {e}")
                continue
            if not f.endswith((".txt", ".conf", ".list")):
                continue
            seen_any = True
            if os.path.getsize(f) == 0:
                add(rel, 0, "空文件")
                continue
            is_geoip = "/geoip/" in norm + "/"
            with open(f, encoding="utf-8", errors="replace") as tf:
                for i, raw in enumerate(tf, 1):
                    l = raw.strip()
                    if not l or l.startswith("#"):
                        continue
                    if branch in ("adg", "singbox"):
                        ok = (l.startswith("||") and l.endswith("^")) or (l.startswith("@@||") and l.endswith("^"))
                        if not ok:
                            add(rel, i, f"{branch} 语法异常: {l[:50]!r}")
                            continue
                        dom = l.removeprefix("@@").removeprefix("||").removesuffix("^")
                        if not is_valid_domain(dom, allow_tld=True):
                            add(rel, i, f"{branch} 域名异常: {l[:50]!r}")
                    elif is_geoip:
                        if not is_valid_ip_or_cidr(l):
                            add(rel, i, f"geoip 异常行: {l[:50]!r}")
                    elif branch == "mihomo":
                        if l.startswith(("DOMAIN-KEYWORD,", "DOMAIN-REGEX,")):
                            add(rel, i, f"keyword/regex 未剥离: {l[:40]!r}")
                            continue
                        body = l[2:] if l.startswith("+.") else l
                        if "*" in l or " " in body:
                            continue
                        if ":" in body or "/" in body or not is_valid_domain(body, allow_tld=True):
                            add(rel, i, f"trie 无法承载: {l[:50]!r}")
                    elif branch in ("smartdns", "mosdns-x"):
                        m = re.match(r"^(full:|domain:|keyword:|regexp:)?(.*)$", l)
                        pfx, body = m.group(1) or "", m.group(2)
                        if pfx in ("keyword:", "regexp:"):
                            continue
                        if branch == "smartdns" and pfx == "domain:":
                            add(rel, i, f"smartdns 不应出现 domain: 前缀: {l[:40]!r}")
                        if branch == "mosdns-x" and not pfx:
                            add(rel, i, f"mosdns-x 裸行应为 domain: 前缀: {l[:40]!r}")
                        if body.startswith(("-.", "+.", "*", "-")) or " " in body or "/" in body \
                                or not is_valid_domain(body, allow_tld=True):
                            add(rel, i, f"{branch} 非法行: {l[:50]!r}")

    if not seen_any:
        add(output_base, 0, "未扫描到任何规则文件 (构建产物缺失?)")
    return issues


def main():
    output_base = sys.argv[1] if len(sys.argv) > 1 else "output"
    issues = lint(output_base)
    if issues:
        print(f"❌ 产物语法门禁: {len(issues)} 处异常")
        for x in issues[:50]:
            print("  ", x)
        if len(issues) > 50:
            print(f"   ... 其余 {len(issues) - 50} 处略")
        sys.exit(1)
    print("✅ 产物语法门禁: 全部通过")


if __name__ == "__main__":
    main()
