const fs=require('fs'); eval(fs.readFileSync(require('path').join(__dirname,'..','src','dsp.js'),'utf8'));
const sr=48000;
function sine(f,sec,amp=0.5){const a=new Float32Array(Math.round(sec*sr));for(let i=0;i<a.length;i++)a[i]=amp*Math.sin(2*Math.PI*f*i/sr);return a;}
function run(tracks,offs,T,semi){
  const P=Math.pow(2,semi/12);
  let D=0; tracks.forEach((x,k)=>D=Math.max(D,offs[k]/sr+x.length/sr));
  const Lout=Math.round(D*sr/T); const outs=tracks.map(()=>new Float32Array(Lout));
  const Ys=[],Os=[];
  tracks.forEach((x,k)=>{ if(P===1){Ys.push(x);Os.push(offs[k]);} else {const y=new Float32Array(resampleLen(x.length,P)); for(const f of resampleGen(x,P,y)); Ys.push(y); Os.push(Math.round(offs[k]/P));}});
  const Ly=Math.ceil(D*sr/P);
  for(const f of wsolaGen(Ys,Os,Ly,P/T,sr,outs));
  return outs;
}
function freq(a){let c=0;const s=Math.floor(a.length*0.3),e=Math.floor(a.length*0.7);for(let i=s+1;i<e;i++)if(a[i-1]<=0&&a[i]>0)c++;return c/((e-s)/sr);}
function rmsRange(a){const w=2400;let mn=1e9,mx=0;for(let s=Math.floor(a.length*0.1);s+w<a.length*0.9;s+=w){let e=0;for(let i=s;i<s+w;i++)e+=a[i]*a[i];e=Math.sqrt(e/w);mn=Math.min(mn,e);mx=Math.max(mx,e);}return [mn.toFixed(3),mx.toFixed(3)];}
for (const [T,semi] of [[0.75,0],[1,3],[0.5,7],[1.5,-7],[1.2,-2]]){
  const o=run([sine(440,10)],[0],T,semi)[0];
  console.log(`T=${T} semi=${semi}: len=${(o.length/sr).toFixed(3)}s expect ${(10/T).toFixed(3)}  f=${freq(o).toFixed(1)} expect ${(440*Math.pow(2,semi/12)).toFixed(1)}  rms(min,max)=${rmsRange(o)}`);
}
// sync test: clicks track1 every 0.5s; track2 clicks shifted by 0.25s via offset
function clicks(sec,phase){const a=new Float32Array(Math.round(sec*sr));for(let t=phase;t<sec;t+=0.5){const i0=Math.round(t*sr);for(let k=0;k<200&&i0+k<a.length;k++)a[i0+k]+=Math.exp(-k/30)*Math.sin(2*Math.PI*2000*k/sr);}
 for(let i=0;i<a.length;i++)a[i]+=0.05*Math.sin(2*Math.PI*220*i/sr);return a;}
function peaksAt(a){const res=[];const w=Math.round(0.05*sr);for(let s=0;s+w<=a.length;s+=Math.round(0.5*sr*0+w)){}return res;}
function onsets(a){const out=[];let last=-1e9;const env=0.3;for(let i=0;i<a.length;i++){if(Math.abs(a[i])>env&&i-last>sr*0.2){out.push(i/sr);last=i;}}return out;}
const T=0.8, offS=Math.round(0.25*sr);
const [o1,o2]=run([clicks(6,0),clicks(6,0)],[0,offS],T,2);
const a1=onsets(o1),a2=onsets(o2);
console.log('track1 onsets',a1.slice(0,6).map(x=>x.toFixed(4)).join(' '));
console.log('track2 onsets',a2.slice(0,6).map(x=>x.toFixed(4)).join(' '));
console.log('diffs (expect '+(0.25/T).toFixed(4)+')',a1.slice(0,8).map((x,i)=>(a2[i]-x).toFixed(4)).join(' '));
// perf: 3 min, two tracks, music-like
function music(sec,seed){let s=seed;const rnd=()=>(s=(s*16807)%2147483647)/2147483647;const a=new Float32Array(Math.round(sec*sr));for(let i=0;i<a.length;i++){const t=i/sr;a[i]=0.3*Math.sin(2*Math.PI*(220+50*Math.sin(t))*t)+0.2*Math.sin(2*Math.PI*330*t)+0.05*(rnd()-0.5);}return a;}
const m1=music(180,7),m2=music(170,11);
let t0=Date.now(); run([m1,m2],[0,Math.round(3.3*sr)],0.8,4); console.log('3min x2 T=0.8 +4st:',Date.now()-t0,'ms');
t0=Date.now(); run([m1],[0],0.8,0); console.log('3min x1 T=0.8 0st:',Date.now()-t0,'ms');
console.log('--- harder tones');
for (const f0 of [523, 880, 1500, 110]) for (const [T,semi] of [[1,3],[0.7,-5],[1.3,2]]){
  const o=run([sine(f0,6)],[0],T,semi)[0];
  console.log(`f0=${f0} T=${T} semi=${semi}: f=${freq(o).toFixed(1)} exp ${(f0*Math.pow(2,semi/12)).toFixed(1)} rms=${rmsRange(o)}`);
}
