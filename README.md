<div align="center">

# 📦 Sing-box 规则订阅

![规则总数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E6%80%BB%E6%95%B0-329,518-blue)
![规则集数](https://img.shields.io/badge/%E8%A7%84%E5%88%99%E9%9B%86%E6%95%B0-114-success)
![格式](https://img.shields.io/badge/%E6%A0%BC%E5%BC%8F-.srs%20%2F%20.json-informational)
![0--Diff对齐](https://img.shields.io/badge/0--Diff-%E7%99%BE%E5%88%86%E7%99%BE%E5%AF%B9%E9%BD%90-brightgreen)

<i>由 <a href="https://github.com/wuiiled/Wuiiled_Setup">Wuiiled_Setup</a> 规则自动化引擎实时构建分发</i><br>
<sub>🕐 最后更新：2026-09-27 00:00:48 (Asia/Shanghai)</sub>

</div>

---

## 💡 如何使用

在下方分类表格中 **右键点击** 对应链接，选择 **复制链接地址**，填入客户端订阅即可。

<details>
<summary><b>🛠️ Sing-box 配置示例</b>（点击展开）</summary>

在 `config.json` 的 `route.rule_set` 中配置远程规则集。将下方 `{tag}` 替换为表格中的规则名（推荐优先使用高效的二进制 `.srs`）：

```json
{
  "tag": "{tag}",
  "type": "remote",
  "format": "binary",
  "url": "https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/{tag}.srs",
  "download_detour": "direct"
}
```

</details>

## 📑 规则分类快速导航

[🤖](#ai) · [💬](#social) · [🎬](#media) · [🎮](#gaming) · [💰](#finance) · [🌐](#cloud) · [🇨🇳](#china) · [🛡️](#security) · [🛠️](#custom) · [🌍](#geoip)

---

<span id="ai"></span>

### 🤖 人工智能与开发 (AI & Dev)

| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | JSON (源码) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-ai`** | 全球主流 AI 服务合集 (自研列表 ∪ dat 分类) | 上游: MetaCubeX/meta-rules-dat · ruleset.skk.moe · DustinWin/ruleset_geodata · dat 分类 category-ai-!cn | `196` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-ai.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-ai.json) |
| **`geosite-openai`** | OpenAI / ChatGPT 官方服务与 API | dat 分类 openai · 含 OpenAI | `23` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-openai.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-openai.json) |
| **`geosite-anthropic`** | Anthropic Claude 官方服务与 API | dat 分类 anthropic · 含 Anthropic | `8` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-anthropic.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-anthropic.json) |
| **`geosite-gemini`** | Google Gemini / Bard 人工智能服务 | dat 分类 google-gemini · 含 Gemini | `43` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-gemini.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-gemini.json) |
| **`geosite-github`** | GitHub 代码托管平台与开发者资产 | dat 分类 github · 含 GitHub / npm | `64` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-github.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-github.json) |
| **`geosite-gitlab`** | GitLab 代码托管与 DevOps 云服务 | dat 分类 gitlab · 含 GitLab | `5` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-gitlab.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-gitlab.json) |
| **`geosite-docker`** | Docker Hub 容器镜像与注册表 | dat 分类 docker · 含 Docker | `6` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-docker.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-docker.json) |
| **`geosite-stackoverflow`** | Stack Overflow 与开发者技术社区 | dat 分类 stackexchange · 含 StackExchange | `25` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-stackoverflow.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-stackoverflow.json) |
| **`geosite-npm`** | Node.js NPM 官方包管理器软件源 | dat 分类 npmjs · 含 npm | `3` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-npm.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-npm.json) |

<span id="social"></span>

### 💬 社交与即时通讯 (Social & IM)

| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | JSON (源码) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-communication`** | 全球即时通讯与在线会议聚合 | dat 分类 category-communication · 含 Discord / Telegram / WhatsApp / Signal / LINE | `151` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-communication.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-communication.json) |
| **`geosite-social-media`** | 全球社交网络与媒体平台聚合 | dat 分类 category-social-media-!cn · 含 X/Twitter / Instagram / Bluesky / Facebook/Meta / Threads | `625` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-social-media.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-social-media.json) |
| **`geosite-telegram`** | Telegram 电报全系官方通讯服务 | dat 分类 telegram · 含 Telegram | `21` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-telegram.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-telegram.json) |
| **`geosite-discord`** | Discord 语音与社群即时通讯平台 | dat 分类 discord · 含 Discord | `28` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-discord.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-discord.json) |
| **`geosite-whatsapp`** | WhatsApp 即时通讯与端到端加密 | dat 分类 whatsapp · 含 WhatsApp | `13` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-whatsapp.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-whatsapp.json) |
| **`geosite-signal`** | Signal 隐私加密即时通讯服务 | dat 分类 signal · 含 Signal | `8` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-signal.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-signal.json) |
| **`geosite-line`** | LINE 亚洲流行即时通讯与生活服务 | dat 分类 line · 含 LINE | `20` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-line.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-line.json) |
| **`geosite-x`** | X (原 Twitter) 官方社交媒体平台 | dat 分类 x · 含 X/Twitter | `27` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-x.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-x.json) |
| **`geosite-instagram`** | Instagram 社交图像与短视频平台 | dat 分类 instagram · 含 Instagram | `74` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-instagram.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-instagram.json) |
| **`geosite-threads`** | Threads 文本社交互动媒体平台 | dat 分类 threads · 含 Threads | `2` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-threads.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-threads.json) |
| **`geosite-reddit`** | Reddit 全球兴趣与新闻社区 | dat 分类 reddit · 含 Reddit | `12` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-reddit.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-reddit.json) |
| **`geosite-bluesky`** | Bluesky 去中心化社交网络平台 | dat 分类 bluesky · 含 Bluesky | `3` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-bluesky.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-bluesky.json) |
| **`geosite-tiktok`** | TikTok 国际版短视频平台 | dat 分类 tiktok · 含 TikTok | `37` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-tiktok.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-tiktok.json) |

