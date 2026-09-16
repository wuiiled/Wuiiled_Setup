# -*- coding: utf-8 -*-
import os

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
    # Reject-addon
    "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/scripts/Reject-addon.txt",
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
    "https://ruleset.skk.moe/List/non_ip/ai.conf",
]

FAKE_IP_URLS = [
    "https://raw.githubusercontent.com/vernesong/OpenClash/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list",
    "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list",
    "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/scripts/fake-ip-addon.txt",
    "https://ruleset.skk.moe/Internal/clash_fake_ip_filter.yaml"
]

DROP_URLS = [
    "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt",
    "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/rules/Custom_Reject-drop.txt"
]

CUSTOM_RULES = {
    "geosite-custom-direct": "rules/Custom_Direct_DOMAIN.txt",
    "geoip-custom-direct": "rules/Custom_Direct_IP.txt",
    "geosite-custom-dns": "rules/Custom_DNS_DOMAIN.txt",
    "geoip-custom-dns": "rules/Custom_DNS_IP.txt",
    "geosite-custom-emby": "rules/Custom_Emby.txt",
    "geosite-custom-proxy": "rules/Custom_Proxy.txt",
    "geosite-custom-download": "rules/Custom_Download.txt",
    "LocationDKS": "rules/LocationDKS.txt",
}

MIHOMO_SKK = {
    "alibaba": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/alibaba.txt",
    "tencent": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/tencent.txt",
    "bilibili": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/bilibili.txt",
    "xiaomi": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/xiaomi.txt",
    "bytedance": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/bytedance.txt",
    "baidu": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/baidu.txt",
    "qihoo360": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/qihoo360.txt",
    "domestic": "https://ruleset.skk.moe/Clash/non_ip/domestic.txt",
    "geosite-download": "https://ruleset.skk.moe/Clash/domainset/download.txt",
    "geosite-microsoft-cdn": "https://ruleset.skk.moe/Clash/non_ip/microsoft_cdn.txt",
    "geosite-apple-services": "https://ruleset.skk.moe/Clash/non_ip/apple_services.txt",
    "geosite-apple-cn": "https://ruleset.skk.moe/Clash/non_ip/apple_cn.txt",
    "geosite-apple-cdn": "https://ruleset.skk.moe/Clash/domainset/apple_cdn.txt",
    "geoip-stream": "https://ruleset.skk.moe/List/ip/stream.conf",
    "geoip-apple": "https://ruleset.skk.moe/List/ip/apple_services.conf",
}

ADG_URLS = {
    "PCDN": "https://raw.githubusercontent.com/wuiiled/PCDN-mihomo-list/main/pcdn.list"
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
    "3ffe::/16",
    "100::/64",
    "2a03:2880:f100::/40",
    "2001:db8::/32",
    "::1",
    "::",
]
