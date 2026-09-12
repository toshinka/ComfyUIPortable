import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import { resolveHistoryScalars } from '../app/static/history-settings.js';
const app = (await readFile(new URL('../app/static/app.js', import.meta.url), 'utf8')).replaceAll('\r\n','\n');
const html = await readFile(new URL('../app/static/index.html', import.meta.url), 'utf8');
class Element {
  value=''; textContent=''; disabled=false; hidden=false; children=[]; listeners={}; attributes={};
  replaceChildren(...children){ this.children=children; }
  append(...children){ this.children.push(...children); }
  setAttribute(k,v){ this.attributes[k]=v; }
  addEventListener(k,fn){ this.listeners[k]=fn; }
  fire(k){ this.listeners[k]?.(); }
}
const elements = new Map();
const $ = id => { if(!elements.has(id)) elements.set(id,new Element()); return elements.get(id); };
const state = { mode:'video',videoType:'standard',playableSelections:{ standard:{model_name:null,loras:[]},reference:{model_name:null,loras:[]} },
config:{playable:{defaults:{standard:'fl',reference:'ref'},models:{standard:['fl','fl-alt'],reference:['ref']},lora:{state:'AVAILABLE',names:['a','b','c']}}}};
const context = vm.createContext({ state, $, modelInput:$('video-model'),loraStack:$('lora-stack'),document:{createElement:()=>new Element()},loadConfig:()=>{} });
// Extract bounded production function declarations, without booting the application.
for(const name of ['playableSelection','populateNamedOptions','renderPlayableControls','playablePayload','restorePlayableSettings']) {
  const match = app.match(new RegExp(`function ${name}\\([^]*?\\n\\}`));
  assert.ok(match, name); vm.runInContext(match[0],context);
}
const events=app.slice(app.indexOf('modelInput.addEventListener("change"'),app.indexOf('promptInput.addEventListener("input"'));
vm.runInContext(events,context);
const call=(s)=>vm.runInContext(s,context);
call('renderPlayableControls()');
assert.equal($('video-model').value,'fl');
$('video-model').value='fl-alt'; $('video-model').fire('change');
assert.equal(state.playableSelections.standard.model_name,'fl-alt');
$('video-model').value='fl'; $('video-model').fire('change');
assert.equal($('video-model-controls').hidden,false);
assert.equal($('lora-stack').children.length,0);
assert.equal($('add-lora').disabled,false);
$('add-lora').fire('click');
assert.equal(state.playableSelections.standard.loras[0].strength,1);
assert.throws(()=>call('playablePayload()'),/Choose a file/);
let row=$('lora-stack').children[0];
row.children[0].value='a'; row.children[0].fire('change');
row.children[1].value='0.8'; row.children[1].fire('input');
$('add-lora').fire('click');
row=$('lora-stack').children[1]; row.children[0].value='b'; row.children[0].fire('change');
$('add-lora').fire('click');
row=$('lora-stack').children[2]; row.children[0].value='c'; row.children[0].fire('change');
assert.equal($('add-lora').disabled,true);
$('add-lora').fire('click'); assert.equal(state.playableSelections.standard.loras.length,3);
assert.deepEqual(JSON.parse(JSON.stringify(call('playablePayload()'))),{model_name:'fl',loras:[{name:'a',strength:0.8},{name:'b',strength:1},{name:'c',strength:1}]});
// Capability refresh retains stale choices; server will reject, never fallback.
state.config.playable.models.standard=['fl-alt']; state.config.playable.lora.names=[];
call('renderPlayableControls()');
assert.equal($('video-model').value,'fl');
assert.ok($('video-model').children.some(x=>x.textContent==='fl · unavailable'));
assert.equal(state.playableSelections.standard.loras.length,3);
assert.equal($('lora-stack').children[0].children[0].value,'a');
state.videoType='reference'; call('renderPlayableControls()'); assert.equal($('video-model').value,'ref');
assert.equal($('lora-stack').children.length,0);
state.videoType='standard'; call('renderPlayableControls()'); assert.equal($('lora-stack').children.length,3);
// Hidden video constraints cannot block Still or Prep/Edit form validity.
state.mode='still'; call('renderPlayableControls()');
assert.equal($('video-model-controls').hidden,true);
assert.ok($('lora-stack').children.every(row=>row.children[0].disabled && row.children[1].disabled));
state.mode='video'; state.config.playable.lora.state='UNAVAILABLE'; call('renderPlayableControls()');
assert.equal($('lora-status').textContent,'Unavailable for this Native profile');
assert.equal($('add-lora').disabled,true);
$('lora-stack').children[1].children[2].fire('click');
assert.deepEqual(state.playableSelections.standard.loras.map(x=>x.name),['a','c']);
const options={resolutionValues:['512x288','608x352','736x416'],durationValues:['3','5','10','15'],stepsValue:'20'};
const settings=resolveHistoryScalars({request:{prompt:'retained',width:512,height:288,duration:3,seed:'9223372036854775807',steps:20,model_name:'missing',loras:[{name:'old',strength:-2}]}},options);
context.settings=settings; call('restorePlayableSettings(settings)');
assert.equal($('video-model').value,'missing'); assert.equal(call('playablePayload()').loras[0].name,'old');
const advanced=html.slice(html.indexOf('<details class="advanced-panel">'),html.indexOf('</details>',html.indexOf('<details class="advanced-panel">')));
for(const id of ['resolution','duration','video-model','lora-stack']) assert.ok(advanced.includes(`id="${id}"`));
assert.equal((html.match(/<summary>Advanced<\/summary>/g)||[]).length,1);
assert.ok(app.includes('Object.assign(payload, playablePayload())'));
assert.equal(app.includes('payload.duration = 5'),false);
assert.equal(app.includes('h3_play1_lora_'),false);
assert.equal(app.includes('unet_name'),false);
console.log('H3-PLAY1 Advanced UI behavior, stale retention, route isolation, History and payload: PASS');
