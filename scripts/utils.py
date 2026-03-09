#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import time
import re
import urllib.request
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

WORK_DIR = tempfile.mkdtemp(prefix="wuiiled_convert_")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCLUDE_FILE = os.path.join(SCRIPT_DIR, "exclude-keyword.txt")
os.environ["LC_ALL"] = "C"

def cleanup():
    if os.path.exists(WORK_DIR):
        try: shutil.rmtree(WORK_DIR)
        except: pass

import atexit
atexit.register(cleanup)

def check_mihomo():
    return shutil.which("mihomo") is not None

def download_file(url, timeout=20, retries=3):
    ua = "Mozilla/5.0 (compatible; MihomoRuleConverter/1.0)"
    req = urllib.request.Request(url, headers={'User-Agent': ua})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception:
            if attempt == retries - 1: return ""
            time.sleep(1)
    return ""

def download_files_parallel(output_file, urls):
    content_list = []
    with ThreadPoolExecutor(max_workers=min(len(urls) + 1, 10)) as executor:
        futures_map = {executor.submit(download_file, url): url for url in urls}
        results = []
        for url in urls:
            for future, f_url in futures_map.items():
                if f_url == url:
                    content = future.result()
                    if content.strip():
                        if not content.endswith('\n'): content += '\n'
                        results.append(content)
                    break
    with open(output_file, 'w', encoding='utf-8') as f:
        if results: f.write("".join(results))

def normalize_domain_line(line):
    line = line.strip()
    line = re.sub(r'[\$#].*', '', line)
    line = re.sub(r'^(0\.0\.0\.0|127\.0\.0\.1)\s+', '', line)
    if line.startswith("!"): return None
    if line.startswith("@@"): line = line[2:]
    line = line.replace("||", "").replace("^", "").replace("|", "")
    line = re.sub(r'^(domain-keyword|domain-suffix|domain),', '', line)
    if ',' in line: line = line.split(',')[0]
    line = re.sub(r'^(\+\.|\.)', '', line)
    line = line.rstrip('.')
    if '.' not in line or '*' in line or not re.match(r'^[a-z0-9_]', line) or re.match(r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$', line) or '/' in line: return None
    return line

def process_normalize_domain(input_file, output_file, skip_allow_rules=False):
    if not os.path.exists(input_file):
        open(output_file, 'w').close()
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
        open(output_file, 'w').close()
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
        f.write('\n'.join(result_lines) + '\n')

def apply_advanced_whitelist_filter(block_in, allow_in, final_out):
    combined_data = []
    if os.path.exists(allow_in):
        with open(allow_in, 'r', encoding='utf-8') as f:
            for line in f:
                key = line.strip()
                if key: combined_data.append({'key': key[::-1], 'type': 1, 'original': None})
    if os.path.exists(block_in):
        with open(block_in, 'r', encoding='utf-8') as f:
            for line in f:
                original = line.strip()
                if not original: continue
                pure = original
                if pure.startswith("+."): pure = pure[2:]
                elif pure.startswith("."): pure = pure[1:]
                combined_data.append({'key': pure[::-1], 'type': 0, 'original': original})
    combined_data.sort(key=lambda x: (x['key'], x['type']))
    active_white_root, buffered_key, buffered_line, final_lines = "", "", "", []
    for item in combined_data:
        key, typ, original = item['key'], item['type'], item['original']
        if active_white_root and key.startswith(active_white_root + "."): continue
        is_child_or_equal = bool(buffered_key and (key == buffered_key or key.startswith(buffered_key + ".")))
        if is_child_or_equal:
            if typ == 1: buffered_key, buffered_line, active_white_root = "", "", key
        else:
            if buffered_line: final_lines.append(buffered_line)
            if typ == 1: active_white_root, buffered_key, buffered_line = key, "", ""
            else: buffered_key, buffered_line, active_white_root = key, original, ""
    if buffered_line: final_lines.append(buffered_line)
    with open(final_out, 'w', encoding='utf-8') as f: f.write('\n'.join(final_lines) + '\n')

def finalize_output(src, dst_dir, base_name, mode):
    if not os.path.exists(src) or os.path.getsize(src) == 0: return
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
        try: 
            subprocess.run(["mihomo", "convert-ruleset", "domain", "text", txt_path, mrs_path], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e: 
            print(f"⚠️ 警告: 转换 {base_name}.mrs 发生异常:\n{e.stderr}")