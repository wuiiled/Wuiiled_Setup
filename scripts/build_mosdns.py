import os
import re
import utils
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
        print(f"✅ [MosDNS] {'ad_domain_list':<25} | 规则数: {len(lines):,}")

    # 2. SKK 规则
    for name, url in providers.MIHOMO_SKK.items():
        if name == "download": continue
        content = utils.download_file(url)
        lines = []
        for line in content.splitlines():
            cleaned = utils.clean_mihomo_domain_line(line)
            if not cleaned or 'skk.moe' in line or cleaned == '+.':
                continue
            
            if cleaned.startswith('+.'):
                line = 'domain:' + cleaned[2:]
            else:
                line = 'full:' + cleaned
            lines.append(line)
        with open(f"output/mosdns-x/{name}.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print(f"✅ [MosDNS] {name:<25} | 规则数: {len(lines):,}")