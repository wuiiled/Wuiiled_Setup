<div align="center">

# 📦 mihomo 规则订阅导航

<i>由 Wuiiled_Setup 规则自动化构建引擎实时构建分发</i><br>
<i>最后更新时间：2026-09-19 23:34:22 (Asia/Shanghai)</i>
</div>

---

## 💡 如何使用
在下方表格中，**右键点击**对应规则链接，选择 **“复制链接地址”** 填入客户端订阅即可。

### 🛠️ Mihomo (Clash Meta) 客户端配置示例
在配置文件的 `rule-providers` 中配置规则提供者（推荐优先使用高性能的 `.mrs`）：
```yaml
rule-providers:
  geosite-ad:
    type: http
    behavior: domain
    format: mrs
    url: "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ad.mrs"
    path: ./ruleset/geosite-ad.mrs
    interval: 86400
```

### 🌐 GeoSite 域名 规则集
| 🗂️ 规则名称 (Rule) | 🔢 条数 | ⚡️ 高性能二进制 (.mrs) | 📄 纯文本 (.txt) |
| :--- | :---: | :---: | :---: |
| **`geosite-ad`** | <kbd>222,978</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ad.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ad.txt) |
| **`geosite-ai`** | <kbd>50</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ai.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ai.txt) |
| **`geosite-alibaba`** | <kbd>89</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-alibaba.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-alibaba.txt) |
| **`geosite-apple-cdn`** | <kbd>159</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-cdn.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-cdn.txt) |
| **`geosite-apple-cn`** | <kbd>9</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-cn.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-cn.txt) |
| **`geosite-apple-services`** | <kbd>16</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-services.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-services.txt) |
| **`geosite-apple-tvplus`** | <kbd>16</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-tvplus.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-tvplus.txt) |
| **`geosite-baidu`** | <kbd>30</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-baidu.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-baidu.txt) |
| **`geosite-bilibili`** | <kbd>18</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bilibili.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bilibili.txt) |
| **`geosite-bytedance`** | <kbd>69</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bytedance.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bytedance.txt) |
| **`geosite-cn`** | <kbd>6,438</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-cn.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-cn.txt) |
| **`geosite-communication`** | <kbd>151</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-communication.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-communication.txt) |
| **`geosite-custom-direct`** | <kbd>71</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-direct.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-direct.txt) |
| **`geosite-custom-dns`** | <kbd>18</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-dns.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-dns.txt) |
| **`geosite-custom-download`** | <kbd>2</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-download.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-download.txt) |
| **`geosite-custom-emby`** | <kbd>24</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-emby.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-emby.txt) |
| **`geosite-custom-proxy`** | <kbd>4</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-proxy.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-proxy.txt) |
| **`geosite-disney`** | <kbd>245</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-disney.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-disney.txt) |
| **`geosite-domestic`** | <kbd>865</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-domestic.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-domestic.txt) |
| **`geosite-download`** | <kbd>1,964</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-download.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-download.txt) |
| **`geosite-emby`** | <kbd>24</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-emby.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-emby.txt) |
| **`geosite-fakeip-filter`** | <kbd>152</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-fakeip-filter.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-fakeip-filter.txt) |
| **`geosite-games`** | <kbd>1,127</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-games.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-games.txt) |
| **`geosite-games-cn`** | <kbd>282</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-games-cn.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-games-cn.txt) |
| **`geosite-geolocation-!cn`** | <kbd>27,241</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-geolocation-!cn.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-geolocation-!cn.txt) |
| **`geosite-gfw`** | <kbd>4,365</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-gfw.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-gfw.txt) |
| **`geosite-github`** | <kbd>64</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-github.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-github.txt) |
| **`geosite-google`** | <kbd>1,047</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-google.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-google.txt) |
| **`geosite-httpdns`** | <kbd>50</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-httpdns.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-httpdns.txt) |
| **`geosite-location-dks`** | <kbd>5</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-location-dks.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-location-dks.txt) |
| **`geosite-media`** | <kbd>1,580</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-media.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-media.txt) |
| **`geosite-microsoft`** | <kbd>749</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-microsoft.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-microsoft.txt) |
| **`geosite-microsoft-cdn`** | <kbd>51</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-microsoft-cdn.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-microsoft-cdn.txt) |
| **`geosite-netflix`** | <kbd>42</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-netflix.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-netflix.txt) |
| **`geosite-onedrive`** | <kbd>11</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-onedrive.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-onedrive.txt) |
| **`geosite-porn`** | <kbd>6,660</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-porn.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-porn.txt) |
| **`geosite-private`** | <kbd>147</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-private.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-private.txt) |
| **`geosite-qihoo360`** | <kbd>25</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-qihoo360.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-qihoo360.txt) |
| **`geosite-reject-drop`** | <kbd>34</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-reject-drop.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-reject-drop.txt) |
| **`geosite-social-media`** | <kbd>624</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-social-media.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-social-media.txt) |
| **`geosite-spotify`** | <kbd>28</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-spotify.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-spotify.txt) |
| **`geosite-tencent`** | <kbd>50</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-tencent.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-tencent.txt) |
| **`geosite-tiktok`** | <kbd>37</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-tiktok.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-tiktok.txt) |
| **`geosite-xiaomi`** | <kbd>18</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-xiaomi.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-xiaomi.txt) |
| **`geosite-youtube`** | <kbd>191</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-youtube.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-youtube.txt) |

### 🌐 GeoIP 地址 规则集
| 🗂️ 规则名称 (Rule) | 🔢 条数 | ⚡️ 高性能二进制 (.mrs) | 📄 纯文本 (.txt) |
| :--- | :---: | :---: | :---: |
| **`geoip-apple`** | <kbd>10</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-apple.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-apple.txt) |
| **`geoip-cn`** | <kbd>9,940</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-cn.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-cn.txt) |
| **`geoip-custom-direct`** | <kbd>4</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-custom-direct.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-custom-direct.txt) |
| **`geoip-custom-dns`** | <kbd>34</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-custom-dns.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-custom-dns.txt) |
| **`geoip-facebook`** | <kbd>123</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-facebook.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-facebook.txt) |
| **`geoip-gfw`** | <kbd>800</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-gfw.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-gfw.txt) |
| **`geoip-google`** | <kbd>8,360</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-google.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-google.txt) |
| **`geoip-private`** | <kbd>17</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-private.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-private.txt) |
| **`geoip-stream`** | <kbd>19</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-stream.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-stream.txt) |
| **`geoip-telegram`** | <kbd>12</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-telegram.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-telegram.txt) |
| **`geoip-twitter`** | <kbd>19</kbd> | [👉 复制 MRS 直链](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-twitter.mrs) | [👉 查看 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-twitter.txt) |

