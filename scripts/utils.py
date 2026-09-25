#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import shutil
import tempfile
import atexit
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# 清洗/规范化函数统一收敛到 core/cleaner (单一实现, 防止两份副本语义漂移);
# utils 保留原函数名作为薄委托, 兼容既有调用方与测试。
from core.cleaner import (
    normalize_domain_line,
    clean_ip_line,
    clean_mihomo_domain_line,
)

WORK_DIR = None
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCLUDE_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "rules", "addons", "exclude-keyword.txt"))
os.environ["LC_ALL"] = "C"

def get_work_dir():
    global WORK_DIR
    if WORK_DIR is None:
        WORK_DIR = tempfile.mkdtemp(prefix="wuiiled_convert_")
        atexit.register(cleanup)
    return WORK_DIR

def cleanup():
    global WORK_DIR
    if WORK_DIR and os.path.exists(WORK_DIR):
        try:
            shutil.rmtree(WORK_DIR)
        except OSError as e:
            print(f"⚠️ 临时目录清理失败: {e}")
        finally:
            WORK_DIR = None

def check_tool(binary: str) -> bool:
    """检查编译器二进制是否可用; 在 GitHub Actions 上缺失时直接中断流程。"""
    if shutil.which(binary):
        return True
    if sys.platform == "win32" and shutil.which("wsl"):
        return True
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"❌ 错误: 在 GitHub Actions 环境中未找到 '{binary}' 编译器！必须中断任务以防生成残缺规则集。")
        sys.exit(1)
    return False

def check_mihomo():
    return check_tool("mihomo")

def safe_copy(src, dst):
    """跨平台安全复制文件，自动规避 Windows 不区分大小写导致的 SameFileError。"""
    try:
        if os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(dst)):
            return
        shutil.copyfile(src, dst)
    except shutil.SameFileError:
        pass
    except Exception as e:
        print(f"⚠️ 复制文件失败: {src} -> {dst}: {e}")

def download_file(url, timeout=15, retries=3):
    """文本下载统一走 core.fetcher (镜像回退+重试的单一实现)。

    延迟导入: core.fetcher 顶层 import utils (get_work_dir/_resolve_cmd),
    调用时导入可避免模块加载期的循环依赖。
    """
    import core.fetcher as fetcher
    return fetcher.fetch_text_url(url, timeout=timeout, retries=retries)

def download_files_parallel(output_file, urls):
    with ThreadPoolExecutor(max_workers=min(len(urls) + 1, 10)) as executor:
        futures_map = {executor.submit(download_file, url): url for url in urls}
        results = []
        success_count = 0
        fail_count = 0
        for future, url in futures_map.items():
            try:
                content = future.result()
                if content.strip():
                    if not content.endswith('\n'): content += '\n'
                    results.append(content)
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                print(f"⚠️ 并行下载异常: {url} -> {e}")
                fail_count += 1
    if urls:
        print(f"📥 下载完成: {success_count} 成功, {fail_count} 失败 (共 {len(urls)} 源)")
    with open(output_file, 'w', encoding='utf-8') as f:
        if results: f.write("".join(results))

