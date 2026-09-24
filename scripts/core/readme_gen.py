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
        "geosite-figma", "geosite-canva", "geosite-zoom"
    ]),
    ("china", "🇨🇳 国内直连与核心大厂 (China & Ecosystem)", [
        "geosite-cn", "geosite-!cn", "geosite-alibaba", "geosite-tencent",
        "geosite-bilibili", "geosite-xiaomi", "geosite-bytedance", "geosite-baidu",
        "geosite-qihoo360", "geosite-domestic", "geosite-apple-cn", "geosite-download"
    ]),
    ("security", "🛡️ 安全防护与过滤拦截 (Security & Blocking)", [
        "geosite-ad", "geosite-ad-precise", "geosite-ad-allow", "geosite-gfw",
        "geosite-reject-drop", "geosite-fakeip-filter", "geosite-porn", "geosite-httpdns",
        "geosite-private"
    ]),
    ("custom", "🛠️ 本地自定义与特征分流 (Custom Routing)", [
        "geosite-custom-direct", "geosite-custom-dns", "geosite-custom-emby",
        "geosite-custom-proxy", "geosite-custom-download", "geosite-location-dks"
    ]),
    ("geoip", "🌍 GeoIP 地址段网段集合 (IP Networks)", [
        "geoip-cn", "geoip-google", "geoip-telegram", "geoip-twitter",
        "geoip-facebook", "geoip-gfw", "geoip-private", "geoip-stream",
        "geoip-apple", "geoip-custom-direct", "geoip-custom-dns"
    ]),
    ("alias", "🔗 兼容别名规则集 (Compatibility Aliases)", [
        "geosite-emby", "geosite-game", "geosite-microsoftcdn",
        "geosite-appleservice", "geosite-applecn", "geosite-applecdn"
    ])
]

