# 🚀 All-in-One 网络分流规则构建引擎 (v2.0)

这是一个高度自动化、零平台耦合、支持多客户端生态的无服务器（Serverless）网络分流规则构建与分发引擎。

基于 GitHub Actions 每日定时运行，自动从**天灵官方仓库（1715173329）**、广告黑名单以及各大知名上游源拉取最新元数据，经过**深度清洗、白名单过滤、前缀树去重优化与正则压缩**后，编译为五大平台专属格式，并自动分发至对应的独立订阅分支。

---

## 🎯 客户端订阅分支与格式导航

我们在独立孤儿分支（Orphan Branch）中维护各客户端专属规则。点击下方链接即可进入对应分支查看完整的**双格式合一规则导航表格**与订阅直链：

* 📦 [**Sing-box 分支**](./../../tree/singbox) - 提供高性能 `.srs` 二进制与 `.json` 规则（采用 Version 5 标准，兼容 sing-box 1.14.x）。
* 📦 [**Mihomo (Clash Meta) 分支**](./../../tree/mihomo) - 提供高性能 `.mrs` 二进制与 `.txt` 规则。
* 📦 [**SmartDNS 分支**](./../../tree/smartdns) - 提供标准的 `domain-set` 与 `ip-set` 语法规则。
* 📦 [**MosDNS 分支**](./../../tree/mosdns-x) - 提供专为 MosDNS-X 适配的 `domain:` / `full:` 语法规则。
* 📦 [**AdGuard Home 分支**](./../../tree/adg) - 提供标准的 AdGuard 过滤语法规则。

---

## 🌐 规则生态全景体系

本项目对规则集实行规范的 **`geosite/`**（域名集）与 **`geoip/`**（IP/CIDR集）两级目录分类隔离，并在命名上统一保留 `geosite-` 与 `geoip-` 标准前缀。

### 1. 天灵官方权威提纯规则集 (100% 0-Diff 绝对一致)
直接对齐核心开发者**天灵 Shen (`1715173329`)**官方发布的 Release 与 `rule-set` 分支，由官方预编译二进制直接导入，在 Sing-box 平台上达成 **100.000% 字节级/语义级完全一致（差集为 0）**，并无损导出至 Mihomo、SmartDNS、MosDNS 等全平台生态：

| 🗂️ 规则名称 | 📝 描述说明 | 🌐 权威上游 |
| :--- | :--- | :--- |
| **`geosite-cn`** | 🇨🇳 中国大陆域名直连合集 (41,953 条规则，精确无缝) | 天灵 `sing-geosite` |
| **`geosite-geolocation-!cn`** | 🌐 非中国大陆节点域名合集 | 天灵 `sing-geosite` |
| **`geosite-gfw`** | 🧱 GFW 域名列表 | 天灵 `sing-geosite` |
| **`geosite-google`** | 🔍 Google 全球全系服务 | 天灵 `sing-geosite` |
| **`geosite-youtube`** | 📺 YouTube 影音流媒体 | 天灵 `sing-geosite` |
| **`geosite-github`** | 🐙 GitHub 开发者服务与资产 | 天灵 `sing-geosite` |
| **`geosite-onedrive`** | ☁️ Microsoft OneDrive 存储服务 | 天灵 `sing-geosite` |
| **`geosite-microsoft`** | 🪟 Microsoft 全球产品与服务 | 天灵 `sing-geosite` |
| **`geosite-tiktok`** | 🎵 TikTok 国际版短视频 | 天灵 `sing-geosite` |
| **`geosite-spotify`** | 🎧 Spotify 音乐流媒体 | 天灵 `sing-geosite` |
| **`geosite-netflix`** | 🎬 Netflix 奈飞影音 | 天灵 `sing-geosite` |
| **`geosite-disney`** | 🏰 Disney+ 迪士尼流媒体 | 天灵 `sing-geosite` |
| **`geosite-porn`** | 🔞 成人内容与不良网站 | 天灵 `sing-geosite` |
| **`geosite-media`** | 📻 全球多媒体与流媒体服务 | 天灵 `sing-geosite` |
| **`geosite-communication`** | 💬 全球即时通讯与在线会议 | 天灵 `sing-geosite` |
| **`geosite-social-media`** | 📱 全球社交网络与媒体平台 | 天灵 `sing-geosite` |
| **`geosite-games`** | 🎮 全球热门游戏与平台联机服务 | 天灵 `sing-geosite` |
| **`geosite-games-cn`** | 🎮 国内热门网络游戏与加速服务 | 天灵 `sing-geosite` |
| **`geosite-private`** | 🔒 局域网与内部保留域名 | 天灵 `sing-geosite` |
| **`geosite-apple-tvplus`** | 🍏 Apple TV+ 影音分流 | 天灵 `sing-geosite` |
| **`geosite-httpdns`** | 🛡️ 国内 APP 内置 HTTPDNS 解析劫持拦截 | 天灵 `sing-geosite` |
| **`geoip-cn`** | 🇨🇳 中国大陆三大运营商 IPv4/IPv6 网段 | 天灵 `sing-geoip` |
| **`geoip-google`** | 🔍 Google 官方全网 IPv4/IPv6 网段 | 天灵 `sing-geoip` |
| **`geoip-telegram`** | ✈️ Telegram 官方网段 | 天灵 `sing-geoip` |
| **`geoip-twitter`** | 🐦 Twitter / X 官方网段 | 天灵 `sing-geoip` |
| **`geoip-facebook`** | 📘 Meta / Facebook 官方网段 | 天灵 `sing-geoip` |
| **`geoip-private`** | 🔒 局域网保留与私有 IP 地址 | 天灵 `sing-geoip` |

