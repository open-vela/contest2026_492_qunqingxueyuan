"""Fill only the technical-report portion of the official retained template."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from hashlib import sha256
from copy import deepcopy
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'docs/templates/technical-report.docx'
assert sha256(source.read_bytes()).hexdigest() == '94247bfe0ed960629b138108316dccdd2827761bbe9cc8d5fe48e1c78ad396a8'
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
q = lambda name: '{'+ns['w']+'}'+name
with ZipFile(source) as z:
    parts = {n: z.read(n) for n in z.namelist()}
root = E.fromstring(parts['word/document.xml'])
body = root.find('w:body', ns)
paras = body.findall('w:p', ns)
tables = body.findall('w:tbl', ns)

def fill(p, text, prose=False):
    run = p.find('w:r', ns)
    props = deepcopy(run.find('w:rPr', ns)) if run is not None and run.find('w:rPr', ns) is not None else None
    for child in list(p):
        if child.tag not in [q('pPr'), q('bookmarkStart'), q('bookmarkEnd')]:
            p.remove(child)
    if prose:
        for num in p.findall('w:pPr/w:numPr', ns):
            num.getparent().remove(num)
    r = E.SubElement(p, q('r'))
    if props is not None: r.append(props)
    for i, line in enumerate(text.split('\n')):
        if i: E.SubElement(r, q('br'))
        t = E.SubElement(r, q('t')); t.text = line

abstract = 'FlyReflex 面向 AI 控制设备的快速避险需求，在上层规划与执行动作之间加入本地安全反射。项目从 MaleCNS v1.0 提取 LPLC2、LC4 至 DNp01 的直接连接，将 4862 和 6362 个突触归一化为 433:567，形成整数泄漏聚合模型。C 核心在 openvela ARM64 模拟器中运行，通过安全仲裁覆盖危险前进指令，并提供 LVGL 与浏览器双场地演示。200 个合成场景中，100 个危险场景全部触发，100 个安全场景无误触发。本次模拟器 1000 次测试的事件到仲裁中位数为 2.256 微秒。结果不代表真实视觉识别率或实体 MCU 性能。'
assert len(abstract) <= 300
content = {
0: 'FlyReflex 技术报告',
7: abstract,
10: '项目背景与问题定义。具身智能设备可由上层智能体理解任务并规划动作，但网络请求和模型推理不能保证固定响应时间。当设备继续执行前进指令而障碍物快速靠近时，安全动作需要在本地独立产生。本项目验证这条安全路径，不将模拟器中的碰撞演示等同于真实机器人安全认证。',
11: '技术难点。第一，必须追溯神经连接来源，避免把人为调整的阈值称为生物测量。第二，反射计算需要确定性执行，并且能够覆盖上层指令。第三，交互演示必须保持左右场地条件一致，断开数据连接后不能继续展示伪实时结果。',
12: '创新点。作品将可追溯的果蝇连接统计、轻量整数反射模型和嵌入式安全仲裁结合。双场地接收相同攻击输入，观众可以主动改变方向、蓄力和速度，观察延迟控制与加入本地反射后的差异。三节点是细胞群聚合，不是三个真实细胞，也不是完整果蝇大脑仿真。',
14: '系统分为三层。openvela 内运行反射引擎、安全仲裁、状态快照、NSH 命令和 LVGL 图形界面。主机 Python bridge（通信桥）负责协议转换和连接管理。浏览器负责场景几何、交互与渲染，安全决策使用 C 核心返回值。\n浏览器交互 → 主机通信桥 → openvela C 核心 → 仲裁结果 → 通信桥 → 浏览器\n本地输入 → LPLC2 / LC4 聚合 → DNp01 / GF 聚合 → Safety Arbiter（安全仲裁器）\n上层 Agent 指令 ────────────────────────────────→ 安全仲裁器',
15: '方案选型。MVP 使用官方 goldfish ARM64 模拟器，以便在比赛周期内验证算法、系统集成和可重复构建。直接采用复杂视觉规划会扩大计算和标定范围；仅用云端模型则不能提供独立本地安全路径。MiMo 只承担高层语义和工具调用，不参与逐帧反射计算。断网不会使云端请求进入反射计算路径；Guard 快照过期时返回 STOP。',
16: '关键模块。FR2 控制协议按帧传入两侧输入并返回决策；通信桥串行管理 C 进程或模拟器会话。两侧使用相同物理步长、碰撞半径和执行器规则。左侧采用明确标记的 Agent 延迟模型，右侧增加即时反射。该延迟是工程仿真参数，不是 MiMo 的实测推理耗时。',
18: '反射模型。输入是归一化至 0–1000 的角尺寸代理量与扩张速度代理量。加权驱动为两路活动乘以 433 和 567 后除以 1000，按整数截断。下一时刻膜状态为上一状态乘以 350 后除以 1000，再加驱动，上限 1200。低于 300 为 SAFE，300–849 为 CAUTION，达到 850 为 DANGER。该模型是离散泄漏聚合模型，不声称复现真实神经元放电动力学。\n科学来源。MaleCNS v1.0 查询得到 LPLC2→DNp01 4862 个突触、185 个细胞对；LC4→DNp01 6362 个突触、126 个细胞对。归一化规则为各类计数除以 11224，再乘 1000 四舍五入。连接、body ID、查询语句和原始响应保存在 data/connectome/。阈值、泄漏、输入编码及动作映射均为 ENGINEERING_PARAMETER。',
19: '安全仲裁。SAFE / CAUTION 时允许普通 AI 指令；DANGER 时 ESCAPE 覆盖 FORWARD，输出 REFLEX_OVERRIDE。非法输入按失效状态输出 STOP。Guard 请求同样进入该仲裁器，不能直接驱动执行器，也不能修改阈值。快照超过 1500 ms 或不存在时返回 INVALID 和 STOP。\n云端接口。采用小米 MiMo 的兼容接口，通过鉴权请求执行高层工具调用。订阅密钥使用 Token Plan 专用地址。密钥由本地隐蔽输入提供，不进入源码、报告或证据文件。当前真实 Agent 调用尚在验收，不能把接口实现等同于调用成功。',
20: 'openvela 能力。已落地图形能力：LVGL 与 framebuffer 展示神经活动、风险状态及仲裁结果。C 核心作为 NSH 内建应用交叉编译，使用单调时钟测量计算区间，并通过任务运行环境执行。AI Agent 作为独立模块接入 Guard。未修改 NuttX 内核，也未声称完成新硬件驱动适配。建议后续提供标准化安全仲裁接口和带时间戳的结构化遥测能力。',
22: '软件架构。app/flyreflex 存放 C 应用；tools 存放通信桥、提取脚本及验收工具；web 存放 Three.js 交互演示；runtime_skills 存放运行时 Skill；data 分离原始连接数据、处理结果和工程参数；tests 与 docs/evidence 保存测试和证据。正式 manifest 将赛事仓应用映射到 packages/demos/contest2026_492_flyreflex。',
23: '关键流程。\n接收输入 → 检查范围 → 更新两路活动与 GF 状态 → 判断危险 → 仲裁 AI 指令 → 输出最终动作\n输入非法 → STOP；通信断开 → 冻结实时演示并提示连接丢失；快照过期 → Guard 返回 STOP。\n主机演示模式使用本地主机 C 参考实现并明确标记。连接 openvela 时由模拟器中的 C 应用作出安全判断。',
24: '硬件设计与适配。本届 MVP 使用官方 simulator，未制作新 PCB / 实体硬件，未连接真实摄像头或电机，没有物料清单和实物接线。未完成全新硬件平台适配或驱动开发。后续迁移需要重新验证采集延迟、执行器制动能力、时序和功耗。',
25: '交互端。浏览器以暖灰背景和双场地对比展示控制效果。用户后拖蓄力、选择方向后发射障碍球，可改变速度和加速度，发射数量没有人为弹药上限。采用连续碰撞检测，避免高速粒子穿透。未瞄准核心的攻击不进入躲避成功率统计，两侧接收同一攻击序列。LVGL 保留 SAFE、SLOW、DANGER、RECOVERY 场景入口。',
26: '自定义 Skill。FlyReflex Guard 定义于 runtime_skills/flyreflex-guard.md，部署路径为 /data/agent/skills/flyreflex-guard.md。触发语句包括“查询安全状态”和“向前移动”。run_shell 只额外允许精确的查询命令和 FORWARD 仲裁请求；不开放任意 FlyReflex 子命令。危险请求仍返回 ESCAPE，过期请求返回 STOP。当前已验证底层 Guard 接口，Agent 自主加载与触发的端到端证据尚未完成。',
27: '3.5 系统测试与结果分析',
28: '测试环境。2026 年 9 月 18 日在 Windows 主机及 WSL Linux 工作区进行测试，目标为 openvela goldfish ARM64 官方模拟器。本地候选代码尚未冻结，远端已提交版本与候选版区分记录于 docs/FINAL_ACCEPTANCE.md。独立官方仓同步完成，最终候选版 clean clone 全流程仍须复验。',
29: '功能测试。C 核心 CTest 1/1、前端 Node 测试 9/9、Python 通信桥测试 3/3 通过。覆盖安全输入、快速逼近、指令覆盖、恢复、非法输入、确定性、高速碰撞、同输入一致性和断线状态。模拟器输出可观察 DANGER、AI=FORWARD、REFLEX=ESCAPE、FINAL=ESCAPE、REFLEX_OVERRIDE；恢复后回到 AI 控制。原始运行记录见 docs/evidence/target-runtime.txt。',
30: '性能测试。以下为本次 openvela ARM64 simulator measurement，单位为 ns，样本数 1000。\n指标                         min / mean / median / P95 / P99 / max\nreflex_compute       1232 / 1518 / 1264 / 1296 / 2528 / 112512\nevent_to_arbiter      2224 / 2791 / 2256 / 2304 / 5296 / 179120\n计时不包含摄像头采集、网络、浏览器渲染和电机响应，也不是 MCU 实机时延。UI 单次采样与批量 benchmark 分布不同，不能直接比较一个单帧数值与中位数。功耗：Not measured — simulator-only prototype。尚无最终版本的资源占用趋势数据。',
31: '可靠性测试。SYNTHETIC SCENARIO VALIDATION 使用固定随机种子 492，包含 100 个危险和 100 个安全场景，每场景 20 帧。正确触发 100、误触发 0、漏触发 0，触发率 100%、误触发率 0%、漏触发率 0%。测试范围是人工定义的合成输入族，不冒充真实视觉准确率。非法输入、过期状态的兜底动作为 STOP，但不能保证模型对未覆盖输入的泛化能力。尚未完成 30 分钟连续运行和内存增长验证，不宣称达到安全认证或量产可靠性。',
33: 'AI 辅助用于代码实现、数据提取脚本、测试设计和材料整理。人工负责目标设定、演示交互要求和结果确认。开发中通过测试发现并处理分支历史不一致、构建路径依赖和实时数据来源标识等问题。未建立无 AI 对照工时，因此不声称节省了特定百分比。真实 Coding 日志按官方导出流程另行提交，不手工伪造会话。',
35: '成果总结。已形成可追溯连接数据、整数 C 反射核心、安全仲裁、openvela 图形演示和浏览器交互对比。现有实验支持在模拟输入条件下通过本地反射覆盖危险前进指令。发布前仍需完成 Agent 端到端验证、最终独立构建、正式日志和演示视频验收。',
36: '应用前景。目标用户是移动机器人、教育机器人和具身设备的研发团队，使用场景是上层规划不能保证固定响应时延的设备。后续可提供嵌入式安全组件、适配与验证服务。当前没有商业订单、市场规模调查或量产成本实测，不将潜在用途写成已实现收入或市场份额。',
37: '不足与未来工作。现阶段输入是几何代理量，缺少真实摄像头、真实执行器和硬件时序测试。三节点聚合丢失了细胞级差异，突触数量也不等同于生理突触效能。后续需要采集实测数据、标定误报和漏检、验证极端输入、开展长时间运行与功耗测试，并在独立 MCU / SoC 平台上重新测量整个传感到动作链路。科学依据与数据追溯见 docs/SCIENTIFIC_BASIS.md 和 docs/DATA_PROVENANCE.md；软件遵循 Apache-2.0，第三方和数据许可见 THIRD_PARTY_NOTICES.md。'
}
# Replace prior draft results with the verified 19 September candidate results.
content[7] = abstract.replace('2.256', '2.320')
content[11] = '技术难点。连接来源必须可追溯，工程阈值不能冒充生物测量。反射计算必须覆盖危险指令。双场地条件应一致，断线后必须停止展示实时结果。'
content[14] = content[14].replace('上层 Agent 指令 ────────────────────────────────→ 安全仲裁器', '上层 Agent 指令 → 同一安全仲裁器 → 最终动作')
content[23] = content[23].replace(' → 仲裁 AI 指令 → 输出最终动作', '\n危险状态与 AI 指令 → 安全仲裁 → 输出最终动作')
content[19] = content[19].replace('当前真实 Agent 调用尚在验收，不能把接口实现等同于调用成功。', '已在模拟器中实测 MiMo 读取 Guard Skill 并调用前进接口，工具退出码为 0；危险时最终命令为 ESCAPE，Agent 正确报告安全接管。该次三轮模型请求与两次工具调用合计约 18 秒，不属于反射延迟。')
content[26] = content[26].replace('当前已验证底层 Guard 接口，Agent 自主加载与触发的端到端证据尚未完成。', '2026 年 9 月 19 日已验证真实 Agent 读取 Skill、调用 run_shell、接收仲裁结果并报告 ESCAPE。调用前后 NSH 快照均为新鲜危险状态。证据见 docs/evidence/agent-guard-serial.txt 与 agent-guard-runtime.txt。')
content[26] = content[26].replace('证据见 docs/evidence/agent-guard-serial.txt 与 agent-guard-runtime.txt。', '串口记录与调用前后快照保存在 docs/evidence/。')
content[28] = '测试环境。2026 年 9 月 18 至 19 日在 Windows 主机及 WSL Linux 工作区验证，目标为 openvela goldfish ARM64 模拟器。独立 repo init/sync 后覆盖本地候选应用，补齐官方 Git LFS 库并完成交叉构建和启动。代码尚未冻结到远端发布提交，不能称为最终远端 clean clone 验收。构建散列及配置见 docs/evidence/agent-build-provenance.md。'
content[29] = content[29].replace('target-runtime.txt', 'agent-firmware-runtime.txt')
content[30] = '性能测试。修复后的 Agent 候选固件在 openvela ARM64 模拟器内测量 1000 次，单位为 ns。\n指标                         min / mean / median / P95 / P99 / max\nreflex_compute       1232 / 1439 / 1280 / 1360 / 2816 / 50368\nevent_to_arbiter      2224 / 2757 / 2320 / 2448 / 5312 / 126992\n计时不包含摄像头、网络、浏览器渲染和电机响应，不是实体 MCU 时延。UI 单帧与批量基准属于不同采样。功耗未测量，目前仅为模拟器原型。原始输出见 docs/evidence/agent-firmware-runtime.txt。'
content[31] = content[31].replace('尚未完成 30 分钟连续运行和内存增长验证，不宣称达到安全认证或量产可靠性。', '旧候选固件完成 1801.61 秒、586 轮危险与恢复检查，59 次堆采样的已用空间均为 1810784 字节。新版 Agent 固件的长时间测试另行记录；旧结果不能替代新版或浏览器桥接稳定性验收。不宣称达到安全认证或量产可靠性。')
content[31] = content[31].replace('旧候选固件完成 1801.61 秒、586 轮危险与恢复检查，59 次堆采样的已用空间均为 1810784 字节。新版 Agent 固件的长时间测试另行记录；旧结果不能替代新版或浏览器桥接稳定性验收。', '新版 Agent 候选固件完成 1800.28 秒、589 轮危险与恢复检查，59 次堆采样的已用空间均为 2361248 字节。该测试覆盖模拟器命令行场景与堆占用，不等同于浏览器桥接长期稳定性验证。')
content[33] = content[33].replace('真实 Coding 日志按官方导出流程另行提交，不手工伪造会话。', '当前缺少官方工具导出的原始 Coding 日志，该项提交要求尚未满足；运行日志不能代替开发会话。')
content[35] = '成果总结。已完成可追溯连接数据、整数 C 反射核心、安全仲裁、openvela 图形演示和浏览器交互对比，并验证真实 MiMo Agent 通过 Guard Skill 请求前进后被本地危险状态覆盖为 ESCAPE。现有结果限于模拟输入与模拟动作。正式发布仍缺最终版本冻结与完整回归、官方开发日志、演示成片和提交包验收。'
# Final release content is explicitly separated from historical measurements.
content[7] = 'FlyReflex 面向 AI 控制设备的快速避险需求，在上层规划与动作之间加入 openvela 本地安全反射。MaleCNS v1.0 的 LPLC2、LC4 至 DNp01 连接计数为 4862、6362，形成 433:567 结构权重。浏览器经 HTTP bridge 与 Telnet 调用真实 C 核心，危险时把 FORWARD 覆盖为 ESCAPE；MiMo 经 ai_agent、Guard Skill 和 run_shell 使用同一仲裁层。200 个合成场景中危险触发 100/100，安全误触发 0/100。世界与 Agent 延迟为仿真，安全决策在 openvela 执行；结果不代表真实相机、机器人或 MCU 性能。'
content[14] = '系统分三层：openvela 内运行整数 C 反射、安全仲裁、Guard 快照及 LVGL；宿主机 Python bridge 转发协议；浏览器生成合成输入并呈现返回动作。\nBrowser → HTTP POST /step → Python bridge → Telnet / NSH → flyreflex control → C reflex / arbiter → FR2 JSON → Browser\nMiMo → ai_agent → Guard Skill → run_shell → flyreflex guard → 同一 C arbiter'
content[16] = '浏览器每个 25 ms 仿真步等待目标 C 应答后才推进物理。页面显示 requested FORWARD 与 actual ESCAPE，校验 source=openvela 和序号。通信失败显示 OPENVELA DISCONNECTED 与 PAUSED，不继续推进或累计成功；重连清空统计。左侧 Agent 延迟为工程仿真，不是 MiMo 的真实推理耗时。LVGL 是独立的本地合成场景，不与浏览器场景实时同步。'
content[26] = '运行时自定义 Skill 为 runtime_skills/flyreflex-guard.md，部署至 /data/agent/skills/flyreflex-guard.md。真实 MiMo 工具证据包含读取 Skill、run_shell、Guard 返回、exit=0 与最终 ESCAPE 覆盖回答。开发期 skills/flyreflex-provenance 用于校验 311 条直连边与结构权重，两类 Skill 用途不同。'
content[28] = '最终构建状态与源码版本由 docs/FINAL_RELEASE_REPORT.md 和 docs/evidence/final-clean-build.txt 记录。正式工作区为 D:/openvela_official，Linux 工具链运行在 WSL Ubuntu-D；最新赛事源码通过 Git 提交进入独立构建分支，不以旧临时 nuttx 代替新构建。ai_agent 需要赛事仓公开的 allowlist 与错误分支生命周期补丁，由 configure_agent_guard.sh 重放；补丁尚未进入公共上游，不隐瞒此依赖。'
content[29] = '本次重新执行：C core 1/1 PASS，Browser 10/10 PASS，Python bridge 4/4 PASS，Skill provenance PASS；固定 seed=492 的合成场景 danger 100/100 触发，safe 0/100 误触发。Browser 测试覆盖遥测来源、非法帧与序号拒绝。真实目标测试检查 SAFE/FORWARD、DANGER 下 FORWARD→ESCAPE、非法输入 STOP、Guard 过期 STOP、socket 断开 HTTP 503。真实目标最终重测结果以发布报告为准，不能把历史 PASS 自动当作新固件 PASS。'
content[30] = '历史候选固件 benchmark，1000 次，单位 ns：reflex_compute median/P95/P99 = 1280/1360/2816；event_to_arbiter = 2320/2448/5312。该组数据来自 agent-firmware-runtime.txt，非本次新固件测量。计时仅覆盖事件处理到 C 仲裁，不含摄像头、网络、浏览器或电机；不代表 MCU 性能。若本次复测完成，新数据单独记录于 final-release-target-runtime.txt，不混合两组分布。'
content[31] = '可靠性边界。历史 Agent 候选固件曾完成 1800.28 秒、589 轮危险与恢复检查，59 次堆采样一致；这不是本次新固件长时间测试，也不等同于 Browser bridge 长时间运行验证。非法输入和超过 1500 ms 的 Guard 快照返回 STOP；断线时浏览器暂停并清除当前有效动作。无生产安全认证与量产可靠性主张。'
content[33] = 'AI Coding 实际主要使用 Codex，辅助实现、测试、数据提取与材料；运行时高层模型是 Xiaomi MiMo，二者职责不同。初始两 session 已透明转换为 2080 条赛事事件，官方 validator ALL OK，凭据扫描 PASS。原始 rollout SHA256 保留，source 未修改；新格式兼容限制和脱敏记录公开。最终 release 会话将在关闭后由 finalize_last_codex_session.py 追加，不提前声称全部日志完成。未做逐行贡献或无 AI 对照工时统计。'
content[35] = '成果总结。已形成可追溯连接数据、整数反射模型、C 仲裁、真实 openvela Browser 闭环与 MiMo Guard 工具链。最终发布验证见 FINAL_RELEASE_REPORT.md；视频由成员手动录制，源码与 AI Coding logs 放赛事仓，技术报告与不超过 5 分钟视频组成提交 ZIP。最终 PR 合并和官网提交由参赛者完成。'
for i, text in content.items(): fill(paras[i], text, i not in [0,27])
info = ['FlyReflex 基于真实果蝇连接组的嵌入式安全反射层','群青学院','李孝淼：总体方案、核心开发、系统集成、测试验证及提交材料整理。\n王鹏舜：参与部分 UI 设计和验收测试。','AI 硬件产品创新方向的端侧安全反射原型']
ai = ['未做逐行归属统计，不填写未经核实的百分比。','Codex / ChatGPT，辅助代码、测试和文档工作。','使用浏览器自动化及文件工具进行演示检查；未使用 VelaJS MCP 或 Figma MCP。','开发期 provenance 校验 Skill；运行时 FlyReflex Guard Skill；文档与 PDF 技能用于报告制作。','跨账号开发总量未完整统计。MiMo 调用用量单独记录，不以单次用量代替开发总量。']
for table, values in [(tables[2],info),(tables[3],ai)]:
    for row in table.findall('w:tr',ns):
        rowprops = row.find('w:trPr', ns)
        if rowprops is None: rowprops = E.SubElement(row,q('trPr'))
        E.SubElement(rowprops,q('cantSplit'))
    firstprops = table.find('w:tr/w:trPr', ns)
    E.SubElement(firstprops,q('tblHeader'))
    for row, value in zip(table.findall('w:tr',ns)[1:], values):
        cell = row.findall('w:tc',ns)[1]
        p = cell.find('w:p',ns)
        fill(p,value)
        for extra in cell.findall('w:p',ns)[1:]: cell.remove(extra)
for i in [1,2,3,4,*range(38,46)]: body.remove(paras[i])
for i in [0,1,4]: body.remove(tables[i])
for i in [5,6,8,9,13,17,21,27,32,34]:
    props = paras[i].find('w:pPr', ns)
    E.SubElement(props,q('keepNext'))
    E.SubElement(props,q('keepLines'))
E.SubElement(paras[11].find('w:pPr', ns), q('keepLines'))
parts['word/document.xml'] = E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
target=ROOT / 'submission/FlyReflex_技术报告.docx'
with ZipFile(target,'w',ZIP_DEFLATED) as z:
    for name, data in parts.items(): z.writestr(name,data)
with ZipFile(source) as a, ZipFile(target) as b:
    assert all(a.read(n)==b.read(n) for n in a.namelist() if n!='word/document.xml')
print('Created report candidate; source and preserve-only parts unchanged.')
