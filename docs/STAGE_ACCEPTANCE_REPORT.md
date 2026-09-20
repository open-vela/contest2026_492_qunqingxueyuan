> 历史阶段记录，原测试与问题保持原样。当前发布状态以 [FINAL_RELEASE_REPORT.md](FINAL_RELEASE_REPORT.md) 为准。

# FlyReflex 阶段验收报告

| 项目 | 内容 |
|---|---|
| 验收阶段 | 最终集成：演示层与 openvela 真实执行层闭环 |
| 验收日期 | 2026-09-19 |
| 队伍 ID | contest2026_492_qunqingxueyuan |
| 工作目录 / 分支 | `D:\openvela` / `feature/visual-story` |
| 验收对象 | openvela ARM64 模拟器原型、浏览器演示、Python bridge、MiMo Guard 链路 |
| 报告性质 | 根据本阶段实际测试记录与落盘证据编制；编写报告时未重新执行全套测试 |
| 阶段结论 | **本阶段功能验收通过；最终提交就绪验收尚未完成。** |

## 一、验收目标与范围

本阶段目标是在不重写 C 核心、不更换技术栈的前提下，让浏览器输入真正进入 openvela 内的 FlyReflex，由目标端返回安全动作并驱动画面；同时确认 MiMo 通过 Guard Skill 和 `run_shell` 使用同一目标执行层。

验收覆盖安全放行、危险覆盖、非法数值输入保护、Guard 状态过期、通信断开与恢复，以及真实模型工具调用。实体机器人、摄像头识别、MCU 性能、生产安全认证、LVGL 与浏览器场景同步不属于本阶段已通过范围。

## 二、调查结论与实施内容

调查发现，仓库原有 bridge 已支持 `POST /step → Telnet → flyreflex control`；C CLI 已提供 FR2 JSON，并将控制结果发布为 Guard 可查询的共享快照。因此，本次主要完成真实路径的启用、校验与现场验证，而非从零新增通信链路。

| 实施项 | 本阶段完成内容 |
|---|---|
| 浏览器入口 | 默认选择 openvela 实时模式，主机参考模式保留且明确标识 |
| 动作可见性 | 展示 AGENT DECISION、FlyReflex 状态、ACTUAL ACTION；保留最近一次真实覆盖记录 |
| 应答完整性 | bridge 与浏览器检查来源、序号、动作枚举、状态及数值字段，拒绝不合格应答 |
| 通信保护 | 浏览器请求期限设为 1500 ms；通信失败暂停世界推进，清除当前有效动作展示 |
| Guard 部署 | 从仓库原始 Skill 文件部署至 `/data/agent/skills/flyreflex-guard.md`，回读验证 |
| 目标验收 | 新增真实 HTTP / Telnet 集成测试，不使用 host 或 mock 代替目标 |
| MiMo 验收 | 复用现有测试工具，支持外部密钥文件和独立证据路径，记录真实串口调用证据 |
| 可复现性 | 补充启动、测试、端口、固件路径与会话 provenance 文档 |

C 安全算法、阈值、连接组权重及既有 benchmark 数据均未修改。

## 三、最终执行关系

```text
Browser：仿真世界与几何输入
  → HTTP POST /step
  → Python bridge：转发与协议校验
  → Telnet / NSH
  → openvela flyreflex control
  → C 反射计算 + 安全仲裁
  → FR2 JSON
  → Browser：根据真实动作推进动画

MiMo
  → ai_agent
  → FlyReflex Guard Skill
  → run_shell
  → flyreflex guard issue_agent_command FORWARD
  → 同一 openvela 中的共享快照与 C 安全仲裁器
```

两条路径在同一目标实例上分别验收。MiMo 测试期间暂停浏览器，由专用 `control` 输入流保持危险快照新鲜；这不代表浏览器和云端请求的并发负载已经通过专项测试。

## 四、功能验收结果

| 编号 | 场景与操作 | 实际结果 | 判定 |
|---|---|---|---|
| A | HTTP 发送安全输入，独立 NSH 查询 Guard | 目标来源 openvela，SAFE / FORWARD；Guard 同样返回 FORWARD | 通过 |
| B | 危险输入下请求 FORWARD | `agent_b=FORWARD`、`state=DANGER`、`action=ESCAPE`；Guard 返回 REFLEX_OVERRIDE | 通过 |
| C | 直接向真实 CLI 发送负数传感输入 | INVALID / STOP；共享 Guard 也返回 STOP | 通过 |
| D | 停止更新后等待 1.7 秒，再请求 Guard | `fresh=false`、INVALID / STOP、FAILSAFE | 通过 |
| E1 | 集成测试主动断开真实目标 socket | HTTP 503，返回 DATA CONNECTION LOST，无伪造动作 | 通过 |
| E2 | 浏览器运行时停止 bridge，再点击发射 | OPENVELA DISCONNECTED、PAUSED；发射及碰撞/避让计数不增长 | 通过 |
| E3 | 重启 bridge 并点击重新连接 | 恢复 OPENVELA CONNECTED、SAFE / FORWARD，统计清零 | 通过 |
| F | MiMo 读取 Skill，调用 run_shell 请求前进 | 串口确认 Guard 命令实际执行且 exit=0；模型报告 ESCAPE 覆盖 FORWARD | 通过 |

非法输入验收的具体范围为 CLI 非法数值输入，以及协议字段校验。不能由此推导所有可能的畸形字节流均已穷举验证。HTTP 层非法输入会先被拒绝，不会伪称目标已返回 STOP。

浏览器现场默认中心攻击记录：左侧碰撞 1 次、避让 0 次；右侧碰撞 0 次、避让 1 次。页面保留的真实记录为：

```text
openvela · seq=245:
requested=FORWARD → actual=ESCAPE · state=DANGER
```

