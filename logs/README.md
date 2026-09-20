# logs/ — AI Coding 日志目录

存放你在开发中与 AI 工具的对话日志，和作品代码一并提交。

> 初始两次 Codex 会话已透明转换为赛事 JSONL，官方 validator ALL OK，最终凭据扫描 PASS。本次 release 会话需结束后追加；说明与唯一归档命令见 [AI_LOG_EXPORT_MANUAL](../docs/AI_LOG_EXPORT_MANUAL.md)。development_log.md 仅为工程摘要。

## 目录结构

```text
logs/
└── <github_login>/              # 你的 GitHub 用户名，一人一目录
    ├── manifest.json            # 会话清单
    └── <date>/                  # 日期 YYYY-MM-DD
        └── <tool>__<sid>.jsonl  # 一个会话一个文件（工具名与 session id 用 __ 连接）
```

- `<tool>`：`claude-code` / `opencode` / `codex` / `kiro`
- 每个 `.jsonl` 每行一个事件；本项目以公开 converter 兼容新 Codex rollout，并用官方 validator 校验。来源、格式限制与脱敏过程见 provenance 文档。

导出与提交的完整步骤、字段定义见[《AI Coding 日志归集与提交手册》](https://github.com/open-vela/docs/blob/dev-ai-contest-2026/zh-cn/contest_2026/ai_coding_log_guide.md)。
