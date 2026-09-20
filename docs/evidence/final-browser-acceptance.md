# Browser / openvela acceptance, 2026-09-19

Observed through the actual browser UI at `http://127.0.0.1:8090/`, backed by WSL Telnet target `127.0.0.1:10025`.

| Test | Observed result |
|---|---|
| Startup / safe | openvela live selected by default; OPENVELA CONNECTED; requested FORWARD, state SAFE, actual FORWARD |
| Default center shot | Actual retained target record: `openvela · seq=245: requested=FORWARD → actual=ESCAPE · state=DANGER` |
| Animation / outcome | Left: collision 1, avoidance 0. Right: collision 0, avoidance 1. Actual rendered scene inspected. |
| Stop the actual bridge process | OPENVELA DISCONNECTED, actual `PAUSED (通信失败)`, no current requested/state, `仿真已暂停 · 无有效目标动作` |
| Click fire while disconnected | Launch count remained 1; both outcome counters unchanged |
| Restart bridge and reconnect | OPENVELA CONNECTED, SAFE / FORWARD; launch and collision counters reset to 0 |

This is a manual UI acceptance record, not an automatic performance benchmark. Physics and agent delay are simulated. Runtime actions are target C results. The retained override is labeled historical; disconnection does not present it as a current action.

MiMo acceptance used the same target and the repository control producer with browser paused. `final-agent-tool-trace.txt` records `read_file` of the Guard Skill, execution of `run_shell`, and `popen(flyreflex guard issue_agent_command FORWARD) exit=0`. `final-agent-guard-runtime.txt` records the final model report of ESCAPE / REFLEX_OVERRIDE and independently queried real snapshots before and after the request. All new evidence was checked for an exact match of the privately loaded credential: 0 matches.
