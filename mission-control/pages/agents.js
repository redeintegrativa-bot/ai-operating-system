/**
 * AIOS Mission Control - Agents Page
 * Agent management with grid/list views and detail modals.
 */
const Pages = window.Pages || {};

Pages.Agents = {
  _filter: { search: '', status: 'all', capability: 'all' },
  _view: 'grid',

  render() {
    const el = document.createElement('div');
    el.className = 'agents-page animate-fade-in';

    const allCaps = [...new Set(Store.state.agents.flatMap(a => a.capabilities))].sort();

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Agents</h1>
          <p class="page-subtitle">${Store.state.agents.length} registered agents</p>
        </div>
        <div class="page-actions">
          <div class="flex gap-2">
            <button class="btn btn-ghost btn-icon view-btn active" data-view="grid" aria-label="Grid view">▦</button>
            <button class="btn btn-ghost btn-icon view-btn" data-view="list" aria-label="List view">☰</button>
          </div>
        </div>
      </div>
      <div class="filter-bar">
        <div class="filter-search">
          <span class="filter-search-icon">🔍</span>
          <input type="text" placeholder="Search agents..." id="agent-search" aria-label="Search agents">
        </div>
        <select class="filter-select" id="agent-status-filter" aria-label="Filter by status">
          <option value="all">All Status</option>
          <option value="online">Online</option>
          <option value="busy">Busy</option>
          <option value="offline">Offline</option>
        </select>
        <select class="filter-select" id="agent-cap-filter" aria-label="Filter by capability">
          <option value="all">All Capabilities</option>
          ${allCaps.map(c => `<option value="${c}">${c}</option>`).join('')}
        </select>
      </div>
      <div id="agents-container"></div>
    `;

    requestAnimationFrame(() => {
      this._renderAgents(el);
      this._bindEvents(el);
    });

    return el;
  },

  _renderAgents(container) {
    const ctr = container.querySelector('#agents-container');
    if (!ctr) return;

    let agents = [...Store.state.agents];

    if (this._filter.search) {
      const q = this._filter.search.toLowerCase();
      agents = agents.filter(a => a.name.toLowerCase().includes(q) || a.description.toLowerCase().includes(q));
    }
    if (this._filter.status !== 'all') {
      agents = agents.filter(a => a.status === this._filter.status);
    }
    if (this._filter.capability !== 'all') {
      agents = agents.filter(a => a.capabilities.includes(this._filter.capability));
    }

    if (agents.length === 0) {
      ctr.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🤖</div><div class="empty-state-title">No agents found</div><div class="empty-state-text">Try adjusting your filters.</div></div>';
      return;
    }

    if (this._view === 'grid') {
      ctr.innerHTML = '';
      ctr.className = 'agents-grid';
      agents.forEach(agent => {
        const card = Components.Card.create({
          type: 'agent',
          data: agent,
          onClick: () => this._showDetail(agent)
        });
        ctr.appendChild(card);
      });
    } else {
      ctr.innerHTML = '';
      const table = Components.DataTable.create({
        columns: [
          { key: 'avatar', label: '', render: (v) => `<span style="font-size: 1.5rem;">${v}</span>` },
          { key: 'name', label: 'Name', sortable: true },
          { key: 'status', label: 'Status', render: (v) => `<span class="badge badge-${v}">${v}</span>` },
          { key: 'capabilities', label: 'Capabilities', render: (v) => v.map(c => `<span class="badge badge-tag">${c}</span>`).join(' ') },
          { key: 'currentTask', label: 'Current Task', render: (v) => v || '<span style="color: var(--text-muted);">Idle</span>' }
        ],
        data: agents,
        searchable: false,
        onRowClick: (row) => this._showDetail(row)
      });
      ctr.appendChild(table);
    }
  },

  _bindEvents(container) {
    container.querySelector('#agent-search')?.addEventListener('input', (e) => {
      this._filter.search = e.target.value;
      this._renderAgents(container);
    });

    container.querySelector('#agent-status-filter')?.addEventListener('change', (e) => {
      this._filter.status = e.target.value;
      this._renderAgents(container);
    });

    container.querySelector('#agent-cap-filter')?.addEventListener('change', (e) => {
      this._filter.capability = e.target.value;
      this._renderAgents(container);
    });

    container.querySelectorAll('.view-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        container.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this._view = btn.dataset.view;
        this._renderAgents(container);
      });
    });
  },

  _showDetail(agent) {
    const missions = Store.state.missions.filter(m => m.agents.includes(agent.id));
    const tasks = Store.state.tasks.filter(t => t.assignee === agent.id);

    const modal = Components.Modal.create({
      title: `${agent.avatar} ${agent.name}`,
      size: 'lg',
      content: `
        <div style="display: flex; gap: 16px; margin-bottom: 20px; align-items: flex-start;">
          <div style="font-size: 3rem;">${agent.avatar}</div>
          <div>
            <p style="color: var(--text-secondary); margin-bottom: 8px;">${agent.description}</p>
            <span class="badge badge-${agent.status}">${agent.status}</span>
          </div>
        </div>
        <div style="margin-bottom: 20px;">
          <h4 style="margin-bottom: 8px;">Capabilities</h4>
          <div style="display: flex; gap: 6px; flex-wrap: wrap;">
            ${agent.capabilities.map(c => `<span class="badge badge-tag">${c}</span>`).join('')}
          </div>
        </div>
        ${agent.currentTask ? `
          <div style="margin-bottom: 20px;">
            <h4 style="margin-bottom: 8px;">Current Task</h4>
            <div style="padding: 12px; background: var(--bg-input); border-radius: var(--radius-sm); font-size: 0.9rem;">⚡ ${agent.currentTask}</div>
          </div>
        ` : ''}
        <div style="margin-bottom: 20px;">
          <h4 style="margin-bottom: 8px;">Missions (${missions.length})</h4>
          ${missions.length > 0 ? missions.map(m => `
            <div style="display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--border);">
              <span class="badge badge-${m.status}">${m.status}</span>
              <span style="font-size: 0.85rem;">${m.name}</span>
              <span style="margin-left: auto; font-size: 0.75rem; color: var(--text-muted);">${m.progress}%</span>
            </div>
          `).join('') : '<p style="color: var(--text-muted); font-size: 0.85rem;">No missions assigned</p>'}
        </div>
        <div>
          <h4 style="margin-bottom: 8px;">Tasks (${tasks.length})</h4>
          ${tasks.length > 0 ? tasks.slice(0, 5).map(t => `
            <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0; font-size: 0.85rem;">
              <span class="badge badge-${t.priority}" style="font-size: 0.6rem;">${t.priority}</span>
              <span style="color: var(--text-secondary);">${t.title}</span>
            </div>
          `).join('') : '<p style="color: var(--text-muted); font-size: 0.85rem;">No tasks assigned</p>'}
        </div>
      `
    });
    modal.show();
  }
};
