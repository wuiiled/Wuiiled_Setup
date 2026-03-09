# 🚀 All-in-One 网络分流规则构建引擎

这是一个高度自动化的无服务器（Serverless）规则转换与分发引擎。
基于 GitHub Actions 每日定时运行，自动从上游拉取最新的规则元数据，经过**清洗、白名单过滤、智能去重合并**后，自动编译为四大平台支持的格式，并分发到独立的订阅分支。

## 🎯 支持的客户端分支与格式

我们在不同的孤儿分支（Orphan Branch）中维护了对应平台的专属规则，点击链接即可进入获取订阅直链：

* 📦 [**Mihomo (Clash Meta)**](./../../tree/mihomo) - 提供 `.mrs` 二进制与 `.txt` 文本规则。
* 📦 [**Sing-box**](./../../tree/singbox) - 提供 `.srs` 二进制与 `.json` 规则（采用最新 Version 4 标准优化内存）。
* 📦 [**AdGuard Home**](./../../tree/adg) - 提供标准的 AdGuard 过滤语法规则。
* 📦 [**MosDNS**](./../../tree/mosdns-x) - 提供专为 MosDNS-X 适配的 `domain:` / `full:` 语法规则。

---

## 📊 核心复合规则 (合成逻辑与元数据来源)

以下规则是由 Python 脚本动态拉取多个上游源，经过深度处理（正则清洗、应用白名单、前缀树优化去重）后生成的强力复合规则：

| 🗂️ 规则名称 | 📝 作用 | 🌐 上游元数据来源 (Sources) |
| :--- | :--- | :--- |
| **`ADs_merged`** | **终极去广告/防追踪**<br>*(剔除了数十万重复项与误杀项)* | 1. `pmkol/easymosdns` 广告列表<br>2. AdGuard 官方过滤列表 (1, 3, 4)<br>3. `ForestL18` PCDN 拦截库<br>4. Pi-hole 拦截名单<br>5. `Cats-Team/AdRules` 域名集<br>6. 库内自定义拦截 `Reject-addon.txt` |
| **`AIs_merged`** | **AI 服务合集**<br>*(ChatGPT/Claude/Gemini等)* | 1. `MetaCubeX` AI 列表<br>2. `skk.moe` AI 配置<br>3. `DustinWin` AI 规则<br>4. `ConnersHua` AI 附加规则 |
| **`Fake_IP_Filter`** | **Fake-IP 过滤名单**<br>*(不适合走 Fake-IP 的域名)* | 1. `OpenClash` 默认过滤列表<br>2. `ShellCrash` 过滤列表<br>3. `DustinWin` 过滤列表<br>4. `skk.moe` 过滤列表<br>5. 库内自定义 `fake-ip-addon.txt` |
| **`Reject_Drop`** | **高危/垃圾流量丢弃** | 1. `skk.moe` 拒绝丢弃列表<br>2. 库内自定义 `Custom_Reject-drop.txt` |
| **`CN_merged`** | **国内直连合集** | 1. `353355.xyz` 国内附加列表<br>2. `skk.moe` 国内域名合集 |

### 🛡️ 白名单防误杀机制
上述 `ADs_merged` 和 `Reject_Drop` 在生成前，会严格经过以下白名单的过滤，确保不会造成正常网站（如淘宝、微软、苹果服务）的断流：
* `Cats-Team/AdRules` Allowlist
* AdGuardSDNSFilter Exceptions
* 库内自定义白名单 `scripts/exclude-keyword.txt`

---

## 🧩 基础分流规则来源

这部分规则主要直接继承自业界知名的规则维护者，保证分类的精准度和更新频率。

### 1. 互联网大厂服务 (源自 SKK)
由 `ruleset.skk.moe` 提供，按国内大厂生态精准分类：
* **`alibaba`** (阿里巴巴系)
* **`tencent`** (腾讯系)
* **`bilibili`** (哔哩哔哩)
* **`xiaomi`** (小米系)
* **`bytedance`** (字节跳动)
* **`baidu`** (百度系)
* **`qihoo360`** (奇虎360)

### 2. Apple 生态服务 (源自 Repcz)
* **`AppleProxy`**：苹果非大陆服务（通常需走代理，如 News, AI）
* **`AppleServers`**：苹果核心服务器
* **`AppleCN`**：苹果中国大陆本地服务（CDN，需直连）

### 3. 其他功能性分类
* **`private`**：局域网与保留 IP (源自 `ForestL18`)
* **`download`**：迅雷/BT/PT/各大应用商店下载流量 (源自 `skk.moe`)
* **`domestic`**：国内常用服务 (源自 `skk.moe`)
* **`PCDN`**：各大视频/网盘网站的 PCDN 节点拦截 (用于 AdGuard，源自库内 `pcdn.list`)
* **`Httpdns`**：拦截国内 APP 内置的 HTTPDNS 解析防劫持 (用于 AdGuard，源自 `MetaCubeX`)

---

## 🛠️ 本地自定义规则 (Custom Rules)

存放在主分支 `rules/` 目录下，用于满足个人的特殊路由需求，每次构建时会原样打包并转换格式：

* `Custom_Direct.txt` (含 IP/DOMAIN) —— 强制直连
* `Custom_Proxy.txt` —— 强制代理
* `Custom_DNS.txt` (含 IP/DOMAIN) —— 强制指定 DNS 解析
* `Custom_Emby.txt` —— Emby 媒体服分流
* `LocationDKS.txt` —— 特定地域服务

---

> **⚙️ Build Powered by Python & GitHub Actions**
> 本项目核心算法采用 Python 多线程并发下载与前缀树智能去重，执行速度快，内存开销小。每天 00:00 与 12:00 自动更新并发布。