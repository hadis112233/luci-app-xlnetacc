# luci-app-xlnetacc
适用于 OpenWRT/LEDE 纯Shell实现的迅雷快鸟客户端

依赖（安装包自动安装）：openssl-util、ca-bundle、tesseract（本地 OCR）、imagemagick（验证码图片去噪预处理）。HTTP 客户端优先使用 `wget-ssl`，精简固件中会自动回退到系统 `wget`。


更新到支持快鸟新协议 300

详情见恩山论坛介绍帖 [依然是改良作品，这次的目标是 -- 迅雷快鸟](http://www.right.com.cn/forum/thread-267641-1-1.html)

# Fix
* 增加验证码获取，解决 "为了您的帐号安全，请输入图形验证码[6]" 问题，不建议开启帐号重新登录
* 适配高版本 OpenWRT
* 支持配置 ChatGPT 验证码识别（默认 Agnes（agnes-2.5-flash），未配置 API Key 时使用手动输入）
* 支持本地 OCR 识别：安装包会自动依赖 tesseract；配置 API Key 时优先使用 AI，识别失败自动回退本地 OCR/手动输入

# 验证码识别配置（免费方案）

快鸟登录遇到 "为了您的帐号安全，请输入图形验证码[6]" 时，插件会按以下顺序自动识别：

**AI 服务（配置了 API Key）-> 本地 tesseract OCR -> 手动输入**

识别前会自动对验证码图片做去噪预处理（放大 + 灰度 + 阈值去除干扰线，依赖 ImageMagick，安装包已自动带上），能明显提升识别率。

自动识别最多提交 5 次；无论是“未识别出字符”还是“识别结果被服务器拒绝”都会计入上限，之后自动切换为手动输入，避免连续错误提交。

使用 Gemini 2.5 Flash 时，插件会禁用模型思考并预留 128 个输出 token，避免模型在推理阶段耗尽原本仅 30 token 的验证码输出额度。

> 登录和 AI 请求会校验证书。迅雷现有的部分历史提速接口仅提供 HTTP，这是服务端协议限制；请避免在不可信网络中使用，直到迅雷提供 HTTPS 接口。

## 方案一：OpenRouter 免费视觉模型（推荐）

OpenRouter 是聚合平台，注册免费，可用它上面的免费视觉模型。在 [openrouter.ai](https://openrouter.ai) 注册后进入 [API Keys](https://openrouter.ai/settings/keys) 创建 Key，然后在 LuCI 页面填写：

- Base URL：`https://openrouter.ai/api/v1`
- Model：`google/gemma-4-31b-it:free`（当前在架的免费视觉模型，也可用 `google/gemma-4-26b-a4b-it:free`、`nvidia/nemotron-nano-12b-v2-vl:free`）
- API Key：你的 OpenRouter Key

> 注意：OpenRouter 免费模型会不定期上下架，若提示模型不存在，可在 [模型列表](https://openrouter.ai/models?q=:free) 里筛选支持 Vision 的 `:free` 模型替换。

## 方案二：Google Gemini 官方免费额度

Google AI Studio 提供免费 Key（每天约 1500 次请求，视觉能力强）。在 [aistudio.google.com](https://aistudio.google.com/apikey) 免费创建 Key 后填写：

- Base URL：`https://generativelanguage.googleapis.com/v1beta/openai`
- Model：`gemini-2.5-flash`
- API Key：你的 Gemini Key

## 方案三：通义千问 VL（阿里云百炼，国内直连）

新用户有免费额度，国内网络直连无需代理。在 [阿里云百炼](https://bailian.console.aliyun.com/) 开通并创建 API Key 后填写：

- Base URL：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- Model：`qwen-vl-plus`（或 `qwen-vl-max`）
- API Key：你的百炼 API Key

## 方案四：Agnes（默认）

- Base URL：`https://apihub.agnes-ai.com/v1`
- Model：`agnes-2.5-flash`

> 实测该免费模型的看图能力较弱，对快鸟验证码识别率不高，建议优先使用上面几个方案。

## 手动输入模式

不填 API Key（且本地未装 tesseract 时）自动进入手动模式：浏览器打开
`http://<路由器IP>/luci-static/resources/xlnetacc_verify.jpg` 查看验证码，
在 180 秒内执行 `echo 'xxxx' > /tmp/xlnetacc_verify_code` 即可。

排障看日志：`cat /var/log/xlnetacc.log`