---

### 2. 原创复合提纯规则集 (深度清洗与防误杀)
以下规则由引擎动态汇聚多个业界知名数据源，经**前缀树自优化、终极正则压缩、多重白名单防误杀**过滤生成：

| 🗂️ 规则名称 | 📝 作用 | 🌐 上游元数据来源 (Sources) |
| :--- | :--- | :--- |
| **`geosite-ad`** | **终极去广告/防追踪**<br>*(剔除数十万重复项与误杀项)* | 1. `pmkol/easymosdns` 广告列表<br>2. AdGuard 官方过滤列表 (1, 3, 4)<br>3. Dan Pollock 广告列表<br>4. Pi-hole 拦截名单<br>5. `Cats-Team/AdRules` 域名集<br>6. AWAvenue Ads Rule<br>7. OISD Small<br>8. 本地补丁 `rules/addons/reject-addon.txt` |
| **`geosite-ai`** | **全球主流 AI 服务合集**<br>*(ChatGPT/Claude/Gemini/Copilot等)* | 1. `MetaCubeX` AI 列表<br>2. `skk.moe` AI 配置<br>3. `DustinWin` AI 规则 |
| **`geosite-fakeip-filter`** | **Fake-IP 排除名单**<br>*(终极正则压缩，彻底消除冗余)* | 1. `OpenClash` 默认过滤列表<br>2. `ShellCrash` 过滤列表<br>3. `DustinWin` 过滤列表<br>4. `skk.moe` 过滤列表<br>5. 本地补丁 `rules/addons/fake-ip-addon.txt` |
| **`geosite-reject-drop`** | **高危垃圾流量直接丢弃** | 1. `skk.moe` 丢弃列表<br>2. 本地名单 `rules/Custom_Reject-drop.txt` |
| **`geoip-gfw`** | **GFW 投毒 IP 与靶心网段** | 1. ChinaDNS 经典投毒 IPv4<br>2. EasyMosdns 投毒网段 CIDR<br>3. GFW 经典假 IPv6 靶心列表 |

> [!TIP]
> **🛡️ 智能白名单防误杀机制**：
> `geosite-ad` 与 `geosite-reject-drop` 预先经过 `Cats-Team/AdRules` Allowlist、`AdGuard SDNS Filter` Exceptions 以及本地 `rules/addons/exclude-keyword.txt`、`rules/Custom_Direct_DOMAIN.txt` 的多层差集扣除，杜绝正常购物、网银与工作网站断流。

> [!NOTE]
> **🔀 白名单策略按平台分叉**：
> Mihomo / Sing-box 规则集为单集合格式，无法表达“拦截父域但放行子域”的例外，因此采用 Option A（含白名单子域的父域整体放行，宁放过勿错杀）；
> **OxiDNS**（消费 smartdns 分支）支持 matcher 否定与 sequence 短路，故 smartdns 分支额外输出 `geosite-ad-allow.txt`（独立白名单）配合 `geosite-ad.txt`（精确黑名单），实现真正的“父域拦截 + 子域放行”。


---

### 3. 知名生态服务与上游分类 (SKK 维护)
由 `ruleset.skk.moe` 权威提供，按国内大厂与核心基础设施精准分类：
* **`geosite-alibaba`** (阿里巴巴系)
* **`geosite-tencent`** (腾讯系)
* **`geosite-bilibili`** (哔哩哔哩)
* **`geosite-xiaomi`** (小米系)
* **`geosite-bytedance`** (字节跳动)
* **`geosite-baidu`** (百度系)
* **`geosite-qihoo360`** (奇虎360)
* **`geosite-apple-services`** / **`geosite-apple-cn`** / **`geosite-apple-cdn`** (Apple 核心与 CDN 细分)
* **`geosite-microsoft-cdn`** (微软 CDN)
* **`geosite-domestic`** (国内常用服务合集)
* **`geosite-download`** (应用商店与 P2P 下载流量)
* **`geoip-stream`** (流媒体服务 IP 网段)
* **`geoip-apple`** (Apple 核心服务 IP 网段)

