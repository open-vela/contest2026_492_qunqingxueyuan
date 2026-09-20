#!/usr/bin/env bash
# Isolated emulator artifacts: do not disturb an existing GUI instance.
set -euo pipefail
workspace="${1:?Usage: bash tools/run_web_emulator.sh /path/to/openvela-workspace}"
output="${FLYREFLEX_FIRMWARE_DIR:-$workspace/cmake_out/vela_goldfish-arm64-v8a-ap}"
demo_dir=$(mktemp -d /tmp/flyreflex-web-XXXXXX)
for file in nuttx .config vela_system.bin vela_data.bin; do
  cp --reflink=auto "$output/$file" "$demo_dir/$file"
done
printf 'Isolated emulator artifacts: %s\n' "$demo_dir"
cd "$workspace"
exec ./emulator.sh "$demo_dir" -no-window -ports "${FLYREFLEX_EMULATOR_PORTS:-5556,5557}" -grpc "${FLYREFLEX_GRPC_PORT:-8556}" -grpc-use-jwt
