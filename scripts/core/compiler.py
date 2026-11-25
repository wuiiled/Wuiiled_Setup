# -*- coding: utf-8 -*-
"""
Thread-safe binary compiler wrappers (sing-box / mihomo) and temp work dir management.
"""

import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from typing import List

WORK_DIR = None
_WORK_DIR_LOCK = threading.Lock()
_COMPILE_LOCK = threading.Lock()
_COMPILE_FAILURES: List[str] = []


def get_work_dir() -> str:
    global WORK_DIR
    if WORK_DIR is None:
        with _WORK_DIR_LOCK:
            if WORK_DIR is None:
                WORK_DIR = tempfile.mkdtemp(prefix="wuiiled_convert_")
                atexit.register(cleanup)
    return WORK_DIR


def cleanup() -> None:
    global WORK_DIR
    if WORK_DIR and os.path.exists(WORK_DIR):
        try:
            shutil.rmtree(WORK_DIR)
        except OSError as e:
            print(f"⚠️ 临时目录清理失败: {e}")
        finally:
            WORK_DIR = None


def check_tool(binary: str) -> bool:
    """Check whether compiler binary is available; fail fast in GitHub Actions if missing."""
    if os.environ.get("WUIILED_ALLOW_MISSING_COMPILERS") == "1":
        return False
    if shutil.which(binary):
        return True
    if sys.platform == "win32" and shutil.which("wsl"):
        return True
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"❌ 错误: 在 GitHub Actions 环境中未找到 '{binary}' 编译器！必须中断任务以防生成残缺规则集。")
        sys.exit(1)
    return False


def _resolve_cmd(cmd: List[str]) -> List[str]:
    binary = cmd[0]
    if shutil.which(binary):
        return cmd
    if sys.platform == "win32" and shutil.which("wsl"):
        wsl_bin_dir = os.environ.get("WUIILED_BIN_DIR", "/usr/local/bin")
        wsl_cmd = ["wsl", f"{wsl_bin_dir}/{binary}"]
        for arg in cmd[1:]:
            if isinstance(arg, str) and (":\\" in arg or ":/" in arg or arg.startswith(("output/", "rules/"))):
                abs_path = os.path.abspath(arg)
                drive, rest = os.path.splitdrive(abs_path)
                wsl_path = f"/mnt/{drive[0].lower()}{rest.replace(chr(92), '/')}"
                wsl_cmd.append(wsl_path)
            else:
                wsl_cmd.append(arg)
        return wsl_cmd
    return cmd


def compile_ruleset(cmd: List[str], output_name: str) -> None:
    """Execute ruleset compilation; record failures for post-build assertion."""
    try:
        resolved_cmd = _resolve_cmd(cmd)
        subprocess.run(resolved_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 警告: 编译 {output_name} 发生异常:\n{e.stderr}")
        with _COMPILE_LOCK:
            _COMPILE_FAILURES.append(output_name)


def assert_no_compile_failures() -> None:
    """Fail build if any binary compilation failed."""
    with _COMPILE_LOCK:
        failures = list(_COMPILE_FAILURES)
    if failures:
        raise RuntimeError(
            f"编译产物完整性校验失败 ({len(failures)} 个二进制失败): " + ", ".join(failures)
        )


def decompile_srs(srs_path: str, json_path: str) -> dict:
    """Decompile a .srs file via sing-box and return parsed JSON."""
    subprocess.run(
        _resolve_cmd(["sing-box", "rule-set", "decompile", srs_path, "-o", json_path]),
        check=True, capture_output=True, text=True,
    )
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)