该结果仅证明这次演示场景的闭环及动作表现，不构成总体避障成功率结论。

## 五、回归测试与证据

| 验证项 | 本阶段结果 | 证据或复现入口 |
|---|---|---|
| C core | 1/1 PASS | `ctest --test-dir build --output-on-failure`，本阶段执行记录 |
| Browser tests | 10/10 PASS | `npm test --prefix web`，本阶段执行记录 |
| Python bridge tests | 4/4 PASS | `python -m unittest discover -s tests -p test_web_bridge.py` |
| Synthetic validation | 危险 100/100 正确触发；安全误触发 0/100 | [合成验证结果](evidence/final-synthetic-validation.json) |
| 真实目标集成 | PASS | [目标集成 JSON](evidence/real-openvela-integration.json) |
| 浏览器人工验收 | 安全、危险、断线、恢复通过 | [浏览器验收记录](evidence/final-browser-acceptance.md) |
| MiMo 工具执行 | 实际 run_shell 与 Guard 命令执行确认 | [串口工具日志](evidence/final-agent-tool-trace.txt) |
| MiMo 最终反馈 | ESCAPE / REFLEX_OVERRIDE，前后快照一致 | [模型运行记录](evidence/final-agent-guard-runtime.txt) |
| 既有赛事日志校验 | 1 个文件、1868 个 events，ALL OK | 官方 validate-log 工具，本阶段执行记录 |
| 新增证据密钥检查 | 已使用密钥的完整字符串匹配数为 0 | 本阶段检查记录；不等同于所有敏感信息均经全面审计 |

目标报告的系统信息为 ARM64 NuttX/openvela，构建标识含 `dd92bcf4257`、`Sep 19 2026 11:00:38`。本阶段未重新测量历史微秒级 benchmark，也未重复 1800 秒长期运行测试；历史结果不得视为本阶段新增性能或稳定性验收结果。

## 六、演示运行条件

验收使用 WSL `Ubuntu-D`，浏览器服务端口 **8090**，目标 Telnet 映射端口 **10025**，独立模拟器端口 **5558/5559**、gRPC 端口 **8558**。浏览器与 bridge 静态资源服务由同一 Python 服务提供。

```powershell
cd D:\openvela
npm ci --prefix web
wsl -d Ubuntu-D -- python3 /mnt/d/openvela/tools/web_bridge.py --port 8090 --target-port 10025
```

浏览器访问 <http://127.0.0.1:8090>。运行前需启动对应模拟器并完成 NSH 网络与端口映射。完整模拟器启动命令、固件目录覆盖、Skill 部署及 MiMo 配置见 [最终集成操作文档](FINAL_INTEGRATION.md)。本报告记录验收时配置，不将服务持续在线作为已验证事实。

## 七、真实性与能力边界

1. **Visual world is simulated**：物体运动、几何输入、碰撞统计和动画在浏览器中执行。
2. **Agent latency is simulated**：双场地左侧为人为延迟控制模型，不是真实 MiMo 推理时延。
3. **Safety decision is executed by FlyReflex on openvela**：仅实时模式作此声明；主机参考模式明确另行标识。
4. FORWARD 表示安全仲裁允许正常仿真行为，ESCAPE 表示仿真避让动作，均不代表实体设备运动。
5. 连接组直接突触计数及归一化权重具有数据来源；泄漏、阈值、输入编码和动作映射仍为工程参数。
6. 通信失败时浏览器采取 PAUSED；这不是伪造一条来自 openvela 的 STOP。Guard 快照过期时的 STOP 则由目标 C 逻辑返回。

## 八、遗留问题与提交前关闭条件

| 优先级 | 未关闭事项 | 影响与关闭条件 |
|---|---|---|
| P0 | 本次 AI Coding 会话最终导出 | 会话结束并落盘后，用现有 converter 转换、检查脱敏，再对最终 logs 运行官方校验获得 ALL OK |
| P0 | 固件产物持久化与冷启动复现 | 原构建目录缺少 nuttx，本次从已有临时候选目录复制启动；提交前保留完整产物或重建，并验证从稳定路径冷启动 |
| P0 | 提交版本尚未冻结发布 | 按文件清单审核已有未提交材料，用户确认后再 commit/push；记录最终源码版本与固件对应关系 |
| P1 | 原 10023 实例拒绝新 Telnet 客户端 | 诊断期间出现连接槽位问题；本次以独立 10025 实例完成验收。若继续使用旧实例，应恢复并复测 |
| P1 | 单会话及多生产者限制 | 正式演示只保留一个 bridge 会话；不要让多个输入流竞争同一 Guard 快照 |
| P2 | LVGL 未同步浏览器场景 | 保持原独立合成场景展示，不声称与浏览器状态实时一致 |

目前结论适用于已验证的模拟器实例和场景，不构成“全部比赛提交工作完成”的签署。

## 九、交付与过程记录

代码、测试、运行工具和证据文件清单见 [FINAL_INTEGRATION.md](FINAL_INTEGRATION.md)；阶段结束时的工作区状态见 [Git 状态记录](FINAL_INTEGRATION_GIT_STATUS.txt)。本报告新增文件为 `docs/STAGE_ACCEPTANCE_REPORT.md`。未执行 Git 自动暂存、提交或推送。

AI Coding 会话 ID：`01a0b9b4-c572-7b70-b99b-35cd4196ac14`。原始 rollout 路径、开始时间、cwd 和退出后的转换命令见 [会话 provenance](AI_CODING_SESSION_NOTES.md)。该 provenance 文档及本报告都不是赛事 AI Coding Log 的替代品。

**验收意见：同意本阶段功能成果进入提交准备阶段；完成日志归档、固件可复现与版本冻结后，再进行最终提交就绪确认。**
