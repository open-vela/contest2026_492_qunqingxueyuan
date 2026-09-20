import test from 'node:test';
import assert from 'node:assert/strict';
import {validateReply} from '../telemetry.js';
test('reject malformed, stale and host telemetry in live mode',()=>{
  const sample={source:'openvela',seq:7,agent_a:'FORWARD',agent_b:'FORWARD',action:'ESCAPE',state:'DANGER',lplc2:1000,lc4:1000,gf:1000,latency_ns:1000};
  assert.equal(validateReply(sample,'live',7),sample);
  for(const patch of [{source:'host-reference'},{seq:6},{action:'unknown'},{state:null},{gf:true},{agent_a:null}])
    assert.throws(()=>validateReply({...sample,...patch},'live',7));
});
