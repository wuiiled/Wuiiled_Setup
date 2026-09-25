# -*- coding: utf-8 -*-
"""
Upstream URL definitions and custom rule mappings.
All local addons and custom rules are loaded directly from disk in manager.py.
"""

ALLOW_URLS = [
    # Cats-Team dns-allowlist
    "https://raw.githubusercontent.com/Cats-Team/AdRules/script/mod/rules/dns-allowlist.txt",
    # AdGuard SDNS Filter exceptions
    "https://raw.githubusercontent.com/AdguardTeam/AdGuardSDNSFilter/master/Filters/exceptions.txt",
    # anudeepND whitelist
    "https://raw.githubusercontent.com/anudeepND/whitelist/master/domains/whitelist.txt",
]

ADS_BLOCK_URLS = [
    # EasyMosdns ad_domain_list
    "https://raw.githubusercontent.com/pmkol/easymosdns/rules/ad_domain_list.txt",
    # AdGuard DNS Filter
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt",
    # Peter Lowe's Blocklist
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_3.txt",
    # Dan Pollock's List
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_4.txt",
    # Adobe Telemetry
    "https://a.dove.isdumb.one/pihole.txt",
    # Cats-Team adrules_domainset
    "https://raw.githubusercontent.com/Cats-Team/AdRules/main/adrules_domainset.txt",
    # AWAvenue Ads Rule Geosite
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-Geosite.txt",
    # OISD Small
    "https://raw.githubusercontent.com/sjhgvr/oisd/main/domainswild_small.txt",
]

AI_URLS = [
    # MetaCubeX 海外 AI 分类 (classical list)
    "https://github.com/MetaCubeX/meta-rules-dat/raw/meta/geo/geosite/category-ai-!cn.list",
    "https://ruleset.skk.moe/List/non_ip/ai.conf",
    # DustinWin AI 规则
    "https://github.com/DustinWin/ruleset_geodata/raw/mihomo-ruleset/ai.list",
]

FAKE_IP_URLS = [
    "https://raw.githubusercontent.com/vernesong/OpenClash/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list",
    "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list",
    # DustinWin Fake-IP 过滤
    "https://raw.githubusercontent.com/DustinWin/ruleset_geodata/mihomo-ruleset/fakeip-filter.list",
    "https://ruleset.skk.moe/Internal/clash_fake_ip_filter.yaml"
]

DROP_URLS = [
    "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt",
]

# 注: 原 CN_URLS_1/CN_URLS_2 (cn-additional-list + SKK domestic) 已迁移至
# rules/patches/geosite-cn.txt 的 include 指令, 与天灵配方 cn 统一经补丁通道合并。

CUSTOM_RULES = {
    "geosite-custom-direct": "rules/Custom_Direct_DOMAIN.txt",
    "geoip-custom-direct": "rules/Custom_Direct_IP.txt",
    "geosite-custom-dns": "rules/Custom_DNS_DOMAIN.txt",
    "geoip-custom-dns": "rules/Custom_DNS_IP.txt",
    "geosite-custom-emby": "rules/Custom_Emby.txt",
    "geosite-custom-proxy": "rules/Custom_Proxy.txt",
    "geosite-custom-download": "rules/Custom_Download.txt",
    "geosite-location-dks": "rules/LocationDKS.txt",
}

MIHOMO_SKK = {
    "geosite-alibaba": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/alibaba.txt",
    "geosite-tencent": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/tencent.txt",
    "geosite-bilibili": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/bilibili.txt",
    "geosite-xiaomi": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/xiaomi.txt",
    "geosite-bytedance": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/bytedance.txt",
    "geosite-baidu": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/baidu.txt",
    "geosite-qihoo360": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/qihoo360.txt",
    "geosite-domestic": "https://ruleset.skk.moe/Clash/non_ip/domestic.txt",
    "geosite-download": "https://ruleset.skk.moe/Clash/domainset/download.txt",
    "geosite-microsoft-cdn": "https://ruleset.skk.moe/Clash/non_ip/microsoft_cdn.txt",
    "geosite-apple-services": "https://ruleset.skk.moe/Clash/non_ip/apple_services.txt",
    "geosite-apple-cn": "https://ruleset.skk.moe/Clash/non_ip/apple_cn.txt",
    "geosite-apple-cdn": "https://ruleset.skk.moe/Clash/domainset/apple_cdn.txt",
    "geoip-stream": "https://ruleset.skk.moe/List/ip/stream.conf",
    "geoip-apple": "https://ruleset.skk.moe/List/ip/apple_services.conf",
}

