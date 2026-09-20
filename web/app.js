import {createArena} from './scene.js';
import {makeWorld,launch,sense,advance,DT} from './physics.js';
import {validateReply} from './telemetry.js';
const $=id=>document.getElementById(id);
let world=makeWorld(),mode='live',paused=false,lost=false,busy=false,seq=0,epoch=0,reset=true,drag=null,lastStep=0;
let session=crypto.randomUUID(),result=null;
let arenas=[];
try{arenas=['a','b'].map((name,i)=>createArena($('arena-'+name),i));}
catch(error){$('connection').textContent='3D 初始化失败';document.querySelector('.instruction').textContent='请启用浏览器硬件加速后刷新';throw error;}
function resetWorld(){world=makeWorld();seq=0;epoch++;session=crypto.randomUUID();reset=true;result=null;drag=null;lost=false;$('lost').hidden=true;$('delay').disabled=false;$('last-override').textContent='尚无安全覆盖记录';$('connection').textContent='连接中';}
function fire(start,pull){if(lost||paused)return;if(launch(world,start,pull,+$('speed').value,+$('accel').value))$('delay').disabled=true;}
['a','b'].forEach((name,i)=>{
  const el=$('arena-'+name);
  el.onpointerdown=e=>{if(e.button!==0||lost||paused)return;const p=arenas[i].point(e);if(!p||Math.hypot(p.x,p.z)<1||Math.hypot(p.x,p.z)>5.8)return;drag={start:p,end:p,pointer:e.pointerId,side:i};el.setPointerCapture(e.pointerId);};
  el.onpointermove=e=>{if(!drag||drag.pointer!==e.pointerId||drag.side!==i)return;const p=arenas[i].point(e);if(p)drag.end=p;};
  el.onpointerup=e=>{if(!drag||drag.pointer!==e.pointerId||drag.side!==i)return;const {start,end}=drag;drag=null;fire(start,{x:start.x-end.x,z:start.z-end.z});};
  el.onpointercancel=()=>{drag=null;};
  el.onkeydown=e=>{if(e.key===' '){e.preventDefault();fire({x:0,z:4.5},{x:0,z:-.7});}};
});
$('example').onclick=()=>fire({x:0,z:4.5},{x:0,z:-.7});
$('pause').onclick=()=>{paused=!paused;drag=null;$('pause').textContent=paused?'继续':'暂停';};
$('reset').onclick=resetWorld;
$('mode').onchange=()=>{mode=$('mode').value;resetWorld();};
$('retry').onclick=resetWorld;
$('details').onclick=()=>$('about').showModal();$('close').onclick=()=>$('about').close();
for(const [id,unit] of [['speed','m/s'],['accel','m/s²'],['delay','ms']])$(id).oninput=()=>{$(id+'-value').textContent=`${$(id).value} ${unit}`;};
document.addEventListener('visibilitychange',()=>{if(document.hidden){paused=true;drag=null;$('pause').textContent='继续';}});
async function step(){
  if(busy||paused||lost)return;
  busy=true;const version=epoch,requestSeq=seq++,sensors=[sense(world,0),sense(world,1)];
  try{
    const response=await fetch('/step',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode,session,seq:requestSeq,reset:reset?1:0,delay:Math.round(+$('delay').value/25),sa:sensors[0].size,ra:sensors[0].rate,sb:sensors[1].size,rb:sensors[1].rate}),signal:AbortSignal.timeout(1500)});
    if(!response.ok)throw Error('connection');const next=await response.json();if(version!==epoch)return;
    validateReply(next,mode,requestSeq);
    if(next.restarted&&!reset)throw Error('session');
    result=next;reset=false;advance(world,result,sensors,Math.round(+$('delay').value/25));
    if(next.agent_b==='FORWARD'&&next.action==='ESCAPE')$('last-override').textContent=`最近真实覆盖 · ${next.source} · seq=${next.seq}: requested=FORWARD → actual=ESCAPE · state=${next.state}`;
    $('connection').textContent=mode==='live'?'OPENVELA CONNECTED':'HOST REFERENCE CONNECTED';$('backend').textContent=mode==='live'?'Safety decision is executed by FlyReflex on openvela':'DEMO MODE · 本机 C 核心';
  }catch(error){if(version===epoch){lost=true;result=null;drag=null;$('lost').hidden=false;$('connection').textContent=mode==='live'?'OPENVELA DISCONNECTED':'HOST REFERENCE DISCONNECTED';$('backend').textContent='仿真已暂停 · 无有效目标动作';}}
  finally{busy=false;}
}
function render(now){
  if(now-lastStep>=DT*1000&&!busy){lastStep=now;step();}
  arenas.forEach(a=>a.draw(world,drag));
  world.stats.forEach((s,i)=>{const name=i?'b':'a',total=s.hit+s.saved;$('score-'+name).textContent=total?`${Math.round(s.saved/total*100)}%`:'—';$('hit-'+name).textContent=s.hit;$('saved-'+name).textContent=s.saved;const c=world.cores[i];$('state-'+name).textContent=c.flash>0?'发生碰撞':c.hold>0?(i&&result?.action==='ESCAPE'?'反射避让':'Agent 避让'):world.shots.length?'等待响应':'等待发射';});
  $('shots').textContent=world.launched;$('activity').textContent=`神经活动 ${result?.gf??0} / 1200`;
  $('requested').textContent=result?.agent_b??'—';$('actual').textContent=lost?'PAUSED (通信失败)':paused?'PAUSED (用户暂停)':result?.action??'等待目标';$('reflex-state').textContent=result?.state??'—';
  $('power').textContent=drag?`发射速度 ${(+$('speed').value+Math.min(3,Math.hypot(drag.start.x-drag.end.x,drag.start.z-drag.end.z))*2).toFixed(1)} m/s`:'拖动蓄力';
  requestAnimationFrame(render);
}
requestAnimationFrame(render);
