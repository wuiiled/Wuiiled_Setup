#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import os
import sys
import time
import urllib.request
import ipaddress

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def decode_varint(stream):
    res = 0
    shift = 0
    while True:
        b = stream.read(1)
        if not b: return None
        val = b[0]
        res |= (val & 0x7F) << shift
        if not (val & 0x80): break
        shift += 7
    return res

def parse_geosite(dat_bytes):
    stream = io.BytesIO(dat_bytes)
    total_len = len(dat_bytes)
    domain_map = {}
    
    while stream.tell() < total_len:
        tag = decode_varint(stream)
        if tag is None: break
        field_num = tag >> 3
        wire_type = tag & 0x7
        if field_num == 1 and wire_type == 2:
            length = decode_varint(stream)
            entry_bytes = stream.read(length)
            
            es = io.BytesIO(entry_bytes)
            code = ""
            domains = []
            attributes = {}
            
            while es.tell() < len(entry_bytes):
                etag = decode_varint(es)
                if etag is None: break
                efield = etag >> 3
                ewire = etag & 0x7
                if efield == 1 and ewire == 2:
                    elen = decode_varint(es)
                    code = es.read(elen).decode('utf-8', errors='ignore').lower()
                elif efield == 2 and ewire == 2:
                    dlen = decode_varint(es)
                    dbytes = es.read(dlen)
                    ds = io.BytesIO(dbytes)
                    dtype = 0
                    dval = ""
                    attrs = []
                    while ds.tell() < len(dbytes):
                        dtag = decode_varint(ds)
                        if dtag is None: break
                        dfield = dtag >> 3
                        dwire = dtag & 0x7
                        if dfield == 1 and dwire == 0:
                            dtype = decode_varint(ds)
                        elif dfield == 2 and dwire == 2:
                            flen = decode_varint(ds)
                            dval = ds.read(flen).decode('utf-8', errors='ignore')
                        elif dfield == 3 and dwire == 2:
                            flen = decode_varint(ds)
                            ab = ds.read(flen)
                            as_io = io.BytesIO(ab)
                            while as_io.tell() < len(ab):
                                atag = decode_varint(as_io)
                                if atag is None: break
                                if (atag >> 3) == 1:
                                    klen = decode_varint(as_io)
                                    attrs.append(as_io.read(klen).decode('utf-8', errors='ignore'))
                                    break
                                else:
                                    break
                        elif dwire == 0: decode_varint(ds)
                        elif dwire == 2: ds.read(decode_varint(ds))
                        elif dwire == 1: ds.read(8)
                        elif dwire == 5: ds.read(4)
                    
                    items = []
                    if dtype == 0:
                        items.append(('keyword', dval))
                    elif dtype == 1:
                        items.append(('regex', dval))
                    elif dtype == 2:
                        if '.' in dval:
                            items.append(('domain', dval))
                        items.append(('domain_suffix', '.' + dval))
                    elif dtype == 3:
                        items.append(('domain', dval))
                        
                    domains.extend(items)
                    for a in attrs:
                        attributes.setdefault(a, []).extend(items)
                elif ewire == 0: decode_varint(es)
                elif ewire == 2: es.read(decode_varint(es))
                elif ewire == 1: es.read(8)
                elif ewire == 5: es.read(4)
                
            if code:
                domain_map[code] = list(dict.fromkeys(domains))
                for attr, attr_entries in attributes.items():
                    domain_map[f"{code}@{attr}"] = list(dict.fromkeys(attr_entries))
        elif wire_type == 0: decode_varint(stream)
        elif wire_type == 2: stream.read(decode_varint(stream))
        elif wire_type == 1: stream.read(8)
        elif wire_type == 5: stream.read(4)
        
    return domain_map

def filter_tags(data):
    code_list = list(data.keys())
    bad_code_list = []
    
    for code in code_list:
        parts = code.split("@")
        if len(parts) != 2: continue
        tag, attr = parts[0], parts[1]
        last_name = tag.split("-")[-1] if "-" in tag else tag
        
        if last_name == attr:
            del data[code]
            continue
            
        if f"!{last_name}" == attr or last_name == f"!{attr}":
            bad_code_list.append((tag, code))
            
    for base_tag, bad_code in bad_code_list:
        if bad_code in data and base_tag in data:
            bad_set = set(data[bad_code])
            del data[bad_code]
            data[base_tag] = [item for item in data[base_tag] if item not in bad_set]

