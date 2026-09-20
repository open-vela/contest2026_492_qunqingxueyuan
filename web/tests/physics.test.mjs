import test from 'node:test';
import assert from 'node:assert/strict';
import {makeWorld,launch,sense,advance,sweptHit} from '../physics.js';
test('swept collision catches fast particles crossing the entire core',()=>{
  assert.equal(sweptHit({x:-3,z:0},{x:3,z:0},.5),true);
  assert.equal(sweptHit({x:-3,z:1},{x:3,z:1},.5),false);
});
test('one launch is shared by both lanes; off-target shots do not score',()=>{
  const w=makeWorld();launch(w,{x:2,z:4},{x:0,z:-1},4,0);
  assert.equal(w.shots[0].aimed,false);
  for(let i=0;i<200;i++)advance(w,{agent_a:'FORWARD',action:'FORWARD'},[sense(w,0),sense(w,1)]);
  assert.deepEqual(w.stats,[{hit:0,saved:0},{hit:0,saved:0}]);
  assert.equal(w.shots.length,0);
});
test('no ammunition cap and acceleration changes velocity',()=>{
  const w=makeWorld();for(let i=0;i<300;i++)launch(w,{x:0,z:4},{x:0,z:-1},2,3);
  assert.equal(w.shots.length,300);const v=w.shots[0].v;
  advance(w,{agent_a:'FORWARD',action:'FORWARD'},[sense(w,0),sense(w,1)]);
  assert.ok(w.shots[0].v>v);
});
test('identical immediate commands have identical movement and outcomes',()=>{
  const w=makeWorld();launch(w,{x:4,z:0},{x:-1,z:0},4,0);
  for(let i=0;i<150;i++)advance(w,{agent_a:'ESCAPE',action:'ESCAPE',state:'DANGER'},[sense(w,0),sense(w,1)],0);
  assert.deepEqual(w.cores[0],w.cores[1]);assert.deepEqual(w.stats[0],w.stats[1]);
});
