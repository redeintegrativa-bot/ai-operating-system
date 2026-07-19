/**
 * AIOS Mission Control - Kanban Page
 * Full Kanban board with drag-and-drop and task management.
 */
const Pages = window.Pages || {};

Pages.Kanban = {
  _filter: { agent: 'all', priority: 'all', tag: 'all' },

  render() {
    const el = document.createElement('div');
    el.className = 'kanban-page animate-fade-in';

    const agents = Store.state.agents;
    const allTags = [...new Set(Store.state.tasks.flatMap(t => t.tags || []))].sort();

    el.innerHTML = `
      <div class="page-header" style="flex-shrink: 0;">
        <div>
          <h1 class="page-title">Kanban Board</h1>
          <p class="page-subtitle">Drag and drop tasks between columns</p>
        </div>
        <div class="page-actions">
          <button class="btn btn-primary" id="kb-add-task">+ New Task</button>
        </div>
      </div>
      <div class="filter-bar" style="flex-shrink: 0;">
        <select class="filter-select" id="kb-agent-filter" aria-label="Filter by agent">
          <option value="all">All Agents</option>
          ${agents.map(a => `<option value="${a.id}">${a.avatar} ${a.name}</option>`).join('')}
        </select>
        <select class="filter-select" id="kb-priority-filter" aria-label="Filter by priority">
          <option value="all">All Priority</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select class="filter-select" id="kb-tag-filter" aria-label="Filter by tag">
          <option value="all">All Tags</option>
          ${allTags.map(t => `<option value="${t}">${t}</option>`).join('')}
        </select>
      </div>
      <div id="kb-board" style="flex: 1; min-height: 0;"></div>
    `;

    requestAnimationFrame(() => {
      this._renderBoard(el);
      this._bindEvents(el);
    });

    return el;
  },

  _getFilteredTasks() {
    let tasks = [...Store.state.tasks];

    if (this._filter.agent !== 'all') {
      tasks = tasks.filter(t => t.assignee === parseInt(this._filter.agent));
    }
    if (this._filter.priority !== 'all') {
      tasks = tasks.filter(t => t.priority === this._filter.priority);
    }
    if (this._filter.tag !== 'all') {
      tasks = tasks.filter(t => (t.tags || []).includes(this._filter.tag));
    }

    return tasks;
  },

  _renderBoard(container) {
    const boardEl = container.querySelector('#kb-board');
    if (!boardEl) return;

    boardEl.innerHTML = '';

    const tasks = this._getFilteredTasks();

    const board = Components.KanbanBoard.create({
      tasks,
      onTaskMove: (taskId, from, to) => {
        Store.updateItem('tasks', taskId, { column: to });
        App.showToast(`Task moved to ${to.replace('_', ' ')}`, 'info');
      },
      onTaskClick: (task) => this._showTaskDetail(task),
      onAddTask: (column) => this.showCreateModal(column)
    });

    boardEl.appendChild(board);
  },

  _bindEvents(container) {
    container.querySelector('#kb-add-task')?.addEventListener('click', () => {
      this.showCreateModal();
    });

    container.querySelector('#kb-agent-filter')?.addEventListener('change', (e) => {
      this._filter.agent = e.target.value;
      this._renderBoard(container);
    });

    container.querySelector('#kb-priority-filter')?.addEventListener('change', (e) => {
      this._filter.priority = e.target.value;
      this._renderBoard(container);
    });

    container.querySelector('#kb-tag-filter')?.addEventListener('change', (e) => {
      this._filter.tag = e.target.value;
      this._renderBoard(container);
    });
  },

  showCreateModal(defaultColumn) {
    const agents = Store.state.agents;
    const missions = Store.state.missions.filter(m => m.status !== 'completed');

    const modal = Components.Modal.create({
      title: 'Create New Task',
      size: 'md',
      content: `
        <div class="form-group">
          <label class="form-label">Title</label>
          <input class="form-input" id="task-title" placeholder="Task title">
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <div class="form-group">
            <label class="form-label">Column</label>
            <select class="form-select" id="task-column">
              <option value="backlog" ${defaultColumn === 'backlog' ? 'selected' : ''}>Backlog</option>
              <option value="todo" ${defaultColumn === 'todo' ? 'selected' : ''}>To Do</option>
              <option value="in_progress" ${defaultColumn === 'in_progress' ? 'selected' : ''}>In Progress</option>
              <option value="review" ${defaultColumn === 'review' ? 'selected' : ''}>Review</option>
              <option value="done" ${defaultColumn === 'done' ? 'selected' : ''}>Done</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Priority</label>
            <select class="form-select" id="task-priority">
              <option value="high">High</option>
              <option value="medium" selected>Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Assignee</label>
          <select class="form-select" id="task-assignee">
            <option value="">Unassigned</option>
            ${agents.map(a => `<option value="${a.id}">${a.avatar} ${a.name}</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Tags (comma separated)</label>
          <input class="form-input" id="task-tags" placeholder="e.g. backend, auth">
        </div>
        <div class="form-group">
          <label class="form-label">Mission (optional)</label>
          <select class="form-select" id="task-mission">
            <option value="">No mission</option>
            ${missions.map(m => `<option value="${m.id}">${m.name}</option>`).join('')}
          </select>
        </div>
      `,
      footer: `
        <button class="btn btn-secondary" id="task-cancel">Cancel</button>
        <button class="btn btn-primary" id="task-create">Create</button>
      `
    });

    modal.show();

    modal.el.querySelector('#task-cancel')?.addEventListener('click', () => modal.hide());
    modal.el.querySelector('#task-create')?.addEventListener('click', () => {
      const title = modal.el.querySelector('#task-title').value.trim();
      if (!title) { App.showToast('Task title is required', 'warning'); return; }

      const tags = modal.el.querySelector('#task-tags').value.split(',').map(t => t.trim()).filter(Boolean);
      const assignee = modal.el.querySelector('#task-assignee').value;
      const mission = modal.el.querySelector('#task-mission').value;

      Store.addItem('tasks', {
        title,
        column: modal.el.querySelector('#task-column').value,
        priority: modal.el.querySelector('#task-priority').value,
        assignee: assignee ? parseInt(assignee) : null,
        tags,
        mission: mission ? parseInt(mission) : null
      });

      modal.hide();
      App.showToast('Task created successfully', 'success');

      // Re-render board
      const container = document.querySelector('.kanban-page');
      if (container) this._renderBoard(container);
    });
  },

  _showTaskDetail(task) {
    const agent = Store.findById('agents', task.assignee);
    const mission = task.mission ? Store.findById('missions', task.mission) : null;

    const modal = Components.Modal.create({
      title: task.title,
      size: 'md',
      content: `
        <div style="display: flex; gap: 8px; margin-bottom: 16px;">
          <span class="badge badge-${task.priority}">${task.priority}</span>
          <span class="badge badge-tag">${task.column.replace('_', ' ')}</span>
        </div>
        <div style="margin-bottom: 16px;">
          <div class="form-label">Assignee</div>
          ${agent ? `<div style="display: flex; align-items: center; gap: 8px; font-size: 0.9rem;">${agent.avatar} ${agent.name}</div>` : '<span style="color: var(--text-muted);">Unassigned</span>'}
        </div>
        ${mission ? `
          <div style="margin-bottom: 16px;">
            <div class="form-label">Mission</div>
            <div style="font-size: 0.9rem;">🎯 ${mission.name}</div>
          </div>
        ` : ''}
        <div style="margin-bottom: 16px;">
          <div class="form-label">Tags</div>
          <div style="display: flex; gap: 6px; flex-wrap: wrap;">
            ${(task.tags || []).map(t => `<span class="badge badge-tag">${t}</span>`).join('') || '<span style="color: var(--text-muted);">No tags</span>'}
          </div>
        </div>
      `
    });
    modal.show();
  }
};
