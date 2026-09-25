# -*- coding: utf-8 -*-
"""
Intelligent README Generator for All Distribution Branches.
Generates beautiful, compact, dual-format tables and copy-paste client configurations.
Completely replaces the fragile inline Bash script in GitHub Actions.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set

import providers

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

NL = chr(10)


# Branch display metadata: (emoji, title, format badge text, primary format)
_BRANCH_META = {
    "singbox":  ("📦", "Sing-box",  ".srs / .json",  "binary"),
    "mihomo":   ("📦", "Mihomo (Clash Meta)", ".mrs / .txt", "mrs"),
    "smartdns": ("📦", "SmartDNS",  "domain-set / ip-set", "txt"),
    "mosdns-x": ("📦", "MosDNS-X",  "domain: / full:", "txt"),
    "adg":      ("📦", "AdGuard Home", "AdGuard filter", "txt"),
}

# Unified Categorization and Metadata for all 120+ rule sets
CATEGORY_DEFS = [
    ("ai", "🤖 人工智能与开发 (AI & Dev)", [
        "geosite-ai", "geosite-openai", "geosite-anthropic", "geosite-gemini",
        "geosite-github", "geosite-gitlab", "geosite-docker", "geosite-stackoverflow", "geosite-npm"
    ]),
    ("social", "💬 社交与即时通讯 (Social & IM)", [
        "geosite-communication", "geosite-social-media", "geosite-telegram", "geosite-discord",
        "geosite-whatsapp", "geosite-signal", "geosite-line", "geosite-x",
        "geosite-instagram", "geosite-threads", "geosite-reddit", "geosite-bluesky", "geosite-tiktok"
    ]),
    ("media", "🎬 影音流媒体与娱乐 (Media & Streaming)", [
        "geosite-media", "geosite-entertainment", "geosite-youtube", "geosite-netflix",
        "geosite-disney", "geosite-spotify", "geosite-apple-tvplus", "geosite-hbo",
        "geosite-hulu", "geosite-primevideo", "geosite-twitch", "geosite-bahamut",
        "geosite-abema", "geosite-niconico", "geosite-dmm", "geosite-pixiv",
        "geosite-vimeo", "geosite-dailymotion", "geosite-deezer", "geosite-soundcloud", "geosite-tidal"
    ]),
    ("gaming", "🎮 游戏平台与联机服务 (Gaming)", [
        "geosite-games", "geosite-games-cn", "geosite-games-!cn", "geosite-steam",
        "geosite-epicgames", "geosite-playstation", "geosite-xbox", "geosite-nintendo",
        "geosite-ea", "geosite-ubisoft", "geosite-rockstar", "geosite-blizzard",
        "geosite-riotgames", "geosite-mihoyo", "geosite-hoyoverse"
    ]),
    ("finance", "💰 金融支付与加密货币 (Finance & Crypto)", [
        "geosite-paypal", "geosite-stripe", "geosite-wise", "geosite-binance", "geosite-okx"
    ]),
    ("cloud", "🌐 网络基建与协同办公 (Cloud & SaaS)", [
        "geosite-cloudflare", "geosite-fastly", "geosite-akamai", "geosite-vercel",
        "geosite-netlify", "geosite-microsoft", "geosite-microsoft-cdn", "geosite-onedrive",
        "geosite-google", "geosite-apple-services", "geosite-apple-cdn", "geosite-notion",
        "geosite-figma", "geosite-canva", "geosite-zoom", "geosite-netdisk-!cn"
    ]),
    ("china", "🇨🇳 国内直连与核心大厂 (China & Ecosystem)", [
        "geosite-cn", "geosite-!cn", "geosite-alibaba", "geosite-tencent",
        "geosite-bilibili", "geosite-xiaomi", "geosite-bytedance", "geosite-baidu",
        "geosite-qihoo360", "geosite-domestic", "geosite-apple-cn", "geosite-download"
    ]),
    ("security", "🛡️ 安全防护与过滤拦截 (Security & Blocking)", [
        "geosite-ad", "geosite-ad-precise", "geosite-ad-allow", "geosite-gfw",
        "geosite-reject-drop", "geosite-fakeip-filter", "geosite-porn", "geosite-httpdns",
        "geosite-private", "geosite-pcdn"
    ]),
    ("custom", "🛠️ 本地自定义与特征分流 (Custom Routing)", [
        "geosite-custom-direct", "geosite-custom-dns", "geosite-custom-emby",
        "geosite-custom-proxy", "geosite-custom-download", "geosite-location-dks"
    ]),
    ("geoip", "🌍 GeoIP 地址段网段集合 (IP Networks)", [
        "geoip-cn", "geoip-google", "geoip-telegram", "geoip-twitter",
        "geoip-facebook", "geoip-gfw", "geoip-private", "geoip-stream",
        "geoip-apple", "geoip-custom-direct", "geoip-custom-dns"
    ])
]

# 人工服务描述表。"说明/包含" 列由构建期 manifest 动态渲染:
#   dat 派生 -> "dat 分类 <code> · 含 <已验证平台>"; 合成/自研 -> "上游: <仓库列表>"。
# 禁止在此写死条数或平台清单 —— 会随上游漂移 (由 tests/test_readme_gen.py 防护)。
RULE_METADATA: Dict[str, Dict[str, str]] = {
    # 🤖 AI & Dev
    "geosite-ai": {"desc": "全球主流 AI 服务合集 (自研列表 ∪ dat 分类)"},
    "geosite-openai": {"desc": "OpenAI / ChatGPT 官方服务与 API"},
    "geosite-anthropic": {"desc": "Anthropic Claude 官方服务与 API"},
    "geosite-gemini": {"desc": "Google Gemini / Bard 人工智能服务"},
    "geosite-github": {"desc": "GitHub 代码托管平台与开发者资产"},
    "geosite-gitlab": {"desc": "GitLab 代码托管与 DevOps 云服务"},
    "geosite-docker": {"desc": "Docker Hub 容器镜像与注册表"},
    "geosite-stackoverflow": {"desc": "Stack Overflow 与开发者技术社区"},
    "geosite-npm": {"desc": "Node.js NPM 官方包管理器软件源"},

    # 💬 Social & IM
    "geosite-communication": {"desc": "全球即时通讯与在线会议聚合"},
    "geosite-social-media": {"desc": "全球社交网络与媒体平台聚合"},
    "geosite-telegram": {"desc": "Telegram 电报全系官方通讯服务"},
    "geosite-discord": {"desc": "Discord 语音与社群即时通讯平台"},
    "geosite-whatsapp": {"desc": "WhatsApp 即时通讯与端到端加密"},
    "geosite-signal": {"desc": "Signal 隐私加密即时通讯服务"},
    "geosite-line": {"desc": "LINE 亚洲流行即时通讯与生活服务"},
    "geosite-x": {"desc": "X (原 Twitter) 官方社交媒体平台"},
    "geosite-instagram": {"desc": "Instagram 社交图像与短视频平台"},
    "geosite-threads": {"desc": "Threads 文本社交互动媒体平台"},
    "geosite-reddit": {"desc": "Reddit 全球兴趣与新闻社区"},
    "geosite-bluesky": {"desc": "Bluesky 去中心化社交网络平台"},
    "geosite-tiktok": {"desc": "TikTok 国际版短视频平台"},

    # 🎬 Media & Streaming
    "geosite-media": {"desc": "国际新闻媒体与区域电视台聚合 (新闻社/报媒/区域电视)"},
    "geosite-entertainment": {"desc": "全球影音娱乐与流媒体聚合"},
    "geosite-youtube": {"desc": "YouTube 视频流媒体与 YouTube Music"},
    "geosite-netflix": {"desc": "Netflix 奈飞全球影音流媒体平台"},
    "geosite-disney": {"desc": "Disney+ 迪士尼流媒体播放服务"},
    "geosite-spotify": {"desc": "Spotify 全球最大音乐流媒体服务"},
    "geosite-apple-tvplus": {"desc": "Apple TV+ 苹果原创影视流媒体"},
    "geosite-hbo": {"desc": "HBO Max / HBO 全球影视服务"},
    "geosite-hulu": {"desc": "Hulu 影视点播流媒体平台"},
    "geosite-primevideo": {"desc": "Amazon Prime Video 亚马逊影音"},
    "geosite-twitch": {"desc": "Twitch 全球游戏与互动直播平台"},
    "geosite-bahamut": {"desc": "巴哈姆特动画疯 (台湾主流动漫平台)"},
    "geosite-abema": {"desc": "AbemaTV 日本网络电视流媒体"},
    "geosite-niconico": {"desc": "Niconico (N站) 日本弹幕视频网站"},
    "geosite-dmm": {"desc": "DMM.com 日本综合数字内容娱乐"},
    "geosite-pixiv": {"desc": "Pixiv (P站) 日本插画二次元艺术社区"},
    "geosite-vimeo": {"desc": "Vimeo 高清原创视频创作分享平台"},
    "geosite-dailymotion": {"desc": "Dailymotion 国际视频共享服务"},
    "geosite-deezer": {"desc": "Deezer 高保真音乐流媒体服务"},
    "geosite-soundcloud": {"desc": "SoundCloud 原创音乐与音频分享"},
    "geosite-tidal": {"desc": "TIDAL HiFi 无损高品质音乐流媒体"},

    # 🎮 Gaming
    "geosite-games": {"desc": "全球热门游戏与联机加速合集"},
    "geosite-games-cn": {"desc": "国内主流网络游戏与加速服务"},
    "geosite-games-!cn": {"desc": "外服主机与端游联机加速合集"},
    "geosite-steam": {"desc": "Valve Steam 全球最大游戏平台"},
    "geosite-epicgames": {"desc": "Epic Games 游戏商城与虚幻联机"},
    "geosite-playstation": {"desc": "Sony PlayStation Network (PSN)"},
    "geosite-xbox": {"desc": "Microsoft Xbox Live 游戏与 GamePass"},
    "geosite-nintendo": {"desc": "Nintendo 任天堂 Switch 联机与商城"},
    "geosite-ea": {"desc": "Electronic Arts (EA / Origin) 平台"},
    "geosite-ubisoft": {"desc": "Ubisoft Connect 育碧游戏与联机"},
    "geosite-rockstar": {"desc": "Rockstar Games 摇滚之星 (GTA/RDR)"},
    "geosite-blizzard": {"desc": "Blizzard 暴雪战网国际服联机服务"},
    "geosite-riotgames": {"desc": "Riot Games 拳头游戏 (LOL/Valorant)"},
    "geosite-mihoyo": {"desc": "米哈游 (MiHoYo) 原神/星铁境外分流"},
    "geosite-hoyoverse": {"desc": "HoYoverse 米哈游海外发行平台"},

    # 💰 Finance & Crypto
    "geosite-paypal": {"desc": "PayPal 全球主流跨境在线支付平台"},
    "geosite-stripe": {"desc": "Stripe 国际在线支付结算网关"},
    "geosite-wise": {"desc": "Wise (原 TransferWise) 跨境汇款"},
    "geosite-binance": {"desc": "币安 (Binance) 全球最大加密货币交易"},
    "geosite-okx": {"desc": "欧易 (OKX) 全球主流加密货币交易"},

    # 🌐 Cloud & SaaS
    "geosite-cloudflare": {"desc": "Cloudflare 全球 CDN 与安全防护"},
    "geosite-fastly": {"desc": "Fastly 边缘云计算与高性能 CDN"},
    "geosite-akamai": {"desc": "Akamai 全球核心 CDN 与边缘加速"},
    "geosite-vercel": {"desc": "Vercel 前端云开发与部署托管平台"},
    "geosite-netlify": {"desc": "Netlify 静态网站托管与 Serverless"},
    "geosite-microsoft": {"desc": "Microsoft 微软全球产品与 Office 365"},
    "geosite-microsoft-cdn": {"desc": "Microsoft 微软全球资源分发 CDN"},
    "geosite-onedrive": {"desc": "Microsoft OneDrive 云端存储服务"},
    "geosite-google": {"desc": "Google 全球核心产品生态与服务"},
    "geosite-apple-services": {"desc": "Apple 苹果全球核心云服务与 iCloud"},
    "geosite-apple-cdn": {"desc": "Apple 苹果官方资产与软件更新 CDN"},
    "geosite-notion": {"desc": "Notion 现代协同办公笔记与知识库"},
    "geosite-figma": {"desc": "Figma 云端协作界面设计平台"},
    "geosite-canva": {"desc": "Canva 可画全球在线平面设计平台"},
    "geosite-zoom": {"desc": "Zoom 全球主流企业在线视频会议"},
    "geosite-netdisk-!cn": {"desc": "海外网盘与云存储服务 (境外代理分流)"},

    # 🇨🇳 China Ecosystem
    "geosite-cn": {"desc": "🇨🇳 中国大陆域名双源合并合集 (精编+自有)"},
    "geosite-!cn": {"desc": "🌐 非中国大陆节点域名合集 (境外代理)"},
    "geosite-alibaba": {"desc": "阿里巴巴系服务 (淘宝/天猫/阿里云/钉钉)"},
    "geosite-tencent": {"desc": "腾讯系服务 (微信/QQ/腾讯云/腾讯视频)"},
    "geosite-bilibili": {"desc": "哔哩哔哩 (B站) 视频与直播核心资产"},
    "geosite-xiaomi": {"desc": "小米系生态服务 (MIUI/米家/云服务)"},
    "geosite-bytedance": {"desc": "字节跳动系服务 (抖音/头条/飞书)"},
    "geosite-baidu": {"desc": "百度系服务 (搜索/网盘/地图/文心一言)"},
    "geosite-qihoo360": {"desc": "奇虎 360 安全防护与搜索服务"},
    "geosite-domestic": {"desc": "国内常用互联网服务合集 (SKK 维护)"},
    "geosite-apple-cn": {"desc": "Apple 苹果中国大陆本地化加速域名"},
    "geosite-download": {"desc": "应用商店、软件源与大文件下载直连分流"},

    # 🛡️ Security & Blocking
    "geosite-ad": {"desc": "终极去广告 / 防追踪 (单集合保守版)"},
    "geosite-ad-precise": {"desc": "去广告黑名单精确版 (双集合黑名单B)", "note": "配合 geosite-ad-allow 达成 0 误杀"},
    "geosite-ad-allow": {"desc": "去广告防误杀白名单 (双集合白名单B)", "note": "前置短路放行，彻底消除误杀断流"},
    "geosite-gfw": {"desc": "GFW 封锁与污染域名列表"},
    "geosite-reject-drop": {"desc": "高危威胁、挖矿与垃圾流量直接丢弃"},
    "geosite-fakeip-filter": {"desc": "Fake-IP 排除名单 (正则压缩防漏网)"},
    "geosite-porn": {"desc": "成人内容与不良网站拦截 (含本地补丁)"},
    "geosite-httpdns": {"desc": "国内 APP 内置 HTTPDNS 解析防劫持"},
    "geosite-private": {"desc": "局域网保留与私有/路由器后台域名"},
    "geosite-pcdn": {"desc": "PCDN 边缘上传业务拦截过滤 (ADG 格式)", "note": "上游: wuiiled/PCDN-mihomo-list · AdGuard 规则格式"},

    # 🛠️ Custom Routing
    "geosite-custom-direct": {"desc": "本地自定义直连域名与服务", "note": "用户本地规则: rules/Custom_Direct_DOMAIN.txt"},
    "geosite-custom-dns": {"desc": "本地自定义 DNS 解析与重定向", "note": "用户本地规则: rules/Custom_DNS_DOMAIN.txt"},
    "geosite-custom-emby": {"desc": "本地自定义 Emby / Jellyfin 媒体服", "note": "用户本地规则: rules/Custom_Emby.txt"},
    "geosite-custom-proxy": {"desc": "本地自定义强制代理规则", "note": "用户本地规则: rules/Custom_Proxy.txt"},
    "geosite-custom-download": {"desc": "本地自定义强制直连下载", "note": "用户本地规则: rules/Custom_Download.txt"},
    "geosite-location-dks": {"desc": "抖音/快手/小红书 IP 归属地分流", "note": "精准定位相关请求分流"},

    # 🌍 GeoIP
    "geoip-cn": {"desc": "🇨🇳 中国大陆三大运营商 IPv4/IPv6 权威网段"},
    "geoip-google": {"desc": "🔍 Google 官方全网 IPv4/IPv6 网段"},
    "geoip-telegram": {"desc": "✈️ Telegram 电报官方数据中心网段"},
    "geoip-twitter": {"desc": "🐦 Twitter / X 官方数据中心网段"},
    "geoip-facebook": {"desc": "📘 Meta / Facebook 官方数据中心网段"},
    "geoip-gfw": {"desc": "🧱 GFW 投毒 IP 与伪造靶心网段拦截"},
    "geoip-private": {"desc": "🔒 局域网私有保留 IP 网段"},
    "geoip-stream": {"desc": "📻 知名流媒体服务官方 IP 网段"},
    "geoip-apple": {"desc": "🍏 Apple 苹果服务官方 IP 网段"},
    "geoip-custom-direct": {"desc": "📌 本地自定义直连 IP 地址网段", "note": "用户本地规则: rules/Custom_Direct_IP.txt"},
    "geoip-custom-dns": {"desc": "📌 本地自定义 DNS 解析 IP 地址", "note": "用户本地规则: rules/Custom_DNS_IP.txt"},
}


# 平台 -> 代表域名。构建期对每个集合做真实包含性检查, 只有命中的平台才会
# 渲染进 README 说明列 —— 宣称的内容永远等于集合实际包含的内容。
# 判断语义: 代表域名本身是集合成员, 或被集合中某个 domain_suffix 覆盖。
PLATFORM_MARKERS: Dict[str, List[str]] = {
    # AI & Dev
    "OpenAI": ["openai.com", "chatgpt.com"],
    "Anthropic": ["anthropic.com", "claude.ai"],
    "Gemini": ["gemini.google.com", "deepmind.com"],
    "GitHub": ["github.com", "githubusercontent.com"],
    "GitLab": ["gitlab.com"],
    "Docker": ["docker.io", "docker.com"],
    "StackExchange": ["stackoverflow.com", "stackexchange.com"],
    "npm": ["npmjs.org", "npmjs.com"],
    # Social & IM
    "Telegram": ["telegram.org", "telegram.com", "t.me"],
    "Discord": ["discord.com", "discord.gg", "discordapp.com"],
    "WhatsApp": ["whatsapp.com", "whatsapp.net"],
    "Signal": ["signal.org", "whispersystems.org"],
    "LINE": ["line.me", "line-apps.com"],
    "X/Twitter": ["x.com", "twitter.com", "twimg.com"],
    "Instagram": ["instagram.com", "cdninstagram.com"],
    "Threads": ["threads.net"],
    "Reddit": ["reddit.com", "redd.it", "redditstatic.com"],
    "Bluesky": ["bsky.app", "bsky.social"],
    "TikTok": ["tiktok.com", "tiktokv.com", "byteoversea.com"],
    "Facebook/Meta": ["facebook.com", "fbcdn.net"],
    # Media & Streaming
    "YouTube": ["youtube.com", "googlevideo.com", "youtu.be"],
    "Netflix": ["netflix.com", "nflxvideo.net", "nflxext.com"],
    "Disney+": ["disneyplus.com", "bamgrid.com", "disney.com"],
    "Spotify": ["spotify.com", "scdn.co"],
    "Apple TV+": ["tv.apple.com"],
    "HBO": ["hbo.com", "max.com", "hbomax.com"],
    "Hulu": ["hulu.com", "hulustream.com"],
    "Prime Video": ["primevideo.com", "aiv-cdn.net"],
    "Twitch": ["twitch.tv", "ttvnw.net"],
    "巴哈姆特": ["gamer.com.tw"],
    "Abema": ["abema.tv"],
    "Niconico": ["nicovideo.jp"],
    "DMM": ["dmm.com"],
    "Pixiv": ["pixiv.net", "pximg.net"],
    "Vimeo": ["vimeo.com"],
    "Dailymotion": ["dailymotion.com"],
    "Deezer": ["deezer.com"],
    "SoundCloud": ["soundcloud.com"],
    "TIDAL": ["tidal.com"],
    # 新闻媒体 (dat category-media 实际构成)
    "半岛电视台": ["aljazeera.com", "aljazeera.net"],
    "法新社": ["afp.com"],
    "今日俄罗斯": ["rt.com", "actualidad-rt.com"],
    "澳大利亚九号台": ["9now.com.au", "9news.com.au"],
    "台湾4GTV": ["4gtv.tv"],
    "6park": ["6park.com"],
    # Gaming
    "Steam": ["steampowered.com", "steamcommunity.com"],
    "Epic Games": ["epicgames.com", "unrealengine.com"],
    "PlayStation": ["playstation.com", "playstation.net"],
    "Xbox": ["xbox.com", "xboxlive.com"],
    "Nintendo": ["nintendo.com", "nintendo.net"],
    "EA": ["ea.com", "origin.com"],
    "Ubisoft": ["ubisoft.com", "ubi.com"],
    "Rockstar": ["rockstargames.com", "rsg.sc"],
    "Blizzard": ["battle.net", "blizzard.com"],
    "Riot Games": ["riotgames.com", "leagueoflegends.com"],
    "米哈游": ["mihoyo.com", "mihoyo.hk"],
    "HoYoverse": ["hoyoverse.com", "hoyolab.com"],
    "网易游戏": ["netease.com", "netease.im", "163.com"],
    "腾讯游戏": ["qq.com", "tencent.com"],
    "哔哩哔哩": ["bilibili.com", "bilivideo.com"],
    # Finance
    "PayPal": ["paypal.com", "paypalobjects.com"],
    "Stripe": ["stripe.com", "stripe.network"],
    "Wise": ["wise.com", "transferwise.com"],
    "Binance": ["binance.com", "bnbstatic.com"],
    "OKX": ["okx.com", "okex.com"],
    # Cloud & SaaS
    "Cloudflare": ["cloudflare.com", "cloudflare-dns.com"],
    "Fastly": ["fastly.com", "fastly.net"],
    "Akamai": ["akamai.com", "akamaiedge.net"],
    "Vercel": ["vercel.com", "vercel.app"],
    "Netlify": ["netlify.com", "netlify.app"],
    "Microsoft": ["microsoft.com", "office.com", "live.com"],
    "OneDrive": ["onedrive.live.com", "1drv.ms", "1drv.com"],
    "Google": ["google.com", "gstatic.com", "android.com"],
    "Apple": ["apple.com", "icloud.com", "mzstatic.com"],
    "Notion": ["notion.so", "notion.site"],
    "Figma": ["figma.com"],
    "Canva": ["canva.com", "canvastatic.com"],
    "Zoom": ["zoom.us", "zoom.com"],
    # 网盘
    "Dropbox": ["dropbox.com", "dropboxusercontent.com", "getdropbox.com"],
    "MEGA": ["mega.nz", "mega.io", "mega.co.nz"],
    "TeraBox": ["terabox.com", "1024terabox.com", "freeterabox.com"],
    "PikPak": ["mypikpak.com"],
    "Google Drive": ["drive.google.com", "googleusercontent.com"],
    # 国内大厂
    "阿里巴巴": ["taobao.com", "aliyun.com", "alipay.com"],
    "腾讯": ["qq.com", "tencent.com"],
    "百度": ["baidu.com", "bcebos.com"],
    "字节跳动": ["bytedance.com", "douyin.com", "feishu.cn"],
    "小米": ["mi.com", "xiaomi.com"],
    "奇虎360": ["360.cn", "360.com", "qhimg.com"],
}


def marker_in_ruleset(marker: str, rs) -> bool:
    """判断平台代表域名是否真实命中集合: 是成员, 或被某个 domain_suffix 覆盖。"""
    m = (marker or "").strip().lower().lstrip(".")
    if not m:
        return False
    if m in {d.lower() for d in rs.domains}:
        return True
    for s in rs.domain_suffixes:
        s = s.lstrip(".").lower()
        if s and (m == s or m.endswith("." + s)):
            return True
    return False


def compute_markers(rs) -> List[str]:
    """返回集合中真实存在的平台名。按命中代表域名数量降序 —— 大集合 (如 !cn)
    命中平台很多时, 排前面的自然是在集合中占重大头的平台。GeoIP 不适用。"""
    if getattr(rs, "category", "") == "geoip":
        return []
    hits = []
    for plat, marks in PLATFORM_MARKERS.items():
        n = sum(1 for mk in marks if marker_in_ruleset(mk, rs))
        if n:
            hits.append((n, plat))
    hits.sort(key=lambda t: -t[0])
    return [plat for _n, plat in hits]


def build_manifest(all_rules) -> Dict[str, dict]:
    """把每个规则集的来源画像与已验证平台落成 manifest 供 README 渲染。"""
    out: Dict[str, dict] = {}
    for name, rs in all_rules.items():
        out[name] = {
            "kind": getattr(rs, "source_kind", ""),
            "dat_code": getattr(rs, "dat_code", ""),
            "sources": list(getattr(rs, "sources", []) or []),
            "markers": compute_markers(rs),
            "count": rs.total_count,
        }
    return out


def write_manifest(all_rules, output_base_dir: str = "output") -> str:
    os.makedirs(output_base_dir, exist_ok=True)
    path = os.path.join(output_base_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(build_manifest(all_rules), f, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"  🗂️ [manifest] 来源画像已写入 {path}")
    return path


def _load_manifest(output_base_dir: str) -> Dict[str, dict]:
    path = os.path.join(output_base_dir, "manifest.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _manifest_note(entry: dict) -> str:
    """把 manifest 条目渲染成 README 说明列文本。"""
    kind = entry.get("kind", "")
    sources = entry.get("sources") or []
    if kind == "dat":
        parts = [f"dat 分类 {entry.get('dat_code', '')}"]
        markers = entry.get("markers") or []
        if markers:
            head = markers[:6]
            tail = f" 等 {len(markers)} 项" if len(markers) > 6 else ""
            parts.append("含 " + " / ".join(head) + tail)
        return " · ".join(parts)
    if kind == "recipe":
        return "配方合成: " + " ∪ ".join(sources) if sources else ""
    if kind in ("self", "skk", "geoip-srs"):
        return "上游: " + " · ".join(sources) if sources else ""
    if kind == "custom":
        return f"用户本地规则: {sources[0]}" if sources else ""
    return ""


_REVERSE_DAT: Optional[Dict[str, str]] = None


def _fallback_dat_code(bname: str) -> str:
    """manifest 缺席时的兜底: 从 TIANLING_GEOSITES 反推 dat 分类码。"""
    global _REVERSE_DAT
    if _REVERSE_DAT is None:
        try:
            from core.manager import TIANLING_GEOSITES
            _REVERSE_DAT = {out: up[len("geosite-"):] for up, out in TIANLING_GEOSITES.items()}
        except Exception:
            _REVERSE_DAT = {}
    return _REVERSE_DAT.get(bname, "")


def _render_note(bname: str, manifest: Dict[str, dict]) -> str:
    entry = manifest.get(bname)
    if entry:
        note = _manifest_note(entry)
        if note:
            return note
    meta = RULE_METADATA.get(bname, {})
    if meta.get("note"):
        return meta["note"]
    code = _fallback_dat_code(bname)
    return f"dat 分类 {code}" if code else "-"


def count_file_rules(file_path: str) -> int:
    """Accurately count rules inside a .json, .txt, or other format file."""
    if not os.path.exists(file_path):
        return 0
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".json":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            total = 0
            for r in data.get("rules", []):
                for val in r.values():
                    if isinstance(val, list):
                        total += len(val)
                    elif isinstance(val, str):
                        total += 1
            return total
        except Exception:
            return 0
    elif ext in (".txt", ".conf", ".list"):
        try:
            count = 0
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        count += 1
            return count
        except Exception:
            return 0
    return 0


def _total_rules(target_dir: str) -> Tuple[int, int]:
    """Sum rule counts and distinct rule-sets across geosite/geoip subdirs and root rule files."""
    total_items = 0
    distinct_rules = set()
    legacy_names = set(os.path.splitext(k)[0] for k in providers.OXIDNS_RULE_FILES)

    for sub in ("geosite", "geoip"):
        d = os.path.join(target_dir, sub)
        if os.path.isdir(d):
            seen = set()
            for f in os.listdir(d):
                base = os.path.splitext(f)[0]
                if base in seen:
                    continue
                seen.add(base)
                distinct_rules.add(base)
                cand = None
                for ext in (".json", ".txt", ".conf", ".list"):
                    c2 = os.path.join(d, base + ext)
                    if os.path.exists(c2):
                        cand = c2
                        break
                if cand is not None:
                    total_items += count_file_rules(cand)

    for f in os.listdir(target_dir):
        p = os.path.join(target_dir, f)
        if os.path.isfile(p) and f != "README.md":
            base = os.path.splitext(f)[0]
            if base in legacy_names:
                # OxiDNS 兼容副本: 与 geosite/ 内同名规则集重复, 不重复计数
                continue
            distinct_rules.add(base)
            total_items += count_file_rules(p)

    return total_items, len(distinct_rules)


def generate_branch_readme(target: str, output_base_dir: str, repo: str = "wuiiled/Wuiiled_Setup"):
    """Generate README.md in output/<target>/README.md with unified, categorized tables."""
    target_dir = os.path.join(output_base_dir, target)
    if not os.path.exists(target_dir):
        return

    emoji, title, fmt_badge, _ = _BRANCH_META.get(target, ("📦", target, "", "txt"))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_items, total_sets = _total_rules(target_dir)
    manifest = _load_manifest(output_base_dir)

    lines = []
    lines.append('<div align="center">')
    lines.append("")
    lines.append(f"# {emoji} {title} 规则订阅")
    lines.append("")
    lines.append(f'![规则总数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E6%80%BB%E6%95%B0-{total_items:,}-blue)')
    lines.append(f'![规则集数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E9%9B%86%E6%95%B0-{total_sets}-success)')
    lines.append(f'![格式](https://img.shields.io/badge/%E6%A0%BC%E5%BC%8F-{fmt_badge.replace(" ", "%20").replace("/", "%2F")}-informational)')
    # 0-Diff 是 singbox 分支 dat 派生集合对天灵 sing-geosite 的验证性质, 其他分支不做此宣称
    if target == "singbox":
        lines.append('![0--Diff对齐](https://img.shields.io/badge/0--Diff-%E7%99%BE%E5%88%86%E7%99%BE%E5%AF%B9%E9%BD%90-brightgreen)')
    lines.append("")
    lines.append('<i>由 <a href="https://github.com/' + repo + '">Wuiiled_Setup</a> 规则自动化引擎实时构建分发</i><br>')
    lines.append(f'<sub>🕐 最后更新：{now_str} (Asia/Shanghai)</sub>')
    lines.append("")
    lines.append("</div>")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 💡 如何使用")
    lines.append("")
    lines.append("在下方分类表格中 **右键点击** 对应链接，选择 **复制链接地址**，填入客户端订阅即可。")
    lines.append("")

    # Client configuration examples
    if target == "singbox":
        lines.append('<details>')
        lines.append('<summary><b>🛠️ Sing-box 配置示例</b>（点击展开）</summary>')
        lines.append("")
        lines.append("在 `config.json` 的 `route.rule_set` 中配置远程规则集。将下方 `{tag}` 替换为表格中的规则名（推荐优先使用高效的二进制 `.srs`）：")
        lines.append("")
        lines.append("```json")
        lines.append('{\n  "tag": "{tag}",\n  "type": "remote",\n  "format": "binary",\n  "url": "' + f"https://raw.githubusercontent.com/{repo}/singbox/rules/geosite/{{tag}}.srs" + '",\n  "download_detour": "direct"\n}')
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    elif target == "mihomo":
        lines.append('<details>')
        lines.append('<summary><b>🛠️ Mihomo (Clash Meta) 配置示例</b>（点击展开）</summary>')
        lines.append("")
        lines.append("在配置文件的 `rule-providers` 中配置规则提供者（推荐优先使用高性能的 `.mrs`）：")
        lines.append("")
        lines.append("```yaml")
        lines.append("rule-providers:")
        lines.append("  geosite-ad:")
        lines.append("    type: http")
        lines.append("    behavior: domain")
        lines.append("    format: mrs")
        lines.append(f'    url: "https://raw.githubusercontent.com/{repo}/mihomo/rules/geosite/geosite-ad.mrs"')
        lines.append("    path: ./ruleset/geosite-ad.mrs")
        lines.append("    interval: 86400")
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    elif target == "smartdns":
        lines.append('<details>')
        lines.append('<summary><b>🛠️ SmartDNS 配置示例</b>（点击展开）</summary>')
        lines.append("")
        lines.append("在 `smartdns.conf` 中引入规则集文件：")
        lines.append("")
        lines.append("```conf")
        lines.append("domain-set -name geosite-cn -file /etc/smartdns/rules/geosite-cn.txt")
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    elif target == "mosdns-x":
        lines.append('<details>')
        lines.append('<summary><b>🛠️ MosDNS 配置示例</b>（点击展开）</summary>')
        lines.append("")
        lines.append("在 `config.yaml` 的插件配置中引入规则集：")
        lines.append("")
        lines.append("```yaml")
        lines.append("plugins:")
        lines.append("  - tag: site_cn")
        lines.append("    type: domain_set")
        lines.append("    args:")
        lines.append("      files:")
        lines.append(f'        - "/etc/mosdns/rules/geosite-cn.txt"')
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    elif target == "adg":
        lines.append('<details>')
        lines.append('<summary><b>🛠️ AdGuard Home 配置示例</b>（点击展开）</summary>')
        lines.append("")
        lines.append("在 **过滤器** -> **DNS 封锁清单** 中添加自定义订阅链接，直接粘贴下方表格中的订阅直链。")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    # Map files existing in target directory
    geosite_dir = os.path.join(target_dir, "geosite")
    geoip_dir = os.path.join(target_dir, "geoip")

    available_geosites: Set[str] = set()
    if os.path.exists(geosite_dir):
        available_geosites = {os.path.splitext(f)[0] for f in os.listdir(geosite_dir)}

    available_geoips: Set[str] = set()
    if os.path.exists(geoip_dir):
        available_geoips = {os.path.splitext(f)[0] for f in os.listdir(geoip_dir)}

    root_files: Dict[str, str] = {}
    legacy_names = set(os.path.splitext(k)[0] for k in providers.OXIDNS_RULE_FILES)
    for f in os.listdir(target_dir):
        p = os.path.join(target_dir, f)
        if os.path.isfile(p) and f != "README.md":
            base = os.path.splitext(f)[0]
            if base in legacy_names:
                # OxiDNS 兼容副本: 不在 README 中重复渲染
                continue
            root_files[base] = f

    # Quick Jump Table of Contents
    lines.append("## 📑 规则分类快速导航")
    lines.append("")
    nav_links = []
    for cat_id, cat_title, rule_names in CATEGORY_DEFS:
        has_items = any(r in available_geosites or r in available_geoips or r in root_files for r in rule_names)
        if has_items:
            clean_anchor = cat_title.split(' ')[0]
            nav_links.append(f"[{clean_anchor}](#{cat_id})")
    lines.append(" · ".join(nav_links))
    lines.append("")
    lines.append("---")
    lines.append("")

    # Render each category
    rendered_rules: Set[str] = set()

    for cat_id, cat_title, rule_names in CATEGORY_DEFS:
        cat_items = []
        for rname in rule_names:
            if rname in available_geosites:
                cat_items.append((rname, "geosite", os.path.join(geosite_dir, rname)))
            elif rname in available_geoips:
                cat_items.append((rname, "geoip", os.path.join(geoip_dir, rname)))
            elif rname in root_files:
                cat_items.append((rname, "root", os.path.join(target_dir, root_files[rname])))

        if not cat_items:
            continue

        lines.append(f'<span id="{cat_id}"></span>')
        lines.append("")
        lines.append(f"### {cat_title}")
        lines.append("")

        if target == "singbox":
            lines.append("| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | JSON (源码) |")
            lines.append("| :--- | :--- | :--- | ---: | :---: | :---: |")
            for bname, location, file_prefix in cat_items:
                rendered_rules.add(bname)
                json_p = file_prefix + ".json"
                srs_p = file_prefix + ".srs"
                count = count_file_rules(json_p)
                count_str = f"{count:,}" if count > 0 else "-"
                rel_dir = "geosite" if location == "geosite" else "geoip"
                srs_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_dir}/{bname}.srs"
                json_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_dir}/{bname}.json"
                srs_link = f"[📥 SRS]({srs_url})" if os.path.exists(srs_p) else "-"
                json_link = f"[📄 JSON]({json_url})" if os.path.exists(json_p) else "-"
                meta = RULE_METADATA.get(bname, {})
                desc = meta.get("desc", bname)
                note = _render_note(bname, manifest)
                lines.append(f"| **`{bname}`** | {desc} | {note} | `{count_str}` | {srs_link} | {json_link} |")
            lines.append("")

        elif target == "mihomo":
            lines.append("| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |")
            lines.append("| :--- | :--- | :--- | ---: | :---: | :---: |")
            for bname, location, file_prefix in cat_items:
                rendered_rules.add(bname)
                txt_p = file_prefix + ".txt"
                mrs_p = file_prefix + ".mrs"
                count = count_file_rules(txt_p)
                count_str = f"{count:,}" if count > 0 else "-"
                rel_dir = "geosite" if location == "geosite" else "geoip"
                mrs_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_dir}/{bname}.mrs"
                txt_url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_dir}/{bname}.txt"
                mrs_link = f"[📥 MRS]({mrs_url})" if os.path.exists(mrs_p) else "-"
                txt_link = f"[📄 TXT]({txt_url})" if os.path.exists(txt_p) else "-"
                meta = RULE_METADATA.get(bname, {})
                desc = meta.get("desc", bname)
                note = _render_note(bname, manifest)
                lines.append(f"| **`{bname}`** | {desc} | {note} | `{count_str}` | {mrs_link} | {txt_link} |")
            lines.append("")

        else:
            lines.append("| 规则名称 | 描述 | 条数 | 订阅链接 |")
            lines.append("| :--- | :--- | ---: | :---: |")
            for bname, location, file_prefix in cat_items:
                rendered_rules.add(bname)
                txt_p = file_prefix if location == "root" else file_prefix + ".txt"
                count = count_file_rules(txt_p)
                count_str = f"{count:,}" if count > 0 else "-"
                if location == "root":
                    rel_p = os.path.basename(txt_p)
                    url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_p}"
                else:
                    rel_dir = "geosite" if location == "geosite" else "geoip"
                    url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{rel_dir}/{bname}.txt"
                meta = RULE_METADATA.get(bname, {})
                desc = meta.get("desc", bname)
                lines.append(f"| **`{bname}`** | {desc} | `{count_str}` | [📥 直链]({url}) |")
            lines.append("")

    # Fallback for any unrendered rules
    remaining_geosites = sorted(list(available_geosites - rendered_rules))
    remaining_geoips = sorted(list(available_geoips - rendered_rules))
    remaining_roots = sorted(list(set(root_files.keys()) - rendered_rules))

    if remaining_geosites or remaining_geoips or remaining_roots:
        lines.append("### 📌 其他规则集")
        lines.append("")
        lines.append("| 规则文件 | 条数 | 订阅 |")
        lines.append("| :--- | ---: | :---: |")
        for bname in remaining_geosites:
            txt_p = os.path.join(geosite_dir, f"{bname}.txt")
            if not os.path.exists(txt_p):
                txt_p = os.path.join(geosite_dir, f"{bname}.json")
            count = count_file_rules(txt_p)
            count_str = f"{count:,}" if count > 0 else "-"
            ext = ".srs" if target == "singbox" else (".mrs" if target == "mihomo" else ".txt")
            url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/geosite/{bname}{ext}"
            lines.append(f"| **`{bname}`** | `{count_str}` | [📥 直链]({url}) |")
        for bname in remaining_geoips:
            txt_p = os.path.join(geoip_dir, f"{bname}.txt")
            if not os.path.exists(txt_p):
                txt_p = os.path.join(geoip_dir, f"{bname}.json")
            count = count_file_rules(txt_p)
            count_str = f"{count:,}" if count > 0 else "-"
            ext = ".srs" if target == "singbox" else (".mrs" if target == "mihomo" else ".txt")
            url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/geoip/{bname}{ext}"
            lines.append(f"| **`{bname}`** | `{count_str}` | [📥 直链]({url}) |")
        for bname in remaining_roots:
            p = os.path.join(target_dir, root_files[bname])
            count = count_file_rules(p)
            count_str = f"{count:,}" if count > 0 else "-"
            url = f"https://raw.githubusercontent.com/{repo}/{target}/rules/{root_files[bname]}"
            lines.append(f"| **`{root_files[bname]}`** | `{count_str}` | [📥 直链]({url}) |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append('<div align="center">')
    lines.append("")
    lines.append(f'[🏠 返回主仓库](https://github.com/{repo}) · [⭐ Star 支持](https://github.com/{repo})')
    lines.append("")
    lines.append("</div>")

    readme_path = os.path.join(target_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(NL.join(lines) + NL)
    print(f"  📄 [README] 为分支 {target:<10} 成功生成订阅导航 (包含 {total_sets} 个规则集, 共 {total_items:,} 条规则)")


def generate_all_readmes(output_base_dir: str = "output", repo: str = "wuiiled/Wuiiled_Setup"):
    """Generate README.md for all 5 platform outputs."""
    print("\n📝 正在生成全平台订阅导航文档 (README.md)...")
    for target in ("singbox", "mihomo", "smartdns", "mosdns-x", "adg"):
        generate_branch_readme(target, output_base_dir, repo)
