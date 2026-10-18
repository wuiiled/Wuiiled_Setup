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
from typing import List

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

import providers
from core.cleaner import normalize_domain_line, _domain_ancestors, idna_domain as _idna_domain
from core.models import RuleSet

WORK_DIR = None
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCLUDE_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "rules", "addons", "exclude-keyword.txt"))
os.environ["LC_ALL"] = "C"

_WORK_DIR_LOCK = threading.Lock()
_COMPILE_FAILURES = []


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
    """检查编译器二进制是否可用；在 GitHub Actions 上缺失时直接中断流程。"""
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
    """跨平台安全复制 (Windows 大小写去重)。"""
    if os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(dst)):
        return
    shutil.copyfile(src, dst)


def download_file(url, timeout=15, retries=3):
    """文本下载统一走 core.fetcher (镜像回退+重试的单一实现)。"""
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
                    if not content.endswith('\n'):
                        content += '\n'
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
        if results:
            f.write("".join(results))


def process_normalize_domain(input_file, output_file, skip_allow_rules=False):
    if not os.path.exists(input_file):
        with open(output_file, 'w', encoding='utf-8'):
            pass
        return
    domains = set()
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip().lower()
            if not line:
                continue
            if skip_allow_rules and line.startswith("@@"):
                continue
            res = normalize_domain_line(line)
            if res:
                domains.add(_idna_domain(res))
    with open(output_file, 'w', encoding='utf-8') as f:
        for d in sorted(domains):
            f.write(d + '\n')


def apply_keyword_filter(input_file, output_file):
    if not os.path.exists(input_file):
        with open(output_file, 'w', encoding='utf-8'):
            pass
        return
    keywords = []
    if os.path.exists(EXCLUDE_FILE) and os.path.getsize(EXCLUDE_FILE) > 0:
        with open(EXCLUDE_FILE, 'r', encoding='utf-8') as kf:
            keywords = [k.strip().lower() for k in kf if k.strip() and not k.strip().startswith("#")]
    if not keywords:
        safe_copy(input_file, output_file)
        return
    with open(input_file, 'r', encoding='utf-8') as infile:
        kept = [line for line in infile if not any(kw in line.lower() for kw in keywords)]
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.writelines(kept)


def optimize_smart_self(input_file, output_file):
    if not os.path.exists(input_file) or os.path.getsize(input_file) == 0:
        with open(output_file, 'w', encoding='utf-8'):
            pass
        return
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        clean = line
        is_wildcard = False
        if clean.startswith("+."):
            clean, is_wildcard = clean[2:], True
        elif clean.startswith("."):
            clean, is_wildcard = clean[1:], True
        parts = clean.split(".")
        parts.reverse()
        if parts:
            data.append({'parts': parts, 'is_wildcard': is_wildcard, 'original': line})
    data.sort(key=lambda x: (x['parts'], not x['is_wildcard']))
    result_lines = []
    last_root = None
    for item in data:
        curr, is_covered = item['parts'], False
        if last_root is not None and len(curr) >= len(last_root) and curr[:len(last_root)] == last_root:
            is_covered = True
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
                line = line.strip().lower().lstrip('+').lstrip('.')
                if not line or line.startswith('#'):
                    continue
                allow_set.add(line)
                parts = line.split('.')
                for i in range(1, len(parts)):
                    allow_parents_set.add(".".join(parts[i:]))

    final_lines = []
    if os.path.exists(block_in):
        with open(block_in, 'r', encoding='utf-8') as f:
            for line in f:
                original = line.strip()
                if not original or original.startswith('#'):
                    continue
                pure = original.lower().lstrip('+').lstrip('.')
                if pure in allow_parents_set or any(anc in allow_set for anc in _domain_ancestors(pure)):
                    continue
                final_lines.append(original)

    with open(final_out, 'w', encoding='utf-8') as f:
        if final_lines:
            f.write('\n'.join(final_lines) + '\n')


