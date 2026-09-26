<div align="center">

# 📦 Mihomo (Clash Meta) 规则订阅

![规则总数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E6%80%BB%E6%95%B0-548,173-blue)
![规则集数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E9%9B%86%E6%95%B0-118-success)
![格式](https://img.shields.io/badge/%E6%A0%BC%E5%BC%8F-.mrs%20%2F%20.txt-informational)

<i>由 <a href="https://github.com/wuiiled/Wuiiled_Setup">Wuiiled_Setup</a> 规则自动化引擎实时构建分发</i><br>
<sub>🕐 最后更新：2026-09-27 00:00:48 (Asia/Shanghai)</sub>

</div>

---

## 💡 如何使用

在下方分类表格中 **右键点击** 对应链接，选择 **复制链接地址**，填入客户端订阅即可。

<details>
<summary><b>🛠️ Mihomo (Clash Meta) 配置示例</b>（点击展开）</summary>

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

</details>

## 📑 规则分类快速导航

[🤖](#ai) · [💬](#social) · [🎬](#media) · [🎮](#gaming) · [💰](#finance) · [🌐](#cloud) · [🇨🇳](#china) · [🛡️](#security) · [🛠️](#custom) · [🌍](#geoip)

---

<span id="ai"></span>

### 🤖 人工智能与开发 (AI & Dev)

| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-ai`** | 全球主流 AI 服务合集 (自研列表 ∪ dat 分类) | 上游: MetaCubeX/meta-rules-dat · ruleset.skk.moe · DustinWin/ruleset_geodata · dat 分类 category-ai-!cn | `195` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ai.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ai.txt) |
| **`geosite-openai`** | OpenAI / ChatGPT 官方服务与 API | dat 分类 openai · 含 OpenAI | `22` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-openai.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-openai.txt) |
| **`geosite-anthropic`** | Anthropic Claude 官方服务与 API | dat 分类 anthropic · 含 Anthropic | `8` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-anthropic.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-anthropic.txt) |
| **`geosite-gemini`** | Google Gemini / Bard 人工智能服务 | dat 分类 google-gemini · 含 Gemini | `43` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-gemini.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-gemini.txt) |
| **`geosite-github`** | GitHub 代码托管平台与开发者资产 | dat 分类 github · 含 GitHub / npm | `64` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-github.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-github.txt) |
| **`geosite-gitlab`** | GitLab 代码托管与 DevOps 云服务 | dat 分类 gitlab · 含 GitLab | `5` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-gitlab.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-gitlab.txt) |
| **`geosite-docker`** | Docker Hub 容器镜像与注册表 | dat 分类 docker · 含 Docker | `6` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-docker.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-docker.txt) |
| **`geosite-stackoverflow`** | Stack Overflow 与开发者技术社区 | dat 分类 stackexchange · 含 StackExchange | `25` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-stackoverflow.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-stackoverflow.txt) |
| **`geosite-npm`** | Node.js NPM 官方包管理器软件源 | dat 分类 npmjs · 含 npm | `3` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-npm.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-npm.txt) |

<span id="social"></span>

### 💬 社交与即时通讯 (Social & IM)

| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-communication`** | 全球即时通讯与在线会议聚合 | dat 分类 category-communication · 含 Discord / Telegram / WhatsApp / Signal / LINE | `151` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-communication.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-communication.txt) |
| **`geosite-social-media`** | 全球社交网络与媒体平台聚合 | dat 分类 category-social-media-!cn · 含 X/Twitter / Instagram / Bluesky / Facebook/Meta / Threads | `625` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-social-media.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-social-media.txt) |
| **`geosite-telegram`** | Telegram 电报全系官方通讯服务 | dat 分类 telegram · 含 Telegram | `21` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-telegram.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-telegram.txt) |
| **`geosite-discord`** | Discord 语音与社群即时通讯平台 | dat 分类 discord · 含 Discord | `28` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-discord.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-discord.txt) |
| **`geosite-whatsapp`** | WhatsApp 即时通讯与端到端加密 | dat 分类 whatsapp · 含 WhatsApp | `13` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-whatsapp.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-whatsapp.txt) |
| **`geosite-signal`** | Signal 隐私加密即时通讯服务 | dat 分类 signal · 含 Signal | `8` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-signal.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-signal.txt) |
| **`geosite-line`** | LINE 亚洲流行即时通讯与生活服务 | dat 分类 line · 含 LINE | `20` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-line.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-line.txt) |
| **`geosite-x`** | X (原 Twitter) 官方社交媒体平台 | dat 分类 x · 含 X/Twitter | `27` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-x.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-x.txt) |
| **`geosite-instagram`** | Instagram 社交图像与短视频平台 | dat 分类 instagram · 含 Instagram | `74` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-instagram.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-instagram.txt) |
| **`geosite-threads`** | Threads 文本社交互动媒体平台 | dat 分类 threads · 含 Threads | `2` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-threads.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-threads.txt) |
| **`geosite-reddit`** | Reddit 全球兴趣与新闻社区 | dat 分类 reddit · 含 Reddit | `12` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-reddit.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-reddit.txt) |
| **`geosite-bluesky`** | Bluesky 去中心化社交网络平台 | dat 分类 bluesky · 含 Bluesky | `3` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bluesky.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bluesky.txt) |
| **`geosite-tiktok`** | TikTok 国际版短视频平台 | dat 分类 tiktok · 含 TikTok | `37` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-tiktok.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-tiktok.txt) |

