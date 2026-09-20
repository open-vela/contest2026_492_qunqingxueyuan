> 历史阶段记录，原测试与问题保持原样。当前发布状态以 [FINAL_RELEASE_REPORT.md](FINAL_RELEASE_REPORT.md) 为准。

# Release Candidate

- RC source commit: `70db07b10ba3c10d7d2c36c3160debaebd05ebcf`。
- Date: 2026-09-19。
- Branch: `feature/visual-story`。
- Scope: 应用、web、bridge、Skill、重放补丁与验收工具。核心进入冻结，只允许修复阻塞问题。
- 后续报告和验收证据是文档更新，不改变此源代码 RC；最终提交 SHA 将另行记录。
- 远端尚未发布本 RC。用户导出日志后再 final commit/push/PR。

## 验证状态

正在从此 commit 的本地独立 clone 执行主机测试，并检查 openvela 应用字节一致后执行 `cmake --build ... --clean-first -j4`。结果完成前不记 PASS。
旧 evidence 文件均为候选历史记录，不能自动代表本 RC。
