# -*- coding: utf-8 -*-
"""
Upstream URL definitions and custom rule mappings.
All local addons and custom rules are loaded directly from disk in core/loaders.
"""

TARGET_BRANCHES = ("singbox", "mihomo", "smartdns", "mosdns-x", "adg")

# 白名单双层产物 (wuiiled/ad-whitelist-bot 唯一合成点):
#   main  = 后缀档 — 策展引用层 + 深条目, 放行语义覆盖其全部子域
#   exact = 精确档 — 裁决型来源的裸根域 (eTLD+1), 消费端按整域精确匹配、不连坐子域
ALLOW_URLS = [
    "https://raw.githubusercontent.com/wuiiled/ad-whitelist-bot/main/output/merged_false_positive_whitelist.txt"
]

ALLOW_EXACT_URLS = [
    "https://raw.githubusercontent.com/wuiiled/ad-whitelist-bot/main/output/merged_false_positive_whitelist_exact.txt"
]

ADS_BLOCK_URLS = [
    # AdGuard DNS Filter
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt",
    # Peter Lowe's Blocklist
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_3.txt",
    # Adobe Telemetry (Pi-hole 精确语义列表: loader 侧剥离已被具体子域覆盖的裸根域 adobe.io)
    "https://a.dove.isdumb.one/pihole.txt",
    # AWAvenue Ads Rule Geosite No.Unwelcome
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-Adguard-No.Unwelcome.txt",
    # OISD Small (官方直链; fetcher 内置 sjhgvr 镜像回退)
    "https://small.oisd.nl",
    # anti-AD
    "https://raw.githubusercontent.com/privacy-protection-tools/anti-AD/master/anti-ad-adguard.txt",
    # Hagezi Blocklists Light
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/light.txt",
]

# 精确匹配型广告源: 仅应剥离存在同族具体子域的裸根域, 防止后缀化连坐正常业务子域
EXACT_SEMANTIC_AD_URLS = frozenset({
    "https://a.dove.isdumb.one/pihole.txt",
})

# 来源画像: 完整 URL -> 展示名 (与 ADS_BLOCK_URLS 单一事实源绑定)
ADS_BLOCK_SOURCE_NAMES = {
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt": "AdGuard DNS filter",
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_3.txt": "Peter Lowe",
    "https://a.dove.isdumb.one/pihole.txt": "isdumb/Pi-hole",
    "https://small.oisd.nl": "OISD Small",
    "https://raw.githubusercontent.com/sjhgvr/oisd/main/oisd_small.txt": "OISD Small",
    "https://raw.githubusercontent.com/privacy-protection-tools/anti-AD/master/anti-ad-adguard.txt": "anti-AD",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/light.txt": "HaGeZi",
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-Adguard-No.Unwelcome.txt": "AWAvenue (广告+隐私)",
}

AI_URLS = [
    # MetaCubeX 海外 AI 分类 (classical list)
    "https://github.com/MetaCubeX/meta-rules-dat/raw/meta/geo/geosite/category-ai-!cn.list",
    "https://ruleset.skk.moe/List/non_ip/ai.conf",
    # DustinWin AI 规则
    "https://github.com/DustinWin/ruleset_geodata/raw/mihomo-ruleset/ai.list",
    # MagicRule GlobalAI (blackmatrix7/ios_rule_script 继承仓, Surge 规则集)
    "https://magicrule.pages.dev/#/c/Surge/r/24dbbb36-e5c5-4800-8fde-4af469213846",
    # dler-io AI Suite (Clash Provider)
    "https://github.com/dler-io/Rules/blob/main/Clash/Provider/AI%20Suite.yaml",
]

AI_IGNORED_ASNS: set = set()

# 任意源拉取失败时回退"上一次完整拉取"缓存的最大有效天数
SOURCE_CACHE_MAX_AGE_DAYS: int = 14

# ASN 第三级回退: 本仓库 mihomo 分支已发布的 geoip-ai.txt
GEOIP_AI_PUBLISHED_URL = "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-ai.txt"

FAKE_IP_URLS = [
    "https://raw.githubusercontent.com/vernesong/OpenClash/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list",
    "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list",
    "https://ruleset.skk.moe/Internal/clash_fake_ip_filter.yaml",
]

DROP_URLS = [
    "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt",
]

# IPTV 境外直播与流媒体规则 (Gary & Cathy 源)
IPTV_URLS = [
    "https://raw.githubusercontent.com/marcuccilli/gary/main/iptv_surge.list",
    "https://raw.githubusercontent.com/marcuccilli/Cathy/main/cathy_surge.list",
]

# geosite-stream 境外流媒体总集的 dat 分类清单 (视频/音频流媒体服务本体)
STREAM_DAT_CATEGORIES = (
    "netflix", "disney", "hbo", "hulu", "primevideo", "apple-tvplus", "youtube",
    "fox", "abc", "pbs", "bbc", "discoveryplus", "dazn",
    "spotify", "tidal", "deezer", "soundcloud", "kkbox",
    "bahamut", "abema", "niconico", "kktv", "litv", "mytvsuper", "japonx",
    "tiktok", "twitch", "viu", "tvb", "olevod",
    "tver", "hamivideo", "formula1", "hotstar", "amc", "catchplay",
    "imdb", "nhk", "rumble",
)

STREAM_URLS = [
    "https://raw.githubusercontent.com/sve1r/Rules-For-Quantumult-X/develop/Rules/Media/ForeignMedia.list",
    "https://ruleset.skk.moe/List/ip/stream.conf",
]

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
    "geoip-apple": "https://ruleset.skk.moe/List/ip/apple_services.conf",
}

PCDN_URLS = [
    "https://raw.githubusercontent.com/wuiiled/PCDN-mihomo-list/main/pcdn.list",
]

# OxiDNS (smartdns / mosdns-x 分支) 发布白名单, 与线上 config downloads 段一一对应
OXIDNS_RULESETS = (
    "geosite-cn",
    "geosite-ad",
    "geosite-custom-emby",
    "geosite-!cn",
    "geoip-cn",
    "geosite-apple-cdn",
    "geosite-apple-cn",
    "geosite-apple-services",
    "geosite-microsoft-cdn",
    "geosite-alibaba",
    "geosite-baidu",
    "geosite-bilibili",
    "geosite-bytedance",
    "geosite-qihoo360",
    "geosite-tencent",
    "geosite-xiaomi",
)

OXIDNS_EXTRA_RULESETS = {"geosite-ad-precise", "geosite-ad-allow", "geoip-gfw"}

OXIDNS_SUBDIR_ALIASES = {
    "geosite/geosite-geolocation-!cn.txt": "geosite-!cn",
}

GFW_IP_URLS = [
    "https://raw.githubusercontent.com/pmkol/easymosdns/rules/gfw_ip_list.txt",
]
