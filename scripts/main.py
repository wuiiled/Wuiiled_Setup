#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import build_mihomo
import build_adg
import build_mosdns

def main():
    print("⚡️ 创建基础输出目录...")
    for d in ["output/mihomo", "output/adg", "output/mosdns-x"]:
        os.makedirs(d, exist_ok=True)

    print("\n🚀 [1/2] 开始构建 Mihomo 规则 (基础依赖)...")
    try:
        build_mihomo.run_all()
    except Exception as e:
        print(f"❌ Mihomo 规则构建失败: {e}")
        sys.exit(1)

    print("\n🚀 [2/2] 开始并行构建 ADG 与 MosDNS 规则...")
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(build_adg.run_all),
            executor.submit(build_mosdns.run_all)
        ]
        # 强制捕获并抛出子线程中的异常，拒绝静默失败！
        for future in futures:
            future.result()

    print("\n🎉 所有规则转换与打包任务完美执行完毕！")

if __name__ == "__main__":
    main()