(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const base = document.body.dataset.base;
  const announce = message => {
    $('.announcement').textContent = message;
    setTimeout(() => { $('.announcement').textContent = ''; }, 3000);
  };
  document.querySelectorAll('.copy-code, .copy-link').forEach(button => {
    button.addEventListener('click', async () => {
      const content = button.classList.contains('copy-code')
        ? button.closest('.code-block').querySelector('code').textContent
        : document.querySelector('link[rel="canonical"]').href;
      try {
        await navigator.clipboard.writeText(content);
        announce(button.classList.contains('copy-code') ? '代码已复制' : '链接已复制');
      } catch {
        announce('暂时无法访问剪贴板，请手动复制。');
      }
    });
  });
  if (document.body.dataset.page !== 'archive') return;
  const form = $('#filters');
  const results = $('#archive-results');
  const pagination = $('#archive-pagination');
  const error = $('#filter-error');
  const names = ['q', 'kind', 'tag', 'month', 'from', 'to'];
  const PAGE_SIZE = 12;
  let posts = [], currentPage = 1, timer;
  const param = () => new URLSearchParams(location.search);
  function restore() {
    const params = param();
    names.forEach(name => { form.elements.namedItem(name).value = params.get(name) || ''; });
    currentPage = Math.max(1, Number.parseInt(params.get('page'), 10) || 1);
  }
  function persist(replace = false) {
    const params = new URLSearchParams();
    names.forEach(name => {
      const value = form.elements.namedItem(name).value.trim();
      if (value) params.set(name, value);
    });
    if (currentPage > 1) params.set('page', currentPage);
    const next = location.pathname + (params.size ? '?' + params : '');
    if (next !== location.pathname + location.search) {
      history[replace ? 'replaceState' : 'pushState']({}, '', next);
    }
  }
  function render() {
    const state = Object.fromEntries(names.map(name => [name, form.elements.namedItem(name).value.trim()]));
    if (state.from && state.to && state.from > state.to) {
      error.textContent = '起始日期不能晚于结束日期。'; error.hidden = false;
      results.innerHTML = ''; pagination.innerHTML = ''; $('#result-count').textContent = '请调整日期范围';
      return;
    }
    error.hidden = true;
    const words = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    const matches = posts.filter(post =>
      (!state.kind || post.kind === state.kind) &&
      (!state.tag || post.tags.includes(state.tag)) &&
      (!state.month || post.date.startsWith(state.month)) &&
      (!state.from || post.date >= state.from) && (!state.to || post.date <= state.to) &&
      words.every(word => post.search.toLowerCase().includes(word))
    );
    const pages = Math.max(1, Math.ceil(matches.length / PAGE_SIZE));
    currentPage = Math.min(currentPage, pages);
    $('#result-count').textContent = `${matches.length} 条记录`;
    const visible = matches.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
    results.replaceChildren();
    let month = '';
    visible.forEach(post => {
      if (post.date.slice(0, 7) !== month) {
        month = post.date.slice(0, 7);
        const heading = document.createElement('h2');
        heading.className = 'month-label'; heading.textContent = month.replace('-', ' / ');
        results.append(heading);
      }
      // HTML is produced by the escaping, schema-validated static builder, never query text.
      results.insertAdjacentHTML('beforeend', post.html);
    });
    if (!visible.length) {
      const box = document.createElement('div'); box.className = 'empty';
      const h = document.createElement('h2'); h.textContent = posts.length ? '这组条件下，还没有记录。' : '还没有发布的想法。';
      const p = document.createElement('p'); p.textContent = posts.length ? '换一个词，或放宽日期范围。' : '下一次讨论里的灵光一闪，可以从这里留下来。';
      box.append(h, p); results.append(box);
    }
    pagination.innerHTML = pages > 1 ? `<nav class="pagination" aria-label="筛选结果翻页"><button data-page="${currentPage - 1}" ${currentPage === 1 ? 'disabled' : ''}>← 上一页</button><span>${currentPage} / ${pages}</span><button data-page="${currentPage + 1}" ${currentPage === pages ? 'disabled' : ''}>下一页 →</button></nav>` : '';
  }
  async function start() {
    const response = await fetch(`${base}/data/index.json`, {cache: 'no-cache'});
    if (!response.ok) throw new Error('索引暂时没有加载成功。');
    posts = (await response.json()).posts;
    restore(); render(); persist(true);
    form.addEventListener('submit', event => { event.preventDefault(); clearTimeout(timer); currentPage = 1; render(); persist(); });
    form.addEventListener('input', event => {
      if (event.target.name !== 'q') return;
      clearTimeout(timer); timer = setTimeout(() => { currentPage = 1; render(); persist(true); }, 150);
    });
    form.addEventListener('change', event => {
      if (event.target.name === 'q') return;
      clearTimeout(timer); currentPage = 1; render(); persist();
    });
    form.addEventListener('reset', () => {
      clearTimeout(timer);
      setTimeout(() => { currentPage = 1; render(); persist(); }, 0);
    });
    pagination.addEventListener('click', event => {
      const button = event.target.closest('[data-page]');
      if (!button || button.disabled) return;
      currentPage = Number(button.dataset.page); render(); persist();
      $('#result-count').scrollIntoView({block: 'start', behavior: 'smooth'});
    });
    window.addEventListener('popstate', () => { clearTimeout(timer); restore(); render(); });
  }
  start().catch(() => {
    error.textContent = '筛选索引暂时无法加载。下方已有记录仍可阅读，刷新页面可重试。';
    error.hidden = false;
    form.querySelectorAll('input, select, button').forEach(control => { control.disabled = true; });
  });
})();