<span id="media"></span>

### 🎬 影音流媒体与娱乐 (Media & Streaming)

| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-media`** | 国际新闻媒体与区域电视台聚合 (新闻社/报媒/区域电视) | dat 分类 category-media · 含 半岛电视台 / 今日俄罗斯 / 澳大利亚九号台 / 法新社 / 台湾4GTV / 6park | `1,580` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-media.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-media.txt) |
| **`geosite-entertainment`** | 全球影音娱乐与流媒体聚合 | dat 分类 category-entertainment · 含 YouTube / Netflix / Disney+ / HBO / TikTok / Spotify 等 30 项 | `2,127` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-entertainment.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-entertainment.txt) |
| **`geosite-youtube`** | YouTube 视频流媒体与 YouTube Music | dat 分类 youtube · 含 YouTube | `178` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-youtube.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-youtube.txt) |
| **`geosite-netflix`** | Netflix 奈飞全球影音流媒体平台 | dat 分类 netflix · 含 Netflix | `24` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-netflix.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-netflix.txt) |
| **`geosite-disney`** | Disney+ 迪士尼流媒体播放服务 | dat 分类 disney · 含 Disney+ / Hulu | `224` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-disney.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-disney.txt) |
| **`geosite-spotify`** | Spotify 全球最大音乐流媒体服务 | dat 分类 spotify · 含 Spotify | `28` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-spotify.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-spotify.txt) |
| **`geosite-apple-tvplus`** | Apple TV+ 苹果原创影视流媒体 | dat 分类 apple-tvplus · 含 Apple TV+ | `8` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-tvplus.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-tvplus.txt) |
| **`geosite-hbo`** | HBO Max / HBO 全球影视服务 | dat 分类 hbo · 含 HBO | `65` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-hbo.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-hbo.txt) |
| **`geosite-hulu`** | Hulu 影视点播流媒体平台 | dat 分类 hulu · 含 Hulu | `48` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-hulu.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-hulu.txt) |
| **`geosite-primevideo`** | Amazon Prime Video 亚马逊影音 | dat 分类 primevideo · 含 Prime Video | `23` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-primevideo.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-primevideo.txt) |
| **`geosite-twitch`** | Twitch 全球游戏与互动直播平台 | dat 分类 twitch · 含 Twitch | `34` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-twitch.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-twitch.txt) |
| **`geosite-bahamut`** | 巴哈姆特动画疯 (台湾主流动漫平台) | dat 分类 bahamut · 含 巴哈姆特 | `5` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bahamut.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bahamut.txt) |
| **`geosite-abema`** | AbemaTV 日本网络电视流媒体 | dat 分类 abema · 含 Abema | `21` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-abema.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-abema.txt) |
| **`geosite-niconico`** | Niconico (N站) 日本弹幕视频网站 | dat 分类 niconico · 含 Niconico | `10` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-niconico.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-niconico.txt) |
| **`geosite-dmm`** | DMM.com 日本综合数字内容娱乐 | dat 分类 dmm · 含 DMM | `17` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-dmm.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-dmm.txt) |
| **`geosite-pixiv`** | Pixiv (P站) 日本插画二次元艺术社区 | dat 分类 pixiv · 含 Pixiv | `11` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-pixiv.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-pixiv.txt) |
| **`geosite-vimeo`** | Vimeo 高清原创视频创作分享平台 | dat 分类 vimeo · 含 Vimeo | `16` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-vimeo.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-vimeo.txt) |
| **`geosite-dailymotion`** | Dailymotion 国际视频共享服务 | dat 分类 dailymotion · 含 Dailymotion | `3` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-dailymotion.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-dailymotion.txt) |
| **`geosite-deezer`** | Deezer 高保真音乐流媒体服务 | dat 分类 deezer · 含 Deezer | `2` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-deezer.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-deezer.txt) |
| **`geosite-soundcloud`** | SoundCloud 原创音乐与音频分享 | dat 分类 soundcloud · 含 SoundCloud | `3` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-soundcloud.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-soundcloud.txt) |
| **`geosite-tidal`** | TIDAL HiFi 无损高品质音乐流媒体 | dat 分类 tidal · 含 TIDAL | `3` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-tidal.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-tidal.txt) |

<span id="gaming"></span>

### 🎮 游戏平台与联机服务 (Gaming)

| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-games`** | 全球热门游戏与联机加速合集 | dat 分类 category-games · 含 Steam / Epic Games / PlayStation / Xbox / Nintendo / EA 等 12 项 | `1,123` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-games.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-games.txt) |
| **`geosite-games-cn`** | 国内主流网络游戏与加速服务 | dat 分类 category-games-cn · 含 米哈游 | `264` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-games-cn.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-games-cn.txt) |
| **`geosite-games-!cn`** | 外服主机与端游联机加速合集 | dat 分类 category-games-!cn · 含 Steam / Epic Games / PlayStation / Xbox / Nintendo / EA 等 11 项 | `824` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-games-!cn.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-games-!cn.txt) |
| **`geosite-steam`** | Valve Steam 全球最大游戏平台 | dat 分类 steam · 含 Steam | `60` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-steam.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-steam.txt) |
| **`geosite-epicgames`** | Epic Games 游戏商城与虚幻联机 | dat 分类 epicgames · 含 Epic Games | `30` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-epicgames.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-epicgames.txt) |
| **`geosite-playstation`** | Sony PlayStation Network (PSN) | dat 分类 playstation · 含 PlayStation | `4` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-playstation.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-playstation.txt) |
| **`geosite-xbox`** | Microsoft Xbox Live 游戏与 GamePass | dat 分类 xbox · 含 Xbox | `45` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-xbox.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-xbox.txt) |
| **`geosite-nintendo`** | Nintendo 任天堂 Switch 联机与商城 | dat 分类 nintendo · 含 Nintendo | `124` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-nintendo.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-nintendo.txt) |
| **`geosite-ea`** | Electronic Arts (EA / Origin) 平台 | dat 分类 ea · 含 EA | `165` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ea.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ea.txt) |
| **`geosite-ubisoft`** | Ubisoft Connect 育碧游戏与联机 | dat 分类 ubisoft · 含 Ubisoft | `31` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ubisoft.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ubisoft.txt) |
| **`geosite-rockstar`** | Rockstar Games 摇滚之星 (GTA/RDR) | dat 分类 rockstar · 含 Rockstar | `7` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-rockstar.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-rockstar.txt) |
| **`geosite-blizzard`** | Blizzard 暴雪战网国际服联机服务 | dat 分类 blizzard · 含 Blizzard | `25` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-blizzard.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-blizzard.txt) |
| **`geosite-riotgames`** | Riot Games 拳头游戏 (LOL/Valorant) | dat 分类 riot · 含 Riot Games | `54` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-riotgames.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-riotgames.txt) |
| **`geosite-mihoyo`** | 米哈游 (MiHoYo) 原神/星铁境外分流 | dat 分类 mihoyo · 含 HoYoverse / 米哈游 | `25` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-mihoyo.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-mihoyo.txt) |
| **`geosite-hoyoverse`** | HoYoverse 米哈游海外发行平台 | dat 分类 hoyoverse · 含 HoYoverse | `9` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-hoyoverse.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-hoyoverse.txt) |

