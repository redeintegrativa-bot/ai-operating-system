/**
 * AIOS Dashboard - Agents Page
 */
const Pages = window.Pages || {};
Pages.Agents = {
  _el: null, _unsubs: [],

  render() {
    const el = document.createElement('div');
    el.className = 'agents-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Agentes</h1>
          <p class="page-subtitle">Gerencie os agentes de IA do sistema</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary btn-sm"><span class="material-icons">add</span> Novo Agente</button>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="agents-search" placeholder="Filtrar agentes..." oninput="Pages.Agents._filter(this.value)">
      </div>
      <div class="agents-grid grid-3" id="agents-grid">
        <div class="loading-spinner"></div>
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchAgents();
    this._unsubs.push(Store.subscribe('agents', data => this._renderGrid(data)));
    this._unsubs.push(Store.subscribe('loading', () => {
      if (Store.loading.agents && document.getElementById('agents-grid'))
        document.getElementById('agents-grid').innerHTML = '<div class="loading-spinner"></div>';
    }));
  },
  unmount() { this._unsubs.forEach(u => u()); },

  _renderGrid(agents) {
    const grid = document.getElementById('agents-grid');
    if (!grid) return;
    if (!agents || agents.length === 0) { grid.innerHTML = '<div class="empty-state"><span class="empty-icon material-icons">smart_toy</span><p class="empty-text">Nenhum agente disponível</p></div>'; return; }
    grid.innerHTML = agents.map(a => `
      <div class="agent-card card" data-agent-name="${a.name.toLowerCase()}">
        <div class="card-header">
          <span class="agent-avatar">${a.avatar||'🤖'}</span>
          <div>
            <h3 class="card-title">${a.name}</h3>
            <span class="status-badge status-${a.status||'offline'}">${a.status||'offline'}</span>
          </div>
        </div>
        <div class="card-body">
          <div class="agent-capabilities">
            <span class="cap-label">Capacidades:</span>
            <div class="agent-tags">${(a.capabilities||[]).map(c => `<span class="tag">${c}</span>`).join('')}</div>
          </div>
          ${a.currentTask ? `<div class="agent-current-task"><span class="task-label">Tarefa atual:</span><span>${a.currentTask}</span></div>` : ''}
        </div>
      </div>
    `).join('');
  },
  _filter(val) {
    const q = val.toLowerCase();
    document.querySelectorAll('.agent-card').forEach(c => {
      c.classList.toggle('hidden', !(c.dataset.agentName||'').includes(q));
    });
  }
};
