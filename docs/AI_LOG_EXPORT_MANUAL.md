# AI Coding 日志人工导出

状态 BLOCKED。2026-09-19 官方工具实查 `No sessions in staging`。
development_log.md 和 MiMo 运行时串口记录都不能替代开发原始日志。

## 官方依据与限制

[官方指南](https://github.com/open-vela/docs/blob/dev-ai-contest-2026/zh-cn/contest_2026/ai_coding_log_guide.md)，本地 docs 版本 cb0389919ea4fc86774702fb36c08ee9b1366e6c。
已检查 collector 10743591d1034480ecee7c8ffffe9bb251d4474d 的 Codex hook、--help、manifest schema。
要求真实 openvela `.repo/` 工作区，不得造空目录绕过门控。
该版本 --backfill 支持 Claude/OpenCode/MiMoCode/Cursor，没有 Codex 历史导入选项。
Codex CLI hook 注释要求首次在 CLI `/hooks` 中 trust；未验证桌面旧会话补导路径。

## 操作位置与命令

在产生会话的同一系统、同一账户操作。Windows 用 Git Bash；WSL 用原发行版。Windows 会话不会自动出现在 WSL home。
进入完整 openvela 工作区中的 contest2026_492_qunqingxueyuan 子仓：

```bash
bash ../.claude/skills/contest-log-collector/onboarding/install.sh \
  --team-id contest2026_492_qunqingxueyuan --github-login sdh12312
bash ../.claude/skills/contest-log-collector/onboarding/verify-setup.sh
python3 ../.claude/skills/contest-log-collector/tools/export-session.py --list
```

选择实际 FlyReflex 设计、实现、调试、测试与收尾会话，排除私人项目及样例。SESSION_ID 替换为清单实际 ID：

```bash
python3 ../.claude/skills/contest-log-collector/tools/export-session.py --session SESSION_ID
python3 ../.claude/skills/contest-log-collector/tools/export-session.py --session SESSION_ID --confirm
```

清单为空时停止，联系组委会说明 Codex Desktop 历史会话未被采集，请求认可的补导方法。安装不能补造过去的开发记录；不要重演旧工作、手写 JSONL、复制桌面内部日志冒充官方导出。

## 文件与校验

```text
logs/sdh12312/
  manifest.json
  YYYY-MM-DD/codex__真实会话ID.jsonl
```

manifest 由工具生成，不手写。核对 schema_version=1.0、team_id、github_login、非空 sessions；逐条检查 file_path、tool=codex、session_id、event_count、实际开发日期和文件内容。

```bash
python3 ../.claude/skills/contest-log-collector/tools/validate-log.py logs/
python3 ../.claude/skills/contest-log-collector/tools/render-log.py logs/sdh12312/
```

退出码应为 0，但结构通过不证明来源真实。人工核对实际项目内容，不得用 your-github-login 示例。把导出目录路径交回验收，之后才提交推送。

## 隐私

开发对话出现过密钥，官方脱敏不能假定覆盖全部提供商。导出后发现凭据则不提交，联系组委会确认合规脱敏/撤回方式；不要擅改正文、序号或 manifest。建议撤销曾在聊天出现的密钥。用户负责实际导出；本项目不自动抓取公开内部桌面会话。
