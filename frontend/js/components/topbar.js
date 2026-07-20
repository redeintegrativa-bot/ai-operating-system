/**
 * AIOS Dashboard - Topbar Component
 * Top navigation bar with breadcrumbs, search, and actions.
 */
const Components = window.Components || {};

Components.Topbar = {
  _el: null,
  _pageTitles: {
    '/dashboard': 'Dashboard','/login':'Login','/agents':'Agentes',
    '/tasks':'Task Center','/missions':'Missões','/kanban':'Kanban',
    '/memory':'Memória','/capability':'Capability Map','/skills':'Skills',
    '/plugins':'Plugins','/tools':'Ferramentas','/marketplace':'Marketplace',
    '/workspaces':'Workspaces','/analytics':'Analytics','/finances':'Finanças',
    '/logs':'Logs','/status':'Status do Sistema','/settings':'Configurações'
  },

  render(container) {
    this._el = container;
    container.innerHTML = `
      <div class="topbar-left">
        <button class="topbar-menu-btn" aria-label="Toggle menu" onclick="Components.Sidebar.toggle()">
          <span class="material-icons">menu</span>
        </button>
        <div class="topbar-title" id="page-title">Dashboard</div>
      </div>
      <div class="topbar-center">
        <div class="search-box" onclick="Components.Topbar.openSearch()">
          <span class="material-icons search-box-icon">search</span>
          <span class="search-box-placeholder">Buscar...</span>
          <kbd class="search-box-kbd">Ctrl+K</kbd>
        </div>
      </div>
      <div class="topbar-right">
        <div class="topbar-status" id="ws-status" title="WebSocket">
          <span class="status-indicator disconnected"></span>
          <span class="status-label">Offline</span>
        </div>
        <div class="topbar-notifications" id="notif-bell" onclick="Components.Topbar.toggleNotifications()">
          <span class="material-icons">notifications_none</span>
          <span class="notif-badge hidden" id="notif-count">0</span>
        </div>
        <div class="topbar-user" onclick="Router.navigate('/settings')">
          <span class="topbar-avatar">👤</span>
        </div>
      </div>
    `;
    this._subscribeToStore();
  },

  updatePageTitle(path) {
    const el = document.getElementById('page-title');
    if (el) el.textContent = this._pageTitles[path] || path.split('/').pop();
  },

  openSearch() {
    const ov = document.getElementById('search-overlay');
    if (ov) { ov.classList.remove('hidden'); document.getElementById('global-search')?.focus(); }
  },
  closeSearch() {
    const ov = document.getElementById('search-overlay');
    if (ov) ov.classList.add('hidden');
  },

  toggleNotifications() {
    const badge = document.getElementById('notif-count');
    if (badge) badge.classList.add('hidden');
  },
  _subscribeToStore() {
    Store.subscribe('wsStatus', (status) => {
      const el = document.getElementById('ws-status');
      if (!el) return;
      const dot = el.querySelector('.status-indicator');
      const label = el.querySelector('.status-label');
      if (status === 'connected') {
        dot.className = 'status-indicator connected';
        label.textContent = 'Online';
      } else {
        dot.className = 'status-indicator disconnected';
        label.textContent = 'Offline';
      }
    });
    Store.subscribe('notifications', (notifs) => {
      const badge = document.getElementById('notif-count');
      if (!badge) return;
      const unread = (notifs || []).filter(n => !n.read).length;
      badge.textContent = unread;
      badge.classList.toggle('hidden', unread === 0);
    });
  }
};

document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); Components.Topbar.openSearch(); }
  if (e.key === 'Escape') Components.Topbar.closeSearch();
});
