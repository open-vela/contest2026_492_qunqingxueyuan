import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {fileURLToPath} from 'node:url';
import {makeWorld,launch,sense,advance} from '../physics.js';
test('C control comparison: default shot, zero-delay parity, multi-angle input',async()=>{
  const path=fileURLToPath(new URL('../../build/flyreflex_host',import.meta.url));
  const command=process.platform==='win32'?'wsl':path;
  const distro=process.env.FLYREFLEX_WSL_DISTRO;
  const args=process.platform==='win32'?[...(distro?['-d',distro]:[]),'--','/mnt/'+path[0].toLowerCase()+path.slice(2).replaceAll('\\','/'),'control']:['control'];
  const child=spawn(command,args),lines=createInterface({input:child.stdout})[Symbol.asyncIterator]();
  try{
    assert.equal((await lines.next()).value,'FR2 READY');
    for(const config of [{delay:14},{delay:0},{delay:14,crowded:true}]){
      const {delay}=config,w=makeWorld();
      if(config.crowded){
        for(let i=0;i<16;i++){const a=i/16*Math.PI*2;launch(w,{x:4.5*Math.cos(a),z:4.5*Math.sin(a)},{x:-Math.cos(a),z:-Math.sin(a)},9,8);}
      }else launch(w,{x:0,z:4.5},{x:0,z:-.7},4,0);
      for(let seq=0;seq<160;seq++){
        const s=[sense(w,0),sense(w,1)];
        child.stdin.write(`${seq} ${seq===0?1:0} ${delay} ${s[0].size} ${s[0].rate} ${s[1].size} ${s[1].rate}\n`);
        const line=(await lines.next()).value,result=JSON.parse(line.slice(4));
        assert.equal(result.source,'host-reference');advance(w,result,s,delay);
      }
      if(config.crowded){assert.ok(w.stats[1].hit>0);assert.equal(w.stats[1].hit+w.stats[1].saved,16);}
      else if(delay===14){assert.equal(w.stats[0].hit,1);assert.equal(w.stats[1].saved,1);}
      else{assert.deepEqual(w.stats[0],w.stats[1]);assert.deepEqual(w.cores[0],w.cores[1]);}
    }
    child.stdin.write('0 1 0 -1 0 -1 0\n');
    const invalid=JSON.parse((await lines.next()).value.slice(4));
    assert.equal(invalid.action,'STOP');assert.equal(invalid.agent_a,'STOP');
  }finally{child.stdin.end('quit\n');}
});