<span id="finance"></span>

### 💰 金融支付与加密货币 (Finance & Crypto)

| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-paypal`** | PayPal 全球主流跨境在线支付平台 | dat 分类 paypal · 含 PayPal | `245` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-paypal.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-paypal.txt) |
| **`geosite-stripe`** | Stripe 国际在线支付结算网关 | dat 分类 stripe · 含 Stripe | `8` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-stripe.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-stripe.txt) |
| **`geosite-wise`** | Wise (原 TransferWise) 跨境汇款 | dat 分类 wise · 含 Wise | `2` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-wise.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-wise.txt) |
| **`geosite-binance`** | 币安 (Binance) 全球最大加密货币交易 | dat 分类 binance · 含 Binance | `45` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-binance.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-binance.txt) |
| **`geosite-okx`** | 欧易 (OKX) 全球主流加密货币交易 | dat 分类 okx · 含 OKX | `10` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-okx.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-okx.txt) |

<span id="cloud"></span>

### 🌐 网络基建与协同办公 (Cloud & SaaS)

| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-cloudflare`** | Cloudflare 全球 CDN 与安全防护 | dat 分类 cloudflare · 含 Cloudflare | `76` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-cloudflare.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-cloudflare.txt) |
| **`geosite-fastly`** | Fastly 边缘云计算与高性能 CDN | dat 分类 fastly · 含 Fastly | `7` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-fastly.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-fastly.txt) |
| **`geosite-akamai`** | Akamai 全球核心 CDN 与边缘加速 | dat 分类 akamai · 含 Akamai | `81` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-akamai.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-akamai.txt) |
| **`geosite-vercel`** | Vercel 前端云开发与部署托管平台 | dat 分类 vercel · 含 Vercel | `27` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-vercel.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-vercel.txt) |
| **`geosite-netlify`** | Netlify 静态网站托管与 Serverless | dat 分类 netlify · 含 Netlify | `10` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-netlify.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-netlify.txt) |
| **`geosite-microsoft`** | Microsoft 微软全球产品与 Office 365 | dat 分类 microsoft · 含 Microsoft / OneDrive / GitHub / npm / Xbox | `749` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-microsoft.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-microsoft.txt) |
| **`geosite-microsoft-cdn`** | Microsoft 微软全球资源分发 CDN | 上游: ruleset.skk.moe | `51` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-microsoft-cdn.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-microsoft-cdn.txt) |
| **`geosite-onedrive`** | Microsoft OneDrive 云端存储服务 | dat 分类 onedrive · 含 OneDrive | `11` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-onedrive.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-onedrive.txt) |
| **`geosite-google`** | Google 全球核心产品生态与服务 | dat 分类 google · 含 YouTube / Google / Gemini / Google Drive | `1,073` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-google.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-google.txt) |
| **`geosite-apple-services`** | Apple 苹果全球核心云服务与 iCloud | 上游: ruleset.skk.moe | `16` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-services.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-services.txt) |
| **`geosite-apple-cdn`** | Apple 苹果官方资产与软件更新 CDN | 上游: ruleset.skk.moe | `159` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-cdn.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-cdn.txt) |
| **`geosite-notion`** | Notion 现代协同办公笔记与知识库 | dat 分类 notion · 含 Notion | `7` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-notion.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-notion.txt) |
| **`geosite-figma`** | Figma 云端协作界面设计平台 | dat 分类 figma · 含 Figma | `1` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-figma.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-figma.txt) |
| **`geosite-canva`** | Canva 可画全球在线平面设计平台 | dat 分类 canva · 含 Canva | `6` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-canva.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-canva.txt) |
| **`geosite-zoom`** | Zoom 全球主流企业在线视频会议 | dat 分类 zoom · 含 Zoom | `3` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-zoom.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-zoom.txt) |
| **`geosite-netdisk-!cn`** | 海外网盘与云存储服务 (境外代理分流) | dat 分类 category-netdisk-!cn · 含 OneDrive / Dropbox / MEGA / TeraBox / PikPak | `46` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-netdisk-!cn.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-netdisk-!cn.txt) |

