#!/usr/bin/env bash
# Run from a configured openvela workspace. No credentials are handled here.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
config=cmake_out/vela_goldfish-arm64-v8a-ap/.config
test -f "$config"
test -f packages/ai_agent/src/tools/tool_shell.c
for patch in agent-guard-allowlist.patch agent-shell-error-lifetime.patch; do
  if git -C packages/ai_agent apply --check "$project_dir/tools/$patch" 2>/dev/null; then
    git -C packages/ai_agent apply "$project_dir/tools/$patch"
  else
    git -C packages/ai_agent apply --reverse --check "$project_dir/tools/$patch"
  fi
done
python3 "$project_dir/tools/refresh_demo_kconfig.py"
prebuilts/build-tools/linux-x86_64/bin/kconfig-tweak --file "$config" \
  --enable FLYREFLEX --enable EXAMPLES_AI_AGENT_VELA \
  --set-str EXAMPLES_AI_AGENT_VELA_DATA_DIR /data/agent \
  --enable EXAMPLES_AI_AGENT_VELA_SHELL_ALLOWLIST \
  --disable EXAMPLES_AI_AGENT_VELA_SHELL_FULL \
  --disable EXAMPLES_AI_AGENT_VELA_SHELL_DENY \
  --enable SYSLOG_CONSOLE --set-val MQ_MAXMSGSIZE 4096 \
  --enable SYSTEM_POPEN --enable SCHED_CHILD_STATUS \
  --disable AI_AGENT_FEISHU --disable AI_AGENT_WEIXIN --disable AI_AGENT_MQTT \
  --disable AI_AGENT_NODE --disable AI_AGENT_SKILL_SYNC \
  --disable LIB_FFMPEG
set +eu # Upstream setup uses optional variables and nonzero read terminators.
source build/envsetup.sh
lunch vendor/openvela/boards/vela/configs/goldfish-arm64-v8a-ap cmake_out/vela_goldfish-arm64-v8a-ap
set -e
workspace_dir="$PWD"
(cd nuttx && env KCONFIG_CONFIG="$workspace_dir/$config" \
  EXTERNALDIR=dummy DRIVERS_PLATFORM_DIR=dummy APPSDIR="$workspace_dir/apps" \
  APPSBINDIR="$workspace_dir/cmake_out/vela_goldfish-arm64-v8a-ap/apps" \
  BINDIR="$workspace_dir/cmake_out/vela_goldfish-arm64-v8a-ap" olddefconfig)
cmake -S nuttx -B cmake_out/vela_goldfish-arm64-v8a-ap
