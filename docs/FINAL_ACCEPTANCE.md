> 历史阶段记录，原测试与问题保持原样。当前发布状态以 [FINAL_RELEASE_REPORT.md](FINAL_RELEASE_REPORT.md) 为准。

# FlyReflex Final Acceptance

验收日期：2026-09-19。最终判定：**BLOCKED**。

材料补充：已读取用户提供的官方 DOCX 提交模板及报名信息。真实队名为“群青学院”。用户确认：李孝淼负责总体方案、核心开发、系统集成、测试验证和材料；王鹏舜参与部分 UI 设计及验收测试。官方模板要求的章节和材料清单已核对。联系方式不写入公开仓库。

本次收尾进展：真实 MiMo Agent → Skill → run_shell → 本地 Guard → ESCAPE 链路通过，见 `evidence/agent-guard-serial.txt` 与 `evidence/agent-guard-runtime.txt`。工具退出码为 0，Agent 正确报告 REFLEX_OVERRIDE。独立工作区候选固件构建与启动通过，散列、补丁及范围见 `evidence/agent-build-provenance.md`。新版 Agent 固件的 NSH 连续测试完成：1800.28 秒、589 轮通过，59 次堆采样 used 均为 2361248 字节，见 `evidence/soak-agent-firmware.json`。浏览器实时默认攻击、零延迟对照、断线故障注入及恢复通过，见 `evidence/browser-live-acceptance.md`。

本表区分本地候选版本、已提交版本与真实运行证据。未提交的候选版本不能作为最终远端发布版本。禁止将模拟器测试描述为 MCU、摄像头或实体机器人测试。

## 验收清单

| Gate | 状态 | 证据和未完成条件 |
|---|---|---|
| 0 Git 状态 | BLOCKED | 本地 HEAD 为 `484ad052c1fdf4e2a098a24ae4e07c3bd4f2ee7a`，分支 `feature/visual-story`。存在修改及未跟踪文件，尚未冻结。工作目录本身是赛事专属仓，不是上游公共仓。 |
| 1 GitHub 交付 | BLOCKED | 官方 `open-vela/contest2026_492_qunqingxueyuan` 的 `dev-ai-contest-2026` 已包含旧版 FlyReflex，而非仅 scaffold；最新双场地、Guard 和验收修改尚未提交。manifest 已映射 `app/flyreflex`。 |
| 2 README | BLOCKED | README 已有作品说明，并修正本机路径及旧提交状态；最终完整命令仍须按候选版本 clean clone 全程复验。 |
| 3 Clean clone | BLOCKED | 独立 repo init/sync 加本地候选应用覆盖的 ARM64 构建与启动通过。缺少最终已冻结远端提交的无覆盖复现及 LVGL 检查；不能将候选覆盖构建等同于最终 clean clone。 |
| 4 核心功能 | BLOCKED | `evidence/target-runtime.txt` 保存模拟器 safe/slow/danger/recovery、Guard 和 benchmark 输出。最终冻结版本的断线与完整回归尚未完成。 |
| 5 openvela 真实性 | PASS | `evidence/target-runtime.txt` 的 uname、NSH 命令和 C 运行输出；`app/flyreflex/src/` 实现反射、仲裁、单调时钟与 LVGL。Python bridge 和浏览器不在 openvela 内运行。 |
| 6 Runtime Skill | PASS | 真实 MiMo mimo-v2.5 读取已部署 Skill，并通过 run_shell 调用 `flyreflex guard issue_agent_command FORWARD`；popen exit=0，219 字节输出，最终报告 ESCAPE / DANGER / REFLEX_OVERRIDE。调用前后 NSH 快照 fresh=true。证据见 `evidence/agent-guard-serial.txt`、`evidence/agent-guard-runtime.txt`。仅模拟动作，非实体执行器。 |
| 7 科学来源 | PASS | 本次重新执行 `python tools/connectome/fetch_malecns_reflex.py` 与 `python skills/flyreflex-provenance/scripts/verify_provenance.py`。male-cns:v1.0 得到 LPLC2 4862、LC4 6362 个突触，归一化为 433:567。原始查询、时间和连接见 `data/connectome/raw/neuprint_lplc2_lc4_to_dnp01.json`；说明见 `DATA_PROVENANCE.md`。 |
| 8 参数分类 | WARN | `data/engineering/model_params.csv` 区分工程参数；未修改核心 433:567 权重。前端同指令同结果、同攻击、连续碰撞检测测试通过。最终报告仍需完成全部参数与代码逐项对照。 |
| 9 Benchmark | WARN | 修复后 Agent 候选固件 1000 次输出见 `evidence/agent-firmware-runtime.txt`。reflex_compute median/P95/P99=1280/1360/2816 ns；end_to_end=2320/2448/5312 ns。固件散列见构建记录。仍需绑定最终发布 commit 并保存逐样本数据。 |
| 10 测试与可靠性 | WARN | 9 月 19 日重跑 CTest 1/1、Node 9/9、Python 3/3 通过。合成验证见 `evidence/synthetic-validation.json`。新版 Agent 候选固件 30 分钟、589 轮危险/恢复检查通过，堆采样无增长。浏览器交互与断线恢复通过；尚缺浏览器桥接长期测试和最终冻结回归。 |
| 11 技术报告 | WARN | `submission/FlyReflex_技术报告.docx` 及同名 PDF 已按官方模板更新，5 页逐页检查通过，包含真实 Agent 链路、最新候选基准和成员分工。保留模板样式及其他包部件。最终冻结与完整回归后仍需同步结果，当前不代表全套提交 READY。 |
| 12 AI Coding 日志 | BLOCKED | 用户于 2026-09-19 确认没有官方导出日志。`logs/README.md` 明确缺少经官方导出器生成的真实日志；不能用说明文件替代原始会话。 |
| 13 License / Security | BLOCKED | 已有 Apache-2.0 LICENSE，并新增 `THIRD_PARTY_NOTICES.md`。`evidence/release-inventory.json` 扫描源码及 ZIP/Office 内部成员，未发现匹配的凭据；仍不等同于 Git 历史、嵌套压缩包、PDF 和最终提交包的完整审查。 |
| 14 视频 | BLOCKED | 已录制 `submission/FlyReflex_浏览器实录素材.mp4`，101.68 秒，1440×960、25 fps，真实连接 openvela，包含交互、零延迟对照及传输故障注入。它没有旁白、LVGL 和真实 Agent 片段，不能替代完整比赛成片。Agent 调用证据已具备。 |
| 15 提交 ZIP | BLOCKED | 报名队名已确认。缺最终验收版报告与视频；没有生成冒充完整交付的 ZIP。 |

