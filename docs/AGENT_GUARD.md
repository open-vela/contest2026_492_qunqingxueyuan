# FlyReflex Guard 接入与验收

历史最终集成阶段的模拟器端到端调用已通过：MiMo 读取 Skill，调用前进请求，收到 ESCAPE 并报告安全接管。串口证据见 `evidence/final-agent-tool-trace.txt`，调用前后快照及回答见 `evidence/final-agent-guard-runtime.txt`。这不代表最终远端发布或实体机器人已验收，完整状态见 [最终发布验收](FINAL_RELEASE_REPORT.md)。

## 配置

在已完成 CMake 初始配置的 openvela 工作区执行：

```sh
bash contest2026_492_qunqingxueyuan/tools/configure_agent_guard.sh
./build.sh vendor/openvela/boards/vela/configs/goldfish-arm64-v8a-ap/ --cmake -j4
```

脚本保持 Agent 的 allowlist（白名单）模式，仅对两条完全匹配的命令放行：

```text
flyreflex guard query_flyreflex_status
flyreflex guard issue_agent_command FORWARD
```

补丁存于赛事仓 `tools/agent-guard-allowlist.patch`，在工作区应用到 `packages/ai_agent`，不改上游仓历史。不允许 LLM 调用 demo/reset/任意控制命令。生成的 Kconfig 索引会刷新，避免 manifest 新增应用未被旧索引收录。

`tools/agent-shell-error-lifetime.patch` 修复上游 shell 工具错误分支的释放后读取：命令字符串属于 cJSON 对象，必须在格式化错误后再释放对象。保留 KASAN 内存检测。配置启用 `SYSTEM_POPEN` 和 `SCHED_CHILD_STATUS`，以支持命令执行并保留子任务退出状态；不能忽略非零退出码强行返回成功。

独立工作区遇到 `libgui_wrapper.a: file format not recognized` 时，先检查该文件是否为 Git LFS 指针。库属于独立的 `vendor/openvela/boards/vela/libs` 仓库，不是父级 `vendor/openvela` 仓库。执行 `git -C vendor/openvela/boards/vela/libs lfs pull` 下载真实库。重新打开终端后，先 `source build/envsetup.sh` 并 `lunch vendor/openvela/boards/vela/configs/goldfish-arm64-v8a-ap cmake_out/vela_goldfish-arm64-v8a-ap`，再调用 `cmake --build`，否则可能找不到预置 ccache。

## 密钥与模型

小米官方说明区分按量计费和 Token Plan 订阅密钥：前者使用 `api.xiaomimimo.com`，订阅密钥使用 `token-plan-cn.xiaomimimo.com`。本次使用 `mimo-v2.5`。参考 [官方首次调用说明](https://mimo.mi.com/docs/en-US/quick-start/summary/first-api-call)。

`python tools/check_mimo.py` 通过隐藏输入读取密钥，只保存模型、状态、耗时和使用量。`python tools/test_agent_guard.py --port 10024` 用于专门验收实例，隐藏读取密钥并过滤记录中的凭据。不要在公共录屏中输入密钥，不要提交模拟器数据盘或 Agent config/session 文件。测试请求会消耗少量订阅额度。

## 安全边界

Skill 文件部署在 `/data/agent/skills/flyreflex-guard.md`。FORWARD 请求仍由 C 安全仲裁器处理。新鲜危险快照必须返回 ESCAPE，缺失或超过 1500 ms 的快照必须返回 STOP。该接口仅模拟动作，不驱动真实硬件。

云端请求可耗时数秒，因此验收时由独立本地输入流持续更新状态，不能延长快照有效期来掩盖过期输入。测量云端调用与微秒级反射计时必须分别记录。