<span id="media"></span>

### 🎬 影音流媒体与娱乐 (Media & Streaming)

| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | JSON (源码) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-media`** | 国际新闻媒体与区域电视台聚合 (新闻社/报媒/区域电视) | dat 分类 category-media · 含 半岛电视台 / 今日俄罗斯 / 澳大利亚九号台 / 法新社 / 台湾4GTV / 6park | `1,580` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-media.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-media.json) |
| **`geosite-entertainment`** | 全球影音娱乐与流媒体聚合 | dat 分类 category-entertainment · 含 YouTube / Netflix / Disney+ / HBO / TikTok / Spotify 等 30 项 | `2,137` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-entertainment.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-entertainment.json) |
| **`geosite-youtube`** | YouTube 视频流媒体与 YouTube Music | dat 分类 youtube · 含 YouTube | `178` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-youtube.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-youtube.json) |
| **`geosite-netflix`** | Netflix 奈飞全球影音流媒体平台 | dat 分类 netflix · 含 Netflix | `28` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-netflix.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-netflix.json) |
| **`geosite-disney`** | Disney+ 迪士尼流媒体播放服务 | dat 分类 disney · 含 Disney+ / Hulu | `225` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-disney.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-disney.json) |
| **`geosite-spotify`** | Spotify 全球最大音乐流媒体服务 | dat 分类 spotify · 含 Spotify | `28` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-spotify.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-spotify.json) |
| **`geosite-apple-tvplus`** | Apple TV+ 苹果原创影视流媒体 | dat 分类 apple-tvplus · 含 Apple TV+ | `8` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-apple-tvplus.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-apple-tvplus.json) |
| **`geosite-hbo`** | HBO Max / HBO 全球影视服务 | dat 分类 hbo · 含 HBO | `65` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-hbo.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-hbo.json) |
| **`geosite-hulu`** | Hulu 影视点播流媒体平台 | dat 分类 hulu · 含 Hulu | `48` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-hulu.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-hulu.json) |
| **`geosite-primevideo`** | Amazon Prime Video 亚马逊影音 | dat 分类 primevideo · 含 Prime Video | `23` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-primevideo.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-primevideo.json) |
| **`geosite-twitch`** | Twitch 全球游戏与互动直播平台 | dat 分类 twitch · 含 Twitch | `34` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-twitch.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-twitch.json) |
| **`geosite-bahamut`** | 巴哈姆特动画疯 (台湾主流动漫平台) | dat 分类 bahamut · 含 巴哈姆特 | `5` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-bahamut.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-bahamut.json) |
| **`geosite-abema`** | AbemaTV 日本网络电视流媒体 | dat 分类 abema · 含 Abema | `21` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-abema.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-abema.json) |
| **`geosite-niconico`** | Niconico (N站) 日本弹幕视频网站 | dat 分类 niconico · 含 Niconico | `10` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-niconico.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-niconico.json) |
| **`geosite-dmm`** | DMM.com 日本综合数字内容娱乐 | dat 分类 dmm · 含 DMM | `17` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-dmm.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-dmm.json) |
| **`geosite-pixiv`** | Pixiv (P站) 日本插画二次元艺术社区 | dat 分类 pixiv · 含 Pixiv | `11` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-pixiv.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-pixiv.json) |
| **`geosite-vimeo`** | Vimeo 高清原创视频创作分享平台 | dat 分类 vimeo · 含 Vimeo | `17` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-vimeo.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-vimeo.json) |
| **`geosite-dailymotion`** | Dailymotion 国际视频共享服务 | dat 分类 dailymotion · 含 Dailymotion | `3` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-dailymotion.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-dailymotion.json) |
| **`geosite-deezer`** | Deezer 高保真音乐流媒体服务 | dat 分类 deezer · 含 Deezer | `2` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-deezer.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-deezer.json) |
| **`geosite-soundcloud`** | SoundCloud 原创音乐与音频分享 | dat 分类 soundcloud · 含 SoundCloud | `3` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-soundcloud.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-soundcloud.json) |
| **`geosite-tidal`** | TIDAL HiFi 无损高品质音乐流媒体 | dat 分类 tidal · 含 TIDAL | `3` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-tidal.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-tidal.json) |

<span id="gaming"></span>

### 🎮 游戏平台与联机服务 (Gaming)

| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | JSON (源码) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-games`** | 全球热门游戏与联机加速合集 | dat 分类 category-games · 含 Steam / Epic Games / PlayStation / Xbox / Nintendo / EA 等 12 项 | `1,127` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-games.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-games.json) |
| **`geosite-games-cn`** | 国内主流网络游戏与加速服务 | dat 分类 category-games-cn · 含 米哈游 | `265` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-games-cn.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-games-cn.json) |
| **`geosite-games-!cn`** | 外服主机与端游联机加速合集 | dat 分类 category-games-!cn · 含 Steam / Epic Games / PlayStation / Xbox / Nintendo / EA 等 11 项 | `825` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-games-!cn.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-games-!cn.json) |
| **`geosite-steam`** | Valve Steam 全球最大游戏平台 | dat 分类 steam · 含 Steam | `60` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-steam.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-steam.json) |
| **`geosite-epicgames`** | Epic Games 游戏商城与虚幻联机 | dat 分类 epicgames · 含 Epic Games | `33` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-epicgames.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-epicgames.json) |
| **`geosite-playstation`** | Sony PlayStation Network (PSN) | dat 分类 playstation · 含 PlayStation | `4` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-playstation.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-playstation.json) |
| **`geosite-xbox`** | Microsoft Xbox Live 游戏与 GamePass | dat 分类 xbox · 含 Xbox | `45` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-xbox.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-xbox.json) |
| **`geosite-nintendo`** | Nintendo 任天堂 Switch 联机与商城 | dat 分类 nintendo · 含 Nintendo | `124` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-nintendo.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-nintendo.json) |
| **`geosite-ea`** | Electronic Arts (EA / Origin) 平台 | dat 分类 ea · 含 EA | `165` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-ea.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-ea.json) |
| **`geosite-ubisoft`** | Ubisoft Connect 育碧游戏与联机 | dat 分类 ubisoft · 含 Ubisoft | `31` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-ubisoft.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-ubisoft.json) |
| **`geosite-rockstar`** | Rockstar Games 摇滚之星 (GTA/RDR) | dat 分类 rockstar · 含 Rockstar | `7` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-rockstar.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-rockstar.json) |
| **`geosite-blizzard`** | Blizzard 暴雪战网国际服联机服务 | dat 分类 blizzard · 含 Blizzard | `25` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-blizzard.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-blizzard.json) |
| **`geosite-riotgames`** | Riot Games 拳头游戏 (LOL/Valorant) | dat 分类 riot · 含 Riot Games | `54` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-riotgames.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-riotgames.json) |
| **`geosite-mihoyo`** | 米哈游 (MiHoYo) 原神/星铁境外分流 | dat 分类 mihoyo · 含 HoYoverse / 米哈游 | `26` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-mihoyo.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-mihoyo.json) |
| **`geosite-hoyoverse`** | HoYoverse 米哈游海外发行平台 | dat 分类 hoyoverse · 含 HoYoverse | `9` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-hoyoverse.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-hoyoverse.json) |

