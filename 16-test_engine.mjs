import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {execFileSync} from 'node:child_process';import {learn,validate,trace,equivalence,parseRequest} from '../docs/engine.js';
const controls=JSON.parse(fs.readFileSync(new URL('../docs/controls.json',import.meta.url))),python=process.env.PYTHON||'python';
test('complete cross-engine reports and independent native verification',()=>{
 const cases=controls.map(c=>c.target);let z=1987;const rand=n=>{z=(Math.imul(z,1664525)+1013904223)>>>0;return z%n;};
 for(let n=1;n<=6;n++)for(let j=0;j<30;j++)cases.push({alphabet:['a','b','c'],transitions:Array.from({length:n},()=>Array.from({length:3},()=>rand(n))),start:rand(n),accept:Array.from({length:n},(_,i)=>i).filter(()=>rand(2))});
 const reports=cases.map(learn),native=JSON.parse(execFileSync(python,['-c','import sys,json;from dfalab import learn;print(json.dumps([learn(x) for x in json.load(sys.stdin)]))'],{input:JSON.stringify(cases),maxBuffer:64<<20}));assert.deepEqual(reports,native);
 execFileSync(python,['-c','import sys,json;from dfalab import verify;rs=json.load(sys.stdin);assert all(verify(x) for x in rs);print(len(rs))'],{input:JSON.stringify(reports),maxBuffer:64<<20});console.log(reports.length+' complete learning reports independently verified');
});
test('strict bounds, nonaliasing, empty-word mismatch and total products',()=>{
 const d=controls[2].target,before=structuredClone(d),r=learn(d);assert.deepEqual(d,before);r.target.transitions[0][0]=99;assert.deepEqual(d,before);
 for(const bad of [{...d,start:true},{...d,accept:[true]},{...d,alphabet:['b','a']},{...d,transitions:[[false,false]]},{...d,extra:1}])assert.throws(()=>validate(bad));
 const no={alphabet:['a'],transitions:[[0]],start:0,accept:[]},yes={...no,accept:[0]};assert.equal(equivalence(no,yes).counterexample,'');assert.deepEqual(equivalence(no,no).edges,[[0]]);assert.throws(()=>trace(no,'b'));
});

test('strict JSON transport rejects duplicate decoded keys and oversized requests',()=>{
 assert.throws(()=>parseRequest('{"start":0,"start":1}'),/Duplicate/);assert.throws(()=>parseRequest('{"start":0.0}'),/integer/);assert.throws(()=>parseRequest('{"start":0e0}'),/integer/);assert.throws(()=>parseRequest('{"a":0,"\\u0061":1}'),/Duplicate/);assert.throws(()=>parseRequest(' '.repeat(65537)),/64 KiB/);assert.deepEqual(parseRequest(JSON.stringify(controls[0].target)),controls[0].target);
});
