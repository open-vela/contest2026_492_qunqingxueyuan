# FlyReflex Guard

## When to use
Use when the user asks for FlyReflex safety status, or asks the simulated
device to move forward. Trigger examples: 查询安全状态; 当前有危险吗; 向前移动。

## query_flyreflex_status
Use run_shell to execute `flyreflex guard query_flyreflex_status`.
Report the returned state, risk (engineering GF activity, not probability),
reflex, final command and freshness. A stale or missing snapshot is INVALID
and STOP. Never infer SAFE from an absent response.

## issue_agent_command
Only FORWARD is supported. Execute
`flyreflex guard issue_agent_command FORWARD` with run_shell.
The C Safety Arbiter always processes the request. If it returns ESCAPE,
report safety override; do not retry to force FORWARD. Never call an actuator
directly, change thresholds, reset the engine or override the returned command.

## Boundaries
This simulator prototype has no physical actuator. A returned final command
is not proof of physical movement. Status is the most recent sample from
the openvela FlyReflex demo, UI, stream or control process in this boot.
Snapshots older than 1.5 seconds fail closed. Commands need to be permitted
by the device shell security policy; if denied, report it rather than
weakening the security policy. Cloud inference is not in the safety path.

Install this file as `/data/agent/skills/flyreflex-guard.md`.