def merge_tags(data):
    cn_code_list = []
    for code in list(data.keys()):
        if "@" in code:
            parts = code.split("@")
            if parts[1] == "cn" and parts[0].startswith("category-") and not parts[0].endswith("-cn") and not parts[0].endswith("-!cn"):
                cn_code_list.append(code)
        else:
            if code.startswith("category-") and code.endswith("-cn"):
                cn_code_list.append(code)
                
    merged_items = set(data.get("geolocation-cn", []))
    for code in cn_code_list:
        merged_items.update(data.get(code, []))
        
    merged_items.add(('domain_suffix', 'cn'))
    data["cn"] = list(merged_items)
    data["geolocation-cn"] = [item for item in merged_items if item != ('domain_suffix', 'cn')]

GEOSITE_TARGETS = {
    "cn": "geosite-cn",
    "geolocation-!cn": "geosite-geolocation-!cn",
    "gfw": "geosite-gfw",
    "google": "geosite-google",
    "youtube": "geosite-youtube",
    "github": "geosite-github",
    "onedrive": "geosite-onedrive",
    "microsoft": "geosite-microsoft",
    "tiktok": "geosite-tiktok",
    "spotify": "geosite-spotify",
    "netflix": "geosite-netflix",
    "disney": "geosite-disney",
    "category-porn": "geosite-porn",
    "category-media": "geosite-media",
    "category-communication": "geosite-communication",
    "category-social-media-!cn": "geosite-social-media",
    "category-games": "geosite-games",
    "category-games-cn": "geosite-games-cn",
    "private": "geosite-private",
    "apple-tvplus": "geosite-apple-tvplus",
    "category-httpdns-cn": "geosite-httpdns"
}

GEOIP_TARGETS = {
    "geoip-google": "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/text/google.txt",
    "geoip-telegram": "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/text/telegram.txt",
    "geoip-twitter": "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/text/twitter.txt",
    "geoip-facebook": "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/text/facebook.txt",
    "geoip-private": "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/text/private.txt",
    "geoip-cn": "https://gaoyifan.github.io/china-operator-ip/china46.txt"
}

def extract_all(cache_dir="."):
    os.makedirs("output/mihomo", exist_ok=True)
    
    # 1. Download geosite.dat
    dat_path = os.path.join(cache_dir, "geosite.dat")
    if not os.path.exists(dat_path) or (time.time() - os.path.getmtime(dat_path) > 86400):
        print("🌐 正在从 Loyalsoldier 下载最新 geosite.dat...")
        url = "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp, open(dat_path, "wb") as f:
            f.write(resp.read())
            
    print("⚡️ 解析与提纯 GeoSite 规则...")
    t0 = time.time()
    with open(dat_path, "rb") as f:
        dat_bytes = f.read()
    domain_map = parse_geosite(dat_bytes)
    filter_tags(domain_map)
    merge_tags(domain_map)
    print(f"✅ GeoSite 数据解析完毕 (耗时: {time.time() - t0:.2f}s)")
    
    # Export geosite text files
    for src_tag, dst_name in GEOSITE_TARGETS.items():
        items = domain_map.get(src_tag, [])
        lines = set()
        for itype, ival in items:
            if itype == 'domain':
                lines.add(ival)
            elif itype == 'domain_suffix':
                clean_val = ival.lstrip('.')
                lines.add("+." + clean_val)
            elif itype == 'regex':
                lines.add(ival)
            elif itype == 'keyword':
                lines.add(ival)
                
        out_txt = os.path.join("output/mihomo", f"{dst_name}.txt")
        sorted_lines = sorted(list(lines))
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write('\n'.join(sorted_lines) + ('\n' if sorted_lines else ''))
        print(f"✅ [GeoSite] {dst_name:<26} | 规则数: {len(sorted_lines):,}")
        
    # 2. Extract GeoIPs
    print("⚡️ 下载与提纯 GeoIP 规则...")
    for dst_name, url in GEOIP_TARGETS.items():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw_lines = resp.read().decode('utf-8', errors='ignore').splitlines()
                
            clean_ips = []
            for line in raw_lines:
                line = line.strip()
                if not line or line.startswith('#'): continue
                line = line.split('#')[0].strip()
                try:
                    net = ipaddress.ip_network(line, strict=False)
                    clean_ips.append(str(net))
                except ValueError:
                    continue
                    
            clean_ips = sorted(list(set(clean_ips)))
            out_txt = os.path.join("output/mihomo", f"{dst_name}.txt")
            with open(out_txt, "w", encoding="utf-8") as f:
                f.write('\n'.join(clean_ips) + ('\n' if clean_ips else ''))
            print(f"✅ [GeoIP]   {dst_name:<26} | 规则数: {len(clean_ips):,}")
        except Exception as e:
            print(f"⚠️ GeoIP {dst_name} 下载/处理失败: {e}")

if __name__ == "__main__":
    extract_all()
