/* No framework or third-party runtime: GitHub Pages serves these views directly. */
(() => {
  'use strict';
  const base = document.body.dataset.base;
  const page = document.body.dataset.page;
  const $ = (s, root = document) => root.querySelector(s);
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt = d => d.toISOString().slice(0, 10);
  const asDate = s => new Date(`${s}T12:00:00Z`);
  const addDays = (s, n) => { const d = asDate(s); d.setUTCDate(d.getUTCDate() + n); return fmt(d); };
  const daysBetween = (a, b) => Math.round((asDate(a) - asDate(b)) / 86400000);
  const todayIn = tz => new Intl.DateTimeFormat('en-CA', {timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  const query = () => new URLSearchParams(location.search);
  function setQuery(values, replace = false) {
    const p = query();
    Object.entries(values).forEach(([k,v]) => v ? p.set(k,v) : p.delete(k));
    history[replace ? 'replaceState' : 'pushState']({}, '', `${location.pathname}${p.size ? '?' + p : ''}`);
  }
  function empty(title, description, action = '') { return `<div class="empty"><div class="empty-mark">↗</div><h2>${title}</h2><p>${description}</p>${action}</div>`; }
  if (page === 'detail') {
    document.querySelectorAll('.copy-code').forEach(button => button.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(button.parentElement.nextElementSibling.textContent); button.textContent = '已复制'; }
      catch { button.textContent = '请手动选择复制'; }
      setTimeout(() => { button.textContent = '复制'; }, 1800);
    }));
    return;
  }
  async function start() {
    const response = await fetch(`${base}/data/graph.json`, {cache:'no-cache'});
    if (!response.ok) throw new Error('无法读取知识数据');
    const data = await response.json();
    const notes = new Map(data.notes.map(n => [n.id,n]));
    const branches = new Map(data.branches.map(b => [b.id,b]));
    const today = data.demo && data.days.length ? data.days.at(-1).date : todayIn(data.timezone);
    const treeLink = id => `${base}/tree/?node=${encodeURIComponent(id)}`;
    const rootOf = id => { let b = branches.get(id); while (b?.parent) b = branches.get(b.parent); return b?.id; };
    if (page === 'home') home(data, notes, branches, today, treeLink, rootOf);
    else tree(data, notes, branches, treeLink, rootOf);
  }
  function home(data, notes, branches, today, treeLink, rootOf) {
    const app = $('#learning-app');
    const records = data.days.filter(d => d.date <= today);
    const byDay = new Map(records.map(d => [d.date,d]));
    const last = records.at(-1)?.date;
    const gap = last ? daysBetween(today,last) : null;
    let streak = 0, cursor = byDay.has(today) ? today : addDays(today,-1);
    while (byDay.has(cursor)) { streak++; cursor = addDays(cursor,-1); }
    const currentYear = Number(today.slice(0,4));
    const years = [...new Set([currentYear,...records.map(d => Number(d.date.slice(0,4)))])].sort((a,b)=>b-a);
    let year = Number(query().get('year')) || Number(query().get('day')?.slice(0,4)) || currentYear;
    if (!years.includes(year)) year = currentYear;
    const roots = data.branches.filter(b => !b.parent);
    app.innerHTML = `<section class="metrics" aria-label="学习概况"><div class="metric"><div class="metric-label">距离上次学习</div><div class="metric-value metric-status">${gap === null ? '从今天开始' : gap === 0 ? '<span class="status-dot"></span>今天已学习' : `${gap}<small>天 · 回来学一点</small>`}</div></div><div class="metric"><div class="metric-label">累计学习</div><div class="metric-value">${records.length}<small>天</small></div></div><div class="metric"><div class="metric-label">沉淀知识</div><div class="metric-value">${notes.size}<small>个知识点</small></div></div><div class="metric"><div class="metric-label">连续学习</div><div class="metric-value">${streak}<small>天</small></div></div></section>
    <section class="panel calendar-panel"><div class="panel-head"><h2>学习足迹 <span class="muted small" id="year-total"></span></h2><div class="calendar-controls"><label class="small muted" for="year">年份</label><select id="year">${years.map(y=>`<option ${y===year?'selected':''}>${y}</option>`).join('')}</select></div></div><div class="calendar-scroll"><div id="calendar" class="calendar" aria-label="每日学习日历"></div></div><div class="calendar-meta"><span id="calendar-caption"></span><span class="legend">少 <i></i><i></i><i></i><i></i> 多</span></div></section>
    <div class="home-columns"><section><div class="section-title"><h2>每日记录</h2><span class="muted small" id="record-total"></span></div><div class="filter-bar"><input id="record-search" class="search" type="search" placeholder="搜索知识点、当天的理解…" aria-label="搜索学习记录"><select id="branch-filter" aria-label="按知识领域筛选"><option value="">所有领域</option>${roots.map(b=>`<option value="${b.id}">${esc(b.title)}</option>`).join('')}</select></div><div id="active-filter"></div><div id="records"></div><button id="load-more" class="hidden">查看更多记录 ↓</button></section><aside class="home-sidebar"><section class="sidebar-section"><h3>正在生长的领域</h3>${roots.map(b=>{const count=data.notes.filter(n=>rootOf(n.branch)===b.id).length;return `<a class="branch-link" href="${treeLink(b.id)}"><div class="branch-link-top"><span>${esc(b.title)}</span><span class="muted">${count} ↗</span></div><p>${esc(b.description)}</p><div class="track"><span style="width:${notes.size ? Math.round(count/notes.size*100) : 0}%"></span></div></a>`;}).join('')}</section><section class="sidebar-section sidebar-note"><h3>学过，也要再想起。</h3><p>${last ? '回到最近的一次理解，试着用自己的话复述。' : '知识库已经准备好。第一天的学习，会从这里开始生长。'}</p>${last ? `<a href="${treeLink(records.at(-1).entries[0].note)}">重温最近的知识点 ↗</a>` : `<a href="/knowledge/demo/">看看完整演示 ↗</a>`}</section></aside></div>`;
    let selected = query().get('day') || '';
    let search = query().get('q') || '';
    let branch = query().get('branch') || '';
    let limit = 14;
    $('#record-search').value = search;
    $('#branch-filter').value = branch;
    function calendar() {
      const start = `${year}-01-01`, end = `${year}-12-31`;
      const offset = (asDate(start).getUTCDay() + 6) % 7;
      let content = '<span class="day blank"></span>'.repeat(offset);
      for(let d=start;d<=end;d=addDays(d,1)) {
        const record=byDay.get(d), count=record?.entries.length || 0;
        const label=`${d} · ${d>today?'尚未到来':count?record.entries.map(e=>notes.get(e.note).title).join('、'):'未记录学习'}`;
        content += `<button class="day ${d>today?'future':''}" data-date="${d}" data-level="${Math.min(count,4)}" ${d>today?'disabled':''} aria-label="${esc(label)}" title="${esc(label)}" aria-pressed="${selected===d}"></button>`;
      }
      $('#calendar').innerHTML=content;
      $('#year-total').textContent=` / ${records.filter(d=>d.date.startsWith(String(year))).length} 天`;
      $('#calendar-caption').textContent=`${year} 年 1 月 — 12 月 · 点击日期，查看当天的理解`;
    }
    function renderRecords() {
      const term=search.trim().toLowerCase();
      const matched=records.slice().reverse().filter(d=>!selected || d.date===selected).map(d=>({...d,entries:d.entries.filter(e=>{
        const n=notes.get(e.note);
        return (!branch || rootOf(n.branch)===branch) && (!term || [n.title,n.summary,...n.aliases,e.takeaway,d.summary,d.date].join(' ').toLowerCase().includes(term));
      })})).filter(d=>d.entries.length);
      $('#record-total').textContent=`${matched.length} 天`;
      $('#active-filter').innerHTML=selected?`<div class="active-filter">${esc(selected)}<button id="clear-day">查看全部日期 ×</button></div>`:'';
      $('#records').innerHTML=matched.slice(0,limit).map(d=>`<article class="day-record"><div class="day-label"><strong>${d.date.slice(5).replace('-','.')}</strong><span>${d.date.slice(0,4)} · ${['周日','周一','周二','周三','周四','周五','周六'][asDate(d.date).getUTCDay()]}</span></div><div><h3 class="record-heading">${esc(d.summary)}</h3>${d.entries.map(e=>{const n=notes.get(e.note);return `<a class="entry" href="${treeLink(n.id)}"><div class="entry-top"><strong>${esc(n.title)}</strong><span class="tag">${e.kind==='review'?'回顾':esc(branches.get(n.branch).title)}</span><span class="arrow">↗</span></div><p>${esc(e.takeaway)}</p></a>`;}).join('')}</div></article>`).join('') || empty(selected?'这一天，还没有匹配的学习记录':search||branch?'暂时没有匹配的知识':'第一条理解，留给下一次学习。',selected?'选择其他日期，或回到全部记录。':search||branch?'换个关键词或领域试试。':'在当天学习结束时，对 Codex 说「收工」。',!records.length?'<a class="primary" href="/knowledge/demo/">体验学习 → 知识树 → 详情 ↗</a>':'');
      $('#load-more').classList.toggle('hidden',matched.length<=limit);
      $('#clear-day')?.addEventListener('click',()=>{selected='';setQuery({day:''});calendar();renderRecords();});
    }
    $('#calendar').addEventListener('click',e=>{const b=e.target.closest('[data-date]');if(!b)return;selected=b.dataset.date;limit=14;setQuery({day:selected,year});calendar();renderRecords();$('#records').scrollIntoView({block:'nearest',behavior:'smooth'});});
    $('#calendar').addEventListener('keydown',e=>{const b=e.target.closest('[data-date]');if(!b)return;const delta={ArrowLeft:-7,ArrowRight:7,ArrowUp:-1,ArrowDown:1}[e.key];if(delta){e.preventDefault();$(`[data-date="${addDays(b.dataset.date,delta)}"]`)?.focus();}});
    $('#year').addEventListener('change',e=>{year=Number(e.target.value);selected='';setQuery({year,day:''});calendar();renderRecords();});
    $('#record-search').addEventListener('input',e=>{search=e.target.value;limit=14;setQuery({q:search},true);renderRecords();});
    $('#branch-filter').addEventListener('change',e=>{branch=e.target.value;limit=14;setQuery({branch});renderRecords();});
    $('#load-more').addEventListener('click',()=>{limit+=14;renderRecords();});
    window.addEventListener('popstate',()=>{selected=query().get('day')||'';year=Number(query().get('year'))||Number(selected.slice(0,4))||currentYear;search=query().get('q')||'';branch=query().get('branch')||'';$('#year').value=year;$('#record-search').value=search;$('#branch-filter').value=branch;calendar();renderRecords();});
    calendar();renderRecords();
  }
  function tree(data, notes, branches, treeLink, rootOf) {
    const app=$('#tree-app');
    $('#tree-count').textContent=`${notes.size} 个知识点 · ${branches.size} 个分支`;
    app.innerHTML=`<div class="tree-toolbar"><div class="tree-search"><input class="search" id="node-search" type="search" placeholder="搜索知识点，直接定位…" aria-label="搜索并定位知识节点" autocomplete="off"><div id="node-results" class="search-results"></div></div><div class="tree-tools"><button id="zoom-out" aria-label="缩小">−</button><span id="zoom-label" class="small muted">100%</span><button id="zoom-in" aria-label="放大">＋</button><button id="fit">适应画布</button><button id="collapse">收起分支</button><button id="expand">展开全部</button></div></div><div id="map-message" aria-live="polite"></div><div class="map-layout"><div class="map-canvas" tabindex="0" role="region" aria-label="可交互知识树；方向键平移，加减键缩放，Home 适应画布"><div class="map-world"></div><div class="map-help">拖动平移 · 滚轮 / 双指缩放 · 点击节点查看上下文</div></div><aside class="map-context" aria-live="polite"></aside></div><details class="tree-outline"><summary>以大纲浏览全部知识 · 键盘与小屏幕友好</summary><div class="outline-items"></div></details>`;
    const root={id:'knowledge-root',title:'我的知识体系',parent:null,type:'root',description:'把零散的理解，连接成持续生长的知识框架。'};
    const all=new Map([[root.id,root],...data.branches.map(b=>[b.id,{...b,parent:b.parent||root.id,type:'branch'}]),...data.notes.map(n=>[n.id,{...n,parent:n.branch,type:'note'}])]);
    const children=new Map([...all.keys()].map(id=>[id,[]]));
    all.forEach(n=>{if(n.parent)children.get(n.parent).push(n.id);});
    const open=new Set(all.size<=80 ? all.keys() : [root.id,...data.branches.filter(b=>!b.parent).map(b=>b.id)]);
    let selected=root.id,positions=new Map(),scale=1,tx=0,ty=0,totalWidth=0,totalHeight=0;
    const canvas=$('.map-canvas'),world=$('.map-world');
    function transform(){world.style.transform=`translate(${tx}px,${ty}px) scale(${scale})`;$('#zoom-label').textContent=`${Math.round(scale*100)}%`;}
    function zoom(factor,x=canvas.clientWidth/2,y=canvas.clientHeight/2){const next=Math.min(2,Math.max(.18,scale*factor));tx=x-(x-tx)*next/scale;ty=y-(y-ty)*next/scale;scale=next;transform();}
    function fit(){scale=Math.min(1.1,Math.max(.18,Math.min((canvas.clientWidth-70)/totalWidth,(canvas.clientHeight-70)/totalHeight)));tx=(canvas.clientWidth-totalWidth*scale)/2;ty=(canvas.clientHeight-totalHeight*scale)/2;transform();}
    function center(id){const p=positions.get(id);if(!p)return;scale=Math.max(scale,.85);tx=canvas.clientWidth/2-(p.x+96)*scale;ty=canvas.clientHeight/2-(p.y+31)*scale;transform();}
    function render(){
      positions=new Map();let leaf=0,maxDepth=0;
      function place(id,depth){maxDepth=Math.max(maxDepth,depth);const kids=open.has(id)?children.get(id):[];let y;if(kids.length){const ys=kids.map(k=>place(k,depth+1));y=(ys[0]+ys.at(-1))/2;}else{y=leaf++*90;}positions.set(id,{x:depth*260,y});return y;}
      place(root.id,0);totalWidth=maxDepth*260+192;totalHeight=Math.max(1,leaf)*90;
      let paths='';
      positions.forEach((p,id)=>{const n=all.get(id),parent=positions.get(n.parent);if(parent){const x=parent.x+192,y=parent.y+31;paths+=`<path d="M ${x} ${y} C ${x+34} ${y}, ${p.x-34} ${p.y+31}, ${p.x} ${p.y+31}"/>`;}});
      const current=notes.get(selected);
      if(current){const related=new Set([...current.related,...data.notes.filter(n=>n.related.includes(selected)).map(n=>n.id)]);related.forEach(id=>{const a=positions.get(selected),b=positions.get(id);if(a&&b)paths+=`<path class="related-edge" d="M ${a.x+96} ${a.y+62} C ${a.x+96} ${a.y+100}, ${b.x+96} ${b.y+100}, ${b.x+96} ${b.y+62}"/>`;});}
      world.innerHTML=`<svg class="map-lines" aria-hidden="true" width="${totalWidth}" height="${totalHeight}">${paths}</svg>`+[...positions].map(([id,p])=>{const n=all.get(id),kids=children.get(id);return `<div class="map-node ${n.type} ${selected===id?'active':''}" style="left:${p.x}px;top:${p.y}px"><button class="node-main" data-node="${id}" title="${esc(n.title)}" aria-pressed="${selected===id}"><span>${esc(n.title)}</span><small>${n.type==='note'?'知识点 · 查看详情 ↗':n.type==='root'?'AGENTS & MODEL TRAINING':`${kids.length} 个直接子节点`}</small></button>${kids.length?`<button class="node-toggle" data-toggle="${id}" aria-label="${open.has(id)?'收起':'展开'} ${esc(n.title)}" aria-expanded="${open.has(id)}">${open.has(id)?'−':'+'}</button>`:''}</div>`;}).join('');
      transform();
    }
    function context(){
      const n=all.get(selected),isNote=n.type==='note';
      const trail=[];let p=n.parent;while(p){trail.unshift(all.get(p).title);p=all.get(p).parent;}
      const related=isNote?[...new Set([...n.related,...data.notes.filter(a=>a.related.includes(n.id)).map(a=>a.id)])]:[];
      $('.map-context').innerHTML=`<div class="eyebrow">${isNote?'SELECTED KNOWLEDGE':'KNOWLEDGE BRANCH'}</div><p class="small">${esc(trail.join(' / ')||'从这里开始')}</p><h2>${esc(n.title)}</h2><p>${esc(n.summary||n.description)}</p>${isNote?`<div class="memory-mini">${esc(n.memory[0])}</div><a class="primary" href="${base}/notes/${n.id}/">进入知识详情 ↗</a>`:''}${n.parent?`<h3>上层位置</h3><a class="context-link" href="${treeLink(n.parent)}" data-focus="${n.parent}">${esc(all.get(n.parent).title)} ↑</a>`:''}<h3>${isNote?'相关知识':'下层分支与知识'}</h3>${(isNote?related:children.get(n.id)).map(id=>`<a class="context-link" href="${treeLink(id)}" data-focus="${id}">${esc(all.get(id).title)} ↗</a>`).join('')||'<p>这个位置还在等待新的连接。</p>'}${!notes.size?'<p>目前尚无真实学习记录。</p><a class="context-link" href="/knowledge/demo/tree/">查看完整交互演示 ↗</a>':''}`;
    }
    function select(id,update=true,focus=true){if(!all.has(id)){ $('#map-message').innerHTML='<p class="map-error">没有找到这个节点，已展示完整知识树。</p>';id=root.id;}else $('#map-message').textContent='';selected=id;let p=all.get(id).parent;while(p){open.add(p);p=all.get(p).parent;}if(all.get(id).type!=='note')open.add(id);render();context();if(focus)center(id);if(update)setQuery({node:id});}
    function outline(id){const n=all.get(id);return `<li><button data-focus="${id}">${esc(n.title)}${n.type==='note'?' ↗':''}</button>${children.get(id).length?`<ul>${children.get(id).map(outline).join('')}</ul>`:''}</li>`;}
    $('.outline-items').innerHTML=`<ul>${outline(root.id)}</ul>`;
    app.addEventListener('click',e=>{const node=e.target.closest('[data-node]'),toggle=e.target.closest('[data-toggle]'),focus=e.target.closest('[data-focus]');if(node){if(selected===node.dataset.node && notes.has(selected)){location.href=`${base}/notes/${selected}/`;return;}select(node.dataset.node);}if(toggle){const id=toggle.dataset.toggle;open.has(id)?open.delete(id):open.add(id);render();}if(focus){e.preventDefault();select(focus.dataset.focus);$('#node-results').innerHTML='';$('#node-search').value='';}});
    world.addEventListener('focusin',e=>{const b=e.target.closest('[data-node]');if(b)center(b.dataset.node);});
    $('#node-search').addEventListener('input',e=>{const q=e.target.value.trim().toLowerCase();const matches=[...all.values()].filter(n=>[n.title,n.summary,...(n.aliases||[])].join(' ').toLowerCase().includes(q)).slice(0,20);$('#node-results').innerHTML=q?(matches.map(n=>`<button data-focus="${n.id}">${esc(n.title)}<small>${n.type==='note'?esc(branches.get(n.branch).title):'分类分支'}</small></button>`).join('')||'<p class="small muted" style="padding:12px">没有匹配节点</p>'):'';});
    $('#node-search').addEventListener('keydown',e=>{if(e.key==='Escape')$('#node-results').innerHTML='';if(e.key==='ArrowDown'){e.preventDefault();$('#node-results button')?.focus();}if(e.key==='Enter')$('#node-results button')?.click();});
    $('#zoom-in').onclick=()=>zoom(1.25);$('#zoom-out').onclick=()=>zoom(.8);$('#fit').onclick=fit;
    $('#collapse').onclick=()=>{open.clear();open.add(root.id);selected=root.id;setQuery({node:root.id});render();context();fit();};
    $('#expand').onclick=()=>{all.forEach((_,id)=>open.add(id));render();fit();};
    canvas.addEventListener('wheel',e=>{e.preventDefault();const r=canvas.getBoundingClientRect();zoom(Math.exp(-e.deltaY*.002),e.clientX-r.left,e.clientY-r.top);},{passive:false});
    const pointers=new Map();let previous=null;
    function gesture(){const ps=[...pointers.values()];if(ps.length===1)return{x:ps[0].x,y:ps[0].y,d:0};if(ps.length>1)return{x:(ps[0].x+ps[1].x)/2,y:(ps[0].y+ps[1].y)/2,d:Math.hypot(ps[0].x-ps[1].x,ps[0].y-ps[1].y)};return null;}
    canvas.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});previous=gesture();});
    canvas.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});const next=gesture();if(previous){tx+=next.x-previous.x;ty+=next.y-previous.y;if(next.d&&previous.d){const r=canvas.getBoundingClientRect();zoom(next.d/previous.d,next.x-r.left,next.y-r.top);}else transform();}previous=next;});
    const release=e=>{pointers.delete(e.pointerId);previous=gesture();};canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);
    canvas.addEventListener('keydown',e=>{if(e.target!==canvas)return;const changes={ArrowLeft:[40,0],ArrowRight:[-40,0],ArrowUp:[0,40],ArrowDown:[0,-40]};if(changes[e.key]){e.preventDefault();tx+=changes[e.key][0];ty+=changes[e.key][1];transform();}if(['+','=','-','Home'].includes(e.key)){e.preventDefault();e.key==='Home'?fit():zoom(e.key==='-'?.8:1.25);}});
    new ResizeObserver(()=>{if(query().has('node'))center(selected);else fit();}).observe(canvas);
    window.addEventListener('popstate',()=>select(query().get('node')||root.id,false));
    select(query().get('node')||root.id,false,false);if(query().has('node'))center(selected);else fit();
  }
  start().catch(error=>{
    const target=$('#learning-app')||$('#tree-app');
    target.innerHTML=empty('知识库暂时没有打开',esc(error.message),'<button onclick="location.reload()">重新加载</button>');
  });
})();
