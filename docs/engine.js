// Original browser implementation of classic Angluin L*, not a new algorithm.
export const shortlex=xs=>[...new Set(xs)].sort((a,b)=>a.length-b.length||a.localeCompare(b));
export function validate(d){
 if(!d||Object.getPrototypeOf(d)!==Object.prototype||Object.keys(d).sort().join(',')!=='accept,alphabet,start,transitions')throw Error('DFA needs exactly alphabet, transitions, start and accept');
 const a=d.alphabet,t=d.transitions,f=d.accept,n=t?.length,integer=x=>Number.isInteger(x)&&x>=0&&x<n;
 if(!Array.isArray(a)||a.length<1||a.length>3||a.some(x=>typeof x!=='string'||!(/^[a-z]$/).test(x))||JSON.stringify(a)!==JSON.stringify([...new Set(a)].sort()))throw Error('Use 1..3 sorted distinct ASCII lowercase letters');
 if(!Array.isArray(t)||n<1||n>6||t.some(r=>!Array.isArray(r)||r.length!==a.length||r.some(x=>!integer(x))))throw Error('Use 1..6 states and one valid transition per letter');
 if(!integer(d.start)||!Array.isArray(f)||f.some(x=>!integer(x))||JSON.stringify(f)!==JSON.stringify([...new Set(f)].sort((a,b)=>a-b)))throw Error('Invalid start or accepting states');return d;
}
export function trace(d,w,initial=d.start){let q=initial,qs=[q];for(const c of w){const k=d.alphabet.indexOf(c);if(k<0)throw Error('Word contains a letter outside the alphabet');q=d.transitions[q][k];qs.push(q);}return qs;}
const accepts=(d,w,start=d.start)=>d.accept.includes(trace(d,w,start).at(-1));
export function equivalence(left,right,initial=[left.start,right.start]){
 const pairs=[initial],words=[''],edges=[],outputs=[],ids=new Map([[initial.join(','),0]]);let counterexample=null;
 for(let i=0;i<pairs.length;i++){
  const [p,q]=pairs[i],out=[left.accept.includes(p),right.accept.includes(q)];outputs.push(out);if(out[0]!==out[1]&&counterexample===null)counterexample=words[i];
  edges.push(left.alphabet.map((c,k)=>{const z=[left.transitions[p][k],right.transitions[q][k]],key=z.join(',');if(!ids.has(key)){ids.set(key,pairs.length);pairs.push(z);words.push(words[i]+c);}return ids.get(key);}));
 }
 return {pairs,words,edges,outputs,counterexample};
}
export function learn(input){
 const d=structuredClone(validate(input)),a=d.alphabet,cache=new Map(),steps=[];let S=[''],E=[''];
 while(steps.length<64){
  const domain=shortlex(S.concat(S.flatMap(s=>a.map(c=>s+c)))),queries=[];
  for(const w of shortlex(domain.flatMap(s=>E.map(e=>s+e))))if(!cache.has(w)){const path=trace(d,w),answer=d.accept.includes(path.at(-1));cache.set(w,answer);queries.push({word:w,answer,path});}
  const signatures=new Map(domain.map(s=>[s,E.map(e=>cache.get(s+e)).map(Number).join('')])),bits=s=>[...signatures.get(s)].map(c=>c==='1');
  const closure=domain.filter(s=>!S.includes(s)&&!S.some(t=>signatures.get(t)===signatures.get(s))),consistency=[];
  for(let i=0;i<S.length;i++)for(let j=i+1;j<S.length;j++)if(signatures.get(S[i])===signatures.get(S[j]))for(const c of a){const suffixes=E.filter((e,k)=>bits(S[i]+c)[k]!==bits(S[j]+c)[k]);if(suffixes.length)consistency.push({left:S[i],right:S[j],letter:c,suffixes});}
  const step={S:[...S],E:[...E],rows:domain.map(word=>({word,bits:bits(word)})),queries,closure,consistency};
  if(consistency.length){const x=consistency[0],add=x.letter+x.suffixes[0];step.action={kind:'consistency',add};E=shortlex([...E,add]);}
  else if(closure.length){const add=closure[0];step.action={kind:'closure',add};S=shortlex([...S,add]);}
  else{
   const representatives=[],stateIds=new Map();for(const s of S)if(!stateIds.has(signatures.get(s))){stateIds.set(signatures.get(s),representatives.length);representatives.push(s);}
   const h={alphabet:[...a],transitions:representatives.map(s=>a.map(c=>stateIds.get(signatures.get(s+c)))),start:stateIds.get(signatures.get('')),accept:representatives.map((s,i)=>cache.get(s)?i:-1).filter(i=>i>=0)},eq=equivalence(d,h);
   step.action={kind:'conjecture',hypothesis:{dfa:h,representatives},equivalence:eq};
   const w=eq.counterexample;if(w!==null)S=shortlex(S.concat(Array.from({length:w.length+1},(_,k)=>w.slice(0,k))));
  }
  steps.push(step);
  if(step.action.kind==='conjecture'&&step.action.equivalence.counterexample===null){
   const final=step.action.hypothesis.dfa,rr=equivalence(final,final),access=Array(final.transitions.length);rr.pairs.forEach((p,i)=>access[p[0]]=rr.words[i]);const distinctions=[];
   for(let p=0;p<final.transitions.length;p++)for(let q=p+1;q<final.transitions.length;q++)distinctions.push({left:p,right:q,suffix:equivalence(final,final,[p,q]).counterexample});
   return {schema:'dfalab-learning-v1',target:d,steps,final,minimality:{access,distinctions},stats:{membership_queries:cache.size,equivalence_queries:steps.filter(s=>s.action.kind==='conjecture').length,closure_repairs:steps.filter(s=>s.action.kind==='closure').length,consistency_repairs:steps.filter(s=>s.action.kind==='consistency').length}};
  }
 }
 throw Error('Bounded learning trace exceeded 64 steps');
}

export function parseRequest(text){
 if(new TextEncoder().encode(text).length>65536)throw Error('Input exceeds 64 KiB');
 const value=JSON.parse(text),tokens=text.match(/"(?:\\.|[^"\\])*"|true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|[{}\[\],:]/g);let i=0;
 function walk(){const t=tokens[i++];if(t==='{'){const seen=new Set();if(tokens[i]==='}'){i++;return;}while(true){const key=JSON.parse(tokens[i++]);if(seen.has(key))throw Error('Duplicate JSON key');seen.add(key);i++;walk();if(tokens[i++]==='}')break;}}
 else if(t==='['){if(tokens[i]===']'){i++;return;}while(true){walk();if(tokens[i++]===']')break;}}}
 if(tokens.some(t=>/^-?[0-9]/.test(t)&&/[.eE]/.test(t)))throw Error('State IDs need integer JSON literals');walk();return value;
}
