/**
 * AIOS Mission Control - Topbar Component
 * Fixed top bar with search, notifications, and user actions.
 */
const Components = window.Components || {};

Components.Topbar = {
  /** @type {HTMLElement|null} */
  _el: null,

  /**
   * Render the topbar into the target element.
   * @param {HTMLElement} container
   */
  render(container) {
    this._el = container;
    container.innerHTML = this._buildHTML();
    this._bindEvents();
  },

  /**
   * Build topbar HTML.
   * @returns {string}
   * @private
   */
  _buildHTML() {
    const pageNames = {
      dashboard: 'Dashboard', workspaces: 'Workspaces', agents: 'Agents',
      missions: 'Missions', kanban: 'Kanban', memory: 'Memory',
      tools: 'Tools', marketplace: 'Marketplace', finances: 'Finances',
      analytics: 'Analytics'
    };
    const current = Store.state.currentPage;
    const unreadCount = Store.state.notifications.filter(n => !n.read).length;

    return `
      <div class="topbar-breadcrumb">
        <span>AIOS</span>
        <span class="topbar-breadcrumb-sep">/</span>
        <span class="topbar-breadcrumb-current">${pageNames[current] || 'Dashboard'}</span>
      </div>
      <div class="topbar-spacer"></div>
      <div class="topbar-search" id="topbar-search" role="button" tabindex="0" aria-label="Search">
        <span>🔍</span>
        <span class="topbar-search-text">Search...</span>
        <kbd class="topbar-search-kbd">⌘K</kbd>
      </div>
      <div class="topbar-actions">
        <div class="dropdown" id="quick-actions-dropdown">
          <button class="topbar-btn" aria-label="Quick actions" id="quick-actions-btn">➕</button>
          <div class="dropdown-menu hidden" id="quick-actions-menu">
            <div class="dropdown-item" data-action="new-mission">🎯 New Mission</div>
            <div class="dropdown-item" data-action="new-task">📋 New Task</div>
            <div class="dropdown-item" data-action="new-agent">🤖 New Agent</div>
            <div class="dropdown-item" data-action="new-workspace">📁 New Workspace</div>
          </div>
        </div>
        <div class="dropdown" id="notifications-dropdown">
          <button class="topbar-btn" aria-label="Notifications" id="notifications-btn">
            🔔
            ${unreadCount > 0 ? `<span class="badge">${unreadCount}</span>` : ''}
          </button>
          <div class="dropdown-menu hidden" id="notifications-menu" style="width: 320px;">
            <div style="padding: 8px 12px; font-weight: 600; font-size: 0.85rem; border-bottom: 1px solid var(--border);">Notifications</div>
            ${Store.state.notifications.map(n => `
              <div class="dropdown-item" style="flex-direction: column; align-items: flex-start; gap: 4px; opacity: ${n.read ? '0.6' : '1'}">
                <span style="font-size: 0.8rem;">${n.message}</span>
                <span style="font-size: 0.7rem; color: var(--text-muted);">${n.time}</span>
              </div>
            `).join('')}
          </div>
        </div>
        <div class="topbar-avatar" role="button" tabindex="0" aria-label="User profile">👤</div>
      </div>
    `;
  },

  /**
   * Bind event listeners.
   * @private
   */
  _bindEvents() {
    if (!this._el) return;

    // Search
    const searchEl = this._el.querySelector('#topbar-search');
    if (searchEl) {
      searchEl.addEventListener('click', () => App.showSearch());
      searchEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') App.showSearch();
      });
    }

    // Quick actions toggle
    const qaBtn = this._el.querySelector('#quick-actions-btn');
    const qaMenu = this._el.querySelector('#quick-actions-menu');
    if (qaBtn && qaMenu) {
      qaBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        qaMenu.classList.toggle('hidden');
        // Close notifications
        const notifMenu = this._el.querySelector('#notifications-menu');
        if (notifMenu) notifMenu.classList.add('hidden');
      });
    }

    // Quick action items
    this._el.querySelectorAll('[data-action]').forEach(item => {
      item.addEventListener('click', () => {
        const action = item.dataset.action;
        App.hideDropdowns();
        this._handleQuickAction(action);
      });
    });

    // Notifications toggle
    const notifBtn = this._el.querySelector('#notifications-btn');
    const notifMenu = this._el.querySelector('#notifications-menu');
    if (notifBtn && notifMenu) {
      notifBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        notifMenu.classList.toggle('hidden');
        // Close quick actions
        const qaMenu = this._el.querySelector('#quick-actions-menu');
        if (qaMenu) qaMenu.classList.add('hidden');
      });
    }

    // Close dropdowns on outside click
    document.addEventListener('click', () => App.hideDropdowns());
  },

  /**
   * Handle quick action selection.
   * @param {string} action
   * @private
   */
  _handleQuickAction(action) {
    switch (action) {
      case 'new-mission':
        Router.navigate('/missions');
        setTimeout(() => {
          if (typeof Pages.Missions !== 'undefined' && Pages.Missions.showCreateModal) {
            Pages.Missions.showCreateModal();
          }
        }, 100);
        break;
      case 'new-task':
        Router.navigate('/kanban');
        setTimeout(() => {
          if (typeof Pages.Kanban !== 'undefined' && Pages.Kanban.showCreateModal) {
            Pages.Kanban.showCreateModal();
          }
        }, 100);
        break;
      case 'new-agent':
        Router.navigate('/agents');
        break;
      case 'new-workspace':
        Router.navigate('/workspaces');
        break;
    }
  },

  /**
   * Update the breadcrumb.
   * @param {string} pageId
   */
  updateBreadcrumb(pageId) {
    if (!this._el) return;
    const pageNames = {
      dashboard: 'Dashboard', workspaces: 'Workspaces', agents: 'Agents',
      missions: 'Missions', kanban: 'Kanban', memory: 'Memory',
      tools: 'Tools', marketplace: 'Marketplace', finances: 'Finances',
      analytics: 'Analytics'
    };
    const current = this._el.querySelector('.topbar-breadcrumb-current');
    if (current) current.textContent = pageNames[pageId] || pageId;
  }
};
