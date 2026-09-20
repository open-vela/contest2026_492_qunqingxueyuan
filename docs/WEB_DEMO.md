# 交互避障对比

## 启动

先在 Linux / WSL 按 README 编译 `build/flyreflex_host`。本机演示也运行 C 核心，不再播放固定样本。

```powershell
npm ci --prefix web
python tools/web_bridge.py
```

打开 <http://127.0.0.1:8088>。Windows 桥接通过默认 WSL 发行版运行本项目的 `build/flyreflex_host control`；可用环境变量 `FLYREFLEX_WSL_DISTRO` 指定发行版。Linux 直接启动同一二进制。依赖安装后无需 CDN。

## 操作

- 在任意一侧距中心至少 1 m 的场地按住，向发射方向的反方向拖动，松开发射。两侧生成完全相同的障碍球。
- 拖动距离增加初速度，界面显示合成后的发射速度；速度、加速度作用于后续发射。
- 可连续发射，不设弹药数量上限。已碰撞/飞出两侧场地的球自然回收，不积累离场对象。
- 「向中心发射」提供固定位置的快捷发射；场地获得键盘焦点后空格也可发射。
- Agent 延迟在首次发射后锁定，清空后可调整，防止统计混用不同延迟。
- 清空和数据源切换会清除场景、核心积分状态及统计。

## 对比定义

左侧是 Agent **延迟模型**，不是 LLM。两侧使用相同 C 风险检测器；模型指令进入同样的延迟队列。右侧额外使用原有 `flyreflex_arbitrate` 安全仲裁，允许当前反射立即接管。延迟参数是人为实验条件，不能代表真实大模型性能。

两侧核心半径 0.34 m、障碍球半径 0.16 m、移动上限 3.6 m/s、活动范围半径 2.4 m 相同。ESCAPE 映射为来球方向的垂直运动；两侧使用同一运动代码。Agent 的方向信息也取延迟前样本，防止使用未来信息。多方向攻击只选择最紧迫威胁，不是全局最优路径规划。

浏览器根据威胁球距离与速度生成 0–1000 的角大小/扩张速度代理量：`size = clamp(650 / distance)`，`rate = clamp(220 * speed / distance²)`。这是本演示的几何编码，不是摄像头处理或生物测量。C 核心原有权重、泄漏、阈值、三节点结构不变。

固定仿真步长 25 ms，每步等待 C 核心应答后才推进两侧物理。通信开销只降低整体仿真播放速度，不会给某侧引入额外仿真延迟。暂停时不推进物理。断线立即停止推进，显示 DATA CONNECTION LOST；重新连接会清空本次试验，不跨断线续算成功率。

## 成功率

只统计发射时轨迹会经过原点核心范围的球，避免随意射偏拉高成功率。对每个合格球、每一侧：碰撞记失败，飞出半径 7 m 场地且未碰撞记成功。成功率为 `成功 / (成功 + 碰撞)`，在途球不计分。使用相对运动线段扫掠碰撞，防止高速球跨帧穿透。

同时发射时核心可能已离开原点，因此这是固定靶心攻击下的仿真统计，不是严格的实机成功率评测。未瞄准原点的球仍参与传感和碰撞，只不进入统计。双方都可以失败，不预设优胜方。

## 实时 openvela

编译包含 `flyreflex control` 的固件。在 openvela 工作区根目录启动独立模拟器：

```bash
bash contest2026_492_qunqingxueyuan/tools/run_web_emulator.sh "$PWD"
```

NSH 中：

```text
ifconfig eth0 10.0.2.15 netmask 255.255.255.0
ifup eth0
```

若启动日志没有 telnetd，则执行 `telnetd`。按 Ctrl+A 再按 C 进入 QEMU 控制台：

```text
hostfwd_add tcp:127.0.0.1:10023-:23
```

网页选择「openvela 实时」。桥接自动启动交互控制命令。脚本使用独立临时固件目录与 5556/5557、8556 端口；不影响原有 GUI 实例。NSH/Telnet 仅用于本机开发，不要向公网开放。关闭本次实例可在其 QEMU 控制台输入 `quit`。

## 通信

`POST /step` → 本机桥接 → `flyreflex control` → 原有 C 引擎与仲裁 → JSON 应答。一个桥接服务同时运行一个比较会话，多标签页争用会导致旧会话停止而非悄悄续算。

输入行 `seq reset delay_ticks size_a rate_a size_b rate_b`，其中 delay_ticks 为 0–40。命令返回 `FR2 READY` 后才可输入；`quit` 退出。每帧返回 `FR2` JSON，字段包括 source、seq、agent_a、agent_b、action、lplc2、lc4、gf、state、latency_ns。source 区分 openvela 与 host-reference；桥接检查序号和来源。原来的 FR1 stream 与 LVGL 界面仍可独立使用，但新对比页面不消费 FR1 回放。

## 验证

```text
npm test --prefix web
python -m unittest discover -s tests -p test_web_bridge.py
ctest --test-dir build --output-on-failure
```

前端测试包括真实主机 C 子进程闭环：默认球的碰撞/躲避、零延迟两侧一致、密集多方向攻击下反射侧也会失败、非法输入安全停止，以及高速扫掠碰撞、射偏不计分、300 球无弹药限制和相同执行器行为。

人工验收：拖动瞄准箭头两侧一致、连续发射、暂停/清空、速度/加速度、手机布局。实时断线测试在 QEMU 控制台用 `set_link mynet off`，恢复用 `set_link mynet on`，然后点网页「重新连接」。
