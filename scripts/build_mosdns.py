import os
import re
from utils import download_file
import providers

def run_all():
    os.makedirs("output/mosdns-x", exist_ok=True)

    # 1. 转换 ADs_merged
    base_ads = "output/mihomo/ADs_merged.txt"
    if os.path.exists(base_ads):
        lines = []
        for line in open(base_ads, 'r', encoding='utf-8').read().splitlines():
            if not line.strip(): continue
            line = re.sub(r'^(DOMAIN-SUFFIX,|\+\.)', '', line)
            lines.append(line)
        with open("output/mosdns-x/ad_domain_list.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    # 2. SKK 规则
    for name, url in providers.MIHOMO_SKK.items():
        if name == "download": continue
        content = download_file(url)
        lines = []
        for line in content.splitlines():
            if line.startswith('#') or 'skk.moe' in line or not line.strip(): continue
            line = re.sub(r'^DOMAIN-SUFFIX,', 'domain:', line)
            line = re.sub(r'^DOMAIN,', 'full:', line)
            lines.append(line)
        with open(f"output/mosdns-x/{name}.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')