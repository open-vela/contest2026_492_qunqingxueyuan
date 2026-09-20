# 人工录制素材清单

先核对 RELEASE_CANDIDATE.md。每段前后留 1–2 秒静止帧，分别录制。

| 素材 | 时长 | 必须拍到 |
|---|---|---|
| openvela/LVGL | 35–45 秒 | 模拟器；SAFE：AI FORWARD、REFLEX IDLE、FINAL FORWARD；DANGER：LPLC2/LC4/GF 上升，AI 仍 FORWARD、REFLEX/FINAL ESCAPE、REFLEX_OVERRIDE；latency、RECOVERY、回到 FORWARD。三个指令必须同时清晰。 |
| 浏览器 | 45–60 秒 | openvela 实时来源；双场地、相同延迟、拖动蓄力发射同攻击、左右运动与统计；清空后延迟 0 再试。不宣称永不碰撞。 |
| 真实 MiMo | 40–60 秒 | 模型标识、读取 Guard Skill、FORWARD 请求、fresh DANGER、真实工具返回 ESCAPE 或失效 STOP、模型确认覆盖。等待可剪，流程不可伪造。 |
| benchmark | 15–25 秒 | RC SHA、NSH flyreflex bench 1000、两路径 median/P95/P99；对应 final log，注明 ARM64 simulator。 |
| 科学来源 | 15–25 秒 | DATA_PROVENANCE、MaleCNS v1.0、4862/6362、433:567；字幕：神经动力学参数为工程参数。 |
| 断线恢复，可选 | 10–20 秒 | 断开 bridge/目标、DATA CONNECTION LOST、停止推进、恢复并重置；明示断线方式。 |

MiMo 字幕：MiMo is the high-level agent. FlyReflex remains the local safety path.
即 MiMo 负责高层决策，FlyReflex 负责本地安全反射。不要把单次云端约 18 秒与微秒级本地运算当同类性能比较。
启动命令见 README 与 AGENT_GUARD。密钥必须离屏配置。
现有约 102 秒浏览器素材不能代替完整比赛视频。