def _resolve_cmd(cmd):
    binary = cmd[0]
    if shutil.which(binary):
        return cmd
    if sys.platform == "win32" and shutil.which("wsl"):
        wsl_bin_dir = os.environ.get("WUIILED_BIN_DIR", "/usr/local/bin")
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
    """执行规则集编译命令，失败时记录告警，构建结束由 assert_no_compile_failures 统一裁决。"""
    try:
        resolved_cmd = _resolve_cmd(cmd)
        subprocess.run(resolved_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 警告: 编译 {output_name} 发生异常:\n{e.stderr}")
        _COMPILE_FAILURES.append(output_name)


def assert_no_compile_failures():
    """P1 守卫: 任意二进制编译失败即拒绝发布。"""
    if _COMPILE_FAILURES:
        raise RuntimeError(
            f"编译产物完整性校验失败 ({len(_COMPILE_FAILURES)} 个二进制失败): "
            + ", ".join(_COMPILE_FAILURES)
        )


def decompile_srs(srs_path, json_path):
    """sing-box `rule-set decompile` 的统一封装 (返回解析后的 dict)。"""
    subprocess.run(
        _resolve_cmd(["sing-box", "rule-set", "decompile", srs_path, "-o", json_path]),
        check=True, capture_output=True, text=True,
    )
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_blackwhite_rulesets(work_dir=None):
    """从 manager.load_ads_rules 产出的黑加白文件构造 ad-precise / ad-allow IR (含 IDNA 归一)。"""
    work_dir = work_dir or get_work_dir()
    specs = (
        ("geosite-ad-precise", "blocklist_b.txt", "去广告黑名单精确版 (双集合黑名单B)"),
        ("geosite-ad-allow", "whitelist_b.txt", "去广告防误杀白名单 (双集合白名单B)"),
    )
    out = {}
    for name, fname, desc in specs:
        path = os.path.join(work_dir, "ads", fname)
        if not os.path.exists(path):
            raise RuntimeError(f"黑加白中间产物缺失: {path} (manager.load_ads_rules 未运行?)")
        if os.path.getsize(path) == 0:
            print(f"  [黑加白] {fname} 为空, 跳过 {name} (上游黑名单/白名单为空?)")
            continue
        with open(path, "r", encoding="utf-8") as f:
            entries = {_idna_domain(l.strip()) for l in f if l.strip() and not l.startswith("#")}
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
    缓存键同时校验输入文件 (mtime_ns, size)，避免单元测试在同一 work_dir 下改写输入后读到旧缓存。
    """
    global _ADGAuthGuard
    work_dir = work_dir or get_work_dir()
    out_path = os.path.join(work_dir, "ads", "geosite-ad.adguard.txt")
    blk_path = os.path.join(work_dir, "ads", "blocklist_b.txt")
    wht_path = os.path.join(work_dir, "ads", "whitelist_b.txt")
    for p in (blk_path, wht_path):
        if not os.path.exists(p):
            raise RuntimeError(f"AdGuard 源缺失: {p} (manager 黑白产物未生成)")

    sig = (
        out_path,
        os.stat(blk_path).st_mtime_ns,
        os.stat(blk_path).st_size,
        os.stat(wht_path).st_mtime_ns,
        os.stat(wht_path).st_size,
    )
    if _ADGAuthGuard == sig and os.path.exists(out_path):
        return out_path

    lines = []
    for path, fmt in ((blk_path, "||{}^"), (wht_path, "@@||{}^")):
        with open(path, "r", encoding="utf-8") as f:
            for line in f.read().splitlines():
                domain = _idna_domain(line.strip().lstrip('+').lstrip('.'))
                if domain and not domain.startswith('#'):
                    lines.append(fmt.format(domain))
    tmp_path = f"{out_path}.{os.getpid()}.{threading.get_ident()}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    os.replace(tmp_path, out_path)
    _ADGAuthGuard = sig
    return out_path


def select_oxidns_rules(rules):
    """OxiDNS 发布白名单过滤 + 黑加白 IR 注入 (smartdns / mosdns-x 共用)。"""
    whitelist = set(providers.OXIDNS_RULESETS) | providers.OXIDNS_EXTRA_RULESETS
    out = {name: rs for name, rs in rules.items() if name in whitelist}
    for name, bw in load_blackwhite_rulesets().items():
        if name in whitelist:
            out[name] = bw
    return out


def publish_oxidns_compat(output_dir, rules):
    """OxiDNS 旧命名别名副本: geosite/ 子目录的 geosite-geolocation-!cn.txt。"""
    geosite_out = os.path.join(output_dir, "geosite")
    geoip_out = os.path.join(output_dir, "geoip")
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


def format_oxidns_lines(rs: RuleSet, domain_prefix: str = "domain:", flatten_host_cidr: bool = False) -> List[str]:
    """生成 OxiDNS (mosdns-x / smartdns) 单文件的行列表，委托给 RuleSet.to_oxidns_lines。"""
    return rs.to_oxidns_lines(domain_prefix=domain_prefix, flatten_host_cidr=flatten_host_cidr)


def validate_output_invariants(output_base="output", require_binaries=True):
    """P1 守卫: 关键集合产物必须存在且非空。"""
    def _nonempty_text(path):
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return False
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return any(line.strip() for line in f)

    problems = []
    ox_names = sorted(set(providers.OXIDNS_RULESETS) | providers.OXIDNS_EXTRA_RULESETS)
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
    print(f"  ✅ [守卫] 关键产物不变量校验通过 ({len(ox_names)}x2 DNS 集 + mihomo/adg/singbox 关键集)")


def idna_normalize_rules(rules):
    """遍历全部规则集，把 domain/domain_suffix 桶中的非 ASCII 域名统一转 punycode。"""
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

