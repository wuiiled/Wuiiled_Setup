#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import shutil
import tempfile
import atexit
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor

import providers
from core.cleaner import normalize_domain_line
from core.models import RuleSet

WORK_DIR = None
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCLUDE_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "rules", "addons", "exclude-keyword.txt"))
os.environ["LC_ALL"] = "C"

_WORK_DIR_LOCK = threading.Lock()

def get_work_dir():
    global WORK_DIR
    if WORK_DIR is None:
        with _WORK_DIR_LOCK:
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
    """检查编译器二进制是否可用; 在 GitHub Actions 上缺失时直接中断流程。
    WUIILED_ALLOW_MISSING_COMPILERS=1 时 (测试环境) 不探测、不中断, 返回 False
    —— 必须先于 WSL 探测判断, 否则本机测试会真实调用几十次 WSL 编译器。"""
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

def safe_copy(src, dst):
    """跨平台安全复制 (Windows 大小写去重)。失败直接抛出:
    复制失败意味着分支产物不完整, 静默吞掉会造成部署缺文件。"""
    if os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(dst)):
        return
    shutil.copyfile(src, dst)

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

def decompile_srs(srs_path, json_path):
    """sing-box `rule-set decompile` 的统一封装 (返回解析后的 dict)。
    此前该调用在 fetcher/build_singbox/diff_tianling/测试 各重复一份。"""
    subprocess.run(
        _resolve_cmd(["sing-box", "rule-set", "decompile", srs_path, "-o", json_path]),
        check=True, capture_output=True, text=True,
    )
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_blackwhite_rulesets(work_dir=None):
    """从 manager.load_ads_rules 产出的黑加白文件构造 ad-precise / ad-allow IR。

    这两个集合不在主 IR (all_rules) 中——它们是构建期差集产物。四个导出器
    统一经本函数消费: mihomo 渲染 +.txt/.mrs, smartdns/mosdns 渲染 DNS 语法,
    adg/singbox 经 render_adguard_geosite_ad 派生。"""
    work_dir = work_dir or get_work_dir()
    specs = (
        ("geosite-ad-precise", "blocklist_b.txt", "去广告黑名单精确版 (双集合黑名单B)"),
        ("geosite-ad-allow", "whitelist_b.txt", "去广告防误杀白名单 (双集合白名单B)"),
    )
    out = {}
    for name, fname, desc in specs:
        path = os.path.join(work_dir, "ads", fname)
        if not os.path.exists(path):
            # manager.load_ads_rules 一定会写出这两个文件 (失败会抛错), 缺失 = 编程错误
            raise RuntimeError(f"黑加白中间产物缺失: {path} (manager.load_ads_rules 未运行?)")
        if os.path.getsize(path) == 0:
            print(f"  [黑加白] {fname} 为空, 跳过 {name} (上游黑名单/白名单为空?)")
            continue
        with open(path, "r", encoding="utf-8") as f:
            entries = {l.strip() for l in f if l.strip() and not l.startswith("#")}
        if entries:
            out[name] = RuleSet(
                name=name,
                category="geosite",
                description=desc,
                domain_suffixes=entries,
                source_kind="self",
                sources=["上游黑名单 ∪ 上游白名单 (黑加白差集)"],
            )
    return out

_ADGAuthGuard = None

def render_adguard_geosite_ad(work_dir=None):
    """渲染 geosite-ad 的统一 AdGuard 源文件 (||黑名单B^ + @@||白名单B^)。

    单一渲染实现 + 单一产物: adg 分支直接发布该文件, singbox 分支以
    `rule-set convert --type adguard` 转换为 srs —— 两分支同源派生,
    导出器不各自渲染 (解耦)。内容确定性强; 并发首渲经 临时文件 +
    os.replace 原子落盘, 重复调用幂等。黑加白中间产物缺失时硬失败。
    """
    global _ADGAuthGuard
    work_dir = work_dir or get_work_dir()
    out_path = os.path.join(work_dir, "ads", "geosite-ad.adguard.txt")
    if _ADGAuthGuard == out_path and os.path.exists(out_path):
        return out_path
    lines = []
    for fname, fmt in (("blocklist_b.txt", "||{}^"), ("whitelist_b.txt", "@@||{}^")):
        path = os.path.join(work_dir, "ads", fname)
        if not os.path.exists(path):
            raise RuntimeError(f"AdGuard 源缺失: {path} (manager 黑加白产物未生成)")
        with open(path, "r", encoding="utf-8") as f:
            for line in f.read().splitlines():
                domain = line.strip().lstrip('+.').lstrip('.')
                if domain and not domain.startswith('#'):
                    lines.append(fmt.format(domain))
    # 并发首渲时各线程写各自的 tmp 文件再原子替换 (共用同一 tmp 名会互相截断)
    tmp_path = f"{out_path}.{os.getpid()}.{threading.get_ident()}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    os.replace(tmp_path, out_path)
    _ADGAuthGuard = out_path
    return out_path


