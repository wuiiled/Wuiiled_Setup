#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import build_adg
import build_mihomo
import build_mosdns
import build_singbox
import build_smartdns
import providers
import utils
from core.manager import load_all_rules
from core.readme_gen import generate_all_readmes, write_manifest
from core.validators import DEFAULT_MIN_COUNTS


def main():
    print("==================================================")
    print("🚀 All-in-One 网络分流规则统一构建引擎 (2.1)")
    print("==================================================")

    # 阶段 1: 加载、清洗并打补丁 (纯内存 canonical RuleSet IR)
    try:
        rules = load_all_rules()
    except Exception as e:
        print(f"❌ 规则数据加载/提纯失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 阶段 2: 非 ASCII 域名统一转 punycode
    utils.idna_normalize_rules(rules)

    # 阶段 3: 落来源画像 manifest (仅记录权威 IR, 未受 sing-box 复合规则污染)
    write_manifest(rules, "output")

    # 阶段 4: 重置输出目录并并行导出五大目标平台 (各自拿到独立浅拷贝)
    for branch in providers.TARGET_BRANCHES:
        b_dir = os.path.join("output", branch)
        if os.path.isdir(b_dir):
            shutil.rmtree(b_dir)

    print("\n🚀 [阶段 4/5] 并行构建所有目标平台专属规则...")
    with ThreadPoolExecutor() as executor:
        futures = {
            "Sing-box": executor.submit(build_singbox.run_all, dict(rules)),
            "Mihomo": executor.submit(build_mihomo.run_all, dict(rules)),
            "SmartDNS": executor.submit(build_smartdns.run_all, dict(rules)),
            "MosDNS": executor.submit(build_mosdns.run_all, dict(rules)),
            "AdGuard Home": executor.submit(build_adg.run_all, dict(rules)),
        }
        for name, fut in futures.items():
            try:
                fut.result()
            except Exception as e:
                print(f"❌ {name} 构建失败: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)

    # 阶段 4b: 关键产物不变量、基线底线与编译完整性校验
    utils.validate_output_invariants("output", min_counts=DEFAULT_MIN_COUNTS)
    utils.assert_no_compile_failures()

    # 阶段 5: 自动生成各平台规范 README 导航页
    print("\n🚀 [阶段 5/5] 生成各平台发布分支订阅导航 (README.md)...")
    try:
        generate_all_readmes("output")
    except Exception as e:
        print(f"⚠️ README 生成异常: {e}")

    print("\n🎉 所有规则转换与订阅导航生成任务圆满完成！")


if __name__ == "__main__":
    main()
