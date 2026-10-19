# 多 Agent 安装与验证说明（V0.3 RC1）

标准文件夹结构：weimeta-seedance/SKILL.md、scripts/weimeta_video.py、references/ 等；用户 API Key 必须独立保管，绝不可复制进 Skill ZIP。

## 统一安装步骤

从发行包解压出 weimeta-seedance 文件夹，将其复制到对应 Agent 的 Skills 目录，重新打开 Agent 会话并验证 Skill 能否被主动选择。Mac 及 Linux 支持 Python 3.9+ 标准库运行。Windows 可优先通过 WEIMETA_API_KEY 环境变量配置凭据，仍需按客户端实际沙盒权限联调；本机的交互式 configure 凭据权限机制按 macOS/Linux 设计。

| Agent | 推荐或本机已验证的目录 | 当前验收 |
|---|---|---|
| WorkBuddy | ~/.workbuddy/skills/weimeta-seedance 或 UI 导入本地 ZIP | V5.8.2 自动识别及 doctor、models、dry-run 成功 |
| Codex | ~/.agents/skills/weimeta-seedance（Codex 通用用户级目录） | 文件已部署，当前 Codex CLI 会话未通过；需排查 |
| TRAE | 根据当前 TRAE 版本在技能管理中导入；本机候选 ~/.trae/skills | 本机未安装客户端，需验证实际目录 |
| ZCode | 本机 ~/.zcode/skills/weimeta-seedance | 文件已部署，UI 执行未通过验收 |

WorkBuddy 公开文档：https://open.workbuddy.cn/docs/skill 。Codex 官方 Agent Skills 文档：https://developers.openai.com/codex/skills 。

## 零扣费验证（适用于所有具备本地终端和 HTTPS 调用权限的 Agent）

1. 在技能目录运行：python3 scripts/weimeta_video.py doctor 。
2. 使用自己的唯元智创 API Key，在已授权的环境运行：python3 scripts/weimeta_video.py models 。models 是只读 API 查询。
3. 验证参数构造：python3 scripts/weimeta_video.py generate --mode t2v --prompt '科技产品广告，镜头推进' --ratio 9:16 --duration 8 --resolution 720p --dry-run 。
4. 确认上述流程能被 Agent 自然语言正确触发。dry-run 不发起创建请求；它验证参数和命令调用能力，不能视为生成成功。
5. 获得明确的模型费用授权后，方可执行 --confirm-charge 真实生成；保存任务 ID，再使用 task --task-id 查询与下载。

## 企业推广的证据边界

WorkBuddy 已有真实的 Agent 内识别与三命令执行截图，真实的 Seedance 2.5 文生视频 POST/GET/MP4 下载由本机 CLI 完成。上述两项验证相互独立；暂不宣称所有 Agent 都自动完成实际收费的视频生成。

## 开发者发布

面向市场的 ZIP 第一层为 weimeta-seedance/，其中必须有 SKILL.md。正式上架需按照 WorkBuddy 开放平台创建技能、上传 ZIP、解析、审核、发布。当前为发布候选版，不应把本地安装当成市场上架完成。

API Key 通过 macOS/Linux 下的 python3 scripts/weimeta_video.py configure 交互式安全保存（0600），或由用户本机设置 WEIMETA_API_KEY。切勿把真实密钥粘贴到对话、代码仓库、截图、日志中。
