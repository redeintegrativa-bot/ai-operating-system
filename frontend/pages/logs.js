/**
 * AIOS Dashboard - Logs Page
 */
const Pages = window.Pages || {};
Pages.Logs = {
  _el: null, _unsubs: [],
  _filters: {search:'',level:'all'},
  _autoScroll: true,

  render() {
    const el = document.createElement('div');
    el.className = 'logs-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Logs do Sistema</h1>
          <p class="page-subtitle">Visualize e filtre logs de todos os componentes</p>
        </div>
        <div class="header-actions">
          <label class="checkbox-wrapper"><input type="checkbox" checked onchange="Pages.Logs._autoScroll=this.checked"><span>Auto-scroll</span></label>
          <button class="btn btn-outline btn-sm" onclick="Pages.Logs._copy()"><span class="material-icons">content_copy</span> Copiar</button>
          <button class="btn btn-outline btn-sm" onclick="Pages.Logs._clear()"><span class="material-icons">clear_all</span> Limpar</button>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="logs-search" placeholder="Filtrar logs..." oninput="Pages.Logs._filter({search:this.value})">
        <div class="search-bar-filters">
          <select class="form-select filter-select" id="logs-level" onchange="Pages.Logs._filter({level:this.value})">
            <option value="all">Todos níveis</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="DEBUG">DEBUG</option>
          </select>
        </div>
        <span class="log-count" id="log-count">0 logs</span>
      </div>
      <div class="log-viewer" id="log-viewer" onclick="Pages.Logs._toggleScroll()">
        <div id="log-list" class="log-row-list"><div class="empty-state"><span class="empty-icon material-icons">article</span><p class="empty-text">Nenhum log</p></div></div>
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchSystemLogs();
    this._unsubs.push(Store.subscribe('systemLogs', data => this._renderLogs(data)));
    this._unsubs.push(Store.subscribe('wsEvents', (ev) => {
      if (ev?.type && ev?.timestamp) {
        const logs = Store.state.systemLogs || [];
        logs.push({message:`${ev.type}: ${ev.data?JSON.stringify(ev.data):''}`, level:'DEBUG', time:ev.timestamp||new Date().toISOString()});
        if (logs.length > 500) logs.splice(0, logs.length - 500);
        this._renderLogs(logs);
      }
    }));
  },
  unmount() { this._unsubs.forEach(u => u()); },

  _renderLogs(logs) {
    const list = document.getElementById('log-list');
    const count = document.getElementById('log-count');
    if (!list) return;
    if (!logs || logs.length === 0) { list.innerHTML = '<div class="empty-state"><span class="empty-icon material-icons">article</span><p class="empty-text">Nenhum log</p></div>'; if (count) count.textContent = '0 logs'; return; }
    const viewer = document.getElementById('log-viewer');
    const isAtBottom = this._autoScroll && viewer && (viewer.scrollHeight - viewer.scrollTop - viewer.clientHeight < 100);
    list.innerHTML = logs.slice().reverse().slice(0,200).map(l => {
      const level = l.level || 'INFO';
      const time = l.time ? new Date(l.time).toLocaleTimeString() : '';
      return `<div class="log-row log-${level.toLowerCase()}"><span class="log-time">${time}</span><span class="log-level log-badge log-${level.toLowerCase()}">${level}</span><span class="log-source">${l.source||l.name||'system'}</span><span class="log-msg">${l.message||l.msg||''}</span></div>`;
    }).join('');
    if (count) count.textContent = `${logs.length} logs`;
    if (isAtBottom) viewer.scrollTop = viewer.scrollHeight;
  },
  _filter(changes) {
    Object.assign(this._filters, changes);
    const q = this._filters.search.toLowerCase();
    const level = this._filters.level;
    document.querySelectorAll('.log-row').forEach(row => {
      const text = row.textContent.toLowerCase();
      const lvl = row.classList.contains('log-error') ? 'ERROR' : row.classList.contains('log-warning') ? 'WARNING' : row.classList.contains('log-debug') ? 'DEBUG' : 'INFO';
      const matchSearch = !q || text.includes(q);
      const matchLevel = level === 'all' || lvl === level;
      row.classList.toggle('hidden', !(matchSearch && matchLevel));
    });
  },
  _toggleScroll() { this._autoScroll = !this._autoScroll; },
  _clear() { if (confirm('Limpar logs?')) { Store.state.systemLogs = []; this._renderLogs([]); } },
  _copy() {
    let t = '';
    document.querySelectorAll('.log-row:not(.hidden)').forEach(r => { t += r.textContent.trim() + '\n'; });
    navigator.clipboard.writeText(t).then(() => Components.Toast.success('Logs copiados')).catch(() => {});
  }
};
