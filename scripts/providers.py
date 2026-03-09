ALLOW_URLS = [
    "https://raw.githubusercontent.com/Cats-Team/AdRules/refs/heads/script/script/allowlist.txt",
    "https://raw.githubusercontent.com/AdguardTeam/AdGuardSDNSFilter/master/Filters/exceptions.txt",
]

ADS_BLOCK_URLS = [
    "https://raw.githubusercontent.com/pmkol/easymosdns/rules/ad_domain_list.txt",
    "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/Reject-addon.txt",
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt",
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_3.txt",
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_4.txt",
    "https://raw.githubusercontent.com/ForestL18/rules-dat/mihomo/geo/classical/pcdn.list",
    "https://a.dove.isdumb.one/pihole.txt",
    "https://raw.githubusercontent.com/Cats-Team/AdRules/main/adrules_domainset.txt",
]

AI_URLS = [
    "https://github.com/MetaCubeX/meta-rules-dat/raw/meta/geo/geosite/category-ai-!cn.list",
    "https://ruleset.skk.moe/List/non_ip/ai.conf",
    "https://github.com/DustinWin/ruleset_geodata/raw/mihomo-ruleset/ai.list",
    "https://raw.githubusercontent.com/ConnersHua/RuleGo/refs/heads/master/Surge/Ruleset/Extra/AI.list"
]

FAKE_IP_URLS = [
    "https://raw.githubusercontent.com/vernesong/OpenClash/refs/heads/master/luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list",
    "https://raw.githubusercontent.com/juewuy/ShellCrash/dev/public/fake_ip_filter.list",
    "https://raw.githubusercontent.com/DustinWin/ruleset_geodata/refs/heads/mihomo-ruleset/fakeip-filter.list",
    "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/scripts/fake-ip-addon.txt",
    "https://ruleset.skk.moe/Internal/clash_fake_ip_filter.yaml"
]

DROP_URLS = [
    "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt",
    "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/master/rules/Custom_Reject-drop.txt"
]

CN_URLS_1 = ["https://static-file-global.353355.xyz/rules/cn-additional-list.txt"]
CN_URLS_2 = ["https://ruleset.skk.moe/Clash/non_ip/domestic.txt"]

MIHOMO_GENERIC_RAW = {
    "AppleProxy": "https://raw.githubusercontent.com/Repcz/Tool/refs/heads/X/mihomo/Rules/AppleProxy.list",
    "AppleServers": "https://raw.githubusercontent.com/Repcz/Tool/refs/heads/X/mihomo/Rules/AppleServers.list",
    "AppleCN": "https://raw.githubusercontent.com/Repcz/Tool/refs/heads/X/mihomo/Rules/AppleCN.list",
    "private": "https://raw.githubusercontent.com/ForestL18/rules-dat/refs/heads/mihomo/geo/classical/private.list",
    "Custom_DNS_DOMAIN": "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/rules/Custom_DNS_DOMAIN.txt",
    "Custom_DNS_IP": "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/rules/Custom_DNS_IP.txt",
    "Custom_Direct_DOMAIN": "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/rules/Custom_Direct_DOMAIN.txt",
    "Custom_Direct_IP": "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/rules/Custom_Direct_IP.txt",
    "Custom_Emby": "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/rules/Custom_Emby.txt",
    "Custom_Proxy": "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/rules/Custom_Proxy.txt",
    "LocationDKS": "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/refs/heads/master/rules/LocationDKS.txt"
}

MIHOMO_SKK = {
    "alibaba": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/alibaba.txt",
    "tencent": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/tencent.txt",
    "bilibili": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/bilibili.txt",
    "xiaomi": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/xiaomi.txt",
    "bytedance": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/bytedance.txt",
    "baidu": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/baidu.txt",
    "qihoo360": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/qihoo360.txt",
    "download": "https://ruleset.skk.moe/Clash/domainset/download.txt",
    "domestic": "https://ruleset.skk.moe/Clash/non_ip/domestic.txt"
}

ADG_URLS = {
    "Httpdns": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geosite/category-httpdns-cn.list",
    "PCDN": "https://raw.githubusercontent.com/wuiiled/PCDN-mihomo-list/refs/heads/main/pcdn.list"
}