/* Run through python3 scripts/knowledge_dom_check.py (also used by CI and publishing). */
const {JSDOM} = require('jsdom');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname,'..');
const script = fs.readFileSync(path.join(root,'knowledge/assets/app.js'),'utf8');
async function open(route, options={}) {
  const url=new URL(route,'http://localhost');
  const html=fs.readFileSync(path.join(root,url.pathname,'index.html'),'utf8');
  const dom=new JSDOM(html,{url:url.href,runScripts:'outside-only',pretendToBeVisual:true});
  const w=dom.window;
  const NativeDate=w.Date;
  w.Date=class extends NativeDate {
    constructor(...args){super(...(args.length?args:[options.now||'2026-09-13T04:00:00Z']));}
    static now(){return new NativeDate(options.now||'2026-09-13T04:00:00Z').getTime();}
  };
  w.Element.prototype.scrollIntoView=function(){};
  Object.defineProperty(w.HTMLElement.prototype,'clientWidth',{get(){return options.width||850;}});
  Object.defineProperty(w.HTMLElement.prototype,'clientHeight',{get(){return 570;}});
  w.ResizeObserver=class{observe(){} disconnect(){}};
  w.fetch=async()=>({ok:!options.fail,json:async()=>{
    const data=options.data ? structuredClone(options.data) : JSON.parse(fs.readFileSync(path.join(root,w.document.body.dataset.base,'data/graph.json')));
    if(options.related)data.notes[0].related=[data.notes[1].id];
    return data;
  }});
  w.eval(script);
  await new Promise(resolve=>setTimeout(resolve,20));
  return {dom,w,d:w.document,close:()=>w.close()};
}
function input(w,el,value){el.value=value;el.dispatchEvent(new w.Event('input',{bubbles:true}));}
(async()=>{
  const fixture=JSON.parse(fs.readFileSync(path.join(root,'knowledge/demo/data/graph.json')));
  fixture.demo=false;
  let a=await open('/knowledge/',{data:{...fixture,notes:[],days:[]}});
  assert.match(a.d.querySelector('#records').textContent,/第一条理解/);
  assert.equal(a.d.querySelectorAll('.day[data-level="1"]').length,0);
  a.close();
  a=await open('/knowledge/',{data:fixture});
  assert.equal(a.d.querySelectorAll('.day-record').length,fixture.days.length);
  assert.match(a.d.querySelector('.metrics').textContent,/今天已学习/);
  assert.ok(a.d.querySelector('.entry').href.includes('/knowledge/tree/?node='));
  assert.ok(!a.d.querySelector('.entry').href.includes('/demo/'));
  a.close();
  // New domains and deeper taxonomy must work without hard-coded root names.
  const nested=structuredClone(fixture);
  nested.branches.push(
    {id:'evaluation',title:'模型评测',parent:null,description:'独立评估'},
    {id:'evaluation-methods',title:'评测方法',parent:'evaluation',description:'方法'},
    {id:'sampling-metrics',title:'采样指标',parent:'evaluation-methods',description:'指标'},
    {id:'success-estimation',title:'成功率估计',parent:'sampling-metrics',description:'估计'}
  );
  const moved=nested.notes[0];
  moved.branch='success-estimation';
  a=await open('/knowledge/?branch=evaluation',{data:nested});
  assert.equal(a.d.querySelector('#branch-filter').value,'evaluation');
  const expectedDays=nested.days.filter(day=>day.entries.some(entry=>entry.note===moved.id));
  assert.equal(a.d.querySelectorAll('.day-record').length,expectedDays.length);
  assert.ok([...a.d.querySelectorAll('.entry')].every(el=>el.href.endsWith('node='+moved.id)));
  a.close();
  a=await open('/knowledge/tree/?node='+moved.id,{data:nested});
  assert.ok(a.d.querySelector('.map-node.active').textContent.includes(moved.title));
  assert.ok(a.d.querySelector('.map-context').textContent.includes('模型评测 / 评测方法 / 采样指标 / 成功率估计'));
  a.d.querySelector('#collapse').click();
  input(a.w,a.d.querySelector('#node-search'),moved.title);
  a.d.querySelector('#node-results button').click();
  assert.ok(a.d.querySelector('.map-node.active').textContent.includes(moved.title));
  for(const title of ['模型评测','评测方法','采样指标','成功率估计']){
    assert.ok([...a.d.querySelectorAll('.map-node')].some(el=>el.textContent.includes(title)));
  }
  assert.ok(a.d.querySelector('.map-context .primary').href.endsWith('/notes/'+moved.id+'/'));
  a.close();
  const real=JSON.parse(fs.readFileSync(path.join(root,'knowledge/data/graph.json')));
  assert.equal(real.demo,false);
  if(real.days.length){
    const latest=real.days.at(-1);
    a=await open('/knowledge/?day='+latest.date,{now:latest.date+'T04:00:00Z'});
    assert.equal(a.d.querySelectorAll('.day-record').length,1);
    assert.equal(a.d.querySelectorAll('.entry').length,latest.entries.length);
    assert.ok(a.d.querySelector('#records').textContent.includes(latest.summary));
    a.close();
  }
  a=await open('/knowledge/demo/');
  assert.equal(a.d.querySelectorAll('.day-record').length,3);
  assert.match(a.d.querySelector('.metrics').textContent,/今天已学习/);
  a.d.querySelector('[data-date="2026-09-11"]').click();
  assert.equal(a.d.querySelectorAll('.day-record').length,1);
  assert.match(a.w.location.search,/day=2026-09-11/);
  assert.match(a.d.querySelector('.entry').href,/tree\/\?node=sft-loss-mask/);
  a.d.querySelector('#clear-day').click();
  input(a.w,a.d.querySelector('#record-search'),'masked');
  assert.equal(a.d.querySelectorAll('.day-record').length,1);
  input(a.w,a.d.querySelector('#record-search'),'nothing-matches');
  assert.match(a.d.querySelector('#records').textContent,/暂时没有匹配/);
  input(a.w,a.d.querySelector('#record-search'),'');
  a.d.querySelector('[data-date="2026-09-10"]').click();
  assert.match(a.d.querySelector('#records').textContent,/这一天/);
  a.close();
  a=await open('/knowledge/demo/tree/?node=react-loop',{related:true});
  assert.match(a.d.querySelector('.map-node.active').textContent,/ReAct/);
  assert.equal(a.d.querySelectorAll('.map-node').length,7);
  assert.match(a.d.querySelector('.map-context .primary').href,/notes\/react-loop/);
  assert.equal(a.d.querySelectorAll('.related-edge').length,1);
  const before=a.d.querySelector('#zoom-label').textContent;
  a.d.querySelector('#zoom-in').click();
  assert.notEqual(a.d.querySelector('#zoom-label').textContent,before);
  a.d.querySelector('#collapse').click();
  assert.equal(a.d.querySelectorAll('.map-node').length,3);
  input(a.w,a.d.querySelector('#node-search'),'SFT');
  a.d.querySelector('#node-results button').click();
  assert.match(a.d.querySelector('.map-node.active').textContent,/SFT/);
  assert.match(a.w.location.search,/node=sft-loss-mask/);
  assert.equal(a.d.querySelectorAll('#node-results button').length,0);
  a.d.querySelector('#expand').click();
  assert.equal(a.d.querySelectorAll('.map-node').length,7);
  a.close();
  a=await open('/knowledge/demo/tree/?node=not-found');
  assert.match(a.d.querySelector('#map-message').textContent,/没有找到/);
  assert.match(a.d.querySelector('.map-node.active').textContent,/我的知识体系/);
  a.close();
  a=await open('/knowledge/demo/notes/react-loop/');
  assert.ok(a.d.querySelector('.example[open]'));
  assert.ok(!a.d.querySelector('#recall details').open);
  assert.match(a.d.querySelector('.back-tree').href,/node=react-loop/);
  a.close();
  a=await open('/knowledge/',{fail:true});
  assert.match(a.d.querySelector('#learning-app').textContent,/重新加载/);
  a.close();
  console.log('DOM interaction checks passed: real/demo isolation, day filtering, search, empty/error states, tree focus, collapse/expand, zoom, related edges, detail navigation.');
})().catch(e=>{console.error(e);process.exitCode=1;});
