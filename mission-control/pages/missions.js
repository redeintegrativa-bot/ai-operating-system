/**
 * AIOS Mission Control - Missions Page
 * Mission management with list, detail, and create modal.
 */
const Pages = window.Pages || {};

Pages.Missions = {
  _filter: { search: '', status: 'all', priority: 'all' },

  render() {
    const el = document.createElement('div');
    el.className = 'missions-page animate-fade-in';

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Missions</h1>
          <p class="page-subtitle">Track and manage AIOS missions</p>
        </div>
        <div class="page-actions">
          <button class="btn btn-primary" id="create-mission-btn">+ New Mission</button>
        </div>
      </div>
      <div class="filter-bar">
        <div class="filter-search">
          <span class="filter-search-icon">🔍</span>
          <input type="text" placeholder="Search missions..." id="mission-search" aria-label="Search missions">
        </div>
        <select class="filter-select" id="mission-status-filter" aria-label="Filter by status">
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="pending">Pending</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
        <select class="filter-select" id="mission-priority-filter" aria-label="Filter by priority">
          <option value="all">All Priority</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
      <div class="missions-list" id="missions-list"></div>
    `;

    requestAnimationFrame(() => {
      this._renderMissions(el);
      this._bindEvents(el);
    });

    return el;
  },

  _renderMissions(container) {
    const list = container.querySelector('#missions-list');
    if (!list) return;

    let missions = [...Store.state.missions];

    if (this._filter.search) {
      const q = this._filter.search.toLowerCase();
      missions = missions.filter(m => m.name.toLowerCase().includes(q) || m.description.toLowerCase().includes(q));
    }
    if (this._filter.status !== 'all') missions = missions.filter(m => m.status === this._filter.status);
    if (this._filter.priority !== 'all') missions = missions.filter(m => m.priority === this._filter.priority);

    if (missions.length === 0) {
      list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🎯</div><div class="empty-state-title">No missions found</div><div class="empty-state-text">Create a new mission or adjust your filters.</div></div>';
      return;
    }

    list.innerHTML = missions.map(mission => {
      const agents = mission.agents.map(id => Store.findById('agents', id)).filter(Boolean);
      const statusColors = { pending: 'pending', active: 'active', completed: 'completed', failed: 'failed' };
      const progressColor = mission.progress > 70 ? 'green' : mission.progress > 40 ? '' : 'orange';

      return `
        <div class="card mission-card card-clickable" data-mission-id="${mission.id}" role="button" tabindex="0">
          <div class="mission-info">
            <div class="mission-info-header">
              <span class="mission-name">${mission.name}</span>
              <span class="badge badge-${statusColors[mission.status]}">${mission.status}</span>
              <span class="badge badge-${mission.priority}">${mission.priority}</span>
            </div>
            <div class="mission-desc">${mission.description}</div>
            <div class="mission-meta">
              ${mission.startDate ? `<span>📅 ${mission.startDate}</span>` : ''}
              ${mission.deadline ? `<span>⏰ Due ${mission.deadline}</span>` : ''}
              <span>📋 ${Store.state.tasks.filter(t => t.mission === mission.id).length} tasks</span>
            </div>
          </div>
          <div class="mission-progress">
            <div class="mission-progress-label">
              <span style="color: var(--text-muted);">Progress</span>
              <span class="mission-progress-value">${mission.progress}%</span>
            </div>
            <div class="progress-bar"><div class="progress-bar-fill ${progressColor}" style="width: ${mission.progress}%;"></div></div>
          </div>
          <div class="mission-agents">
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px;">Agents</div>
            <div class="avatar-group">
              ${agents.map(a => `<span class="avatar avatar-md" style="background: var(--bg-input);">${a.avatar}</span>`).join('')}
            </div>
          </div>
        </div>
      `;
    }).join('');

    list.querySelectorAll('.mission-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = parseInt(card.dataset.missionId);
        const mission = Store.findById('missions', id);
        if (mission) this._showDetail(mission);
      });
    });
  },

  _bindEvents(container) {
    container.querySelector('#mission-search')?.addEventListener('input', (e) => {
      this._filter.search = e.target.value;
      this._renderMissions(container);
    });

    container.querySelector('#mission-status-filter')?.addEventListener('change', (e) => {
      this._filter.status = e.target.value;
      this._renderMissions(container);
    });

    container.querySelector('#mission-priority-filter')?.addEventListener('change', (e) => {
      this._filter.priority = e.target.value;
      this._renderMissions(container);
    });

    container.querySelector('#create-mission-btn')?.addEventListener('click', () => {
      this.showCreateModal();
    });
  },

  showCreateModal() {
    const agents = Store.state.agents;
    const modal = Components.Modal.create({
      title: 'Create New Mission',
      size: 'lg',
      content: `
        <div class="form-group">
          <label class="form-label">Mission Name</label>
          <input class="form-input" id="mis-name" placeholder="Enter mission name">
        </div>
        <div class="form-group">
          <label class="form-label">Description</label>
          <textarea class="form-textarea" id="mis-desc" placeholder="Describe the mission..."></textarea>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <div class="form-group">
            <label class="form-label">Priority</label>
            <select class="form-select" id="mis-priority">
              <option value="high">High</option>
              <option value="medium" selected>Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Deadline</label>
            <input class="form-input" type="date" id="mis-deadline">
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Assign Agents</label>
          <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            ${agents.map(a => `
              <label style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: var(--bg-input); border: 1px solid var(--border); border-radius: var(--radius-sm); cursor: pointer; font-size: 0.85rem;">
                <input type="checkbox" value="${a.id}" class="mis-agent-check">
                <span>${a.avatar}</span> ${a.name}
              </label>
            `).join('')}
          </div>
        </div>
      `,
      footer: `
        <button class="btn btn-secondary" id="mis-cancel">Cancel</button>
        <button class="btn btn-primary" id="mis-create">Create Mission</button>
      `
    });

    modal.show();

    modal.el.querySelector('#mis-cancel')?.addEventListener('click', () => modal.hide());
    modal.el.querySelector('#mis-create')?.addEventListener('click', () => {
      const name = modal.el.querySelector('#mis-name').value.trim();
      const desc = modal.el.querySelector('#mis-desc').value.trim();
      if (!name) { App.showToast('Mission name is required', 'warning'); return; }

      const agentIds = [...modal.el.querySelectorAll('.mis-agent-check:checked')].map(cb => parseInt(cb.value));

      Store.addItem('missions', {
        name,
        description: desc,
        priority: modal.el.querySelector('#mis-priority').value,
        deadline: modal.el.querySelector('#mis-deadline').value || null,
        agents: agentIds,
        status: 'pending',
        progress: 0,
        startDate: null
      });

      modal.hide();
      App.showToast('Mission created successfully', 'success');
    });
  },

  _showDetail(mission) {
    const agents = mission.agents.map(id => Store.findById('agents', id)).filter(Boolean);
    const tasks = Store.state.tasks.filter(t => t.mission === mission.id);

    const modal = Components.Modal.create({
      title: mission.name,
      size: 'lg',
      content: `
        <div style="display: flex; gap: 12px; margin-bottom: 20px;">
          <span class="badge badge-${mission.status}">${mission.status}</span>
          <span class="badge badge-${mission.priority}">${mission.priority}</span>
          ${mission.deadline ? `<span style="font-size: 0.8rem; color: var(--text-muted);">Due: ${mission.deadline}</span>` : ''}
        </div>
        <p style="color: var(--text-secondary); margin-bottom: 20px;">${mission.description}</p>
        <div style="margin-bottom: 20px;">
          <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px;">
            <span>Progress</span><span>${mission.progress}%</span>
          </div>
          <div class="progress-bar" style="height: 10px;"><div class="progress-bar-fill" style="width: ${mission.progress}%;"></div></div>
        </div>
        <h4 style="margin-bottom: 12px;">Assigned Agents</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px;">
          ${agents.map(a => `<div style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: var(--bg-input); border-radius: var(--radius-sm); font-size: 0.85rem;">${a.avatar} ${a.name}</div>`).join('')}
        </div>
        <h4 style="margin-bottom: 12px;">Subtasks (${tasks.length})</h4>
        ${tasks.length > 0 ? tasks.map(t => {
          const agent = Store.findById('agents', t.assignee);
          return `<div style="display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 0.85rem;">
            <span class="badge badge-${t.priority}" style="font-size: 0.6rem;">${t.priority}</span>
            <span style="flex: 1;">${t.title}</span>
            <span class="badge badge-tag">${t.column.replace('_', ' ')}</span>
            ${agent ? `<span style="font-size: 0.9rem;">${agent.avatar}</span>` : ''}
          </div>`;
        }).join('') : '<p style="color: var(--text-muted); font-size: 0.85rem;">No subtasks yet</p>'}
      `
    });
    modal.show();
  }
};
