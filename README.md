<div align="center">

# 🚀 Wuiiled Setup

### All-in-One 网络分流规则构建引擎

[![Build](https://github.com/wuiiled/Wuiiled_Setup/actions/workflows/merge.yaml/badge.svg)](https://github.com/wuiiled/Wuiiled_Setup/actions/workflows/merge.yaml)
[![Tests](https://github.com/wuiiled/Wuiiled_Setup/actions/workflows/test.yaml/badge.svg)](https://github.com/wuiiled/Wuiiled_Setup/actions/workflows/test.yaml)
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

<details open>
<summary><b>1️⃣ 官方权威提纯规则集</b>（与上游 100% 0-Diff 一致，点击展开）</summary>

直接对齐上游核心仓库 [`1715173329/sing-geosite`](https://github.com/1715173329/sing-geosite) 与 [`1715173329/sing-geoip`](https://github.com/1715173329/sing-geoip) 的 `rule-set` 分支，由官方预编译二进制直接导入，在 Sing-box 平台达成 **100% 字节级/语义级一致（差集为 0）**，并无损导出至全平台生态。

| 规则名称 | 描述 | 上游 |
| :--- | :--- | :--- |
| **`geosite-cn`** | 🇨🇳 中国大陆域名直连合集 | `sing-geosite` |
| **`geosite-geolocation-!cn`** | 🌐 非中国大陆节点域名合集 | `sing-geosite` |
| **`geosite-gfw`** | 🧱 GFW 域名列表 | `sing-geosite` |
| **`geosite-google`** | 🔍 Google 全球全系服务 | `sing-geosite` |
| **`geosite-youtube`** | 📺 YouTube 影音流媒体 | `sing-geosite` |
| **`geosite-github`** | 🐙 GitHub 开发者服务与资产 | `sing-geosite` |
| **`geosite-onedrive`** | ☁️ Microsoft OneDrive 存储服务 | `sing-geosite` |
| **`geosite-microsoft`** | 🪟 Microsoft 全球产品与服务 | `sing-geosite` |
| **`geosite-tiktok`** | 🎵 TikTok 国际版短视频 | `sing-geosite` |
| **`geosite-spotify`** | 🎧 Spotify 音乐流媒体 | `sing-geosite` |
| **`geosite-netflix`** | 🎬 Netflix 奈飞影音 | `sing-geosite` |
| **`geosite-disney`** | 🏰 Disney+ 迪士尼流媒体 | `sing-geosite` |
| **`geosite-porn`** | 🔞 成人内容与不良网站 | `sing-geosite` |
| **`geosite-media`** | 📻 全球多媒体与流媒体服务 | `sing-geosite` |
| **`geosite-communication`** | 💬 全球即时通讯与在线会议 | `sing-geosite` |
| **`geosite-social-media`** | 📱 全球社交网络与媒体平台 | `sing-geosite` |
| **`geosite-games`** | 🎮 全球热门游戏与平台联机服务 | `sing-geosite` |
| **`geosite-games-cn`** | 🎮 国内热门网络游戏与加速服务 | `sing-geosite` |
| **`geosite-private`** | 🔒 局域网与内部保留域名 | `sing-geosite` |
| **`geosite-apple-tvplus`** | 🍏 Apple TV+ 影音分流 | `sing-geosite` |
| **`geosite-httpdns`** | 🛡️ 国内 APP 内置 HTTPDNS 解析劫持拦截 | `sing-geosite` |
| **`geoip-cn`** | 🇨🇳 中国大陆三大运营商 IPv4/IPv6 网段 | `sing-geoip` |
| **`geoip-google`** | 🔍 Google 官方全网 IPv4/IPv6 网段 | `sing-geoip` |
| **`geoip-telegram`** | ✈️ Telegram 官方网段 | `sing-geoip` |
| **`geoip-twitter`** | 🐦 Twitter / X 官方网段 | `sing-geoip` |
| **`geoip-facebook`** | 📘 Meta / Facebook 官方网段 | `sing-geoip` |
| **`geoip-private`** | 🔒 局域网保留与私有 IP 地址 | `sing-geoip` |

</details>

<details open>
<summary><b>2️⃣ 原创复合提纯规则集</b>（深度清洗与防误杀，点击展开）</summary>

由引擎动态汇聚多个业界知名数据源，经**前缀树自优化、终极正则压缩、多重白名单防误杀**生成：

| 规则名称 | 作用 | 上游数据源 |
| :--- | :--- | :--- |
| **`geosite-ad`** | **终极去广告 / 防追踪**<br>*(剔除数十万重复项与误杀项)* | `pmkol/easymosdns` · AdGuard 官方列表 (1/3/4) · Dan Pollock · Pi-hole · `Cats-Team/AdRules` · AWAvenue · OISD Small · 本地补丁 |
| **`geosite-ai`** | **全球主流 AI 服务合集**<br>*(ChatGPT/Claude/Gemini/Copilot 等)* | `MetaCubeX` · `skk.moe` · `DustinWin` |
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
| **smartdns**（供 OxiDNS） | 黑名单A | 黑名单B | 白名单B |
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
- **`geosite-microsoft-cdn`**（微软 CDN）· **`geosite-domestic`**（国内常用服务）· **`geosite-download`**（应用商店与 P2P 下载）
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
| `Custom_Emby.txt` | `geosite-custom-emby` | 自定义 Emby（兼容别名 `geosite-emby`） |
| `LocationDKS.txt` | `geosite-location-dks` | 抖音/快手/小红书 IP 归属地 |

</details>

---

## 📁 仓库结构

```
Wuiiled_Setup/
├── .github/workflows/      # GitHub Actions：定时构建 + 测试 + 分发
├── rules/                  # 规则源文件与静态补丁（代码与数据物理隔离）
│   ├── addons/             # 白名单关键字 / Fake-IP / 广告 补丁
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
