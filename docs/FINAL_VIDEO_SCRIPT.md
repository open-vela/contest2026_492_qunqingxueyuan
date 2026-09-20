# 最终演示视频脚本

目标 3 分钟，最长 5 分钟。队伍：群青学院；作品：FlyReflex。

| 时间 | 画面与操作 | 讲述重点 |
|---|---|---|
| 0:00–0:20 | 项目名与浏览器双场地 | 上层 AI 可能慢；FlyReflex 在 openvela 本地独立仲裁危险动作。 |
| 0:20–0:40 | OPENVELA CONNECTED，清空并继续，SAFE / FORWARD | 世界和 Agent 延迟是仿真，安全动作由 openvela C 核心返回。 |
| 0:40–1:20 | 点击“向中心发射”，展示最近覆盖记录 | requested=FORWARD、state=DANGER、actual=ESCAPE；Browser → bridge → openvela → Browser。不要将仿真躲避率称为真实识别率。 |
| 1:20–1:45 | 暂时断开目标连接，再恢复，点击“重新连接” | OPENVELA DISCONNECTED / PAUSED，断线不继续推进，不伪造目标动作；重连清空旧统计。 |
| 1:45–2:10 | 暂停网页；终端展示 help、safe / danger，或 LVGL | flyreflex 实际运行于 openvela，危险覆盖为 REFLEX_OVERRIDE；LVGL 是独立合成场景，不与浏览器实时同步。 |
| 2:10–2:50 | 展示已脱敏的 final-agent-tool-trace 与 guard runtime；如现场运行先私下配置 | MiMo → ai_agent → Guard Skill → run_shell → 同一 C 仲裁；真实工具 exit=0，危险时 ESCAPE，快照过期 STOP。历史证据需标注采集阶段。 |
| 2:50–3:00 | 总结与来源表 | 4862 / 6362 突触，433:567 结构权重；阈值、泄漏、输入与动作映射是工程参数。非实体机器人、非 MCU 基准、无生产安全认证。 |

禁止录入密钥、Agent 配置或原始开发 rollout。旧浏览器素材仅供参考，不能代替完整成片。
