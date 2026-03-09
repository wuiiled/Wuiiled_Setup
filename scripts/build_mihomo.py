import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, wait
import utils
import providers

def gen_ads_reject():
    mod_dir = os.path.join(utils.WORK_DIR, "ads")
    os.makedirs(mod_dir, exist_ok=True)
    raw_ads, raw_allow = os.path.join(mod_dir, "raw_ads.txt"), os.path.join(mod_dir, "raw_allow.txt")
    utils.download_files_parallel(raw_ads, providers.ADS_BLOCK_URLS)
    utils.download_files_parallel(raw_allow, providers.ALLOW_URLS)

    clean_ads, filter_ads = os.path.join(mod_dir, "clean_ads.txt"), os.path.join(mod_dir, "filter_ads.txt")
    utils.process_normalize_domain(raw_ads, clean_ads, skip_allow_rules=True)
    utils.apply_keyword_filter(clean_ads, filter_ads)

    merged_allow_raw = os.path.join(mod_dir, "merged_allow_raw.txt")
    allow_content = [open(raw_allow, 'r', encoding='utf-8').read()] if os.path.exists(raw_allow) else []
    if os.path.exists(utils.EXCLUDE_FILE):
        with open(utils.EXCLUDE_FILE, 'r', encoding='utf-8') as f:
            allow_content.extend([l + "\n" for l in f.read().splitlines() if l.strip() and not l.startswith('#')])
    with open(merged_allow_raw, 'w', encoding='utf-8') as f: f.write("".join(allow_content))

    clean_allow, opt_ads, opt_allow, final_ads = [os.path.join(mod_dir, x) for x in ["clean_allow.txt", "opt_ads.txt", "opt_allow.txt", "final_ads.txt"]]
    utils.process_normalize_domain(merged_allow_raw, clean_allow, skip_allow_rules=False)
    utils.optimize_smart_self(filter_ads, opt_ads)
    utils.optimize_smart_self(clean_allow, opt_allow)
    utils.apply_advanced_whitelist_filter(opt_ads, opt_allow, final_ads)
    utils.finalize_output(final_ads, "output/mihomo", "ADs_merged", "add_prefix")

def gen_ai():
    mod_dir = os.path.join(utils.WORK_DIR, "ai")
    os.makedirs(mod_dir, exist_ok=True)
    raw_ai, clean_ai, opt_ai = [os.path.join(mod_dir, x) for x in ["raw_ai.txt", "clean_ai.txt", "opt_ai.txt"]]
    utils.download_files_parallel(raw_ai, providers.AI_URLS)
    utils.process_normalize_domain(raw_ai, clean_ai, skip_allow_rules=False)
    utils.optimize_smart_self(clean_ai, opt_ai)
    utils.finalize_output(opt_ai, "output/mihomo", "AIs_merged", "add_prefix")

def gen_fakeip():
    mod_dir = os.path.join(utils.WORK_DIR, "fakeip")
    os.makedirs(mod_dir, exist_ok=True)
    raw_fakeip_dl = os.path.join(mod_dir, "raw_fakeip_dl.txt")
    utils.download_files_parallel(raw_fakeip_dl, providers.FAKE_IP_URLS)
    unique_lines = set()
    if os.path.exists(raw_fakeip_dl):
        for line in open(raw_fakeip_dl, 'r', encoding='utf-8').read().splitlines():
            line = line.lower()
            if re.match(r'^\s*(dns:|fake-ip-filter:)', line): continue
            line = re.sub(r'^\s*-\s*', '', line).replace('"', '').replace("'", '').replace('\\', '').strip()
            if line and not line.startswith('#'): unique_lines.add(line)
    clean_fakeip, final_fakeip = os.path.join(mod_dir, "clean_fakeip.txt"), os.path.join(mod_dir, "final_fakeip.txt")
    with open(clean_fakeip, 'w', encoding='utf-8') as f: f.write('\n'.join(sorted(unique_lines)) + '\n')
    utils.optimize_smart_self(clean_fakeip, final_fakeip)
    utils.finalize_output(final_fakeip, "output/mihomo", "Fake_IP_Filter_merged", "none")