<span id="china"></span>

### 🇨🇳 国内直连与核心大厂 (China & Ecosystem)

| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-cn`** | 🇨🇳 中国大陆域名双源合并合集 (精编+自有) | 配方合成: 天灵配方精编 cn (geolocation-cn + category-*@cn + category-*-cn + .cn) ∪ cn-additional-list ∪ SKK domestic | `32,630` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-cn.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-cn.txt) |
| **`geosite-!cn`** | 🌐 非中国大陆节点域名合集 (境外代理) | dat 分类 geolocation-!cn · 含 Discord / X/Twitter / Reddit / YouTube / Netflix / Disney+ 等 79 项 | `27,099` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-!cn.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-!cn.txt) |
| **`geosite-alibaba`** | 阿里巴巴系服务 (淘宝/天猫/阿里云/钉钉) | 上游: ruleset.skk.moe | `89` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-alibaba.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-alibaba.txt) |
| **`geosite-tencent`** | 腾讯系服务 (微信/QQ/腾讯云/腾讯视频) | 上游: ruleset.skk.moe | `50` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-tencent.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-tencent.txt) |
| **`geosite-bilibili`** | 哔哩哔哩 (B站) 视频与直播核心资产 | 上游: ruleset.skk.moe | `17` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bilibili.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bilibili.txt) |
| **`geosite-xiaomi`** | 小米系生态服务 (MIUI/米家/云服务) | 上游: ruleset.skk.moe | `18` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-xiaomi.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-xiaomi.txt) |
| **`geosite-bytedance`** | 字节跳动系服务 (抖音/头条/飞书) | 上游: ruleset.skk.moe | `69` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bytedance.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-bytedance.txt) |
| **`geosite-baidu`** | 百度系服务 (搜索/网盘/地图/文心一言) | 上游: ruleset.skk.moe | `30` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-baidu.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-baidu.txt) |
| **`geosite-qihoo360`** | 奇虎 360 安全防护与搜索服务 | 上游: ruleset.skk.moe | `21` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-qihoo360.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-qihoo360.txt) |
| **`geosite-domestic`** | 国内常用互联网服务合集 (SKK 维护) | 上游: ruleset.skk.moe | `866` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-domestic.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-domestic.txt) |
| **`geosite-apple-cn`** | Apple 苹果中国大陆本地化加速域名 | 上游: ruleset.skk.moe | `9` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-cn.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-apple-cn.txt) |
| **`geosite-download`** | 应用商店、软件源与大文件下载直连分流 | 上游: ruleset.skk.moe | `1,964` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-download.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-download.txt) |

<span id="security"></span>

### 🛡️ 安全防护与过滤拦截 (Security & Blocking)

| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-ad`** | 终极去广告 / 防追踪 (单集合保守版) | 上游: pmkol/easymosdns · AdGuard Hostlists (1/3/4) · Dan Pollock · isdumb/Pi-hole · Cats-Team/AdRules · AWAvenue · OISD Small · 本地 reject-addon | `224,448` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ad.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ad.txt) |
| **`geosite-ad-precise`** | 去广告黑名单精确版 (双集合黑名单B) | 配合 geosite-ad-allow 达成 0 误杀 | `218,897` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ad-precise.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ad-precise.txt) |
| **`geosite-ad-allow`** | 去广告防误杀白名单 (双集合白名单B) | 前置短路放行，彻底消除误杀断流 | `69` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ad-allow.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-ad-allow.txt) |
| **`geosite-gfw`** | GFW 封锁与污染域名列表 | dat 分类 gfw · 含 Discord / X/Twitter / Reddit / YouTube / Netflix / Google 等 49 项 | `4,367` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-gfw.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-gfw.txt) |
| **`geosite-reject-drop`** | 高危威胁、挖矿与垃圾流量直接丢弃 | 上游: ruleset.skk.moe · 本地 Custom_Reject-drop | `33` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-reject-drop.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-reject-drop.txt) |
| **`geosite-fakeip-filter`** | Fake-IP 排除名单 (正则压缩防漏网) | 上游: OpenClash · ShellCrash · DustinWin · ruleset.skk.moe · 本地 fake-ip-addon | `149` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-fakeip-filter.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-fakeip-filter.txt) |
| **`geosite-porn`** | 成人内容与不良网站拦截 (含本地补丁) | dat 分类 category-porn | `6,521` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-porn.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-porn.txt) |
| **`geosite-httpdns`** | 国内 APP 内置 HTTPDNS 解析防劫持 | dat 分类 category-httpdns-cn | `50` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-httpdns.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-httpdns.txt) |
| **`geosite-private`** | 局域网保留与私有/路由器后台域名 | dat 分类 private | `130` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-private.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-private.txt) |
| **`geosite-pcdn`** | PCDN 边缘上传业务拦截过滤 | 上游: wuiiled/PCDN-mihomo-list | `33` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-pcdn.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-pcdn.txt) |

