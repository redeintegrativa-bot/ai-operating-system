/**
 * AIOS Mission Control - Card Component
 * Reusable card with multiple variants: stat, agent, task, memory, workspace, tool.
 */
const Components = window.Components || {};

Components.Card = {
  /**
   * Create a card element.
   * @param {Object} options
   * @param {string} options.type - Card variant: 'stat', 'agent', 'task', 'memory', 'workspace', 'tool'
   * @param {string} [options.title]
   * @param {*} [options.value]
   * @param {string} [options.subtitle]
   * @param {string} [options.icon]
   * @param {string} [options.color] - Accent color class
   * @param {Function} [options.onClick]
   * @param {Object} [options.data] - Additional data for specific variants
   * @returns {HTMLElement}
   */
  create(options) {
    const el = document.createElement('div');
    el.className = 'card' + (options.onClick ? ' card-clickable' : '');

    switch (options.type) {
      case 'stat':
        el.innerHTML = this._buildStat(options);
        break;
      case 'agent':
        el.innerHTML = this._buildAgent(options);
        break;
      case 'task':
        el.innerHTML = this._buildTask(options);
        break;
      case 'memory':
        el.innerHTML = this._buildMemory(options);
        break;
      case 'workspace':
        el.innerHTML = this._buildWorkspace(options);
        break;
      case 'tool':
        el.innerHTML = this._buildTool(options);
        break;
      default:
        el.innerHTML = this._buildGeneric(options);
    }

    if (options.onClick) {
      el.addEventListener('click', options.onClick);
      el.setAttribute('tabindex', '0');
      el.setAttribute('role', 'button');
      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          options.onClick(e);
        }
      });
    }

    return el;
  },

  /**
   * Build stat card HTML.
   * @param {Object} opts
   * @returns {string}
   * @private
   */
  _buildStat(opts) {
    const colorClass = opts.color || '';
    const iconBg = {
      blue: 'card-stat-icon',
      green: 'card-stat-icon green',
      orange: 'card-stat-icon orange',
      purple: 'card-stat-icon purple'
    }[colorClass] || 'card-stat-icon';

    return `
      <div class="card-header">
        <span class="card-title">${opts.title || ''}</span>
        <div class="card-icon ${iconBg}">${opts.icon || '📊'}</div>
      </div>
      <div class="card-value">${opts.value ?? '—'}</div>
      ${opts.trend ? `<div class="card-trend ${opts.trend > 0 ? 'up' : 'down'}">${opts.trend > 0 ? '↑' : '↓'} ${Math.abs(opts.trend)}%</div>` : ''}
      ${opts.subtitle ? `<div class="card-subtitle">${opts.subtitle}</div>` : ''}
      ${opts.miniChart ? `<div class="card-mini-chart" style="margin-top: 12px;">${opts.miniChart}</div>` : ''}
    `;
  },

  /**
   * Build agent card HTML.
   * @param {Object} opts
   * @returns {string}
   * @private
   */
  _buildAgent(opts) {
    const agent = opts.data || {};
    const statusBadge = this._getStatusBadge(agent.status);
    const caps = (agent.capabilities || []).slice(0, 3).map(c =>
      `<span class="badge badge-tag">${c}</span>`
    ).join('');

    return `
      <div class="card-agent">
        <div class="card-agent-avatar">${agent.avatar || '🤖'}</div>
        <div class="card-agent-name">${agent.name || 'Unknown Agent'}</div>
        <div class="card-agent-status">${statusBadge}</div>
        <div class="card-agent-capabilities">${caps}</div>
        ${agent.currentTask
          ? `<div class="card-agent-task" title="${agent.currentTask}">⚡ ${agent.currentTask}</div>`
          : `<div class="card-agent-task" style="color: var(--text-muted);">Idle</div>`
        }
      </div>
    `;
  },

  /**
   * Build task card HTML.
   * @param {Object} opts
   * @returns {string}
   * @private
   */
  _buildTask(opts) {
    const task = opts.data || {};
    const priorityBadge = `<span class="badge badge-${task.priority || 'medium'}">${task.priority || 'medium'}</span>`;
    const tags = (task.tags || []).map(t =>
      `<span class="badge badge-tag">${t}</span>`
    ).join('');
    const assignee = Store.findById('agents', task.assignee);
    const assigneeAvatar = assignee ? assignee.avatar : '👤';

    return `
      <div class="card-header" style="margin-bottom: 8px;">
        <div style="display: flex; gap: 6px; align-items: center;">${priorityBadge}</div>
        <div class="kanban-card-assignee">${assigneeAvatar}</div>
      </div>
      <div style="font-weight: 500; font-size: 0.9rem; margin-bottom: 8px;">${task.title || ''}</div>
      <div class="card-task-tags" style="display: flex; gap: 4px; flex-wrap: wrap;">${tags}</div>
    `;
  },

  /**
   * Build memory card HTML.
   * @param {Object} opts
   * @returns {string}
   * @private
   */
  _buildMemory(opts) {
    const memory = opts.data || {};
    const typeBadge = this._getTypeBadge(memory.type);
    const agent = Store.findById('agents', memory.agent);
    const preview = (memory.content || '').substring(0, 120) + (memory.content.length > 120 ? '...' : '');

    return `
      <div class="card-header" style="margin-bottom: 8px;">
        <div style="display: flex; gap: 6px;">${typeBadge}</div>
        <span style="font-size: 0.7rem; color: var(--text-muted);">${memory.date || ''}</span>
      </div>
      <div style="font-weight: 600; margin-bottom: 6px;">${memory.title || ''}</div>
      <div style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 8px;">${preview}</div>
      <div style="font-size: 0.75rem; color: var(--text-muted);">${agent ? agent.avatar + ' ' + agent.name : ''}</div>
    `;
  },

  /**
   * Build workspace card HTML.
   * @param {Object} opts
   * @returns {string}
   * @private
   */
  _buildWorkspace(opts) {
    const ws = opts.data || {};
    const agentAvatars = (ws.agents || []).map(id => {
      const a = Store.findById('agents', id);
      return a ? `<span class="avatar avatar-sm" style="background: var(--bg-input); border: 2px solid var(--bg-card);">${a.avatar}</span>` : '';
    }).join('');

    return `
      <div class="workspace-card-body">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
          <div class="workspace-card-name">${ws.name || ''}</div>
          <span class="badge badge-${ws.status === 'active' ? 'active' : 'pending'}">${ws.status || ''}</span>
        </div>
        <div class="workspace-card-desc">${ws.description || ''}</div>
        <div style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px;">
            <span>Progress</span>
            <span>${ws.progress || 0}%</span>
          </div>
          <div class="progress-bar"><div class="progress-bar-fill" style="width: ${ws.progress || 0}%;"></div></div>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div class="avatar-group">${agentAvatars}</div>
          <span class="workspace-card-tasks">${ws.completedTasks || 0}/${ws.tasks || 0} tasks</span>
        </div>
      </div>
    `;
  },

  /**
   * Build tool card HTML.
   * @param {Object} opts
   * @returns {string}
   * @private
   */
  _buildTool(opts) {
    const tool = opts.data || {};
    const categoryColors = {
      security: 'red', performance: 'orange', development: 'blue',
      testing: 'purple', devops: 'green', data: 'cyan', monitoring: 'pink'
    };
    const catColor = categoryColors[tool.category] || 'blue';

    return `
      <div class="tool-card-header">
        <div class="tool-card-name">${tool.name || ''}</div>
        <span class="badge badge-${catColor}">${tool.category || ''}</span>
      </div>
      <div class="tool-card-desc">${tool.description || ''}</div>
      <div class="tool-card-meta">
        <span>📊 ${tool.usageCount || 0} uses</span>
        <span>🕐 ${tool.lastUsed || 'Never'}</span>
      </div>
      <div class="tool-card-actions">
        <button class="btn btn-primary btn-sm" onclick="App.showToast('Tool execution placeholder', 'info')">▶ Run</button>
        <button class="btn btn-secondary btn-sm">⚙ Configure</button>
      </div>
    `;
  },

  /**
   * Build generic card HTML.
   * @param {Object} opts
   * @returns {string}
   * @private
   */
  _buildGeneric(opts) {
    return `
      ${opts.title ? `<div class="card-title">${opts.title}</div>` : ''}
      ${opts.value != null ? `<div class="card-value">${opts.value}</div>` : ''}
      ${opts.subtitle ? `<div class="card-subtitle">${opts.subtitle}</div>` : ''}
    `;
  },

  /**
   * Get status badge HTML.
   * @param {string} status
   * @returns {string}
   * @private
   */
  _getStatusBadge(status) {
    const map = {
      online: '<span class="badge badge-online">Online</span>',
      busy: '<span class="badge badge-busy">Busy</span>',
      offline: '<span class="badge badge-offline">Offline</span>'
    };
    return map[status] || `<span class="badge badge-tag">${status}</span>`;
  },

  /**
   * Get type badge HTML.
   * @param {string} type
   * @returns {string}
   * @private
   */
  _getTypeBadge(type) {
    const map = {
      episodic: '<span class="badge badge-blue">Episodic</span>',
      semantic: '<span class="badge badge-purple">Semantic</span>',
      procedural: '<span class="badge badge-green">Procedural</span>'
    };
    return map[type] || `<span class="badge badge-tag">${type}</span>`;
  }
};