RULE_METADATA: Dict[str, Dict[str, str]] = {
    # 🤖 AI & Dev
    "geosite-ai": {"desc": "全球主流 AI 服务合集 (自研列表 ∪ dat 分类)", "note": "AI_URLS 多源清洗 ∪ dat category-ai-!cn (经 rules/patches 声明)"},
    "geosite-openai": {"desc": "OpenAI / ChatGPT 官方服务与 API", "note": "ChatGPT, API, Sora, CDN"},
    "geosite-anthropic": {"desc": "Anthropic Claude 官方服务与 API", "note": "Claude.ai, API 接口"},
    "geosite-gemini": {"desc": "Google Gemini / Bard 人工智能服务", "note": "Gemini Web & API 接口"},
    "geosite-github": {"desc": "GitHub 代码托管平台与开发者资产", "note": "github.com, raw, assets, gist"},
    "geosite-gitlab": {"desc": "GitLab 代码托管与 DevOps 云服务", "note": "gitlab.com 及全系生态"},
    "geosite-docker": {"desc": "Docker Hub 容器镜像与注册表", "note": "docker.io, docker.com, registry"},
    "geosite-stackoverflow": {"desc": "Stack Overflow 与开发者技术社区", "note": "Stack Exchange 网络问答社区"},
    "geosite-npm": {"desc": "Node.js NPM 官方包管理器软件源", "note": "npmjs.org, npmjs.com 官方源"},

    # 💬 Social & IM
    "geosite-communication": {"desc": "全球即时通讯与在线会议聚合", "note": "Telegram, Discord, WhatsApp 等 150+ 子类"},
    "geosite-social-media": {"desc": "全球社交网络与媒体平台聚合", "note": "Twitter, Meta, Instagram, Reddit 等 600+ 子类"},
    "geosite-telegram": {"desc": "Telegram 电报全系官方通讯服务", "note": "t.me, telegram.org, 各 DC 核心域名"},
    "geosite-discord": {"desc": "Discord 语音与社群即时通讯平台", "note": "discord.com, discord.gg, cdn 资产"},
    "geosite-whatsapp": {"desc": "WhatsApp 即时通讯与端到端加密", "note": "whatsapp.com, whatsapp.net"},
    "geosite-signal": {"desc": "Signal 隐私加密即时通讯服务", "note": "signal.org, whispersystems.org"},
    "geosite-line": {"desc": "LINE 亚洲流行即时通讯与生活服务", "note": "line.me, line-apps.com"},
    "geosite-x": {"desc": "X (原 Twitter) 官方社交媒体平台", "note": "x.com, twitter.com, twimg.com"},
    "geosite-instagram": {"desc": "Instagram 社交图像与短视频平台", "note": "instagram.com, cdninstagram.com"},
    "geosite-threads": {"desc": "Threads 文本社交互动媒体平台", "note": "threads.net 官方域名"},
    "geosite-reddit": {"desc": "Reddit 全球兴趣与新闻社区", "note": "reddit.com, redd.it, redditstatic.com"},
    "geosite-bluesky": {"desc": "Bluesky 去中心化社交网络平台", "note": "bsky.app, bsky.social"},
    "geosite-tiktok": {"desc": "TikTok 国际版短视频平台", "note": "tiktok.com, tiktokv.com, byteoversea.com"},

    # 🎬 Media & Streaming
    "geosite-media": {"desc": "全球多媒体与流媒体服务大合集", "note": "Netflix, Disney+, YouTube, Spotify 等 1500+ 子类"},
    "geosite-entertainment": {"desc": "全球影音娱乐与流媒体聚合", "note": "涵盖游戏、影音、成人与流行媒体 (2100+ 条)"},
    "geosite-youtube": {"desc": "YouTube 视频流媒体与 YouTube Music", "note": "youtube.com, youtu.be, googlevideo.com"},
    "geosite-netflix": {"desc": "Netflix 奈飞全球影音流媒体平台", "note": "netflix.com, nflxvideo.net, nflxext.com"},
    "geosite-disney": {"desc": "Disney+ 迪士尼流媒体播放服务", "note": "disneyplus.com, bamgrid.com"},
    "geosite-spotify": {"desc": "Spotify 全球最大音乐流媒体服务", "note": "spotify.com, scdn.co, spoti.fi"},
    "geosite-apple-tvplus": {"desc": "Apple TV+ 苹果原创影视流媒体", "note": "tv.apple.com 及全系分发"},
    "geosite-hbo": {"desc": "HBO Max / HBO 全球影视服务", "note": "hbomax.com, hbo.com, max.com"},
    "geosite-hulu": {"desc": "Hulu 影视点播流媒体平台", "note": "hulu.com, hulustream.com"},
    "geosite-primevideo": {"desc": "Amazon Prime Video 亚马逊影音", "note": "primevideo.com, aiv-cdn.net"},
    "geosite-twitch": {"desc": "Twitch 全球游戏与互动直播平台", "note": "twitch.tv, ttvnw.net"},
    "geosite-bahamut": {"desc": "巴哈姆特动画疯 (台湾主流动漫平台)", "note": "gamer.com.tw 动漫播放与社区"},
    "geosite-abema": {"desc": "AbemaTV 日本网络电视流媒体", "note": "abema.tv, ameba.jp"},
    "geosite-niconico": {"desc": "Niconico (N站) 日本弹幕视频网站", "note": "nicovideo.jp, nimg.jp"},
    "geosite-dmm": {"desc": "DMM.com 日本综合数字内容娱乐", "note": "dmm.com, dmm.co.jp"},
    "geosite-pixiv": {"desc": "Pixiv (P站) 日本插画二次元艺术社区", "note": "pixiv.net, pximg.net"},
    "geosite-vimeo": {"desc": "Vimeo 高清原创视频创作分享平台", "note": "vimeo.com, vimeocdn.com"},
    "geosite-dailymotion": {"desc": "Dailymotion 国际视频共享服务", "note": "dailymotion.com, dmcdn.net"},
    "geosite-deezer": {"desc": "Deezer 高保真音乐流媒体服务", "note": "deezer.com, dzcdn.net"},
    "geosite-soundcloud": {"desc": "SoundCloud 原创音乐与音频分享", "note": "soundcloud.com, sndcdn.com"},
    "geosite-tidal": {"desc": "TIDAL HiFi 无损高品质音乐流媒体", "note": "tidal.com, wimpmusic.com"},

    # 🎮 Gaming
    "geosite-games": {"desc": "全球热门游戏与联机加速合集", "note": "涵盖全球主机、PC、手游与官方联机服务 (1100+ 条)"},
    "geosite-games-cn": {"desc": "国内主流网络游戏与加速服务", "note": "米哈游、腾讯、网易、B站等国内游戏服务"},
    "geosite-games-!cn": {"desc": "外服主机与端游联机加速合集", "note": "Steam, Epic, PlayStation, Xbox, 任天堂等"},
    "geosite-steam": {"desc": "Valve Steam 全球最大游戏平台", "note": "steampowered.com, steamcommunity.com"},
    "geosite-epicgames": {"desc": "Epic Games 游戏商城与虚幻联机", "note": "epicgames.com, unrealengine.com"},
    "geosite-playstation": {"desc": "Sony PlayStation Network (PSN)", "note": "playstation.com, playstation.net"},
    "geosite-xbox": {"desc": "Microsoft Xbox Live 游戏与 GamePass", "note": "xbox.com, xboxlive.com"},
    "geosite-nintendo": {"desc": "Nintendo 任天堂 Switch 联机与商城", "note": "nintendo.com, nintendo.net"},
    "geosite-ea": {"desc": "Electronic Arts (EA / Origin) 平台", "note": "ea.com, origin.com"},
    "geosite-ubisoft": {"desc": "Ubisoft Connect 育碧游戏与联机", "note": "ubisoft.com, ubi.com"},
    "geosite-rockstar": {"desc": "Rockstar Games 摇滚之星 (GTA/RDR)", "note": "rockstargames.com, rsg.sc"},
    "geosite-blizzard": {"desc": "Blizzard 暴雪战网国际服联机服务", "note": "battle.net, blizzard.com"},
    "geosite-riotgames": {"desc": "Riot Games 拳头游戏 (LOL/Valorant)", "note": "riotgames.com, leagueoflegends.com"},
    "geosite-mihoyo": {"desc": "米哈游 (MiHoYo) 原神/星铁境外分流", "note": "mihoyo.com 海外加速节点"},
    "geosite-hoyoverse": {"desc": "HoYoverse 米哈游海外发行平台", "note": "hoyoverse.com, hoyolab.com"},

    # 💰 Finance & Crypto
    "geosite-paypal": {"desc": "PayPal 全球主流跨境在线支付平台", "note": "paypal.com, paypalobjects.com"},
    "geosite-stripe": {"desc": "Stripe 国际在线支付结算网关", "note": "stripe.com, stripe.network"},
    "geosite-wise": {"desc": "Wise (原 TransferWise) 跨境汇款", "note": "wise.com, transferwise.com"},
    "geosite-binance": {"desc": "币安 (Binance) 全球最大加密货币交易", "note": "binance.com, bnbstatic.com"},
    "geosite-okx": {"desc": "欧易 (OKX) 全球主流加密货币交易", "note": "okx.com, okex.com"},

    # 🌐 Cloud & SaaS
    "geosite-cloudflare": {"desc": "Cloudflare 全球 CDN 与安全防护", "note": "cloudflare.com, cloudflare-dns.com"},
    "geosite-fastly": {"desc": "Fastly 边缘云计算与高性能 CDN", "note": "fastly.com, fastly.net"},
    "geosite-akamai": {"desc": "Akamai 全球核心 CDN 与边缘加速", "note": "akamai.com, akamaiedge.net"},
    "geosite-vercel": {"desc": "Vercel 前端云开发与部署托管平台", "note": "vercel.com, vercel.app"},
    "geosite-netlify": {"desc": "Netlify 静态网站托管与 Serverless", "note": "netlify.com, netlify.app"},
    "geosite-microsoft": {"desc": "Microsoft 微软全球产品与 Office 365", "note": "microsoft.com, office.com, live.com"},
    "geosite-microsoft-cdn": {"desc": "Microsoft 微软全球资源分发 CDN", "note": "azureedge.net, msftauth.net 等"},
    "geosite-onedrive": {"desc": "Microsoft OneDrive 云端存储服务", "note": "onedrive.live.com, 1drv.ms"},
    "geosite-google": {"desc": "Google 全球核心产品生态与服务", "note": "google.com, gstatic.com, android.com"},
    "geosite-apple-services": {"desc": "Apple 苹果全球核心云服务与 iCloud", "note": "apple.com, icloud.com, mzstatic.com"},
    "geosite-apple-cdn": {"desc": "Apple 苹果官方资产与软件更新 CDN", "note": "apple-dns.net, aaplimg.com"},
    "geosite-notion": {"desc": "Notion 现代协同办公笔记与知识库", "note": "notion.so, notion.site"},
    "geosite-figma": {"desc": "Figma 云端协作界面设计平台", "note": "figma.com 核心服务"},
    "geosite-canva": {"desc": "Canva 可画全球在线平面设计平台", "note": "canva.com, canvastatic.com"},
    "geosite-zoom": {"desc": "Zoom 全球主流企业在线视频会议", "note": "zoom.us, zoom.com"},

    # 🇨🇳 China Ecosystem
    "geosite-cn": {"desc": "🇨🇳 中国大陆域名双源合并合集 (精编+自有)", "note": "天灵配方精编 cn (geolocation-cn + category-*@cn + category-*-cn) ∪ cn-additional-list ∪ SKK domestic"},
    "geosite-!cn": {"desc": "🌐 非中国大陆节点域名合集 (境外代理)", "note": "境外节点精准路由 (27,000+ 域名)"},
    "geosite-alibaba": {"desc": "阿里巴巴系服务 (淘宝/天猫/阿里云/钉钉)", "note": "taobao.com, aliyun.com, alipay.com"},
    "geosite-tencent": {"desc": "腾讯系服务 (微信/QQ/腾讯云/腾讯视频)", "note": "qq.com, weixin.com, tencent.com"},
    "geosite-bilibili": {"desc": "哔哩哔哩 (B站) 视频与直播核心资产", "note": "bilibili.com, bilivideo.com, hdslb.com"},
    "geosite-xiaomi": {"desc": "小米系生态服务 (MIUI/米家/云服务)", "note": "mi.com, xiaomi.com, miui.com"},
    "geosite-bytedance": {"desc": "字节跳动系服务 (抖音/头条/飞书)", "note": "bytedance.com, douyin.com, feishu.cn"},
    "geosite-baidu": {"desc": "百度系服务 (搜索/网盘/地图/文心一言)", "note": "baidu.com, bcebos.com, baidupcs.com"},
    "geosite-qihoo360": {"desc": "奇虎 360 安全防护与搜索服务", "note": "360.cn, 360.com, qhimg.com"},
    "geosite-domestic": {"desc": "国内常用互联网服务合集 (SKK 维护)", "note": "精选国内常见互联网服务直连规则"},
    "geosite-apple-cn": {"desc": "Apple 苹果中国大陆本地化加速域名", "note": "苹果国内直连服务与 CDN 节点"},
    "geosite-download": {"desc": "应用商店、P2P 与大文件下载分流", "note": "BT/PT Tracker、各类更新包直连分流"},

    # 🛡️ Security & Blocking
    "geosite-ad": {"desc": "终极去广告 / 防追踪 (单集合保守版)", "note": "多源清洗，白名单防误杀，开箱即用"},
    "geosite-ad-precise": {"desc": "去广告黑名单精确版 (双集合黑名单B)", "note": "配合 geosite-ad-allow 达成 0 误杀"},
    "geosite-ad-allow": {"desc": "去广告防误杀白名单 (双集合白名单B)", "note": "前置短路放行，彻底消除误杀断流"},
    "geosite-gfw": {"desc": "GFW 封锁与污染域名列表", "note": "精准出海代理分流 (4,300+ 条)"},
    "geosite-reject-drop": {"desc": "高危威胁、挖矿与垃圾流量直接丢弃", "note": "恶意威胁丢弃阻断"},
    "geosite-fakeip-filter": {"desc": "Fake-IP 排除名单 (正则压缩防漏网)", "note": "针对 NTP/STUN/游戏联机等直连解析"},
    "geosite-porn": {"desc": "成人内容与不良网站拦截 (含本地补丁)", "note": "过滤成人内容与涉黄站点 (6,660+ 条)"},
    "geosite-httpdns": {"desc": "国内 APP 内置 HTTPDNS 解析防劫持", "note": "阻止应用绕过本地 DNS 劫持解析"},
    "geosite-private": {"desc": "局域网保留与私有/路由器后台域名", "note": "local, lan, router.asus.com 等"},
    "PCDN": {"desc": "PCDN 边缘上传业务拦截过滤 (ADG 格式)", "note": "AdGuard 规则格式"},

    # 🛠️ Custom Routing
    "geosite-custom-direct": {"desc": "本地自定义直连域名与服务", "note": "用户本地规则: rules/Custom_Direct_DOMAIN.txt"},
    "geosite-custom-dns": {"desc": "本地自定义 DNS 解析与重定向", "note": "用户本地规则: rules/Custom_DNS_DOMAIN.txt"},
    "geosite-custom-emby": {"desc": "本地自定义 Emby / Jellyfin 媒体服", "note": "用户本地规则: rules/Custom_Emby.txt"},
    "geosite-custom-proxy": {"desc": "本地自定义强制代理规则", "note": "用户本地规则: rules/Custom_Proxy.txt"},
    "geosite-custom-download": {"desc": "本地自定义强制直连下载", "note": "用户本地规则: rules/Custom_Download.txt"},
    "geosite-location-dks": {"desc": "抖音/快手/小红书 IP 归属地分流", "note": "精准定位相关请求分流"},

    # 🌍 GeoIP
    "geoip-cn": {"desc": "🇨🇳 中国大陆三大运营商 IPv4/IPv6 权威网段", "note": "权威提纯，覆盖国内所有运营商 (9,940+ 条)"},
    "geoip-google": {"desc": "🔍 Google 官方全网 IPv4/IPv6 网段", "note": "Google 全网 ASN 与数据中心网段 (8,360+ 条)"},
    "geoip-telegram": {"desc": "✈️ Telegram 电报官方数据中心网段", "note": "Telegram 核心服务器网段"},
    "geoip-twitter": {"desc": "🐦 Twitter / X 官方数据中心网段", "note": "X 全球网络基础设施网段"},
    "geoip-facebook": {"desc": "📘 Meta / Facebook 官方数据中心网段", "note": "Meta 全球机房与网络资产"},
    "geoip-gfw": {"desc": "🧱 GFW 投毒 IP 与伪造靶心网段拦截", "note": "拦截 DNS 投毒返回的虚假 IP 靶心"},
    "geoip-private": {"desc": "🔒 局域网私有保留 IP 网段", "note": "RFC 1918 (10.0.0.0/8, 192.168.0.0/16 等)"},
    "geoip-stream": {"desc": "📻 知名流媒体服务官方 IP 网段", "note": "流媒体服务服务器 IP 网段 (SKK 维护)"},
    "geoip-apple": {"desc": "🍏 Apple 苹果服务官方 IP 网段", "note": "Apple 核心服务器 IP 网段 (SKK 维护)"},
    "geoip-custom-direct": {"desc": "📌 本地自定义直连 IP 地址网段", "note": "用户本地规则: rules/Custom_Direct_IP.txt"},
    "geoip-custom-dns": {"desc": "📌 本地自定义 DNS 解析 IP 地址", "note": "用户本地规则: rules/Custom_DNS_IP.txt"},

    # 🔗 Compatibility Aliases
    "geosite-emby": {"desc": "Emby 媒体服 (指向 geosite-custom-emby)", "note": "标准兼容别名"},
    "geosite-game": {"desc": "全球游戏加速 (指向 geosite-games)", "note": "标准兼容别名"},
    "geosite-microsoftcdn": {"desc": "微软 CDN (指向 geosite-microsoft-cdn)", "note": "标准兼容别名"},
    "geosite-appleservice": {"desc": "苹果服务 (指向 geosite-apple-services)", "note": "标准兼容别名"},
    "geosite-applecn": {"desc": "苹果国内服务 (指向 geosite-apple-cn)", "note": "标准兼容别名"},
    "geosite-applecdn": {"desc": "苹果 CDN (指向 geosite-apple-cdn)", "note": "标准兼容别名"},
}


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

    lines = []
    lines.append('<div align="center">')
    lines.append("")
    lines.append(f"# {emoji} {title} 规则订阅")
    lines.append("")
    lines.append(f'![规则总数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E6%80%BB%E6%95%B0-{total_items:,}-blue)')
    lines.append(f'![规则集数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E9%9B%86%E6%95%B0-{total_sets}-success)')
    lines.append(f'![格式](https://img.shields.io/badge/%E6%A0%BC%E5%BC%8F-{fmt_badge.replace(" ", "%20").replace("/", "%2F")}-informational)')
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
                note = meta.get("note", "-")
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
                note = meta.get("note", "-")
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
