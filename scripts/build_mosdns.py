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
        with open(base_ads, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                if not line.strip() or line.startswith('#'): continue
                line = re.sub(r'^(DOMAIN-SUFFIX,|\+\.)', '', line)
                lines.append(line)
        with open("output/mosdns-x/ad_domain_list.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print(f"✅ [MosDNS] {'ad_domain_list':<25} | 规则数: {len(lines):,}")

    # 2. SKK 规则 (从 mihomo 已生成的 txt 读取，不再重复下载)
    for name in providers.MIHOMO_SKK:
        if name == "download": continue
        mihomo_txt = f"output/mihomo/{name}.txt"
        if not os.path.exists(mihomo_txt):
            print(f"⚠️ [MosDNS] {name} 源文件不存在，跳过")
            continue
        lines = []
        with open(mihomo_txt, 'r', encoding='utf-8') as f:
            for line in f:
                cleaned = line.strip()
                if not cleaned or cleaned.startswith('#') or cleaned == '+.':
                    continue
                if 'skk.moe' in cleaned:
                    continue
                # 跳过 IP/CIDR 行：原始代码仅通过 clean_mihomo_domain_line 处理，
                # IP/CIDR 返回 None 被过滤。mihomo 输出含 IP 行，需显式跳过以保持一致。
                if utils.is_valid_ip_or_cidr(cleaned):
                    continue
                if cleaned.startswith('+.'):
                    lines.append('domain:' + cleaned[2:])
                else:
                    lines.append('full:' + cleaned)
        with open(f"output/mosdns-x/{name}.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print(f"✅ [MosDNS] {name:<25} | 规则数: {len(lines):,}")