# CHANGELOG

## v0.3.1 — WorkBuddy display name compatibility

- 将技能展示名修改为 WEIMETA Seedance｜Agent 视频生成，避免技能市场同类名称冲突。
- 底层 name、API 端点、参数及计费安全机制保持不变。


## V0.3.0-RC1 — 2026-10-19

- 新增签名媒体链接及 API 凭据的输出脱敏，真实旧任务 GET 测试通过，无二次扣费。
- macOS 25 项单元测试通过。
- WorkBuddy UI 发现并运行 Skill 的证据已归档；真实 API 调用最终费用 ¥12.158997 已从平台核对。
- 提供 WorkBuddy / Source 可重现构建的安全发行 ZIP、上架说明和四端兼容验收矩阵。
- 基于真实视频关键帧生成公众号 1920×1080 技术封面。
- 未完成项：其他模式收费联调、Codex/ZCode/TRAE 的会话级验收、市场正式审核。


## V0.2 — 2026-10-16

- Python 3.9+ 标准库跨 Agent CLI：doctor、configure、generate、task。
- 支持 t2v / i2v / r2v / edit / extend 请求构造；实际模式兼容性待线上验证。
- 增加离线 dry-run、明确付费确认、任务 ID 管理、查询和下载。
- 新增隐藏输入的 API Key 配置，使用权限 0600 的用户本地配置文件。
- 23 项离线单元测试在 macOS Python 3.9.6 下通过。
- 本机部署至 Codex、TRAE、ZCode、WorkBuddy、通用 Agent Skill 目录。
- 发布用 ZIP 与公众号草稿、三张技术示意图已生成。

2026-10-16 联调补充：有效 Key（0600）与鉴权 GET 测试通过；GET /v1/models 显示 5 个 Seedance 模型 ID；已核验 2.5/2.0 各分辨率与含视频参考的价格档位；修正 2.5 的最小时长与 expired 状态；补充 models 只读子命令。

真实联调通过：用户授权后，成功创建 doubao-seedance-2-5-260628 文生视频任务，查询到 succeeded、下载 MP4 并用 macOS 媒体索引确认 720×1280、8.042 秒、H.264/AAC；使用量 173700 Token，按参考价约 ¥12.16。已导出真实样片和六帧预览，公众号文章更新为实测版。

待发布 Gate：核实最终账单、四端 Agent 实际识别、其他视频模式逐项联调、WorkBuddy 市场审核与品牌素材合规检查。
