/**
 * AIOS Mission Control - Sidebar Component
 * Collapsible navigation sidebar with user profile and status.
 */
const Components = window.Components || {};

Components.Sidebar = {
  /** @type {HTMLElement|null} */
  _el: null,

  /** Navigation items configuration */
  _navItems: [
    { section: 'Main', items: [
      { id: 'dashboard', label: 'Dashboard', icon: '🏠', path: '/dashboard' },
      { id: 'workspaces', label: 'Workspaces', icon: '📁', path: '/workspaces' },
      { id: 'agents', label: 'Agents', icon: '🤖', path: '/agents' },
      { id: 'missions', label: 'Missions', icon: '🎯', path: '/missions' },
      { id: 'kanban', label: 'Kanban', icon: '📋', path: '/kanban' }
    ]},
    { section: 'System', items: [
      { id: 'memory', label: 'Memory', icon: '🧠', path: '/memory' },
      { id: 'tools', label: 'Tools', icon: '🔧', path: '/tools' },
      { id: 'marketplace', label: 'Marketplace', icon: '🏪', path: '/marketplace' }
    ]},
    { section: 'Business', items: [
      { id: 'finances', label: 'Finances', icon: '💰', path: '/finances' },
      { id: 'analytics', label: 'Analytics', icon: '📈', path: '/analytics' }
    ]}
  ],

  /**
   * Render the sidebar into the target element.
   * @param {HTMLElement} container
   */
  render(container) {
    this._el = container;
    container.innerHTML = this._buildHTML();
    this._bindEvents();
  },

  /**
   * Build sidebar HTML.
   * @returns {string}
   * @private
   */
  _buildHTML() {
    const isCollapsed = Store.state.sidebarCollapsed;
    return `
      <div class="sidebar-header">
        <span class="sidebar-logo">🎯</span>
        <span class="sidebar-title">AIOS Mission Control</span>
      </div>
      <button class="sidebar-toggle" aria-label="Toggle sidebar">${isCollapsed ? '›' : '‹'}</button>
      <nav class="sidebar-nav" role="navigation" aria-label="Main navigation">
        ${this._navItems.map(section => `
          <div class="nav-section">
            <div class="nav-section-title">${section.section}</div>
            ${section.items.map(item => `
              <a class="nav-item${Store.state.currentPage === item.id ? ' active' : ''}"
                 href="#${item.path}"
                 data-page="${item.id}"
                 role="link"
                 aria-label="${item.label}">
                <span class="nav-icon">${item.icon}</span>
                <span class="nav-label">${item.label}</span>
              </a>
            `).join('')}
          </div>
        `).join('')}
      </nav>
      <div class="sidebar-footer">
        <div class="sidebar-user" tabindex="0" role="button" aria-label="User menu">
          <div class="sidebar-user-avatar">👤</div>
          <div class="sidebar-user-info">
            <div class="sidebar-user-name">Admin</div>
            <div class="sidebar-user-role">System Operator</div>
          </div>
        </div>
        <div class="sidebar-status">
          <span class="sidebar-status-dot"></span>
          <span class="sidebar-status-text">All Systems Online</span>
        </div>
      </div>
    `;
  },

  /**
   * Bind event listeners.
   * @private
   */
  _bindEvents() {
    if (!this._el) return;

    // Toggle button
    const toggle = this._el.querySelector('.sidebar-toggle');
    if (toggle) {
      toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggle();
      });
    }

    // Nav items
    this._el.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const path = item.getAttribute('href').slice(1);
        Router.navigate(path);
      });
    });
  },

  /**
   * Toggle sidebar collapsed state.
   */
  toggle() {
    const isCollapsed = !Store.state.sidebarCollapsed;
    Store.update('sidebarCollapsed', isCollapsed);

    if (this._el) {
      this._el.classList.toggle('collapsed', isCollapsed);
      const toggle = this._el.querySelector('.sidebar-toggle');
      if (toggle) toggle.textContent = isCollapsed ? '›' : '‹';
    }
  },

  /**
   * Update active state of nav items.
   * @param {string} pageId
   */
  setActive(pageId) {
    Store.update('currentPage', pageId);
    if (!this._el) return;

    this._el.querySelectorAll('.nav-item').forEach(item => {
      const isActive = item.dataset.page === pageId;
      item.classList.toggle('active', isActive);
    });
  }
};
