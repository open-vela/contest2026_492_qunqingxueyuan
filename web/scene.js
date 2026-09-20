import * as THREE from 'three';
import { CORE, PARTICLE } from './physics.js';
export function createArena(element,side){
  const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));element.appendChild(renderer.domElement);
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;
  const scene=new THREE.Scene();scene.background=new THREE.Color('#f3f1ec');
  const camera=new THREE.OrthographicCamera(-6,6,6,-6,.1,40);camera.position.set(0,13,7);camera.lookAt(0,0,0);
  scene.add(new THREE.HemisphereLight(0xffffff,0xb5ab96,2));
  const light=new THREE.DirectionalLight(0xfff5e5,2.5);light.position.set(-5,10,3);light.castShadow=true;light.shadow.mapSize.set(1024,1024);Object.assign(light.shadow.camera,{left:-8,right:8,top:8,bottom:-8,far:30});light.shadow.normalBias=.02;scene.add(light);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(40,40),new THREE.MeshBasicMaterial({color:0xf3f1ec}));floor.rotation.x=-Math.PI/2;scene.add(floor);
  const shadow=new THREE.Mesh(new THREE.PlaneGeometry(40,40),new THREE.ShadowMaterial({opacity:.12}));shadow.rotation.x=-Math.PI/2;shadow.position.y=.002;shadow.receiveShadow=true;scene.add(shadow);
  const material=new THREE.MeshStandardMaterial({color:side?0x86937d:0xa2a099,roughness:.32});
  const core=new THREE.Mesh(new THREE.SphereGeometry(CORE,40,28),material);core.position.y=CORE;core.castShadow=true;scene.add(core);
  const ring=new THREE.Mesh(new THREE.RingGeometry(.44,.455,64),new THREE.MeshBasicMaterial({color:side?0x86937d:0xa2a099,side:THREE.DoubleSide}));ring.rotation.x=-Math.PI/2;ring.position.y=.01;scene.add(ring);
  const boundary=new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(Array.from({length:100},(_,i)=>new THREE.Vector3(Math.cos(i/100*Math.PI*2)*4.8,.01,Math.sin(i/100*Math.PI*2)*4.8))),new THREE.LineBasicMaterial({color:0xd8d4ca}));scene.add(boundary);
  const center=new THREE.Mesh(new THREE.RingGeometry(.055,.065,20),new THREE.MeshBasicMaterial({color:0xbdb8ad,side:THREE.DoubleSide}));center.rotation.x=-Math.PI/2;center.position.y=.01;scene.add(center);
  const shotGeometry=new THREE.SphereGeometry(PARTICLE,16,12),shotMaterial=new THREE.MeshStandardMaterial({color:0xb75e3f,roughness:.45}),meshes=new Map();
  const guide=new THREE.Line(new THREE.BufferGeometry(),new THREE.LineDashedMaterial({color:0xb95939,dashSize:.13,gapSize:.10}));scene.add(guide);guide.visible=false;
  const ghost=new THREE.Mesh(shotGeometry,shotMaterial);scene.add(ghost);ghost.visible=false;
  const arrow=new THREE.ArrowHelper(new THREE.Vector3(0,0,-1),new THREE.Vector3(),1,0xb95939,.22,.12);scene.add(arrow);arrow.visible=false;
  const ray=new THREE.Raycaster(),plane=new THREE.Plane(new THREE.Vector3(0,1,0),0);
  function resize(){const w=element.clientWidth,h=element.clientHeight,aspect=w/h,vertical=Math.max(5.1,5.7/aspect);camera.left=-vertical*aspect;camera.right=vertical*aspect;camera.top=vertical;camera.bottom=-vertical;camera.updateProjectionMatrix();renderer.setSize(w,h,false);}
  new ResizeObserver(resize).observe(element);resize();
  return {
    point(event){const r=renderer.domElement.getBoundingClientRect();ray.setFromCamera(new THREE.Vector2((event.clientX-r.left)/r.width*2-1,-(event.clientY-r.top)/r.height*2+1),camera);const p=new THREE.Vector3();return ray.ray.intersectPlane(plane,p)?{x:p.x,z:p.z}:null;},
    draw(world,drag){
      const c=world.cores[side];core.position.set(c.x,CORE,c.z);ring.position.set(c.x,.01,c.z);material.color.set(c.flash>0?0xc45333:side?0x86937d:0xa2a099);
      const ids=new Set();for(const p of world.shots){if(p.done[side])continue;ids.add(p.id);let m=meshes.get(p.id);if(!m){m=new THREE.Mesh(shotGeometry,shotMaterial);m.castShadow=true;scene.add(m);meshes.set(p.id,m);}m.position.set(p.x,PARTICLE,p.z);}
      for(const [id,m] of meshes)if(!ids.has(id)){scene.remove(m);meshes.delete(id);}
      guide.visible=ghost.visible=arrow.visible=!!drag;
      if(drag){const {start,end}=drag,dx=start.x-end.x,dz=start.z-end.z,d=Math.hypot(dx,dz);ghost.position.set(start.x,PARTICLE,start.z);guide.geometry.dispose();guide.geometry=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(end.x,.03,end.z),new THREE.Vector3(start.x,.03,start.z)]);guide.computeLineDistances();arrow.position.set(start.x,.04,start.z);arrow.setDirection(new THREE.Vector3(dx/(d||1),0,dz/(d||1)));arrow.setLength(Math.min(d,3)+.3,.22,.12);}
      renderer.render(scene,camera);
    }
  };
}
