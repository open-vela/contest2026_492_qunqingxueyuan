# AI Coding 日志归档

初始两次开发会话已从原始 Codex rollout 透明转换。新 rollout 使用 response_item / event_msg，现有 collector 不直接兼容；公开 converter 保留实际事件、时间和工具调用，不解密或伪造 reasoning，不修改 source。来源 SHA256 见 codex_rollout_sha256.txt，转换限制见 AI_CODING_LOG_PROVENANCE.md。

<!-- AI_LOG_TOTALS -->
Archived AI Coding logs: 2 sessions, 2 files, 2080 events. Official validator: ALL OK. Credential scan: PASS.
<!-- /AI_LOG_TOTALS -->

## 本次 release 会话

状态：PENDING CURRENT SESSION FINALIZER。
当前会话尚在写入，不可声称已最终归档。关闭此 Codex 会话后，在 PowerShell 执行唯一归档命令：

```powershell
python -X utf8 D:/openvela/tools/finalize_last_codex_session.py 01a0b9ec-8ebc-7dc1-bd5a-b6f05daa889c --commit
```

脚本等待源文件稳定 30 秒，在临时目录运行 converter、官方 validate-log.py 和高置信凭据扫描，检查旧 session 条目与 JSONL 不变后追加。已封存 session 若源 SHA256 不同，拒绝覆盖。脚本更新 SHA256 清单与本页、README 的真实计数；--commit 仅将此次归档与摘要显式加入本地提交，不自动 push 或 merge。文件稳定不等于会话已结束，必须先关闭会话。

## 本次凭据修复记录

2026-09-19 最终扫描发现第一 session 中 9 处 tp- 前缀密钥未被旧规则覆盖。经用户明确授权，旧 JSONL 与 manifest 已在仓库外原样备份；converter 1.3 从未修改的原始 rollout 重新转换第一 session，事件数仍为 1868，source SHA256 不变。第二 session 的 JSONL 保持原样。未手工编辑 JSONL，未展示密钥。修复后官方校验 ALL OK，凭据扫描 PASS。建议撤销该曾出现在开发对话中的密钥。

开发期 Codex 日志与 MiMo 运行时证据用途不同；development_log.md 和 Agent 串口输出不能替代开发日志。原始 rollout 和仓库外敏感备份均不得提交。
