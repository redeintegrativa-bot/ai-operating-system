/**
 * AIOS Mission Control - Memory Page
 * Memory browser with episodic, semantic, and procedural types.
 */
const Pages = window.Pages || {};

Pages.Memory = {
  _filter: { type: 'all', search: '' },
  _selectedId: null,

  render() {
    const el = document.createElement('div');
    el.className = 'memory-page animate-fade-in';

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Memory Bank</h1>
          <p class="page-subtitle">Browse and search the knowledge base</p>
        </div>
      </div>
      <div class="memory-stats" id="mem-stats"></div>
      <div class="filter-bar">
        <div class="filter-search" style="max-width: 300px;">
          <span class="filter-search-icon">🔍</span>
          <input type="text" placeholder="Search memories..." id="mem-search" aria-label="Search memories">
        </div>
      </div>
      <div class="memory-layout" id="mem-layout"></div>
    `;

    requestAnimationFrame(() => {
      this._renderStats(el);
      this._renderLayout(el);
      this._bindEvents(el);
    });

    return el;
  },

  _renderStats(container) {
    const stats = container.querySelector('#mem-stats');
    if (!stats) return;

    const memories = Store.state.memories;
    const episodic = memories.filter(m => m.type === 'episodic').length;
    const semantic = memories.filter(m => m.type === 'semantic').length;
    const procedural = memories.filter(m => m.type === 'procedural').length;

    stats.innerHTML = `
      <div class="memory-stat"><span>Total</span> <span class="memory-stat-value">${memories.length}</span></div>
      <div class="memory-stat"><span style="color: var(--accent-blue);">Episodic</span> <span class="memory-stat-value">${episodic}</span></div>
      <div class="memory-stat"><span style="color: var(--accent-purple);">Semantic</span> <span class="memory-stat-value">${semantic}</span></div>
      <div class="memory-stat"><span style="color: var(--accent-green);">Procedural</span> <span class="memory-stat-value">${procedural}</span></div>
    `;
  },

  _renderLayout(container) {
    const layout = container.querySelector('#mem-layout');
    if (!layout) return;

    const allTags = [...new Set(Store.state.memories.flatMap(m => m.tags || []))].sort();

    layout.innerHTML = `
      <div class="memory-sidebar">
        <div class="memory-sidebar-title">Types</div>
        <div class="memory-type-item ${this._filter.type === 'all' ? 'active' : ''}" data-type="all">
          <span>All</span> <span class="memory-type-count">${Store.state.memories.length}</span>
        </div>
        <div class="memory-type-item ${this._filter.type === 'episodic' ? 'active' : ''}" data-type="episodic">
          <span>📖 Episodic</span> <span class="memory-type-count">${Store.state.memories.filter(m => m.type === 'episodic').length}</span>
        </div>
        <div class="memory-type-item ${this._filter.type === 'semantic' ? 'active' : ''}" data-type="semantic">
          <span>💡 Semantic</span> <span class="memory-type-count">${Store.state.memories.filter(m => m.type === 'semantic').length}</span>
        </div>
        <div class="memory-type-item ${this._filter.type === 'procedural' ? 'active' : ''}" data-type="procedural">
          <span>🔧 Procedural</span> <span class="memory-type-count">${Store.state.memories.filter(m => m.type === 'procedural').length}</span>
        </div>
        <div class="memory-sidebar-title" style="margin-top: 16px;">Tags</div>
        <div class="memory-tag-cloud">
          ${allTags.map(t => `<span class="tag">${t}</span>`).join('')}
        </div>
      </div>
      <div class="memory-list" id="mem-list"></div>
      <div class="memory-detail" id="mem-detail">
        <div class="empty-state">
          <div class="empty-state-icon">🧠</div>
          <div class="empty-state-text">Select a memory to view details</div>
        </div>
      </div>
    `;

    this._renderMemoryList(layout);
    this._bindLayoutEvents(layout);
  },

  _renderMemoryList(layout) {
    const list = layout.querySelector('#mem-list');
    if (!list) return;

    let memories = [...Store.state.memories];

    if (this._filter.type !== 'all') {
      memories = memories.filter(m => m.type === this._filter.type);
    }
    if (this._filter.search) {
      const q = this._filter.search.toLowerCase();
      memories = memories.filter(m => m.title.toLowerCase().includes(q) || m.content.toLowerCase().includes(q));
    }

    if (memories.length === 0) {
      list.innerHTML = '<div class="empty-state" style="padding: 32px;"><div class="empty-state-text">No memories found</div></div>';
      return;
    }

    list.innerHTML = memories.map(m => {
      const agent = Store.findById('agents', m.agent);
      const isActive = this._selectedId === m.id;
      const preview = m.content.substring(0, 100) + (m.content.length > 100 ? '...' : '');

      return `
        <div class="memory-list-item ${isActive ? 'active' : ''}" data-mem-id="${m.id}">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span class="memory-list-title">${m.title}</span>
            <span class="badge badge-${m.type === 'episodic' ? 'blue' : m.type === 'semantic' ? 'purple' : 'green'}">${m.type}</span>
          </div>
          <div class="memory-list-preview">${preview}</div>
          <div class="memory-list-meta">
            ${agent ? `<span>${agent.avatar} ${agent.name}</span>` : ''}
            <span>📅 ${m.date}</span>
          </div>
        </div>
      `;
    }).join('');

    list.querySelectorAll('.memory-list-item').forEach(item => {
      item.addEventListener('click', () => {
        const id = parseInt(item.dataset.memId);
        this._selectedId = id;
        this._showDetail(layout, Store.findById('memories', id));
        list.querySelectorAll('.memory-list-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
      });
    });
  },

  _showDetail(layout, memory) {
    const detail = layout.querySelector('#mem-detail');
    if (!detail || !memory) return;

    const agent = Store.findById('agents', memory.agent);
    const typeBadge = memory.type === 'episodic' ? 'badge-blue' : memory.type === 'semantic' ? 'badge-purple' : 'badge-green';

    detail.innerHTML = `
      <div class="memory-detail-header">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
          <div class="memory-detail-title">${memory.title}</div>
          <span class="badge ${typeBadge}">${memory.type}</span>
        </div>
        <div class="memory-detail-meta">
          ${agent ? `<span>${agent.avatar} ${agent.name}</span>` : ''}
          <span>📅 ${memory.date}</span>
        </div>
      </div>
      <div class="memory-detail-content" style="white-space: pre-wrap;">${memory.content}</div>
      <div style="margin-top: 16px;">
        <div class="form-label">Tags</div>
        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
          ${(memory.tags || []).map(t => `<span class="badge badge-tag">${t}</span>`).join('')}
        </div>
      </div>
      <div style="margin-top: 16px;">
        <button class="btn btn-secondary btn-sm" onclick="App.showToast('Share feature coming soon', 'info')">📤 Share</button>
      </div>
    `;
  },

  _bindEvents(container) {
    container.querySelector('#mem-search')?.addEventListener('input', (e) => {
      this._filter.search = e.target.value;
      const layout = container.querySelector('#mem-layout');
      if (layout) this._renderMemoryList(layout);
    });
  },

  _bindLayoutEvents(layout) {
    layout.querySelectorAll('.memory-type-item').forEach(item => {
      item.addEventListener('click', () => {
        this._filter.type = item.dataset.type;
        this._selectedId = null;
        layout.querySelectorAll('.memory-type-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        this._renderMemoryList(layout);

        const detail = layout.querySelector('#mem-detail');
        if (detail) {
          detail.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🧠</div><div class="empty-state-text">Select a memory to view details</div></div>';
        }
      });
    });
  }
};
