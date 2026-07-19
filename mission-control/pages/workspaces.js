/**
 * AIOS Mission Control - Workspaces Page
 * Project workspace management with cards and create modal.
 */
const Pages = window.Pages || {};

Pages.Workspaces = {
  _filter: { search: '', status: 'all' },

  render() {
    const el = document.createElement('div');
    el.className = 'workspaces-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Workspaces</h1>
          <p class="page-subtitle">Manage project workspaces and team assignments</p>
        </div>
        <div class="page-actions">
          <button class="btn btn-primary" id="create-workspace-btn">+ New Workspace</button>
        </div>
      </div>
      <div class="filter-bar">
        <div class="filter-search">
          <span class="filter-search-icon">🔍</span>
          <input type="text" placeholder="Search workspaces..." id="ws-search" aria-label="Search workspaces">
        </div>
        <select class="filter-select" id="ws-status-filter" aria-label="Filter by status">
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="planning">Planning</option>
          <option value="completed">Completed</option>
        </select>
      </div>
      <div class="workspaces-grid" id="ws-grid"></div>
    `;

    requestAnimationFrame(() => {
      this._renderGrid(el);
      this._bindEvents(el);
    });

    return el;
  },

  _renderGrid(container) {
    const grid = container.querySelector('#ws-grid');
    if (!grid) return;

    let workspaces = [...Store.state.workspaces];

    if (this._filter.search) {
      const q = this._filter.search.toLowerCase();
      workspaces = workspaces.filter(w => w.name.toLowerCase().includes(q) || w.description.toLowerCase().includes(q));
    }
    if (this._filter.status !== 'all') {
      workspaces = workspaces.filter(w => w.status === this._filter.status);
    }

    if (workspaces.length === 0) {
      grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📁</div><div class="empty-state-title">No workspaces found</div><div class="empty-state-text">Create a new workspace or adjust your filters.</div></div>';
      return;
    }

    grid.innerHTML = '';
    workspaces.forEach(ws => {
      const card = Components.Card.create({
        type: 'workspace',
        data: ws,
        onClick: () => this._showDetail(ws)
      });
      card.className += ' card-workspace';
      grid.appendChild(card);
    });
  },

  _bindEvents(container) {
    container.querySelector('#ws-search')?.addEventListener('input', (e) => {
      this._filter.search = e.target.value;
      this._renderGrid(container);
    });

    container.querySelector('#ws-status-filter')?.addEventListener('change', (e) => {
      this._filter.status = e.target.value;
      this._renderGrid(container);
    });

    container.querySelector('#create-workspace-btn')?.addEventListener('click', () => {
      this._showCreateModal(container);
    });
  },

  _showCreateModal(container) {
    const agents = Store.state.agents;
    const modal = Components.Modal.create({
      title: 'Create New Workspace',
      size: 'md',
      content: `
        <div class="form-group">
          <label class="form-label">Name</label>
          <input class="form-input" id="ws-name" placeholder="Workspace name">
        </div>
        <div class="form-group">
          <label class="form-label">Description</label>
          <textarea class="form-textarea" id="ws-desc" placeholder="Describe the workspace..."></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Status</label>
          <select class="form-select" id="ws-status">
            <option value="planning">Planning</option>
            <option value="active">Active</option>
          </select>
        </div>
      `,
      footer: `
        <button class="btn btn-secondary" id="ws-cancel">Cancel</button>
        <button class="btn btn-primary" id="ws-create">Create</button>
      `
    });

    modal.show();

    modal.el.querySelector('#ws-cancel')?.addEventListener('click', () => modal.hide());
    modal.el.querySelector('#ws-create')?.addEventListener('click', () => {
      const name = modal.el.querySelector('#ws-name').value.trim();
      const desc = modal.el.querySelector('#ws-desc').value.trim();
      if (!name) { App.showToast('Workspace name is required', 'warning'); return; }

      Store.addItem('workspaces', {
        name,
        description: desc,
        agents: [],
        status: modal.el.querySelector('#ws-status').value,
        progress: 0,
        tasks: 0,
        completedTasks: 0
      });

      modal.hide();
      App.showToast('Workspace created successfully', 'success');
      this._renderGrid(container);
    });
  },

  _showDetail(ws) {
    const agents = ws.agents.map(id => Store.findById('agents', id)).filter(Boolean);
    const modal = Components.Modal.create({
      title: ws.name,
      size: 'lg',
      content: `
        <div style="margin-bottom: 16px;">
          <p style="color: var(--text-secondary); margin-bottom: 16px;">${ws.description}</p>
          <div style="display: flex; gap: 16px; margin-bottom: 16px;">
            <span class="badge badge-${ws.status === 'active' ? 'active' : 'pending'}">${ws.status}</span>
            <span style="font-size: 0.85rem; color: var(--text-muted);">${ws.completedTasks}/${ws.tasks} tasks</span>
          </div>
          <div style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px;">
              <span>Progress</span><span>${ws.progress}%</span>
            </div>
            <div class="progress-bar"><div class="progress-bar-fill" style="width: ${ws.progress}%;"></div></div>
          </div>
        </div>
        <h4 style="margin-bottom: 12px;">Assigned Agents</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 12px;">
          ${agents.length > 0 ? agents.map(a => `
            <div style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: var(--bg-input); border-radius: var(--radius-sm);">
              <span>${a.avatar}</span>
              <span style="font-size: 0.85rem;">${a.name}</span>
              <span class="badge badge-${a.status}">${a.status}</span>
            </div>
          `).join('') : '<p style="color: var(--text-muted); font-size: 0.85rem;">No agents assigned</p>'}
        </div>
      `
    });
    modal.show();
  }
};