def gen_ads_drop():
    mod_dir = os.path.join(utils.WORK_DIR, "drop")
    os.makedirs(mod_dir, exist_ok=True)
    raw_rd = os.path.join(mod_dir, "raw_rd.txt")
    utils.download_files_parallel(raw_rd, providers.DROP_URLS)
    rd_lines = set()
    if os.path.exists(raw_rd):
        for line in open(raw_rd, 'r', encoding='utf-8').read().splitlines():
            line = line.strip().lower()
            if not line or line.startswith('#') or "skk.moe" in line: continue
            if line.startswith("domain-suffix,"): line = "+." + line.split(',')[1].strip()
            elif line.startswith("domain,"): line = line.split(',')[1].strip()
            if line != "+.": rd_lines.add(line)
    clean_rd = os.path.join(mod_dir, "clean_rd.txt")
    with open(clean_rd, 'w', encoding='utf-8') as f: f.write('\n'.join(sorted(rd_lines)) + '\n')
    
    raw_allow_temp, merged_allow_raw = os.path.join(mod_dir, "raw_allow_temp.txt"), os.path.join(mod_dir, "merged_allow_raw.txt")
    utils.download_files_parallel(raw_allow_temp, providers.ALLOW_URLS)
    allow_content = [open(raw_allow_temp, 'r', encoding='utf-8').read()] if os.path.exists(raw_allow_temp) else []
    if os.path.exists(utils.EXCLUDE_FILE):
        with open(utils.EXCLUDE_FILE, 'r', encoding='utf-8') as f:
            allow_content.extend([l + "\n" for l in f.read().splitlines() if l.strip() and not l.startswith('#')])
    with open(merged_allow_raw, 'w', encoding='utf-8') as f: f.write("".join(allow_content))
    
    clean_rd_allow, final_rd = os.path.join(mod_dir, "clean_rd_allow.txt"), os.path.join(mod_dir, "final_rd.txt")
    utils.process_normalize_domain(merged_allow_raw, clean_rd_allow, skip_allow_rules=False)
    utils.apply_advanced_whitelist_filter(clean_rd, clean_rd_allow, final_rd)
    utils.finalize_output(final_rd, "output/mihomo", "Reject_Drop_merged", "none")

def gen_cn():
    mod_dir = os.path.join(utils.WORK_DIR, "cn")
    os.makedirs(mod_dir, exist_ok=True)
    raw_cn_1, raw_cn_2 = os.path.join(mod_dir, "raw_cn_1.txt"), os.path.join(mod_dir, "raw_cn_2.txt")
    utils.download_files_parallel(raw_cn_1, providers.CN_URLS_1)
    utils.download_files_parallel(raw_cn_2, providers.CN_URLS_2)
    merged_cn = os.path.join(mod_dir, "merged_cn_raw.txt")
    with open(merged_cn, 'w', encoding='utf-8') as f:
        if os.path.exists(raw_cn_1):
            for line in open(raw_cn_1, 'r', encoding='utf-8').read().splitlines():
                line = line.strip().lower()
                if line and not line.startswith('#'): f.write("+." + line + "\n")
        if os.path.exists(raw_cn_2):
            for line in open(raw_cn_2, 'r', encoding='utf-8').read().splitlines():
                line = line.strip().lower()
                if not line or line.startswith('#') or "skk.moe" in line: continue
                if line.startswith("domain-suffix,"): line = "+." + line.split(',')[1].strip()
                elif line.startswith("domain,"): line = line.split(',')[1].strip()
                else: continue
                f.write(line + "\n")
    final_cn = os.path.join(mod_dir, "final_cn.txt")
    utils.optimize_smart_self(merged_cn, final_cn)
    utils.finalize_output(final_cn, "output/mihomo", "CN_merged", "none")

def gen_extra_mihomo():
    for name, url in providers.MIHOMO_GENERIC_RAW.items():
        content = utils.download_file(url)
        lines = []
        for line in content.splitlines():
            if line.startswith('#') or 'PROCESS-NAME' in line: continue
            line = re.sub(r'^DOMAIN,', '', line)
            line = re.sub(r'^DOMAIN-SUFFIX,', '+.', line)
            if line.strip(): lines.append(line)
        
        print(f"✅ [Mihomo] {name:<25} | 规则数: {len(lines):,}")

        txt_path = f"output/mihomo/{name}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f: f.write('\n'.join(lines) + '\n')
        if utils.check_mihomo():
            rule_type = "ipcidr" if "_IP" in name else "domain"
            subprocess.run(["mihomo", "convert-ruleset", rule_type, "text", txt_path, f"output/mihomo/{name}.mrs"], check=False)

    for name, url in providers.MIHOMO_SKK.items():
        content = utils.download_file(url)
        lines = []
        for line in content.splitlines():
            if line.startswith('#') or 'skk.moe' in line or line.startswith('DOMAIN-WILDCARD,'): continue
            line = re.sub(r'^DOMAIN-SUFFIX,', '+.', line)
            line = re.sub(r'^DOMAIN,', '', line)
            if line.strip() and line.strip() != '+.': lines.append(line)
            
        print(f"✅ [Mihomo] {name:<25} | 规则数: {len(lines):,}")

        txt_path = f"output/mihomo/{name}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f: f.write('\n'.join(lines) + '\n')
        if utils.check_mihomo():
            subprocess.run(["mihomo", "convert-ruleset", "domain", "text", txt_path, f"output/mihomo/{name}.mrs"], check=False)

def run_all():
    tasks = [gen_ads_reject, gen_ai, gen_fakeip, gen_ads_drop, gen_cn, gen_extra_mihomo]
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(t) for t in tasks]
        for future in futures:
            future.result()