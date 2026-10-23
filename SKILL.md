---
name: weimeta-seedance
display_name: WEIMETA Seedance｜Agent 视频生成
display_name_en: WEIMETA Seedance Video Generation
description: 通过唯元智创 WEIMETA API 平台调用 Seedance 进行 AI 视频生成、图生视频、参考素材生成、视频编辑、视频延长、异步任务查询与成片下载。用户提到 Seedance、即梦视频、视频生成、文生视频、图生视频、AI 视频广告、短剧、漫剧、唯元智创视频 API 时使用本 Skill。适用具备 Shell 和 HTTPS 能力的 Codex、TRAE、WorkBuddy、ZCode 等 Agent。
description_zh: 使用唯元智创统一 API 生成、查询并下载 Seedance AI 视频，支持文生视频与多模态视频任务。
description_en: Generate, track and download Seedance videos through the WEIMETA API from compatible coding agents.
version: 0.3.1
author: 唯元智创
---

# WEIMETA Seedance — 唯元智创 AI 视频生成 Skill

本 Skill 使用 Python 3.9+ 标准库提供跨 Agent CLI，Agent 理解自然语言、选择参数并执行本地脚本；真实生成由唯元智创 API 平台处理。需要用户自己配置 WEIMETA_API_KEY 与网络权限。Seedance 2.5 文生视频完整 API 调用与 MP4 下载已通过真实测试；图生、参考、编辑和延长仅通过参数构造测试，线上能力仍需验证。

## 强制规则

1. 优先运行 doctor 和 generate --dry-run，二者均不提交任何计费任务。
2. 真正创建视频前必须取得用户对模型、时长、比例、素材、可能扣费的确认，并显式带 --confirm-charge。
3. 严禁输出或写入真实 API Key、Authorization、未授权素材、带签名的临时 URL 到公开文件。
4. POST 超时不要自动重新提交，可能已经计费；先查管理后台及已返回 task ID。
5. 未经过真实调用，不得宣称视频生成、自动素材上传、动态计价或四端应用商店上架成功。
6. 第三方素材应具备版权及商业使用授权，最终宣传文案不得虚构效果或合规认证。

## 初次配置

用户可以在自己的终端执行 python3 scripts/weimeta_video.py configure，在隐藏输入提示中输入 Key，脚本将 Key 保存为仅当前用户可读的 ~/.config/weimeta/seedance-credentials.json（权限 0600），所有 Agent 共用。也可设置 WEIMETA_API_KEY 环境变量，优先于本地配置文件。可选环境变量 WEIMETA_VIDEO_BASE_URL，默认 https://api.weimeta.cn/volcengine/v1；WEIMETA_SEEDANCE_MODEL，默认 doubao-seedance-2-5-260628。默认配置仍需以唯元智创平台当前实际支持为准。

先定位这个 Skill 的目录，使用 scripts/weimeta_video.py 的绝对路径调用。不要假设 SKILL_PATH 变量存在。

## 离线检查（不扣模型生成费用）

python3 scripts/weimeta_video.py doctor

python3 scripts/weimeta_video.py models

python3 scripts/weimeta_video.py generate --mode t2v --prompt '深蓝色科技产品宣传视频，推镜头，电影感灯光' --ratio 9:16 --duration 8 --resolution 720p --dry-run

dry-run 输出 payload，pricing_verified=false 不代表已通过鉴权或真实计费验证。

## 实际生成（需用户明确同意费用）

python3 scripts/weimeta_video.py generate --mode t2v --prompt '深蓝色科技产品宣传视频，推镜头，电影感灯光' --ratio 9:16 --duration 8 --resolution 720p --confirm-charge

任务成功创建后读取 task_id，使用以下命令等待并下载：

python3 scripts/weimeta_video.py task --task-id '任务ID' --wait --download

## 模式

t2v：文本 prompt；i2v：--first-frame 与可选 --last-frame；r2v：一个或多个 --image、--video、--audio；edit：--video 指向已有视频；extend：--video 指向已有视频。多个相同类型素材可重复传参。

图片/音频接受本地小于等于10MB的允许格式、https 或 asset://；本地视频尚未支持自动上传，应使用已授权的 HTTPS 或 asset:// 引用。本版编辑和延长只面向 Seedance 2.5，具体参数约束以网关真实响应为准。

默认下载目录：~/Downloads/WEIMETA。输出应报告模型、参数、任务 ID、状态、结果目录、失败原因。严禁凭离线 dry-run 断言成片完成。

更多内容见 README.md、references/API.md、references/PRICING.md、references/INSTALL.md。模型价目表包含不同分辨率及是否含视频输入的完整阶梯，属于参考快照；任何实际收费都需按账户费率确认。