<span id="custom"></span>

### 🛠️ 本地自定义与特征分流 (Custom Routing)

| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-custom-direct`** | 本地自定义直连域名与服务 | 用户本地规则: rules/Custom_Direct_DOMAIN.txt | `71` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-direct.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-direct.txt) |
| **`geosite-custom-dns`** | 本地自定义 DNS 解析与重定向 | 用户本地规则: rules/Custom_DNS_DOMAIN.txt | `18` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-dns.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-dns.txt) |
| **`geosite-custom-emby`** | 本地自定义 Emby / Jellyfin 媒体服 | 用户本地规则: rules/Custom_Emby.txt | `24` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-emby.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-emby.txt) |
| **`geosite-custom-proxy`** | 本地自定义强制代理规则 | 用户本地规则: rules/Custom_Proxy.txt | `4` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-proxy.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-proxy.txt) |
| **`geosite-custom-download`** | 本地自定义强制直连下载 | 用户本地规则: rules/Custom_Download.txt | `2` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-download.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-custom-download.txt) |
| **`geosite-location-dks`** | 抖音/快手/小红书 IP 归属地分流 | 用户本地规则: rules/LocationDKS.txt | `5` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-location-dks.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geosite/geosite-location-dks.txt) |

<span id="geoip"></span>

### 🌍 GeoIP 地址段网段集合 (IP Networks)

| 规则名称 | 描述 | 说明/包含 | 条数 | MRS (二进制) | TXT (规则源) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geoip-cn`** | 🇨🇳 中国大陆三大运营商 IPv4/IPv6 权威网段 | 上游: 1715173329/sing-geoip | `9,811` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-cn.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-cn.txt) |
| **`geoip-google`** | 🔍 Google 官方全网 IPv4/IPv6 网段 | 上游: 1715173329/sing-geoip | `8,403` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-google.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-google.txt) |
| **`geoip-telegram`** | ✈️ Telegram 电报官方数据中心网段 | 上游: 1715173329/sing-geoip | `12` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-telegram.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-telegram.txt) |
| **`geoip-twitter`** | 🐦 Twitter / X 官方数据中心网段 | 上游: 1715173329/sing-geoip | `19` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-twitter.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-twitter.txt) |
| **`geoip-facebook`** | 📘 Meta / Facebook 官方数据中心网段 | 上游: 1715173329/sing-geoip | `120` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-facebook.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-facebook.txt) |
| **`geoip-gfw`** | 🧱 GFW 投毒 IP 与伪造靶心网段拦截 | 上游: clowwindy/ChinaDNS · pmkol/easymosdns · 自有 IPv6 靶心表 | `796` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-gfw.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-gfw.txt) |
| **`geoip-private`** | 🔒 局域网私有保留 IP 网段 | 上游: 1715173329/sing-geoip | `17` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-private.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-private.txt) |
| **`geoip-stream`** | 📻 知名流媒体服务官方 IP 网段 | 上游: ruleset.skk.moe | `19` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-stream.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-stream.txt) |
| **`geoip-apple`** | 🍏 Apple 苹果服务官方 IP 网段 | 上游: ruleset.skk.moe | `10` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-apple.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-apple.txt) |
| **`geoip-custom-direct`** | 📌 本地自定义直连 IP 地址网段 | 用户本地规则: rules/Custom_Direct_IP.txt | `4` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-custom-direct.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-custom-direct.txt) |
| **`geoip-custom-dns`** | 📌 本地自定义 DNS 解析 IP 地址 | 用户本地规则: rules/Custom_DNS_IP.txt | `34` | [📥 MRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-custom-dns.mrs) | [📄 TXT](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/mihomo/rules/geoip/geoip-custom-dns.txt) |

---

<div align="center">

[🏠 返回主仓库](https://github.com/wuiiled/Wuiiled_Setup) · [⭐ Star 支持](https://github.com/wuiiled/Wuiiled_Setup)

</div>
