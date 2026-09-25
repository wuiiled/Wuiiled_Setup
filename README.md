<div align="center">

# 🚀 Wuiiled Setup

### All-in-One 网络分流规则构建引擎

[![Build](https://github.com/wuiiled/Wuiiled_Setup/actions/workflows/merge.yaml/badge.svg)](https://github.com/wuiiled/Wuiiled_Setup/actions/workflows/merge.yaml)
[![Tests](https://github.com/wuiiled/Wuiiled_Setup/actions/workflows/test.yaml/badge.svg)](https://github.com/wuiiled/Wuiiled_Setup/actions/workflows/test.yaml)
![Rulesets](https://img.shields.io/badge/%E6%A0%87%E5%87%86%E8%A7%84%E5%88%99%E9%9B%86-113%2B-blue)
![0-Diff](https://img.shields.io/badge/0--Diff%20%E6%B5%8B%E8%AF%95-100%25%20PASS-brightgreen)
![Branches](https://img.shields.io/badge/%E8%AE%A2%E9%98%85%E5%88%86%E6%94%AF-5-blue)
![License](https://img.shields.io/badge/license-MIT-green)

一个高度自动化、零平台耦合、多客户端生态的无服务器（Serverless）网络分流规则构建与分发引擎。

基于 GitHub Actions 每日定时运行，自动从上游权威仓库与各大知名数据源拉取最新元数据，
经**深度清洗、白名单防误杀、前缀树去重与正则压缩**后，编译为五大平台专属格式并自动分发。

</div>

---

## 🎯 客户端订阅分支

各客户端规则维护在独立的孤儿分支（Orphan Branch）中，点击卡片进入对应分支获取订阅直链：

| 客户端 | 分支 | 提供格式 |
| :---: | :---: | :--- |
| 📦 **Sing-box** | [`singbox`](../../tree/singbox) | 高性能 `.srs` 二进制 + `.json`（Version 5，兼容 1.14.x） |
| 📦 **Mihomo (Clash Meta)** | [`mihomo`](../../tree/mihomo) | 高性能 `.mrs` 二进制 + `.txt` |
| 📦 **SmartDNS** | [`smartdns`](../../tree/smartdns) | 标准 `domain-set` / `ip-set` 语法 |
| 📦 **MosDNS** | [`mosdns-x`](../../tree/mosdns-x) | MosDNS-X 适配的 `domain:` / `full:` 语法 |
| 📦 **AdGuard Home** | [`adg`](../../tree/adg) | 标准 AdGuard 过滤语法（`\|\|拦截^` + `@@\|\|放行^`） |

---

## 🌐 规则生态全景体系

规则集统一采用 **`geosite/`**（域名集）与 **`geoip/`**（IP/CIDR 集）两级目录隔离，命名保留 `geosite-` / `geoip-` 标准前缀。
基于 **Loyalsoldier 官方源头 `geosite.dat`（v2ray Protobuf 原生解析）** 与多源深度清洗构建，涵盖 **113+ 个标准规则集**，在 Sing-box 平台达成 **100% 语义级/差集为 0 的权威对齐（0-Diff 严格自动化测试验证）**。

<details open>
<summary><b>1️⃣ 官方权威提纯规则集</b>（原生 Protobuf 源头构建，100% 0-Diff 对齐，点击展开）</summary>

GeoSite 规则直接拉取并解析 Loyalsoldier 官方最新 `geosite.dat` 二进制源文件（融合本地热补丁），杜绝传统反编译过程中的规则丢失；`geosite-cn` 以天灵 sing-geosite 配方本地合成精编 cn（`geolocation-cn` + `category-*@cn` + `category-*-cn` + `.cn`）为基座，再经 `rules/patches/geosite-cn.txt` 合并自有上游列表（`cn-additional-list` + SKK `domestic`）；`geosite-ai` 为自研多源清洗列表 ∪ dat `category-ai-!cn`；`sing-geoip` 系列原样同步：

| 分类 | 包含规则名称 | 核心服务与特点 |
| :--- | :--- | :--- |
| 🤖 **AI 与开发者** | `geosite-openai` · `geosite-anthropic` · `geosite-gemini` · `geosite-github` · `geosite-gitlab` · `geosite-docker` · `geosite-stackoverflow` · `geosite-npm` | ChatGPT / Claude / Gemini / GitHub / Docker / StackOverflow 等官方接口与资产 |
| 💬 **社交与通讯** | `geosite-telegram` · `geosite-discord` · `geosite-whatsapp` · `geosite-signal` · `geosite-line` · `geosite-x` · `geosite-instagram` · `geosite-threads` · `geosite-reddit` · `geosite-bluesky` · `geosite-tiktok` · `geosite-communication` · `geosite-social-media` | 全球主流即时通讯与社媒平台全覆盖 |
| 🎬 **影音流媒体** | `geosite-youtube` · `geosite-netflix` · `geosite-disney` · `geosite-spotify` · `geosite-apple-tvplus` · `geosite-hbo` · `geosite-hulu` · `geosite-primevideo` · `geosite-twitch` · `geosite-bahamut` · `geosite-abema` · `geosite-niconico` · `geosite-dmm` · `geosite-pixiv` · `geosite-vimeo` · `geosite-dailymotion` · `geosite-deezer` · `geosite-soundcloud` · `geosite-tidal` · `geosite-media` · `geosite-entertainment` | 覆盖全球 20+ 顶级影音流媒体服务及动画疯/Abema等区域特色媒体 |
| 🎮 **游戏与联机** | `geosite-steam` · `geosite-epicgames` · `geosite-playstation` · `geosite-xbox` · `geosite-nintendo` · `geosite-ea` · `geosite-ubisoft` · `geosite-rockstar` · `geosite-blizzard` · `geosite-riotgames` · `geosite-mihoyo` · `geosite-hoyoverse` · `geosite-games` · `geosite-games-cn` · `geosite-games-!cn` | Steam/Epic/PSN/Xbox/Switch及各大游戏发行商官方联机服务加速 |
| 💰 **金融与支付** | `geosite-paypal` · `geosite-stripe` · `geosite-wise` · `geosite-binance` · `geosite-okx` | 全球主流跨国支付、结算网关与顶级加密货币交易所 |
| 🌐 **基建与办公** | `geosite-cloudflare` · `geosite-fastly` · `geosite-akamai` · `geosite-vercel` · `geosite-netlify` · `geosite-microsoft` · `geosite-microsoft-cdn` · `geosite-onedrive` · `geosite-google` · `geosite-apple-services` · `geosite-apple-cdn` · `geosite-notion` · `geosite-figma` · `geosite-canva` · `geosite-zoom` · `geosite-netdisk-!cn` | 全球顶级 CDN、云基础设施、前端云平台、现代协同办公软件与海外网盘 (Dropbox/MEGA 等) |
| 🇨🇳 **国内基础路由** | `geosite-cn` · `geosite-!cn` · `geosite-gfw` · `geosite-private` · `geosite-httpdns` · `geosite-porn` | 大陆直连 (天灵精编+自有列表 双源合并)、境外分流 (2.7万条)、GFW列表 (4300+条)、私有局域网、防HTTPDNS劫持、成人内容过滤 |
| 🌍 **GeoIP 地址集** | `geoip-cn` · `geoip-google` · `geoip-telegram` · `geoip-twitter` · `geoip-facebook` · `geoip-private` | 国内运营商 IPv4/IPv6 网段 (9940+条)、Google官方网段 (8360+条)、各巨头官方数据中心网段 |

</details>

<details open>
<summary><b>2️⃣ 原创复合提纯规则集</b>（深度清洗与防误杀，点击展开）</summary>

由引擎动态汇聚多个业界知名数据源，经**前缀树自优化、终极正则压缩、多重白名单防误杀**生成：

| 规则名称 | 作用 | 上游数据源 |
| :--- | :--- | :--- |
| **`geosite-ad`** | **终极去广告 / 防追踪**<br>*(剔除数十万重复项与误杀项)* | `pmkol/easymosdns` · AdGuard 官方列表 (1/3/4) · Dan Pollock · Pi-hole · `Cats-Team/AdRules` · AWAvenue · OISD Small · 本地补丁 |
| **`geosite-ai`** | **全球主流 AI 服务合集**<br>*(自研列表 ∪ dat category-ai-!cn)* | `MetaCubeX` · `skk.moe` · `DustinWin` · dat `category-ai-!cn` |
| **`geosite-fakeip-filter`** | **Fake-IP 排除名单**<br>*(正则压缩，消除冗余)* | `OpenClash` · `ShellCrash` · `DustinWin` · `skk.moe` · 本地补丁 |
| **`geosite-reject-drop`** | **高危垃圾流量直接丢弃** | `skk.moe` · 本地名单 |
| **`geoip-gfw`** | **GFW 投毒 IP 与靶心网段** | ChinaDNS 投毒 IPv4 · EasyMosdns 投毒 CIDR · GFW 假 IPv6 靶心 |

> [!TIP]
> **🛡️ 智能白名单防误杀**：`geosite-ad` 与 `geosite-reject-drop` 预先经过 `Cats-Team/AdRules` Allowlist、`AdGuard SDNS Filter` Exceptions 及本地 `exclude-keyword.txt`、`Custom_Direct_DOMAIN.txt` 的多层差集扣除，杜绝正常购物、网银与工作网站断流。

</details>

<details>
<summary><b>🔀 去广告规则的三套产物</b>（黑名单A / 黑加白双集合 / AdGuard 混合，点击展开）</summary>

上游黑名单经清洗去重后与上游白名单做差集。**凡与上游白名单同名或为其后代的拦截项一律剔除（方向1）**。在此基础上产出三套形态：

- **黑名单A（Option A · 单集合保守版）**：额外把"白名单子域的父域"也剔除（方向2），宁放过勿错杀。对应 `geosite-ad`，各平台默认产物，向后兼容。
- **黑名单B + 白名单B（黑加白精确双集合）**：黑名单B 仅做方向1剔除（保留含白名单子域的父域）；白名单B 收录"会被黑名单B命中且自身不在上游黑名单"的上游白名单项。对应 `geosite-ad-precise` + `geosite-ad-allow`。
- **AdGuard Home（单文件混合）**：原生支持 `@@` 例外，`geosite-ad` 直接输出 `||黑名单B^` + `@@||白名单B^` 混合单文件。

**各分支产物对照**：

| 分支 | `geosite-ad` | `geosite-ad-precise` | `geosite-ad-allow` |
| :--- | :--- | :--- | :--- |
| **smartdns**（供 OxiDNS） | 黑名单A | —（OxiDNS 白名单外） | —（OxiDNS 白名单外） |
| **mihomo** | 黑名单A | 黑名单B | 白名单B |
| **sing-box** | 黑名单A | —（单集合不支持例外） | — |
| **adg** | 黑名单B + 白名单B 混合（`@@` 例外） | — | — |

**使用方式**：OxiDNS 在 sequence 中先 `qname $allow → return` 再 `qname $precise → drop`；mihomo 在 `rules:` 中将 `RULE-SET,geosite-ad-allow,DIRECT` 置于 `RULE-SET,geosite-ad-precise,REJECT` 之前短路。

</details>

<details>
<summary><b>3️⃣ 知名生态服务与上游分类</b>（SKK 维护，点击展开）</summary>

由 [`ruleset.skk.moe`](https://ruleset.skk.moe) 权威提供，按国内大厂与核心基础设施精准分类：

- **`geosite-alibaba`**（阿里巴巴系）· **`geosite-tencent`**（腾讯系）· **`geosite-bilibili`**（哔哩哔哩）
- **`geosite-xiaomi`**（小米系）· **`geosite-bytedance`**（字节跳动）· **`geosite-baidu`**（百度系）· **`geosite-qihoo360`**（奇虎360）
- **`geosite-apple-services`** / **`geosite-apple-cn`** / **`geosite-apple-cdn`**（Apple 核心与 CDN 细分）
- **`geosite-microsoft-cdn`**（微软 CDN）· **`geosite-domestic`**（国内常用服务）· **`geosite-download`**（应用商店与大文件下载）
- **`geoip-stream`**（流媒体 IP 网段）· **`geoip-apple`**（Apple 核心服务 IP 网段）

</details>

<details>
<summary><b>4️⃣ 本地自定义规则</b>（个性化分流，点击展开）</summary>

存放于 `rules/` 目录，直接满足个性化路由需求：

| 源文件 | 生成规则集 | 说明 |
| :--- | :--- | :--- |
| `Custom_Direct_DOMAIN.txt` / `Custom_Direct_IP.txt` | `geosite-custom-direct` | 自定义直连（Sing-box 智能合并域名+IP） |
| `Custom_DNS_DOMAIN.txt` / `Custom_DNS_IP.txt` | `geosite-custom-dns` | 自定义 DNS（Sing-box 智能合并） |
| `Custom_Proxy.txt` | `geosite-custom-proxy` | 自定义代理分流 |
| `Custom_Download.txt` | `geosite-custom-download` | 自定义下载分流 |
| `Custom_Emby.txt` | `geosite-custom-emby` | 自定义 Emby / Jellyfin 媒体服 |
| `LocationDKS.txt` | `geosite-location-dks` | 抖音/快手/小红书 IP 归属地 |

</details>

---

## 📁 仓库结构

```
Wuiiled_Setup/
├── .github/workflows/      # GitHub Actions：定时构建 + 测试 + 分发
├── rules/                  # 规则源文件与静态补丁（代码与数据物理隔离）
│   ├── addons/             # 白名单关键字 / Fake-IP / 广告 补丁
│   ├── patches/            # 热补丁: 手动域名 + include 列表/分类合并 (geosite-porn / geosite-cn / geosite-ai ...)
│   └── Custom_*.txt        # 各类自定义分流名单
├── scripts/                # 构建引擎源码（三层解耦架构）
│   ├── core/               # 核心：models / cleaner / fetcher / manager / readme_gen
│   ├── build_*.py          # 五平台独立导出器
│   ├── main.py             # 统一主入口
│   └── providers.py        # 上游源 URL 配置清单
├── tests/                  # 自动化测试套件（含 0-Diff 对齐校验）
├── singbox/config.json     # Sing-box 参考配置示例
└── README.md               # 本文档
```

---

## 🛠️ 本地运行与测试

**环境依赖**：Python 3.9+ · [mihomo](https://github.com/MetaCubeX/mihomo/releases) · [sing-box](https://github.com/SagerNet/sing-box/releases) 1.14.x（均放入 PATH 或通过 WSL）

```bash
# 一键构建完整流水线并生成各平台 README
PYTHONPATH=scripts python3 scripts/main.py

# 验证所有权威规则集与上游 100% 一致（0-Diff）
PYTHONPATH=scripts python3 -m pytest tests/test_tianling_zero_diff.py -v
```

---

<div align="center">

**⭐ 如果觉得有用，欢迎 Star 支持**

</div>
