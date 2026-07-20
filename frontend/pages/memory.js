/**
 * AIOS Dashboard - Memory Page
 */
const Pages = window.Pages || {};
Pages.Memory = {
  _el: null, _unsubs: [],
  _filter: {search:'',type:'all'},

  render() {
    const el = document.createElement('div');
    el.className = 'memory-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Memória do Sistema</h1>
          <p class="page-subtitle">Memórias episódica, semântica e procedural dos agentes</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary btn-sm"><span class="material-icons">add</span> Nova Memória</button>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="memory-search" placeholder="Buscar na memória..." oninput="Pages.Memory._filter({search:this.value})">
        <div class="search-bar-filters">
          <select class="form-select filter-select" id="memory-type" onchange="Pages.Memory._filter({type:this.value})">
            <option value="all">Todos tipos</option>
            <option value="episodic">Episódica</option>
            <option value="semantic">Semântica</option>
            <option value="procedural">Procedural</option>
          </select>
        </div>
      </div>
      <div class="memory-timeline" id="memory-timeline">
        <div class="loading-spinner"></div>
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchMemories();
    this._unsubs.push(Store.subscribe('memories', data => this._renderTimeline(data)));
    this._unsubs.push(Store.subscribe('loading', () => {
      if (Store.loading.memories && document.getElementById('memory-timeline'))
        document.getElementById('memory-timeline').innerHTML = '<div class="loading-spinner"></div>';
    }));
  },
  unmount() { this._unsubs.forEach(u => u()); },

  _renderTimeline(memories) {
    const container = document.getElementById('memory-timeline');
    if (!container) return;
    if (!memories || memories.length === 0) { container.innerHTML = '<div class="empty-state"><span class="empty-icon material-icons">memory</span><p class="empty-text">Nenhuma memória registrada</p></div>'; return; }
    const typeIcons = {episodic:'📖',semantic:'📚',procedural:'⚙️'};
    const typeLabels = {episodic:'Episódica',semantic:'Semântica',procedural:'Procedural'};
    container.innerHTML = memories.map(m => `
      <div class="memory-item" data-memory-type="${m.memory_type||m.type||'episodic'}" data-memory-content="${(m.content||'').toLowerCase()}">
        <div class="memory-marker"></div>
        <div class="memory-content">
          <div class="memory-header">
            <span class="memory-type-badge memory-${m.memory_type||m.type||'episodic'}">${typeIcons[m.memory_type||m.type||'episodic']} ${typeLabels[m.memory_type||m.type||'episodic']}</span>
            <span class="memory-time">${m.timestamp||m.time?new Date(m.timestamp||m.time).toLocaleString():'—'}</span>
            ${m.agent ? `<span class="memory-agent">${m.agent}</span>` : ''}
          </div>
          <p class="memory-text">${m.content||''}</p>
          ${m.tags && m.tags.length ? `<div class="memory-tags">${m.tags.map(t => `<span class="tag">${t}</span>`).join('')}</div>` : ''}
        </div>
      </div>
    `).join('');
  },
  _filter(changes) {
    Object.assign(this._filter, changes);
    const q = this._filter.search.toLowerCase();
    const type = this._filter.type;
    document.querySelectorAll('.memory-item').forEach(item => {
      const t = item.dataset.memoryType;
      const content = item.dataset.memoryContent;
      const matchSearch = !q || content.includes(q);
      const matchType = type === 'all' || t === type;
      item.classList.toggle('hidden', !(matchSearch && matchType));
    });
  }
};
