# WEIMETA Seedance Skill

**使用唯元智创 API，在 AI Agent 中生成和下载 Seedance 视频。**

[English](#english)

本项目是一个可在支持 Agent Skills 的工具中复用的 Python CLI + SKILL.md，面向 WorkBuddy、Codex、TRAE、ZCode 等具备本地命令执行和 HTTPS 访问权限的 Agent。

## 已验证的能力

2026-10-16，基于唯元智创 API（api.weimeta.cn）实际完成 Seedance 2.5 文生视频创建、状态轮询和 MP4 下载。测试视频为 720 × 1280、8.042 秒、H.264，实际生成消耗 173700 视频 Token，平台账单金额 ¥12.158997。WorkBuddy V5.8.2 另已完成 Skill 识别、doctor、models 与 dry-run 的独立客户端验证。这两项测试属于不同验收链路。

文生视频为**当前已完成端到端验收**的模式。图生视频、参考生视频、视频编辑及延长目前提供参数构造入口，实际 API 兼容性尚需逐项确认。Codex、TRAE、ZCode 的客户端发现机制也尚未通过端到端验收。

## 目录

```text
weimeta-seedance/
├── SKILL.md
├── scripts/
│   └── weimeta_video.py
├── references/
│   ├── API.md
│   ├── INSTALL.md
│   └── PRICING.md
├── examples/
│   └── prompts.md
├── tests/
│   └── test_skill.py
├── LICENSE
└── README.md
```

## 快速开始

要求 Python 3.9+，只使用标准库。

克隆本仓库后进入项目目录。首先使用自己的唯元智创 API Key；在 macOS/Linux 可运行：

```bash
python3 scripts/weimeta_video.py configure
```

脚本会在本机隐藏输入 API Key 并写入仅当前用户可读的 `~/.config/weimeta/seedance-credentials.json`（0600）。也可以通过本机环境变量 `WEIMETA_API_KEY` 配置。**不要把真实 API Key 发送到聊天或提交到仓库。**

### 零扣费检查

```bash
python3 scripts/weimeta_video.py doctor
python3 scripts/weimeta_video.py models
python3 scripts/weimeta_video.py generate --mode t2v \
  --prompt "科技产品宣传，深蓝色展厅，镜头缓慢推进" \
  --ratio 9:16 --duration 8 --resolution 720p --dry-run
```

其中 `doctor` 和 `--dry-run` 不发起付费视频生成。 `models` 通过已授权 API Key 查询可见的 Seedance 模型 ID。

### 真实生成（可能产生费用）

确认当前模型、时长、分辨率及平台计费方式后，执行：

```bash
python3 scripts/weimeta_video.py generate --mode t2v \
  --prompt "科技产品宣传，深蓝色展厅，镜头缓慢推进" \
  --ratio 9:16 --duration 8 --resolution 720p --confirm-charge
```

脚本返回 `task_id` 并在本地保存任务回执。随后可以查询、轮询并下载：

```bash
python3 scripts/weimeta_video.py task --task-id "<真实任务ID>" --wait --download
```

默认下载至 `~/Downloads/WEIMETA`。临时媒体 URL 在输出日志中自动脱敏。生成请求超时后请检查任务记录，**不要盲目重新提交并重复扣费**。

## 跨 Agent 安装

将整个 `weimeta-seedance` 目录复制到目标 Agent 的 Skills 目录，并按照对应客户端的管理界面刷新/导入。各端安装路径、可见权限和执行能力因版本而异，详见 [安装与兼容性说明](references/INSTALL.md)。

## 安全与限制

运行所需的 API Key 由用户本地提供，示例与测试不携带密钥。本地视频自动上传、云端回调、准确实时计费预检和完整批量工作流仍在适配中。API 实际支持的时长、画面规格、输入数量、计费档位以唯元智创实时模型规则为准。相关平台名称及商标归其各自权利人所有，Skill 项目为唯元智创维护的第三方工具。

## 许可证

[MIT License](LICENSE)，Copyright (c) 2026 深圳市唯元智创科技有限公司。

---

## English

WEIMETA Seedance Skill is a reusable `SKILL.md` and Python 3.9+ CLI for Seedance video generation through the WEIMETA API gateway.

Verified: asynchronous text-to-video task submission, task polling, and MP4 download with Seedance 2.5. WorkBuddy independently passed skill discovery, `doctor`, `models`, and `--dry-run` tests. Other agent integrations and advanced video modes require additional end-to-end verification.

Use your own WEIMETA API key. Run `python3 scripts/weimeta_video.py doctor` and `python3 scripts/weimeta_video.py generate --prompt "technology product" --dry-run` for a safe local check. To create a billable task, first review pricing and explicitly add `--confirm-charge`.

MIT licensed.