<span id="finance"></span>

### 💰 金融支付与加密货币 (Finance & Crypto)

| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | JSON (源码) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-paypal`** | PayPal 全球主流跨境在线支付平台 | dat 分类 paypal · 含 PayPal | `245` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-paypal.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-paypal.json) |
| **`geosite-stripe`** | Stripe 国际在线支付结算网关 | dat 分类 stripe · 含 Stripe | `8` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-stripe.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-stripe.json) |
| **`geosite-wise`** | Wise (原 TransferWise) 跨境汇款 | dat 分类 wise · 含 Wise | `2` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-wise.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-wise.json) |
| **`geosite-binance`** | 币安 (Binance) 全球最大加密货币交易 | dat 分类 binance · 含 Binance | `45` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-binance.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-binance.json) |
| **`geosite-okx`** | 欧易 (OKX) 全球主流加密货币交易 | dat 分类 okx · 含 OKX | `10` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-okx.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-okx.json) |

<span id="cloud"></span>

### 🌐 网络基建与协同办公 (Cloud & SaaS)

| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | JSON (源码) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-cloudflare`** | Cloudflare 全球 CDN 与安全防护 | dat 分类 cloudflare · 含 Cloudflare | `76` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-cloudflare.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-cloudflare.json) |
| **`geosite-fastly`** | Fastly 边缘云计算与高性能 CDN | dat 分类 fastly · 含 Fastly | `7` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-fastly.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-fastly.json) |
| **`geosite-akamai`** | Akamai 全球核心 CDN 与边缘加速 | dat 分类 akamai · 含 Akamai | `81` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-akamai.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-akamai.json) |
| **`geosite-vercel`** | Vercel 前端云开发与部署托管平台 | dat 分类 vercel · 含 Vercel | `27` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-vercel.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-vercel.json) |
| **`geosite-netlify`** | Netlify 静态网站托管与 Serverless | dat 分类 netlify · 含 Netlify | `10` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-netlify.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-netlify.json) |
| **`geosite-microsoft`** | Microsoft 微软全球产品与 Office 365 | dat 分类 microsoft · 含 Microsoft / OneDrive / GitHub / npm / Xbox | `749` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-microsoft.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-microsoft.json) |
| **`geosite-microsoft-cdn`** | Microsoft 微软全球资源分发 CDN | 上游: ruleset.skk.moe | `51` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-microsoft-cdn.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-microsoft-cdn.json) |
| **`geosite-onedrive`** | Microsoft OneDrive 云端存储服务 | dat 分类 onedrive · 含 OneDrive | `11` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-onedrive.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-onedrive.json) |
| **`geosite-google`** | Google 全球核心产品生态与服务 | dat 分类 google · 含 YouTube / Google / Gemini / Google Drive | `1,075` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-google.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-google.json) |
| **`geosite-apple-services`** | Apple 苹果全球核心云服务与 iCloud | 上游: ruleset.skk.moe | `16` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-apple-services.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-apple-services.json) |
| **`geosite-apple-cdn`** | Apple 苹果官方资产与软件更新 CDN | 上游: ruleset.skk.moe | `159` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-apple-cdn.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-apple-cdn.json) |
| **`geosite-notion`** | Notion 现代协同办公笔记与知识库 | dat 分类 notion · 含 Notion | `7` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-notion.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-notion.json) |
| **`geosite-figma`** | Figma 云端协作界面设计平台 | dat 分类 figma · 含 Figma | `1` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-figma.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-figma.json) |
| **`geosite-canva`** | Canva 可画全球在线平面设计平台 | dat 分类 canva · 含 Canva | `6` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-canva.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-canva.json) |
| **`geosite-zoom`** | Zoom 全球主流企业在线视频会议 | dat 分类 zoom · 含 Zoom | `3` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-zoom.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-zoom.json) |
| **`geosite-netdisk-!cn`** | 海外网盘与云存储服务 (境外代理分流) | dat 分类 category-netdisk-!cn · 含 OneDrive / Dropbox / MEGA / TeraBox / PikPak | `46` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-netdisk-!cn.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-netdisk-!cn.json) |