def process_normalize_domain(input_file, output_file, skip_allow_rules=False):
    if not os.path.exists(input_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            pass
        return
    domains = set()
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip().lower()
            if not line: continue
            if skip_allow_rules and line.startswith("@@"): continue
            res = normalize_domain_line(line)
            if res: domains.add(res)
    with open(output_file, 'w', encoding='utf-8') as f:
        for d in sorted(domains): f.write(d + '\n')

def apply_keyword_filter(input_file, output_file):
    keywords = []
    if os.path.exists(EXCLUDE_FILE) and os.path.getsize(EXCLUDE_FILE) > 0:
        with open(EXCLUDE_FILE, 'r', encoding='utf-8') as kf:
            keywords = [k.strip().lower() for k in kf if k.strip() and not k.strip().startswith("#")]
    if not keywords:
        shutil.copyfile(input_file, output_file)
        return
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            if not any(kw in line.lower() for kw in keywords):
                outfile.write(line)

def optimize_smart_self(input_file, output_file):
    if not os.path.exists(input_file) or os.path.getsize(input_file) == 0:
        with open(output_file, 'w', encoding='utf-8') as f:
            pass
        return
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"): continue
        clean = line
        is_wildcard = False
        if clean.startswith("+."): clean, is_wildcard = clean[2:], True
        elif clean.startswith("."): clean, is_wildcard = clean[1:], True
        parts = clean.split(".")
        parts.reverse()
        if parts: data.append({'parts': parts, 'is_wildcard': is_wildcard, 'original': line})
    data.sort(key=lambda x: (x['parts'], not x['is_wildcard']))
    result_lines = []
    last_root = None
    for item in data:
        curr, is_covered = item['parts'], False
        if last_root is not None and len(curr) >= len(last_root) and curr[:len(last_root)] == last_root: is_covered = True
        if not is_covered:
            result_lines.append(item['original'])
            last_root = curr if item['is_wildcard'] else None
    with open(output_file, 'w', encoding='utf-8') as f:
        if result_lines:
            f.write('\n'.join(result_lines) + '\n')

def apply_advanced_whitelist_filter(block_in, allow_in, final_out):
    allow_set = set()
    allow_parents_set = set()

    if os.path.exists(allow_in):
        with open(allow_in, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if not line or line.startswith('#'): continue
                if line.startswith("+."): line = line[2:]
                elif line.startswith("."): line = line[1:]
                allow_set.add(line)

                # 构建白名单域名的所有父域名集合，用于 Option A 的子域防误杀检测
                parts = line.split('.')
                for i in range(1, len(parts)):
                    parent = ".".join(parts[i:])
                    allow_parents_set.add(parent)

    final_lines = []
    if os.path.exists(block_in):
        with open(block_in, 'r', encoding='utf-8') as f:
            for line in f:
                original = line.strip()
                if not original or original.startswith('#'): continue
                pure = original.lower()
                if pure.startswith("+."): pure = pure[2:]
                elif pure.startswith("."): pure = pure[1:]

                is_allowed = False

                # 1. 检查当前拦截域名（或其父域名）是否在白名单中
                parts = pure.split('.')
                for i in range(len(parts)):
                    parent = ".".join(parts[i:])
                    if parent in allow_set:
                        is_allowed = True
                        break

                # 2. 检查是否有任何白名单域名属于当前拦截域名的子域。
                # 如果有，为了避免拦截父域时误杀白名单子域，当前拦截域也必须放行（Option A 策略）
                if not is_allowed:
                    if pure in allow_parents_set:
                        is_allowed = True

                if not is_allowed:
                    final_lines.append(original)

    with open(final_out, 'w', encoding='utf-8') as f:
        if final_lines:
            f.write('\n'.join(final_lines) + '\n')

def _resolve_cmd(cmd):
    binary = cmd[0]
    if shutil.which(binary):
        return cmd
    if sys.platform == "win32" and shutil.which("wsl"):
        wsl_bin_dir = os.environ.get("WUIILED_BIN_DIR", "/mnt/f/antigravity/debian13/bin")
        wsl_cmd = ["wsl", f"{wsl_bin_dir}/{binary}"]
        for arg in cmd[1:]:
            if isinstance(arg, str) and (":\\" in arg or ":/" in arg or arg.startswith("output/") or arg.startswith("rules/")):
                abs_path = os.path.abspath(arg)
                drive, rest = os.path.splitdrive(abs_path)
                wsl_path = f"/mnt/{drive[0].lower()}{rest.replace(chr(92), '/')}"
                wsl_cmd.append(wsl_path)
            else:
                wsl_cmd.append(arg)
        return wsl_cmd
    return cmd

def compile_ruleset(cmd, output_name):
    """执行规则集编译命令，失败时打印警告而非中断流程。"""
    try:
        resolved_cmd = _resolve_cmd(cmd)
        subprocess.run(resolved_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 警告: 编译 {output_name} 发生异常:\n{e.stderr}")

def finalize_output(src, dst_dir, base_name, mode):
    if not os.path.exists(src) or os.path.getsize(src) == 0: return
    os.makedirs(dst_dir, exist_ok=True)
    with open(src, 'r', encoding='utf-8') as f: lines = list(set(f.read().splitlines()))
    lines.sort()
    if mode == "add_prefix": lines = ["+." + line if not line.startswith("+.") else line for line in lines]

    rule_count = len(lines)
    print(f"✅ [Mihomo] {base_name:<25} | 规则数: {rule_count:,}")

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"# Count: {rule_count}\n# Updated: {date_str}\n"
    txt_path = os.path.join(dst_dir, f"{base_name}.txt")
    mrs_path = os.path.join(dst_dir, f"{base_name}.mrs")
    with open(txt_path, 'w', encoding='utf-8') as f: f.write(header + "\n".join(lines) + "\n")
    if check_mihomo():
        compile_ruleset(
            ["mihomo", "convert-ruleset", "domain", "text", txt_path, mrs_path],
            f"{base_name}.mrs"
        )

def is_valid_ip_or_cidr(line):
    """
    判断一行内容是否为有效的 IP 或 CIDR (可包含 IP-CIDR 前缀等装饰)。
    与 core.cleaner.is_valid_ip_or_cidr (严格模式) 语义不同: 本函数用于行分类,
    需容忍 classical 规则装饰, 故基于 clean_ip_line 的清洗结果判定。
    """
    return clean_ip_line(line) is not None
