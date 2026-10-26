# Dify 工作流

[youtube_digest.yml](youtube_digest.yml) 来自维护者已运行成功的「YouTube 频道分析」应用导出，包含完整的 22 个节点和 21 条连接。发布副本已清空全部 6 个环境变量值，保留变量名称、类型、节点 ID、参数和连接。

## 导入

1. 在 Dify 工作室选择导入 DSL，上传本目录的 `youtube_digest.yml`，创建新应用。
2. 按提示安装 DeepSeek 模型插件，并在模型供应商中填写自己的 API Key。若导出使用的模型在目标环境不可用，选择可用模型后重新测试。
3. 在 ENV 中填写 `YOUTUBE_API_KEY`、`GMAIL_CLIENT_ID`、`GMAIL_CLIENT_SECRET`、`GMAIL_REFRESH_TOKEN`、`GMAIL_SENDER`、`GMAIL_RECIPIENT`。值中不要额外添加引号。填写方法见 [Gmail API 接入指南](../Gmail_API接入指南.md)。
4. 使用 [示例输入](../examples/input.preview.json)，将 `delivery_mode` 设为 `preview`，检查报告输出。
5. 确认收件邮箱后再使用 `send`，检查最终输出中的 Gmail 邮件 ID，并到邮箱核对邮件。

当前发送部分直接使用 HTTP 和代码节点，不依赖另一个已发布的工作流工具。`.env.example` 是字段清单，Dify 不会自动读取仓库中的 `.env`。

## 版本与来源

- 原应用环境：Docker Dify 1.18.0。
- DSL 版本：`0.7.0`。
- 导出记录的模型插件：`langgenius/deepseek:0.0.26`，完整依赖标识保留在 YAML 中。
- LLM：`deepseek-flash`，回复格式 `json_object`，思考模式关闭，原生结构化输出关闭，最大输出 8192。

Dify 1.18 默认导出 `.ifpkg` 包，同时仍支持 YAML 导入和导出。本 YAML 从原始包的 `app.yaml` 提取后清空凭据；不是将压缩包直接改后缀得到的。原始包没有包含在发布文件中。[Dify 1.18 发布说明](https://github.com/langgenius/dify/discussions/44607)

## 打包验证记录

2026-10-26：

- 22 个节点 ID 唯一，21 条连接有效，图中无环。
- 52 处变量引用均指向存在的上游输出或环境变量；结束节点的输出名称不重复。
- 8 个代码节点的源码与仓库对应 Python 文件一致，函数参数与节点输入名称匹配。
- Gmail 发送使用 POST；raw 请求体只有一个项目；发送节点自动重试关闭。
- 6 个环境变量值均为空；发布文件经过凭据模式与实际导出值检查。
- 清理了 LLM 系统提示词末尾误附的数字行，提示词正文与仓库的 JSON 模式提示词一致。
- 15 项离线测试通过，使用合成数据，不调用外部 API。

维护者已确认原应用运行成功；脱敏 YAML 已完成语法、引用与源码一致性检查，尚未在新 Dify 应用中导入并运行验证。GitHub Actions 配置已提供，远端执行结果要在上传后查看。

## 后续更新

修改 Dify 节点后重新导出，并同步对应 Python 文件和提示词。原始导出先保存在 Git 忽略的 `private/` 目录；清空真实配置值后再更新此 YAML。不要将运行日志、令牌响应、OAuth 凭据 JSON 或含密钥的截图提交到仓库。网页手动上传时需要自行排除这些文件，`.gitignore` 不会替网页筛选。