# PCDN 拦截列表: 统一经 IR 装载 (manager.load_pcdn_rules), 各平台导出并进入来源画像
PCDN_URLS = [
    "https://raw.githubusercontent.com/wuiiled/PCDN-mihomo-list/main/pcdn.list"
]

# OxiDNS (mosdns 分支) 从 smartdns 分支拉取的规则文件清单，
# 与 OxiDNS 配置文件中 downloads 段的 URL 一一对应。
# smartdns / mosdns-x 分支只同步这些规则集；同时在 rules/ 根目录以 OxiDNS
# 期望的历史文件名落一份兼容副本，保证线上 OxiDNS 配置的订阅直链持续可用。
OXIDNS_RULE_FILES = {
    "CN_merged.txt": "geosite-cn",
    "ADs_merged.txt": "geosite-ad",
    "Custom_Emby.txt": "geosite-custom-emby",
    "proxy.txt": "geosite-!cn",
    "cnip.txt": "geoip-cn",
    "apple_cdn.txt": "geosite-apple-cdn",
    "apple_cn.txt": "geosite-apple-cn",
    "apple_services.txt": "geosite-apple-services",
    "microsoft_cdn.txt": "geosite-microsoft-cdn",
    "alibaba.txt": "geosite-alibaba",
    "baidu.txt": "geosite-baidu",
    "bilibili.txt": "geosite-bilibili",
    "bytedance.txt": "geosite-bytedance",
    "qihoo360.txt": "geosite-qihoo360",
    "tencent.txt": "geosite-tencent",
    "xiaomi.txt": "geosite-xiaomi",
}

# 线上 OxiDNS (10.0.0.2, config v1.5.2) 额外订阅、但无需根目录兼容副本的集合
# (直接下载 rules/geosite|geoip/ 下的标准名文件, 2026-09-26 与线上 downloads 段对齐):
#   - 黑加白双集合 (线上 sequence: qname $ad_allow → return 前置短路 + $ad_precise drop)
#   - GFW 投毒 IP 靶心
# 缺失任一项都会让线上对应下载 URL 404、规则文件停更 (2026-09-25~26 事故)。
OXIDNS_EXTRA_RULESETS = {"geosite-ad-precise", "geosite-ad-allow", "geoip-gfw"}

# 线上以旧命名订阅、需在 geosite/ 子目录落一份别名副本的集合:
# 引擎内标准名为 geosite-!cn, 线上 URL 为 rules/geosite/geosite-geolocation-!cn.txt。
# 别名不参与 README 渲染与计数 (readme_gen 排除), 避免"规则集数"虚增。
OXIDNS_SUBDIR_ALIASES = {
    "geosite/geosite-geolocation-!cn.txt": "geosite-!cn",
}

GFW_IP_URLS = [
    "https://raw.githubusercontent.com/clowwindy/ChinaDNS/master/iplist.txt",
    "https://cdn.jsdelivr.net/gh/clowwindy/ChinaDNS@master/iplist.txt",
    "https://raw.githubusercontent.com/pmkol/easymosdns/rules/gfw_ip_list.txt",
    "https://cdn.jsdelivr.net/gh/pmkol/easymosdns@rules/gfw_ip_list.txt",
]

GFW_IPV6_LIST = [
    "2001:4860:4860::8888",
    "2001:4860:4860::8844",
    "2001:da8::666",
    "2404:6800:4008:c01::65",
    "2001:252:0:1::/64",
    "2001:470:20::2",
    "2001:7fa::1",
    "2a03:2880:f100::/40",
    # NOTE: 3ffe::/20 is the mihomo fake-ip v6 range paired with this engine
    # (network topology v4.4+). Kept so OxiDNS resp_ip fallback can identify
    # fake-ip answers. Do NOT widen to 3ffe::/16 or it overflows and wrongly
    # drops legitimate non-fake-ip v6 answers.
    "3ffe::/20",
]
