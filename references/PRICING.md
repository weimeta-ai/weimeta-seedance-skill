# Seedance 价格与费用预检（2026-10-16 核验快照）

此表源于唯元智创已登录模型广场的展示信息，并与火山方舟公开价格说明交叉核对。此处为公开参考刊例，并非账户实付承诺。具体费用取决于账户分组、使用量、输入是否包含视频、输出尺寸、输出时长和后端结算规则。

| 模型 | 分辨率 | 无视频输入（元/百万视频 Token） | 含视频输入（元/百万视频 Token） |
| --- | --- | ---: | ---: |
| doubao-seedance-2-5-260628 | 480p / 720p | 70 | 42 |
| doubao-seedance-2-5-260628 | 1080p | 77 | 46 |
| doubao-seedance-2-0-260128 | 480p / 720p | 46 | 28 |
| doubao-seedance-2-0-260128 | 1080p | 51 | 31 |
| doubao-seedance-2-0-260128 | 4K | 26 | 16 |
| doubao-seedance-2-0-fast-260128 | 480p / 720p | 37 | 22 |
| doubao-seedance-2-0-mini-260615 | 480p / 720p | 23 | 14 |

官方估算方法：预计 Token = (输入视频秒数 + 输出秒数) × 输出视频的宽 × 高 × 帧率 ÷ 1024。实际以 GET 查询结果 usage.completion_tokens 或平台消费账单为准。

假定不含视频输入，720p、16:9 或 9:16、24fps：每秒预计 21,600 Token。Seedance 2.5 生成 4 秒的视频约 86,400 Token，估算 ¥6.048；8 秒约 172,800 Token，估算 ¥12.096。图片、音频不作为视频输入秒数；但模型服务仍可能采用其他最低用量、帧数、定向价或账户费率规则。

当前 Skill 的 --dry-run 仅生成本地预检请求，不会查询余额或创建视频；模型已通过 API Key GET /v1/models 验证存在。付费生成必须确认该账号预计花费并使用 --confirm-charge。

核对来源：
- 唯元智创模型广场：https://weimeta.cn/console/models
- 火山方舟定价文档：https://console.volcengine.com/ark/region:cn-beijing/docs/model-pricing
- 唯元智创创建接口：https://api.weimeta.cn/volcengine/v1/contents/generations/tasks
