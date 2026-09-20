import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { describe, livePacketValid, replayIndex } from '../story.js';
const data=JSON.parse(readFileSync(new URL('../demo.json',import.meta.url)));
test('C replay contains an escape and returns to AI control',()=>{
 const frames=data.scenarios.recovery;
 assert.ok(frames.some(s=>s.action==='ESCAPE'&&s.decision==='REFLEX_OVERRIDE'));
 assert.equal(frames.at(-1).state,'SAFE');assert.equal(frames.at(-1).action,'FORWARD');
 assert.equal(describe(frames.at(-1),true)[0],'SAFE');
});
test('presentation follows action rather than inventing a GF threshold',()=>{
 assert.equal(describe({action:'STOP',state:'INVALID'})[0],'FAILSAFE');
 assert.equal(describe({action:'FORWARD',state:'SAFE',gf:1200})[0],'OBSERVING');
});
test('host replay and disconnected samples cannot masquerade as live',()=>{
 const s={...data.scenarios.recovery[0],seq:0,cycle:0,latency_ns:2000};
 assert.equal(livePacketValid({connected:true,sample:s}),false);
 assert.equal(livePacketValid({connected:false,sample:{...s,source:'openvela'}}),false);
 assert.equal(livePacketValid({connected:true,sample:{...s,source:'openvela'}}),true);
});
test('replay holds closing state before repeating',()=>{
 assert.equal(replayIndex(8,16).index,15);
 assert.equal(replayIndex(9.3,16).cycle,1);
});
