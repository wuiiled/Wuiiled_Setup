#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from concurrent.futures import ThreadPoolExecutor

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from core.manager import load_all_rules
from core.readme_gen import generate_all_readmes
import build_singbox
import build_mihomo
import build_smartdns
import build_mosdns
import build_adg


def main():
    print("==================================================")
    print("🚀 All-in-One 网络分流规则统一构建引擎 (2.0)")
    print("==================================================")

    # 阶段 1: 加载并清洗所有标准规则 (RuleSet IR)
    try:
        rules = load_all_rules()
    except Exception as e:
        print(f"❌ 规则数据加载/提纯失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 阶段 2: 并行导出所有目标平台 (零耦合独立构建)
    print("\n🚀 [阶段 2/3] 并行构建所有目标平台专属规则...")
    with ThreadPoolExecutor() as executor:
        futures = {
            "Sing-box": executor.submit(build_singbox.run_all, rules),
            "Mihomo": executor.submit(build_mihomo.run_all, rules),
            "SmartDNS": executor.submit(build_smartdns.run_all, rules),
            "MosDNS": executor.submit(build_mosdns.run_all, rules),
            "AdGuard Home": executor.submit(build_adg.run_all, rules),
        }
        for name, fut in futures.items():
            try:
                fut.result()
            except Exception as e:
                print(f"❌ {name} 构建失败: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)

    # 阶段 3: 自动生成各平台规范 README 导航页
    print("\n🚀 [阶段 3/3] 生成各平台发布分支订阅导航 (README.md)...")
    try:
        generate_all_readmes("output")
    except Exception as e:
        print(f"⚠️ README 生成异常: {e}")

    print("\n🎉 所有规则转换与订阅导航生成任务圆满完成！")


if __name__ == "__main__":
    main()