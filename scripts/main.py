#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import build_mihomo
import build_adg
import build_mosdns
import build_singbox
import build_smartdns

def main():
    print("⚡️ 创建基础输出目录...")
    for d in ["output/mihomo", "output/adg", "output/mosdns-x", "output/singbox", "output/smartdns"]:
        os.makedirs(d, exist_ok=True)

    print("\n🚀 [阶段 1/2] 构建 Mihomo 规则 (其他平台的前置依赖)...")
    try:
        build_mihomo.run_all()
    except Exception as e:
        print(f"❌ Mihomo 规则构建失败: {e}")
        sys.exit(1)

    print("\n🚀 [阶段 2/2] 并行构建 ADG、MosDNS、Sing-box 与 SmartDNS 规则...")
    with ThreadPoolExecutor() as executor:
        futures = {
            "AdGuard Home": executor.submit(build_adg.run_all),
            "MosDNS": executor.submit(build_mosdns.run_all),
            "Sing-box": executor.submit(build_singbox.run_all),
            "SmartDNS": executor.submit(build_smartdns.run_all),
        }
        for name, future in futures.items():
            try:
                future.result()
                print(f"  ✅ {name} 构建完成")
            except Exception as e:
                print(f"  ❌ {name} 构建失败: {e}")
                sys.exit(1)

    print("\n🎉 所有规则转换与打包任务完美执行完毕！")

if __name__ == "__main__":
    main()