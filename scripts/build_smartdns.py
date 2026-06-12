#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import glob
import utils

def convert_txt_to_smartdns(src_path, dst_path, is_ip):
    base_name = os.path.splitext(os.path.basename(src_path))[0]
    smartdns_lines = []
    
    with open(src_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                smartdns_lines.append(line)
                continue
            
            # 过滤尾部注释
            parts = line.split('#')
            rule = parts[0].strip()
            comment = f" #{parts[1]}" if len(parts) > 1 else ""
            
            if not rule:
                continue
                
            if is_ip:
                # IP-set 模式：只保留有效的 IP 或 CIDR
                cleaned_ip = utils.clean_ip_line(rule)
                if cleaned_ip and utils.is_valid_ip_or_cidr(cleaned_ip):
                    smartdns_lines.append(cleaned_ip + comment)
            else:
                # Domain-set 模式：过滤掉 IP，并转换域名匹配语法
                if utils.is_valid_ip_or_cidr(rule):
                    continue
                    
                if rule.startswith('+.'):
                    converted = rule[2:]
                elif rule.startswith('.'):
                    converted = rule[1:]
                elif rule.startswith('*.'):
                    converted = rule
                elif rule.startswith('-.'):
                    converted = rule
                else:
                    # Mihomo 中不含通配前缀的为精确匹配，映射到 SmartDNS 的 -. 匹配
                    converted = "-." + rule
                    
                smartdns_lines.append(converted + comment)
            
    # 统计有效规则条数 (排除了空行和注释)
    rules_count = sum(1 for l in smartdns_lines if l.strip() and not l.strip().startswith('#'))
    
    if rules_count == 0:
        print(f"⚠️ [SmartDNS] {base_name:<25} | ⚠️ 规则为空被跳过")
        return False
        
    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(smartdns_lines) + '\n')
        
    print(f"✅ [SmartDNS] {base_name:<25} | {'IP-set' if is_ip else 'Domain-set'} | 规则数: {rules_count:,}")
    return True

def run_all():
    os.makedirs("output/smartdns", exist_ok=True)
    # 从已经构建完成的 mihomo 规则文本目录进行转换
    txt_files = glob.glob("output/mihomo/*.txt")
    for src in txt_files:
        base_name = os.path.splitext(os.path.basename(src))[0]
        is_ip = base_name.endswith("_IP") or base_name == "cnip"
        dst = os.path.join("output/smartdns", f"{base_name}.txt")
        convert_txt_to_smartdns(src, dst, is_ip)

if __name__ == '__main__':
    run_all()
