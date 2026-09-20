# AI Coding 日志来源说明（Codex）

本项目的部分开发使用 Codex 完成。当前本机 Codex rollout 使用
`session_meta / event_msg / response_item / turn_context` 等新结构；比赛现有
collector 的 Codex 路径仍按 Claude Code 风格 `message` 结构解析，因此无法直接
生成赛事 `codex__*.jsonl`。

根据赛事交流群答疑，采用以下透明补录流程：

1. 原始 Codex rollout JSONL 保持不修改。
2. 对原始文件计算 SHA256，并记录在 `docs/codex_rollout_sha256.txt`。
3. 使用项目内公开转换脚本，将 `response_item.payload` 中可核对的消息、工具调用、
   工具返回和 token 记录转换到赛事 event schema。
4. 不解密、不伪造 Codex 的 `encrypted_content` reasoning；无法嵌入 textual event
   schema 的图片块不写入转换日志，并在 manifest 中记录跳过数量。
5. 转换后的日志使用官方 `validate-log.py` 校验。
6. 如组委会需要审计，可使用 SHA256 对照本机保留的原始 rollout。

注意：`manifest.json` 的 `collection_mode` schema 当前没有
“manual Codex backfill”枚举，因此保持来源工具兼容值 `cli`，同时额外写入
`conversion_mode=post-hoc-codex-rollout-response_item-v1` 和来源完整性信息，
明确说明这是事后兼容转换而非官方 collector 实时导出。