def select_oxidns_rules(rules):
    """OxiDNS 发布白名单过滤 + 黑加白 IR 注入 (smartdns / mosdns-x 共用,
    此前该机制在两个导出器中逐行复制)。"""
    whitelist = set(providers.OXIDNS_RULE_FILES.values()) | providers.OXIDNS_EXTRA_RULESETS
    out = {name: rs for name, rs in rules.items() if name in whitelist}
    for name, bw in load_blackwhite_rulesets().items():
        if name in whitelist:
            out[name] = bw
    return out


def publish_oxidns_compat(output_dir, rules):
    """OxiDNS 兼容副本: 根目录历史文件名 + geosite/ 子目录旧命名别名
    (两个 DNS 分支共用的发布机制)。"""
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
    for legacy_name, ruleset_name in providers.OXIDNS_RULE_FILES.items():
        rs = rules.get(ruleset_name)
        if rs is None:
            continue
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        src = os.path.join(sub_dir, f"{ruleset_name}.txt")
        if os.path.exists(src):
            safe_copy(src, os.path.join(output_dir, legacy_name))
    for rel, ruleset_name in providers.OXIDNS_SUBDIR_ALIASES.items():
        rs = rules.get(ruleset_name)
        if rs is None:
            continue
        sub_dir = geoip_out if rs.is_geoip else geosite_out
        src = os.path.join(sub_dir, f"{ruleset_name}.txt")
        dst = os.path.join(output_dir, rel)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            safe_copy(src, dst)


def validate_output_invariants(output_base="output", require_binaries=True):
    """P1 守卫: 关键集合产物必须存在且非空。

    上游源整体下载失败时旧流程会发布空集, OxiDNS 04:00 下载空文件会
    清空线上 provider (cn/大厂/黑加白全部失效)。此处对每个分支的
    路由关键产物做非空断言, 违反即抛错 (构建失败, 不部署)。
    """
    def _nonempty_text(path):
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return False
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return any(line.strip() for line in f)

    problems = []
    ox_names = sorted(set(providers.OXIDNS_RULE_FILES.values()) | providers.OXIDNS_EXTRA_RULESETS)
    for branch in ("smartdns", "mosdns-x"):
        for name in ox_names:
            sub = "geoip" if name.startswith("geoip-") else "geosite"
            p = os.path.join(output_base, branch, sub, f"{name}.txt")
            if not _nonempty_text(p):
                problems.append(f"{branch}/{sub}/{name}.txt 缺失或为空")
    for branch in ("mihomo",):
        for name in ("geosite-cn", "geosite-ad", "geosite-ad-precise", "geosite-ad-allow", "geosite-!cn"):
            p = os.path.join(output_base, branch, "geosite", f"{name}.txt")
            if not _nonempty_text(p):
                problems.append(f"{branch}/geosite/{name}.txt 缺失或为空")
        for name in ("geoip-cn", "geoip-gfw"):
            p = os.path.join(output_base, branch, "geoip", f"{name}.txt")
            if not _nonempty_text(p):
                problems.append(f"{branch}/geoip/{name}.txt 缺失或为空")
    for name in ("geosite-ad", "geosite-httpdns", "geosite-pcdn"):
        p = os.path.join(output_base, "adg", f"{name}.txt")
        if not _nonempty_text(p):
            problems.append(f"adg/{name}.txt 缺失或为空")
    if require_binaries:
        for name in ("geosite-cn", "geosite-ad", "geosite-!cn", "geoip-cn"):
            sub = "geoip" if name.startswith("geoip-") else "geosite"
            p = os.path.join(output_base, "singbox", sub, f"{name}.srs")
            if not os.path.exists(p) or os.path.getsize(p) == 0:
                problems.append(f"singbox/{sub}/{name}.srs 缺失或为空")
    if problems:
        raise RuntimeError("关键产物不变量校验失败 (拒绝发布, 防止空集清空线上 provider):\n  - " + "\n  - ".join(problems))
    print(f"  ✅ [守卫] 关键产物不变量校验通过 ({len(ox_names)}×2 DNS 集 + mihomo/adg/singbox 关键集)")


def _idna_domain(value):
    """非 ASCII 域名转 punycode (IDNA)。DNS 线上查询只存在 punycode 形态,
    unicode 条目在任何消费者中都永不命中。转换失败原样返回 (由产物门禁拦截)。"""
    if value.isascii():
        return value
    try:
        return value.encode("idna").decode("ascii").lower()
    except Exception:
        return value


def idna_normalize_rules(rules):
    """遍历全部规则集, 把 domain/domain_suffix 桶中的非 ASCII 域名统一转
    punycode (keyword/regexp 语义不同, 不转换)。必须在补丁/合并全部完成、
    导出开始前调用。返回转换条数。"""
    total = 0
    for name, rs in rules.items():
        converted = 0
        new_domains = set()
        for d in rs.domains:
            v = _idna_domain(d)
            converted += (v != d)
            new_domains.add(v)
        new_suffixes = set()
        for s in rs.domain_suffixes:
            v = _idna_domain(s)
            converted += (v != s)
            new_suffixes.add(v)
        if converted:
            rs.domains, rs.domain_suffixes = new_domains, new_suffixes
            total += converted
            print(f"  [IDNA] {name:<26} | {converted} 条非 ASCII 域名已转 punycode")
    if total:
        print(f"  ✅ [IDNA] 共转换 {total} 条")
    return total
