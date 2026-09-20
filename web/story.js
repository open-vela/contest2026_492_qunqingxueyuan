// Presentation state only. No thresholds, neuron integration or arbitration.
export function describe(sample, escaped = false) {
  if (!sample) return ['OBSERVING', '安静地，观察。', '机器人向前移动，安全反射在本地持续运行。', 0];
  if (sample.action === 'STOP') return ['FAILSAFE', '输入异常，安全停止。', '本地安全层输出停止指令。', 3];
  if (sample.action === 'ESCAPE') return ['ACTION', '先于思考，避让。', 'AI 仍要求前进；openvela 的安全仲裁选择了躲避。', 3];
  if (escaped && sample.state === 'SAFE') return ['SAFE', '危险远去，恢复平静。', '安全层交还控制权，机器人恢复前进。', 4];
  if (sample.state === 'CAUTION') return ['VISUAL INPUT', '看见，正在逼近。', '大小与扩张速度通道响应，信号汇入逃逸节点。', 1];
  return ['OBSERVING', '安静地，观察。', '机器人向前移动，安全反射在本地持续运行。', 0];
}

export function livePacketValid(packet) {
  const s = packet?.sample;
  return packet?.connected === true && s?.source === 'openvela' && s.schema === 1 &&
    ['SAFE', 'CAUTION', 'DANGER', 'INVALID'].includes(s.state) &&
    ['FORWARD', 'ESCAPE', 'STOP', 'LEFT', 'RIGHT', 'IDLE'].includes(s.action) &&
    ['size','rate','lplc2','lc4','gf','frame','count','seq','cycle','latency_ns'].every(k => Number.isFinite(s[k]));
}

export function replayIndex(seconds, count) {
  // Opening 1.0 s, original samples at 0.4 s, closing pause 1.8 s.
  const duration = 1 + count * .4 + 1.8;
  const local = seconds % duration;
  return {index: Math.min(count - 1, Math.max(0, Math.floor((local - 1) / .4))),
    progress: local / duration, cycle: Math.floor(seconds / duration), opening: local < 1};
}
