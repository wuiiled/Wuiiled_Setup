# -*- coding: utf-8 -*-
"""
SmartDNS Branch Rule Exporter.
Decoupled: receives canonical RuleSet IR and generates rules for the smartdns
branch. 实际消费端为 OxiDNS (mosdns 系语法): 裸域名=后缀, full:=精确,
keyword:/regexp:=子串/正则; IP 文件为裸 CIDR (单主机剥 /32、/128)。
"""

import os
import sys
from typing import Dict, Optional

import utils
from core.models import RuleSet

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def build_smartdns_rules(rules: Dict[str, RuleSet], output_dir: str = "output/smartdns"):
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    os.makedirs(geosite_out, exist_ok=True)
    os.makedirs(geoip_out, exist_ok=True)

    # OxiDNS 发布机制 (白名单过滤 + 黑加白注入) 统一在 utils, 两个 DNS 分支共用
    rules = utils.select_oxidns_rules(rules)

    print(f"\n📦 [SmartDNS] 正在构建 {len(rules)} 个 OxiDNS 订阅规则集并输出至 {output_dir}...")

    for name, rs in rules.items():
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        out_path = os.path.join(sub_dir, f"{name}.txt")

        smartdns_lines = []
        if rs.is_geoip:
            for cidr in sorted(rs.ip_cidrs):
                if "." in cidr and cidr.endswith("/32"):
                    smartdns_lines.append(cidr[:-3])
                elif ":" in cidr and cidr.endswith("/128"):
                    smartdns_lines.append(cidr[:-4])
                else:
                    smartdns_lines.append(cidr)
        else:
            # OxiDNS/MosDNS 语法 (消费端为 OxiDNS, 见 rule_matcher/domain.rs:
            # 仅识别 full:/domain:/keyword:/regexp: 四种前缀, 裸行=后缀;
            # SmartDNS 的 -./+. 语法会被 OxiDNS 当字面后缀而成为死条目):
            #   后缀 -> 裸域名; 精确 -> full:; keyword/regexp 原样保留语义
            for s in sorted(rs.domain_suffixes):
                clean_s = s.lstrip('.')
                if clean_s:
                    smartdns_lines.append(clean_s)
            for d in sorted(rs.domains):
                clean_d = d.strip()
                if clean_d and clean_d not in rs.domain_suffixes:
                    smartdns_lines.append(f"full:{clean_d}")
            for k in sorted(rs.domain_keywords):
                smartdns_lines.append(f"keyword:{k}")
            for r in sorted(rs.domain_regexes):
                smartdns_lines.append(f"regexp:{r}")

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(smartdns_lines) + ("\n" if smartdns_lines else ""))

    # OxiDNS 兼容副本 (根目录历史文件名 + 子目录旧命名别名) 统一在 utils
    utils.publish_oxidns_compat(output_dir, rules)

    print("✅ [SmartDNS] OxiDNS 订阅规则集构建完成！")


def run_all(rules: Optional[Dict[str, RuleSet]] = None):
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_smartdns_rules(rules)


if __name__ == '__main__':
    run_all()