<span id="china"></span>

### 🇨🇳 国内直连与核心大厂 (China & Ecosystem)

| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | JSON (源码) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-cn`** | 🇨🇳 中国大陆域名双源合并合集 (精编+自有) | 配方合成: 天灵配方精编 cn (geolocation-cn + category-*@cn + category-*-cn + .cn) ∪ cn-additional-list ∪ SKK domestic | `32,638` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-cn.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-cn.json) |
| **`geosite-!cn`** | 🌐 非中国大陆节点域名合集 (境外代理) | dat 分类 geolocation-!cn · 含 Discord / X/Twitter / Reddit / YouTube / Netflix / Disney+ 等 79 项 | `27,250` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-!cn.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-!cn.json) |
| **`geosite-alibaba`** | 阿里巴巴系服务 (淘宝/天猫/阿里云/钉钉) | 上游: ruleset.skk.moe | `89` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-alibaba.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-alibaba.json) |
| **`geosite-tencent`** | 腾讯系服务 (微信/QQ/腾讯云/腾讯视频) | 上游: ruleset.skk.moe | `50` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-tencent.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-tencent.json) |
| **`geosite-bilibili`** | 哔哩哔哩 (B站) 视频与直播核心资产 | 上游: ruleset.skk.moe | `17` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-bilibili.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-bilibili.json) |
| **`geosite-xiaomi`** | 小米系生态服务 (MIUI/米家/云服务) | 上游: ruleset.skk.moe | `18` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-xiaomi.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-xiaomi.json) |
| **`geosite-bytedance`** | 字节跳动系服务 (抖音/头条/飞书) | 上游: ruleset.skk.moe | `69` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-bytedance.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-bytedance.json) |
| **`geosite-baidu`** | 百度系服务 (搜索/网盘/地图/文心一言) | 上游: ruleset.skk.moe | `30` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-baidu.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-baidu.json) |
| **`geosite-qihoo360`** | 奇虎 360 安全防护与搜索服务 | 上游: ruleset.skk.moe | `21` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-qihoo360.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-qihoo360.json) |
| **`geosite-domestic`** | 国内常用互联网服务合集 (SKK 维护) | 上游: ruleset.skk.moe | `866` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-domestic.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-domestic.json) |
| **`geosite-apple-cn`** | Apple 苹果中国大陆本地化加速域名 | 上游: ruleset.skk.moe | `9` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-apple-cn.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-apple-cn.json) |
| **`geosite-download`** | 应用商店、软件源与大文件下载直连分流 | 上游: ruleset.skk.moe | `1,964` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-download.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-download.json) |

<span id="security"></span>

### 🛡️ 安全防护与过滤拦截 (Security & Blocking)

| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | JSON (源码) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-ad`** | 终极去广告 / 防追踪 (单集合保守版) | 上游: pmkol/easymosdns · AdGuard Hostlists (1/3/4) · Dan Pollock · isdumb/Pi-hole · Cats-Team/AdRules · AWAvenue · OISD Small · 本地 reject-addon | `224,448` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-ad.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-ad.json) |
| **`geosite-gfw`** | GFW 封锁与污染域名列表 | dat 分类 gfw · 含 Discord / X/Twitter / Reddit / YouTube / Netflix / Google 等 49 项 | `4,367` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-gfw.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-gfw.json) |
| **`geosite-reject-drop`** | 高危威胁、挖矿与垃圾流量直接丢弃 | 上游: ruleset.skk.moe · 本地 Custom_Reject-drop | `33` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-reject-drop.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-reject-drop.json) |
| **`geosite-fakeip-filter`** | Fake-IP 排除名单 (正则压缩防漏网) | 上游: OpenClash · ShellCrash · DustinWin · ruleset.skk.moe · 本地 fake-ip-addon | `130` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-fakeip-filter.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-fakeip-filter.json) |
| **`geosite-porn`** | 成人内容与不良网站拦截 (含本地补丁) | dat 分类 category-porn | `6,661` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-porn.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-porn.json) |
| **`geosite-httpdns`** | 国内 APP 内置 HTTPDNS 解析防劫持 | dat 分类 category-httpdns-cn | `50` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-httpdns.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-httpdns.json) |
| **`geosite-private`** | 局域网保留与私有/路由器后台域名 | dat 分类 private | `131` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-private.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-private.json) |
| **`geosite-pcdn`** | PCDN 边缘上传业务拦截过滤 | 上游: wuiiled/PCDN-mihomo-list | `33` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-pcdn.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-pcdn.json) |

