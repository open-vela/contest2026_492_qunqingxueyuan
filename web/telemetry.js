// Wire validation only. Safety decisions always belong to the selected C runtime.
export function validateReply(value, mode, seq) {
  if (!value || value.source !== (mode === 'live' ? 'openvela' : 'host-reference') || value.seq !== seq)
    throw Error('source or sequence');
  for (const key of ['agent_a', 'agent_b', 'action'])
    if (!['FORWARD', 'ESCAPE', 'STOP'].includes(value[key])) throw Error('action');
  if (!['SAFE', 'CAUTION', 'DANGER', 'INVALID'].includes(value.state)) throw Error('state');
  for (const [key, max] of [['lplc2',1000],['lc4',1000],['gf',1200],['latency_ns',1e10]])
    if (!Number.isSafeInteger(value[key]) || value[key] < 0 || value[key] > max) throw Error(key);
  return value;
}
