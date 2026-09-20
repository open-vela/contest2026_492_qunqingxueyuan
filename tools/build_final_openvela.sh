#!/usr/bin/env bash
# Run inside a complete Linux/WSL official workspace, after repo sync and LFS pull.
set -e
workspace="${1:?Usage: bash tools/build_final_openvela.sh /path/to/official/workspace}"
cd "$workspace"
out=cmake_out/vela_goldfish-arm64-v8a-ap
board=vendor/openvela/boards/vela/configs/goldfish-arm64-v8a-ap
# Windows-hosted repo workspaces can materialize tracked shell scripts with
# CRLF. Normalize only scripts whose normalized blob exactly matches Git.
python3 contest2026_492_qunqingxueyuan/tools/normalize_tracked_scripts.py "$workspace"
printf 'BUILD_START_UTC=%s\n' "$(date -u +%FT%TZ)"
git -C contest2026_492_qunqingxueyuan rev-parse HEAD
git -C nuttx rev-parse HEAD
git -C packages/ai_agent rev-parse HEAD
# Upstream environment setup has nonzero optional probes.
set +e
source build/envsetup.sh
lunch "$board" "$out"
set -e
cmake -B "$out" -S nuttx -DBOARD_CONFIG="../$board/" \
  -DCUSTOM_MODULE_PATH="$PWD/build/cmake" \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
  -DEXTRA_FLAGS='-Wno-cpp -Wno-deprecated-declarations' -GNinja
bash contest2026_492_qunqingxueyuan/tools/configure_agent_guard.sh
jobs="${FLYREFLEX_BUILD_JOBS:-$(nproc)}"
cmake --build "$out" --clean-first -j"$jobs"
for file in nuttx .config vela_system.bin vela_data.bin; do
  test -s "$out/$file"
  sha256sum "$out/$file"
done
printf 'BUILD_END_UTC=%s\nBUILD_RESULT=PASS\n' "$(date -u +%FT%TZ)"