<span id="custom"></span>

### 🛠️ 本地自定义与特征分流 (Custom Routing)

| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | JSON (源码) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geosite-custom-direct`** | 本地自定义直连域名与服务 | 用户本地规则: rules/Custom_Direct_DOMAIN.txt | `75` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-custom-direct.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-custom-direct.json) |
| **`geosite-custom-dns`** | 本地自定义 DNS 解析与重定向 | 用户本地规则: rules/Custom_DNS_DOMAIN.txt | `52` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-custom-dns.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-custom-dns.json) |
| **`geosite-custom-emby`** | 本地自定义 Emby / Jellyfin 媒体服 | 用户本地规则: rules/Custom_Emby.txt | `24` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-custom-emby.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-custom-emby.json) |
| **`geosite-custom-proxy`** | 本地自定义强制代理规则 | 用户本地规则: rules/Custom_Proxy.txt | `4` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-custom-proxy.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-custom-proxy.json) |
| **`geosite-custom-download`** | 本地自定义强制直连下载 | 用户本地规则: rules/Custom_Download.txt | `2` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-custom-download.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-custom-download.json) |
| **`geosite-location-dks`** | 抖音/快手/小红书 IP 归属地分流 | 用户本地规则: rules/LocationDKS.txt | `5` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-location-dks.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geosite/geosite-location-dks.json) |

<span id="geoip"></span>

### 🌍 GeoIP 地址段网段集合 (IP Networks)

| 规则名称 | 描述 | 说明/包含 | 条数 | SRS (二进制) | JSON (源码) |
| :--- | :--- | :--- | ---: | :---: | :---: |
| **`geoip-cn`** | 🇨🇳 中国大陆三大运营商 IPv4/IPv6 权威网段 | 上游: 1715173329/sing-geoip | `9,811` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-cn.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-cn.json) |
| **`geoip-google`** | 🔍 Google 官方全网 IPv4/IPv6 网段 | 上游: 1715173329/sing-geoip | `8,403` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-google.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-google.json) |
| **`geoip-telegram`** | ✈️ Telegram 电报官方数据中心网段 | 上游: 1715173329/sing-geoip | `12` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-telegram.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-telegram.json) |
| **`geoip-twitter`** | 🐦 Twitter / X 官方数据中心网段 | 上游: 1715173329/sing-geoip | `19` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-twitter.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-twitter.json) |
| **`geoip-facebook`** | 📘 Meta / Facebook 官方数据中心网段 | 上游: 1715173329/sing-geoip | `120` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-facebook.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-facebook.json) |
| **`geoip-gfw`** | 🧱 GFW 投毒 IP 与伪造靶心网段拦截 | 上游: clowwindy/ChinaDNS · pmkol/easymosdns · 自有 IPv6 靶心表 | `796` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-gfw.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-gfw.json) |
| **`geoip-private`** | 🔒 局域网私有保留 IP 网段 | 上游: 1715173329/sing-geoip | `17` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-private.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-private.json) |
| **`geoip-stream`** | 📻 知名流媒体服务官方 IP 网段 | 上游: ruleset.skk.moe | `19` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-stream.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-stream.json) |
| **`geoip-apple`** | 🍏 Apple 苹果服务官方 IP 网段 | 上游: ruleset.skk.moe | `10` | [📥 SRS](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-apple.srs) | [📄 JSON](https://raw.githubusercontent.com/wuiiled/Wuiiled_Setup/singbox/rules/geoip/geoip-apple.json) |

---

<div align="center">

[🏠 返回主仓库](https://github.com/wuiiled/Wuiiled_Setup) · [⭐ Star 支持](https://github.com/wuiiled/Wuiiled_Setup)

</div>
