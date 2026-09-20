export const DT=.025, CORE=.34, PARTICLE=.16, MOTOR=3.6;
export const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const length=v=>Math.hypot(v.x,v.z);
export function sweptHit(a,b,r){
  const dx=b.x-a.x,dz=b.z-a.z,d=dx*dx+dz*dz;
  const t=d?clamp(-(a.x*dx+a.z*dz)/d,0,1):0;
  return Math.hypot(a.x+t*dx,a.z+t*dz)<=r;
}
export function makeWorld(){return {cores:[{x:0,z:0,hold:0,dir:{x:1,z:0},flash:0},{x:0,z:0,hold:0,dir:{x:1,z:0},flash:0}],shots:[],history:[],stats:[{hit:0,saved:0},{hit:0,saved:0}],launched:0,time:0};}
export function launch(w,start,pull,base,accel){
  const power=length(pull);if(power<.12)return false;
  const dir={x:pull.x/power,z:pull.z/power},v=base+Math.min(power,3)*2;
  const along=-(start.x*dir.x+start.z*dir.z);
  const miss=Math.abs(start.x*dir.z-start.z*dir.x);
  w.shots.push({id:++w.launched,x:start.x,z:start.z,dir,v,accel,aimed:along>0&&miss<=CORE+PARTICLE,done:[false,false]});
  return true;
}
export function sense(w,side){
  const c=w.cores[side];let best=null;
  for(const p of w.shots){
    if(p.done[side])continue;
    const dx=c.x-p.x,dz=c.z-p.z,along=dx*p.dir.x+dz*p.dir.z;
    const lateral=Math.abs(dx*p.dir.z-dz*p.dir.x);
    if(along<=0||lateral>CORE+PARTICLE+.12)continue;
    const dist=Math.hypot(dx,dz),ttc=along/Math.max(p.v,.1);
    if(!best||ttc<best.ttc)best={p,dist,ttc};
  }
  if(!best)return {size:0,rate:0,threat:null};
  return {size:Math.round(clamp(650/best.dist,0,1000)),rate:Math.round(clamp(220*best.p.v/(best.dist*best.dist),0,1000)),threat:best.p};
}
export function advance(w,result,sensors,delayTicks=14){
  w.history.push(sensors.map(s=>s.threat));
  const delayed=w.history[Math.max(0,w.history.length-1-delayTicks)];
  if(w.history.length>41)w.history.shift();
  const old=w.cores.map(c=>({x:c.x,z:c.z}));
  [result.agent_a,result.action].forEach((command,i)=>{
    const c=w.cores[i],p=i===1&&result.state==='DANGER'?sensors[i].threat:delayed[i];
    if(command==='ESCAPE'){
      if(p&&c.hold<=0){let x=-p.dir.z,z=p.dir.x;if(c.x*x+c.z*z<0){x=-x;z=-z;}c.dir={x,z};}
      c.hold=.35;
    }
    if(command!=='STOP'){
      if(c.hold>0){c.x+=c.dir.x*MOTOR*DT;c.z+=c.dir.z*MOTOR*DT;}
      else{const d=length(c);if(d>.01){const step=Math.min(d,.8*DT);c.x-=c.x/d*step;c.z-=c.z/d*step;}}
    }
    const d=length(c);if(d>2.4){c.x*=2.4/d;c.z*=2.4/d;}
    c.hold=Math.max(0,c.hold-DT);c.flash=Math.max(0,c.flash-DT);
  });
  for(const p of w.shots){
    const px=p.x,pz=p.z;const distance=p.v*DT+.5*p.accel*DT*DT;p.v+=p.accel*DT;
    p.x+=p.dir.x*distance;p.z+=p.dir.z*distance;
    for(let i=0;i<2;i++){
      if(p.done[i])continue;const c=w.cores[i];
      if(sweptHit({x:px-old[i].x,z:pz-old[i].z},{x:p.x-c.x,z:p.z-c.z},CORE+PARTICLE)){
        p.done[i]=true;c.flash=.25;if(p.aimed)w.stats[i].hit++;
      }else if(Math.hypot(p.x,p.z)>7){p.done[i]=true;if(p.aimed)w.stats[i].saved++;}
    }
  }
  w.shots=w.shots.filter(p=>!p.done.every(Boolean));w.time+=DT;
}