---

### 4. 本地自定义规则与个性化分流 (Custom Rules)
存放于 `rules/` 目录下，直接满足个性化路由需求：
* `Custom_Direct_DOMAIN.txt` / `Custom_Direct_IP.txt` $\rightarrow$ `geosite-custom-direct`（Sing-box 智能合并域名与 IP 编译为单个规则集）
* `Custom_DNS_DOMAIN.txt` / `Custom_DNS_IP.txt` $\rightarrow$ `geosite-custom-dns`（Sing-box 智能合并）
* `Custom_Proxy.txt` $\rightarrow$ `geosite-custom-proxy`
* `Custom_Download.txt` $\rightarrow$ `geosite-custom-download`
* `Custom_Emby.txt` $\rightarrow$ `geosite-custom-emby` (兼容别名 `geosite-emby`)
* `LocationDKS.txt` $\rightarrow$ `geosite-location-dks` (抖音/快手/小红书 IP 归属地)

---

## 📁 规范仓库结构

```
Wuiiled_Setup/
├── .github/workflows/
│   └── merge.yaml              # GitHub Actions 工作流：定时构建与快速可靠部署
├── rules/                      # 规则源文件与静态补丁（代码与数据严格物理隔离）
│   ├── addons/                 # 静态规则补丁
│   │   ├── exclude-keyword.txt # 白名单防误杀关键字
│   │   ├── fake-ip-addon.txt   # Fake-IP 补充规则
│   │   └── reject-addon.txt    # 广告拦截补充规则
│   ├── Custom_DNS_DOMAIN.txt   # 自定义 DNS 域名
│   ├── Custom_DNS_IP.txt       # 自定义 DNS IP（CIDR）
│   ├── Custom_Direct_DOMAIN.txt# 自定义直连域名
│   ├── Custom_Direct_IP.txt    # 自定义直连 IP（CIDR）
│   ├── Custom_Download.txt     # 自定义下载分流
│   ├── Custom_Emby.txt         # 自定义 Emby 分流
│   ├── Custom_Proxy.txt        # 自定义代理分流
│   ├── Custom_Reject-drop.txt  # 自定义高危丢弃名单
│   └── LocationDKS.txt         # 社交平台地域分流
├── scripts/                    # 纯净构建引擎源码 (三层解耦架构)
│   ├── core/                   # 核心提纯与数据引擎
│   │   ├── models.py           # Canonical RuleSet IR 中间数据模型
│   │   ├── cleaner.py          # 纯算法清洗、前缀树与正则压缩
│   │   ├── fetcher.py          # 统一异步并发拉取与天灵原生对齐
│   │   ├── manager.py          # 全网规则集调度与组装管理器
│   │   └── readme_gen.py       # Python 原生双格式合一 README 生成引擎
│   ├── build_singbox.py        # Sing-box 独立导出器 (.srs + .json)
│   ├── build_mihomo.py         # Mihomo 独立导出器 (.mrs + .txt)
│   ├── build_smartdns.py       # SmartDNS 独立导出器 (.txt)
│   ├── build_mosdns.py         # MosDNS-X 独立导出器 (.txt)
│   ├── build_adg.py            # AdGuard Home 独立导出器 (.txt)
│   ├── main.py                 # 统一主入口
│   ├── providers.py            # 上游源 URL 配置清单
│   └── utils.py                # 跨平台执行与底层通用工具
├── tests/                      # 自动化测试套件
│   ├── test_tianling_zero_diff.py # 0-Diff 绝对对齐天灵自动化测试
│   └── ...
├── singbox/config.json         # Sing-box 参考配置示例
└── README.md                   # 本文档
```

---

## 🛠️ 本地运行与测试

### 环境依赖
- Python 3.8+
- [mihomo](https://github.com/MetaCubeX/mihomo/releases)（放在 PATH 中或通过 WSL）
- [sing-box](https://github.com/SagerNet/sing-box/releases) 1.14.x（放在 PATH 中或通过 WSL）

### 一键构建
```bash
# 执行完整构建流水线并生成各平台 README
PYTHONPATH=scripts python3 scripts/main.py
```

### 自动化 0-Diff 校验
```bash
# 验证所有规则集与天灵官方源 100% 完全一致
PYTHONPATH=scripts python3 -m pytest tests/test_tianling_zero_diff.py -v
```