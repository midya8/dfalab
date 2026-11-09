import {analyze}from'./fault-atlas-engine.js';import{parseRequest,trace}from'./engine.js';
const $=id=>document.getElementById(id),word=w=>w||'ε',put=(id,v)=>$(id).textContent=v;let report=null;window.atlasReport=null;window.atlasSubset=null;window.atlasCandidate=null;
function rows(id,values){$(id).replaceChildren();for(const row of values){const tr=document.createElement('tr');for(const v of row){const td=document.createElement('td');td.textContent=v;tr.append(td);}$(id).append(tr);}}
function options(id,values){$(id).replaceChildren();for(const[v,label]of values){const o=document.createElement('option');o.value=v;o.textContent=label;$(id).append(o);}}
function clear(){report=null;window.atlasReport=null;window.atlasSubset=null;window.atlasCandidate=null;$('output').hidden=true;$('download').disabled=true;$('report').value='';put('error','');}
function candidate(){if(!report)return;const id=Number($('candidate').value),c=report.candidates[id],s=report.subsets[Number($('subset').value)],d=c.machine;window.atlasCandidate=id;const escapes=!c.rejected_by.some(j=>s.tests.includes(j));put('candidate-summary',`Candidate ID: ${id}
Declared states: ${report.request.bound}
Reachable states: ${c.reachable_states}
Start: q${d.start}
Exact equivalence: ${c.counterexample===null?'yes':'NO'}
Passes selected subset: ${escapes?'yes':'no'}
${c.counterexample===null?'Equivalent survivor: not a fault.':escapes?'A real fault escapes this subset.':'The selected subset detects this fault.'}`);rows('machine',d.transitions.map((ts,q)=>['q'+q,d.accept.includes(q)?'yes':'no',ts.map((z,j)=>d.alphabet[j]+' → q'+z).join('; ')]));rows('matrix',report.words.map((w,j)=>[j+' / '+word(w),s.tests.includes(j)?'yes':'no',(report.expected[j]?'1':'0')+' / '+(c.outputs[j]?'1':'0'),trace(d,w).join(' → ')]));put('counterexample',c.counterexample===null?'No distinguishing word: the complete reachable product agrees.':`Word: ${word(c.counterexample)}
Reference path: ${trace(report.request.reference,c.counterexample).join(' → ')}
Candidate path: ${trace(d,c.counterexample).join(' → ')}`);}
function subset(){if(!report)return;const mask=Number($('subset').value),s=report.subsets[mask];window.atlasSubset=mask;for(const box of $('toggles').querySelectorAll('input'))box.checked=Boolean(mask&(1<<Number(box.value)));put('subset-summary',`Mask: ${mask}
Tests: ${s.tests.map(j=>word(report.words[j])).join(', ')||'(empty subset)'}
Test count / resets: ${s.count}
Input letters: ${s.symbols}
Faults rejected: ${s.covered_faults} / ${report.summary.faults}
Faults escaping: ${s.missed_faults}
Complete in this domain: ${s.missed_faults===0?'yes':'NO'}
Optimal under stated objective: ${report.optimal_masks.includes(mask)?'yes':'no'}`);$('survivor').disabled=s.first_survivor===null;candidate();}
function run(){clear();try{report=analyze(parseRequest($('input').value));window.atlasReport=report;$('output').hidden=false;$('download').disabled=false;$('report').value=JSON.stringify(report,null,2);const s=report.summary;put('headline',`${s.candidates} machines. ${s.subsets_checked} test subsets.`);put('summary',`Declared implementation states m: ${s.declared_states}
Candidate machines: ${s.candidates}
Equivalent candidates (not faults): ${s.equivalent}
Nonequivalent candidates: ${s.faults}
Full W-suite tests: ${s.full_tests}
Minimum subset test count: ${s.minimum_tests}
Minimum letters at that count: ${s.minimum_symbols_at_minimum_tests}
Optimal tied subsets: ${s.optimal_suites}`);rows('tests',report.words.map((w,j)=>[j,word(w),report.expected[j]?'accept':'reject',report.candidates.filter(c=>c.rejected_by.includes(j)).length,report.full_suite_essential.includes(j)?'yes':'no']));options('subset',report.subsets.map(s=>[s.mask,`${s.mask}: ${s.count} tests / ${s.symbols} letters / ${s.missed_faults} faults escape${report.optimal_masks.includes(s.mask)?' / OPTIMAL':''}`]));$('subset').value=report.chosen_mask;put('optimal',report.optimal_masks.map(mask=>mask+': '+report.subsets[mask].tests.map(j=>word(report.words[j])).join(', ')).join('\n'));rows('necessity',report.chosen_necessity.map(v=>[v.test,word(report.words[v.test]),v.survivor_without]));$('toggles').replaceChildren();for(let j=0;j<report.words.length;j++){const label=document.createElement('label'),box=document.createElement('input');box.type='checkbox';box.value=j;box.style.width='auto';box.onchange=()=>{let mask=0;for(const b of $('toggles').querySelectorAll('input'))if(b.checked)mask|=1<<Number(b.value);$('subset').value=mask;subset();};label.append(box,document.createTextNode(' '+j+': '+word(report.words[j])));$('toggles').append(label);}options('candidate',report.candidates.map(c=>[c.id,c.id+': '+(c.counterexample===null?'equivalent':'fault')+' / '+c.reachable_states+' reachable / '+c.rejected_by.length+' rejecting tests']));$('candidate').value=0;subset();}catch(e){clear();put('error',e.message);}}
$('run').onclick=run;$('input').oninput=clear;$('subset').onchange=subset;$('candidate').onchange=candidate;$('survivor').onclick=()=>{if(!report)return;const id=report.subsets[Number($('subset').value)].first_survivor;if(id!==null){$('candidate').value=id;candidate();}};$('download').onclick=()=>{if(!report)return;const u=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=u;a.download='dfalab-fault-atlas.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);};
try{const res=await fetch('fault-atlas-controls.json');if(!res.ok)throw Error('Could not load controls');const cs=await res.json();options('control',cs.map((c,j)=>[j,c.name]));$('control').onchange=()=>{$('input').value=JSON.stringify(cs[Number($('control').value)].input,null,2);run();};$('control').value='0';$('control').onchange();}catch(e){put('error',e.message);}
