# 最终真实闭环

当前推荐路径：`D:/openvela` 源码，`D:/openvela_official` 完整工作区，WSL `Ubuntu-D`。所有最终构建与重测结论见 [FINAL_RELEASE_REPORT.md](FINAL_RELEASE_REPORT.md)。旧阶段证据和旧端口保留在 STAGE_ACCEPTANCE_REPORT.md；它们不替代本次验收。

## Actual implementation

Browser `web/app.js` → HTTP `POST /step` → existing Python `Controller` → local Telnet NSH → `flyreflex control` → C engine and arbiter → FR2 JSON → validated reply → browser animation.

MiMo → `ai_agent` → repository `flyreflex-guard` Skill → `run_shell` → `flyreflex guard issue_agent_command FORWARD` → the same C arbiter and shared snapshot published by `control` in the same openvela boot. Snapshots older than 1500 ms produce STOP.

No C algorithm or thresholds changed. Browser now defaults to live openvela, displays requested/state/actual and the latest real override. Both bridge and browser reject malformed, unexpected-source or mismatched-sequence telemetry. Missing response after 1500 ms pauses the browser; it does not invent an openvela STOP result. HTTP invalid inputs are rejected before execution. Numeric invalid inputs sent directly to the CLI return STOP.

Visual world is simulated. Agent latency is simulated. Safety decision is executed by FlyReflex on openvela in live mode. Explicit host-reference mode remains available and labeled. FORWARD means the C arbiter permits the simulated normal behavior; this scene is not a forward-driving robot. No hardware actuator exists.

## 最终启动

在 PowerShell 执行：

```powershell
cd D:/openvela
powershell -ExecutionPolicy Bypass -File tools/start_final_demo.ps1
```

注意：本次 final clean-first 构建未在收尾时间窗内产出一份完整的新固件，因此不能把该启动方式描述为“本次 clean build 新固件”。最终 release 的 BUILD 状态为 PARTIAL、OPENVELA 新固件 smoke 为 BLOCKED。已有 Browser / MiMo / Guard / openvela 闭环证据来自此前实际验证过的 candidate；如使用该 candidate 录制演示，必须明确标注为既有已验证候选固件，不得表述为本次 clean build 产物。端口约定仍为目标 10025、模拟器 5558/5559、gRPC 8558、HTTP 8090。

浏览器打开 http://127.0.0.1:8090。bridge 与目标在同一 WSL。若已有最终模拟器，只需：

```powershell
wsl -d Ubuntu-D -- python3 /mnt/d/openvela/tools/web_bridge.py --port 8090 --target-port 10025
```

`GET /health` 仅证明 bridge 服务正常；目标连接与动作来源必须由 `POST /step` 的 `source=openvela` 证明。页面默认 live，传输失败暂停，不自动切换 host-reference。

## Browser acceptance

1. Safe: clear the scene, resume, wait for OPENVELA CONNECTED, requested FORWARD / state SAFE / actual FORWARD.
2. Danger: click 向中心发射. The retained override record must say `openvela`, requested FORWARD, actual ESCAPE and state DANGER. Watch the right-hand avoidance movement. At default settings the left side collides and the right side avoids.
3. Disconnection: stop the bridge or disconnect target transport. Within the response deadline the page must display OPENVELA DISCONNECTED, PAUSED, no current target action. No continued world stepping or success-count growth. Restart bridge and click 重新连接; statistics reset.
4. Pause is a visual-world pause; it does not keep a target Guard snapshot fresh. MiMo must return STOP if no producer has published fresh data for more than 1.5 seconds.

## Guard Skill 与 MiMo

运行时 Skill 源码为 `runtime_skills/flyreflex-guard.md`，部署到 `/data/agent/skills/flyreflex-guard.md`：

```powershell
wsl -d Ubuntu-D -- python3 /mnt/d/openvela/tools/deploy_guard_skill.py --port 10025
```

暂停网页后才能运行 Agent 验收。现有测试支持从仓库外安全文件读取密钥，不把密钥放在命令行值、仓库或证据中：

```text
python3 tools/test_agent_guard.py --port 10025 --skill-installed --key-file /absolute/private/key-file --output docs/evidence/final-release-agent-runtime.txt
```

实测证据必须包含读取 Skill、run_shell、Guard 返回值与最终覆盖回答；仅有模型口述不算成功。两条必须应用的 ai_agent 补丁与构建配置见 [AGENT_GUARD.md](AGENT_GUARD.md)。这些公共仓修改由赛事仓的公开脚本重放，不声称已经进入上游。

开发期 Skill 位于 `skills/flyreflex-provenance/`，用于验证数据来源；与运行时 Guard Skill 分开。

## 重测命令

```powershell
wsl -d Ubuntu-D -- bash -lc 'cd /mnt/d/openvela && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j4 && ctest --test-dir build --output-on-failure'
npm test --prefix web
python -m unittest discover -s tests -p test_web_bridge.py
wsl -d Ubuntu-D -- python3 /mnt/d/openvela/tools/release_validation.py /mnt/d/openvela/build/flyreflex_host --output /mnt/d/openvela/docs/evidence/final-release-synthetic.json
wsl -d Ubuntu-D -- python3 /mnt/d/openvela/tools/real_openvela_integration.py --port 10025 --output /mnt/d/openvela/docs/evidence/final-release-openvela-smoke.json
python skills/flyreflex-provenance/scripts/verify_provenance.py
python -X utf8 D:/openvela_official/.claude/skills/contest-log-collector/tools/validate-log.py logs/
```

受控测试时暂停网页，避免争用。非法 CLI 输入 STOP；快照超过 1500 ms STOP；真实 socket 断开应 HTTP 503。长时间 soak 与历史 benchmark 只作为对应旧固件证据，不能自动升级为本次结果。

LVGL 保持独立合成场景，不做 Browser–LVGL 实时同步。旧实例不属于最终推荐路径。录制与提交步骤见 FINAL_VIDEO_PREP.md。
