import os
import re
from utils import download_file
import providers

def run_all():
    os.makedirs("output/adg", exist_ok=True)

    # 1. 转换 ADs_merged
    base_ads = "output/mihomo/ADs_merged.txt"
    if os.path.exists(base_ads):
        lines = []
        for line in open(base_ads, 'r', encoding='utf-8').read().splitlines():
            if not line.strip(): continue
            line = re.sub(r'^(DOMAIN-SUFFIX,|DOMAIN,|\+\.)', '||', line)
            if not line.startswith('#'): line = line + '^'
            lines.append(line)
        with open("output/adg/ADs_merged_adg.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    # 2. Httpdns
    content = download_file(providers.ADG_URLS["Httpdns"])
    lines = []
    for line in content.splitlines():
        if not line.strip(): continue
        line = re.sub(r'^\+\.', '||', line)
        if not line.startswith('#'): line = line + '^'
        lines.append(line)
    with open("output/adg/Httpdns_adg.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    # 3. PCDN
    content = download_file(providers.ADG_URLS["PCDN"])
    lines = []
    for line in content.splitlines():
        if 'DOMAIN-REGEX,' in line or line.startswith('#') or not line.strip(): continue
        line = re.sub(r'^(DOMAIN-SUFFIX,|DOMAIN,|\+\.)', '||', line)
        line = line + '^'
        lines.append(line)
    with open("output/adg/PCDN_adg.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')