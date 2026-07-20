/**
 * AIOS Mission Control - Main Application Controller
 * Initializes all subsystems and manages global interactions.
 */
const App = {
  /** @type {HTMLElement|null} */
  _content: null,

  /**
   * Initialize the application.
   */
  init() {
    Store.init();
    this._registerRoutes();
    this._renderLayout();
    this._bindKeyboardShortcuts();
    Router.init();

    // Subscribe to route changes
    window.addEventListener('route:change', (e) => {
      const page = e.detail.path.slice(1).split('/')[0] || 'dashboard';
      Components.Sidebar.setActive(page);
      Components.Topbar.updateBreadcrumb(page);
    });

    console.log('[AIOS] Mission Control initialized');
  },

  /**
   * Register all page routes.
   * @private
   */
  _registerRoutes() {
    Router.register('/dashboard', () => this._renderPage('Dashboard'));
    Router.register('/workspaces', () => this._renderPage('Workspaces'));
    Router.register('/agents', () => this._renderPage('Agents'));
    Router.register('/missions', () => this._renderPage('Missions'));
    Router.register('/kanban', () => this._renderPage('Kanban'));
    Router.register('/memory', () => this._renderPage('Memory'));
    Router.register('/tools', () => this._renderPage('Tools'));
    Router.register('/marketplace', () => this._renderPage('Marketplace'));
    Router.register('/finances', () => this._renderPage('Finances'));
    Router.register('/analytics', () => this._renderPage('Analytics'));
  },

  /**
   * Render the main layout (sidebar + topbar).
   * @private
   */
  _renderLayout() {
    const sidebar = document.getElementById('sidebar');
    const topbar = document.getElementById('topbar');
    this._content = document.getElementById('content');

    if (sidebar) Components.Sidebar.render(sidebar);
    if (topbar) Components.Topbar.render(topbar);
  },

  /**
   * Render a page into the content area.
   * @param {string} pageName
   * @private
   */
  _renderPage(pageName) {
    const page = Pages[pageName];
    if (!page || !this._content) return;

    // Unmount previous page if it has unmount
    if (this._currentPage && this._currentPage.unmount) {
      this._currentPage.unmount();
    }

    this._content.innerHTML = '';
    const el = page.render();
    if (el) {
      this._content.appendChild(el);
    }

    // Mount new page if it has mount
    if (page.mount) {
      page.mount();
    }
    this._currentPage = page;

    // Scroll to top
    this._content.scrollTop = 0;
  },

  /**
   * Bind global keyboard shortcuts.
   * @private
   */
  _bindKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Cmd+K or Ctrl+K: Open search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        this.showSearch();
      }

      // Cmd+N or Ctrl+N: New mission
      if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
        e.preventDefault();
        Router.navigate('/missions');
        setTimeout(() => {
          if (Pages.Missions && Pages.Missions.showCreateModal) {
            Pages.Missions.showCreateModal();
          }
        }, 100);
      }

      // Escape: Close search
      if (e.key === 'Escape') {
        this.hideSearch();
        this.hideDropdowns();
      }
    });
  },

  /**
   * Show the global search overlay.
   */
  showSearch() {
    const overlay = document.getElementById('search-overlay');
    const input = document.getElementById('global-search');
    if (!overlay) return;

    overlay.classList.remove('hidden');
    if (input) {
      input.value = '';
      input.focus();
      input.addEventListener('input', (e) => this._handleSearch(e.target.value));
    }

    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) this.hideSearch();
    });
  },

  /**
   * Hide the global search overlay.
   */
  hideSearch() {
    const overlay = document.getElementById('search-overlay');
    if (overlay) overlay.classList.add('hidden');
  },

  /**
   * Handle search input.
   * @param {string} query
   * @private
   */
  _handleSearch(query) {
    const resultsEl = document.getElementById('search-results');
    if (!resultsEl) return;

    if (!query || query.length < 2) {
      resultsEl.innerHTML = '<div class="search-empty">Type to search agents, missions, tasks, and more...</div>';
      return;
    }

    const q = query.toLowerCase();
    const results = [];

    // Search agents
    Store.state.agents.filter(a => a.name.toLowerCase().includes(q) || a.capabilities.some(c => c.includes(q)))
      .forEach(a => results.push({ icon: a.avatar, title: a.name, type: 'Agent', path: '/agents' }));

    // Search missions
    Store.state.missions.filter(m => m.name.toLowerCase().includes(q) || m.description.toLowerCase().includes(q))
      .forEach(m => results.push({ icon: '🎯', title: m.name, type: 'Mission', path: '/missions' }));

    // Search tasks
    Store.state.tasks.filter(t => t.title.toLowerCase().includes(q))
      .forEach(t => results.push({ icon: '📋', title: t.title, type: 'Task', path: '/kanban' }));

    // Search memories
    Store.state.memories.filter(m => m.title.toLowerCase().includes(q) || m.content.toLowerCase().includes(q))
      .forEach(m => results.push({ icon: '🧠', title: m.title, type: 'Memory', path: '/memory' }));

    // Search tools
    Store.state.tools.filter(t => t.name.toLowerCase().includes(q))
      .forEach(t => results.push({ icon: '🔧', title: t.name, type: 'Tool', path: '/tools' }));

    if (results.length === 0) {
      resultsEl.innerHTML = '<div class="search-empty">No results found</div>';
      return;
    }

    resultsEl.innerHTML = results.slice(0, 8).map(r => `
      <div class="search-result-item" data-path="${r.path}">
        <span class="search-result-icon">${r.icon}</span>
        <div class="search-result-info">
          <div class="search-result-title">${r.title}</div>
          <div class="search-result-type">${r.type}</div>
        </div>
      </div>
    `).join('');

    resultsEl.querySelectorAll('.search-result-item').forEach(item => {
      item.addEventListener('click', () => {
        this.hideSearch();
        Router.navigate(item.dataset.path);
      });
    });
  },

  /**
   * Show a toast notification.
   * @param {string} message
   * @param {string} [type='info'] - 'success', 'error', 'warning', 'info'
   * @param {number} [duration=4000] - Auto-dismiss in ms
   */
  showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || icons.info}</span>
      <span class="toast-message">${message}</span>
      <button class="toast-close" aria-label="Dismiss">&times;</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => this._removeToast(toast));
    container.appendChild(toast);

    setTimeout(() => this._removeToast(toast), duration);
  },

  /**
   * Remove a toast with animation.
   * @param {HTMLElement} toast
   * @private
   */
  _removeToast(toast) {
    if (!toast || !toast.parentNode) return;
    toast.classList.add('removing');
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 250);
  },

  /**
   * Show a modal.
   * @param {string} title
   * @param {string} content - HTML string
   * @param {string} [size='md']
   * @returns {Object} modal handle
   */
  showModal(title, content, size) {
    const modal = Components.Modal.create({ title, content, size });
    modal.show();
    return modal;
  },

  /**
   * Hide all dropdown menus.
   */
  hideDropdowns() {
    document.querySelectorAll('.dropdown-menu').forEach(m => m.classList.add('hidden'));
  }
};

// Boot the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => App.init());
