# Agent candidate build, 2026-09-19

- Result: ARM64 build and simulator boot PASS; not a frozen remote release.
- Workspace: independent repo init/sync plus local candidate `app/flyreflex` overlay.
- Contest baseline: `484ad052c1fdf4e2a098a24ae4e07c3bd4f2ee7a`.
- Upstream ai_agent: `e65550f18759f086d7f544edcf17d1e31223244f` plus the two patches documented in `../AGENT_GUARD.md`.
- Upstream binary libraries: `737880db2d25109811e240d11de6c7e6de3f8cb6`; actual Git LFS objects downloaded from its configured official remote.
- `nuttx` SHA-256: `f9208d854b9ca5b93ec80af27b1dde53ef042472eb46ebe591b547fb1e0bbcd2`.
- Enabled: FLYREFLEX, EXAMPLES_AI_AGENT_VELA, SYSTEM_POPEN, SCHED_CHILD_STATUS, SYSLOG_CONSOLE; MQ_MAXMSGSIZE=4096. Shell remains exact-command allowlist; KASAN remains enabled.
- Build: `source build/envsetup.sh`; `lunch vendor/openvela/boards/vela/configs/goldfish-arm64-v8a-ap cmake_out/vela_goldfish-arm64-v8a-ap`; `cmake --build cmake_out/vela_goldfish-arm64-v8a-ap -j4`, exit 0.
- Runtime: `agent-firmware-runtime.txt`; real Skill call: `agent-guard-runtime.txt` and `agent-guard-serial.txt`.

The successful trace reads the deployed Skill, calls `run_shell` with the exact
FORWARD request, records `popen` exit 0 and 219 output bytes, and reports the
arbiter's ESCAPE/DANGER/REFLEX_OVERRIDE result. Direct NSH snapshots before and
after the request confirm fresh danger. The input stream continuously supplied
synthetic danger; this is not physical sensing or movement.

Trace total elapsed is 18 seconds (three model requests, two tools), not the
microsecond core-reflex latency. Model: MiMo mimo-v2.5, Token Plan endpoint.
The transcript is simulator runtime evidence, not an official AI Coding log.

Failures retained separately: `agent-pclose-diagnostic.txt` records command
output with exit -1 before child exit-state retention was enabled. An earlier
error branch caused a KASAN use-after-free assertion; the patch moves cJSON
deletion after formatting the error. No failure is counted as a pass.
