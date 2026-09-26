<div align="center">

# 📦 MosDNS-X 规则订阅

![规则总数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E6%80%BB%E6%95%B0-514,461-blue)
![规则集数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E9%9B%86%E6%95%B0-19-success)
![格式](https://img.shields.io/badge/%E6%A0%BC%E5%BC%8F-domain:%20%2F%20full:-informational)

<i>由 <a href="https://github.com/wuiiled/Wuiiled_Setup">Wuiiled_Setup</a> 规则自动化引擎实时构建分发</i><br>
<sub>🕐 最后更新：2026-09-27 00:00:49 (Asia/Shanghai)</sub>

</div>

---

## 💡 如何使用

在下方分类表格中 **右键点击** 对应链接，选择 **复制链接地址**，填入客户端订阅即可。

<details>
<summary><b>🛠️ MosDNS 配置示例</b>（点击展开）</summary>

在 `config.yaml` 的插件配置中引入规则集：

```yaml
plugins:
  - tag: site_cn
    type: domain_set
    args:
      files:
        - "/etc/mosdns/rules/geosite-cn.txt"
```

</details>

## 📑 规则分类快速导航

[🌐](#cloud) · [🇨🇳](#china) · [🛡️](#security) · [🛠️](#custom) · [🌍](#geoip)

---

<span id="cloud"></span>

### 🌐 网络基建与协同办公 (Cloud & SaaS)

| 规则名称 | 描述 | 条数 | 订阅链接 |
| :--- | :--- | ---: | :---: |
| **`geosite-microsoft-cdn`** | Microsoft 微软全球资源分发 CDN | `51` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-microsoft-cdn.txt) |
| **`geosite-apple-services`** | Apple 苹果全球核心云服务与 iCloud | `16` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-apple-services.txt) |
| **`geosite-apple-cdn`** | Apple 苹果官方资产与软件更新 CDN | `159` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-apple-cdn.txt) |

<span id="china"></span>

### 🇨🇳 国内直连与核心大厂 (China & Ecosystem)

| 规则名称 | 描述 | 条数 | 订阅链接 |
| :--- | :--- | ---: | :---: |
| **`geosite-cn`** | 🇨🇳 中国大陆域名双源合并合集 (精编+自有) | `32,638` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-cn.txt) |
| **`geosite-!cn`** | 🌐 非中国大陆节点域名合集 (境外代理) | `27,249` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-!cn.txt) |
| **`geosite-alibaba`** | 阿里巴巴系服务 (淘宝/天猫/阿里云/钉钉) | `89` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-alibaba.txt) |
| **`geosite-tencent`** | 腾讯系服务 (微信/QQ/腾讯云/腾讯视频) | `50` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-tencent.txt) |
| **`geosite-bilibili`** | 哔哩哔哩 (B站) 视频与直播核心资产 | `17` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-bilibili.txt) |
| **`geosite-xiaomi`** | 小米系生态服务 (MIUI/米家/云服务) | `18` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-xiaomi.txt) |
| **`geosite-bytedance`** | 字节跳动系服务 (抖音/头条/飞书) | `69` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-bytedance.txt) |
| **`geosite-baidu`** | 百度系服务 (搜索/网盘/地图/文心一言) | `30` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-baidu.txt) |
| **`geosite-qihoo360`** | 奇虎 360 安全防护与搜索服务 | `21` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-qihoo360.txt) |
| **`geosite-apple-cn`** | Apple 苹果中国大陆本地化加速域名 | `9` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-apple-cn.txt) |

<span id="security"></span>

### 🛡️ 安全防护与过滤拦截 (Security & Blocking)

| 规则名称 | 描述 | 条数 | 订阅链接 |
| :--- | :--- | ---: | :---: |
| **`geosite-ad`** | 终极去广告 / 防追踪 (单集合保守版) | `224,448` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-ad.txt) |
| **`geosite-ad-precise`** | 去广告黑名单精确版 (双集合黑名单B) | `218,897` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-ad-precise.txt) |
| **`geosite-ad-allow`** | 去广告防误杀白名单 (双集合白名单B) | `69` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-ad-allow.txt) |

<span id="custom"></span>

### 🛠️ 本地自定义与特征分流 (Custom Routing)

| 规则名称 | 描述 | 条数 | 订阅链接 |
| :--- | :--- | ---: | :---: |
| **`geosite-custom-emby`** | 本地自定义 Emby / Jellyfin 媒体服 | `24` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geosite/geosite-custom-emby.txt) |

<span id="geoip"></span>

### 🌍 GeoIP 地址段网段集合 (IP Networks)

| 规则名称 | 描述 | 条数 | 订阅链接 |
| :--- | :--- | ---: | :---: |
| **`geoip-cn`** | 🇨🇳 中国大陆三大运营商 IPv4/IPv6 权威网段 | `9,811` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geoip/geoip-cn.txt) |
| **`geoip-gfw`** | 🧱 GFW 投毒 IP 与伪造靶心网段拦截 | `796` | [📥 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mosdns-x/rules/geoip/geoip-gfw.txt) |

---

<div align="center">

[🏠 返回主仓库](https://github.com/wuiiled/Wuiiled_Setup) · [⭐ Star 支持](https://github.com/wuiiled/Wuiiled_Setup)

</div>