## 本次可重复测试命令

从项目根目录运行。CMake、CTest 和 Linux 可执行文件在 Linux/WSL 环境执行；Node/Python 测试可在已安装对应工具的主机执行。

```sh
cmake --build .qa/release/candidate-build
ctest --test-dir .qa/release/candidate-build --output-on-failure
python3 tools/release_validation.py .qa/release/candidate-build/flyreflex_host
node --test web/tests/*.test.mjs
python -m unittest discover -s tests -p test_web_bridge.py
```

本次 Windows PowerShell 直接调用 cmake/ctest 未找到命令，改在 WSL 执行后通过；首次合成测试误用二进制名 `flyreflex`，改用实际产物 `flyreflex_host` 后通过。以上失败没有计为通过。

## 数值边界

- 合成验证：100 个危险、100 个安全场景；正确触发 100、误触发 0、漏触发 0；触发率 100%、误触发率 0%、漏触发率 0%。输入是预先定义的合成输入族，不是真实视觉数据。
- 性能：openvela ARM64 simulator measurement。`end_to_end` 是代码内事件处理到仲裁区间，不包括摄像头、网络、浏览器渲染或电机响应。
- UI 单帧耗时与 benchmark 分布是不同采样方式，不能混为同一统计量。
- 功耗：Not measured — simulator-only prototype.
- 本届 MVP 使用官方 simulator，未制作新 PCB / 实体硬件。
- Guard 是模拟指令仲裁接口，不驱动真实执行器。状态超过 1500 ms 时按失效状态返回 STOP。

## 冻结条件

所有硬性阻塞解决后，才执行最终测试、完整安全审查、commit、push、PR 合并及远端 HEAD 核验。当前不得声明 READY TO SUBMIT。
