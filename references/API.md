# WEIMETA 视频网关协议（2026-10-16 联调记录）

默认网关：https://api.weimeta.cn/volcengine/v1

POST /contents/generations/tasks 创建可能计费的任务。
GET /contents/generations/tasks/{id} 查询任务状态和临时视频结果 URL。

请求字段示例：
{"model":"doubao-seedance-2-5-260628","content":[{"type":"text","text":"城市科技展厅镜头"}],"ratio":"9:16","duration":8,"resolution":"720p"}

Header：Authorization: Bearer <用户自己的API Key>，Content-Type: application/json。

任务成功通常返回 id。查询成功通常得到 status=succeeded 与 content.video_url，后者可能有有效期。不同网关版本响应可能不同，需要联调对照。

2026-10-16 已通过本机安全配置的有效 Key 使用 GET /v1/models 确认 5 个 Seedance ID，GET 视频任务列表鉴权成功。随后已通过 POST 创建 Seedance 2.5 文生视频，查询到 succeeded，下载 MP4 并核对实际用量 173700 Token。其他模式未在线验收，参见 PRICING.md 的完整参考价档位（页面价，不保证账户实付）。本版尚无准确扣费预估接口、自动视频上传能力，不得宣传已实现。真实视频案例报告位于 marketing/实测素材/实测案例报告-20261016.md。
