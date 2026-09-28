#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产物语法门禁: 校验 output/<branch> 下每个规则文件的行文法与该分支
消费端解析器一致 (P1-M: `-.` 类死条目曾因此存活)。

各分支文法 (与消费者源码核对过):
  singbox   geosite/*.txt 仅允许 AdGuard 行 (||x^ / @@||x^, geosite-ad 源);
            *.json 必须可解析
  mihomo    geosite: 禁 DOMAIN-KEYWORD/REGEX 行; 主体须为裸域名/+.后缀/*.通配
            (trie 无法承载含 `:` `/` 空格的行); geoip: 纯 IP/CIDR
  smartdns  geosite: 可选 full:/keyword:/regexp: 前缀 + 合法域名主体;
            禁 -./+./domain: 前缀; geoip 及根目录 legacy IP 副本: 纯 IP/CIDR
  mosdns-x  geosite: domain:/full:/keyword:/regexp: 四种前缀; geoip: 纯 IP/CIDR
  adg       ||x^ / @@||x^ + 合法域名主体
通用: 禁空文件; 域名主体禁非 ASCII (IDNA 归一后不应残留); keyword/regexp
正文免域名校验 (语义行)。

用法: PYTHONPATH=scripts python3 scripts/lint_artifacts.py [output_base]
退出码: 有问题 1, 否则 0。
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import providers  # noqa: E402

DOMAIN_OK = re.compile(
    r"^(?=.{1,253}$)([a-z0-9]([a-z0-9_-]{0,61}[a-z0-9])?\.)*[a-z0-9]([a-z0-9_-]{0,61}[a-z0-9])?$", re.I
)
IP_OK = re.compile(r"^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$|^[0-9a-fA-F:]+(/\d{1,3})?$")


def _legacy_geoip_names():
    """根目录历史文件名中承载 IP 列表的 (如 cnip.txt), 按 providers 映射判定。"""
    return {legacy for legacy, target in providers.OXIDNS_RULE_FILES.items()
            if target.startswith("geoip-")}


def lint(output_base="output"):
    issues = []
    seen_any = False

    def add(rel, ln, msg):
        issues.append(f"{rel}:{ln}: {msg}")

    for branch in ("singbox", "mihomo", "smartdns", "mosdns-x", "adg"):
        branch_dir = os.path.join(output_base, branch)
        # 兼容两种布局: 构建布局 output/<branch>/geosite|geoip/...,
        # 部署布局 output/<branch>/rules/geosite|geoip/... (CI 部署时整体移入 rules/)
        root = os.path.join(branch_dir, "rules") if os.path.isdir(os.path.join(branch_dir, "rules")) else branch_dir
        if not os.path.isdir(root):
            add(f"{branch}", 0, "分支产物目录缺失")
            continue
        legacy_geoip = _legacy_geoip_names()
        files = glob.glob(root + "/**/*", recursive=True)
        for f in sorted(files):
            if not os.path.isfile(f):
                continue
            rel = f.replace(output_base.rstrip("/\\") + os.sep, "").replace("\\", "/")
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
                    json.load(open(f, encoding="utf-8"))
                except Exception as e:
                    add(rel, 0, f"JSON 解析失败: {e}")
                continue
            if not f.endswith((".txt", ".conf", ".list")):
                continue
            seen_any = True
            if os.path.getsize(f) == 0:
                add(rel, 0, "空文件")
                continue
            is_geoip = (os.sep + "geoip" + os.sep in f + os.sep) or \
                       (os.path.dirname(f) == root) and (os.path.basename(f) in legacy_geoip)
            for i, raw in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
                l = raw.strip()
                if not l or l.startswith("#"):
                    continue
                if branch == "adg":
                    ok = (l.startswith("||") and l.endswith("^")) or (l.startswith("@@||") and l.endswith("^"))
                    if not ok:
                        add(rel, i, f"adg 语法异常: {l[:50]!r}")
                        continue
                    dom = l.removeprefix("@@").removeprefix("||").removesuffix("^")
                    if not DOMAIN_OK.match(dom):
                        add(rel, i, f"adg 域名异常: {l[:50]!r}")
                elif branch == "singbox":
                    # singbox 分支的 txt 仅 geosite-ad (AdGuard 源)
                    if not ((l.startswith("||") and l.endswith("^")) or (l.startswith("@@||") and l.endswith("^"))):
                        add(rel, i, f"singbox txt 异常: {l[:50]!r}")
                    else:
                        dom = l.removeprefix("@@").removeprefix("||").removesuffix("^")
                        if not DOMAIN_OK.match(dom):
                            add(rel, i, f"singbox 域名异常: {l[:50]!r}")
                elif is_geoip:
                    if not IP_OK.match(l):
                        add(rel, i, f"geoip 异常行: {l[:50]!r}")
                elif branch == "mihomo":
                    if l.startswith(("DOMAIN-KEYWORD,", "DOMAIN-REGEX,")):
                        add(rel, i, f"keyword/regex 未剥离: {l[:40]!r}")
                        continue
                    body = l[2:] if l.startswith("+.") else l
                    if "*" in l or " " in body:
                        continue  # 通配符与消费端特例字面量 (如 'mijia cloud') 合法
                    if ":" in body or "/" in body or not DOMAIN_OK.match(body):
                        add(rel, i, f"trie 无法承载: {l[:50]!r}")
                elif branch in ("smartdns", "mosdns-x"):
                    m = re.match(r"^(full:|domain:|keyword:|regexp:)?(.*)$", l)
                    pfx, body = m.group(1) or "", m.group(2)
                    if pfx in ("keyword:", "regexp:"):
                        continue  # 语义行正文免域名校验
                    if branch == "smartdns" and pfx == "domain:":
                        add(rel, i, f"smartdns 不应出现 domain: 前缀: {l[:40]!r}")
                    if branch == "mosdns-x" and not pfx:
                        add(rel, i, f"mosdns-x 裸行应为 domain: 前缀: {l[:40]!r}")
                    if body.startswith(("-.", "+.", "*", "-")) or " " in body or "/" in body \
                            or not DOMAIN_OK.match(body):
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
