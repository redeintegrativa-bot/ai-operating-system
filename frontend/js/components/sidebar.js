/**
 * AIOS Dashboard - Sidebar Component
 * Collapsible navigation sidebar.
 */
const Components = window.Components || {};

Components.Sidebar = {
  _el: null,
  _navItems: [
    { path: '/dashboard',  icon: 'dashboard',   label: 'Dashboard' },
    { path: '/login',      icon: 'login',       label: 'Login' },
    { path: '/agents',     icon: 'smart_toy',   label: 'Agentes' },
    { path: '/tasks',      icon: 'task',        label: 'Task Center' },
    { path: '/missions',   icon: 'flag',        label: 'Missões' },
    { path: '/kanban',     icon: 'view_column', label: 'Kanban' },
    { path: '/memory',     icon: 'memory',      label: 'Memória' },
    { path: '/capability', icon: 'psychology',  label: 'Capability Map' },
    { path: '/skills',     icon: 'school',      label: 'Skills' },
    { path: '/plugins',    icon: 'extension',   label: 'Plugins' },
    { path: '/tools',      icon: 'handyman',    label: 'Ferramentas' },
    { path: '/marketplace',icon: 'store',       label: 'Marketplace' },
    { path: '/workspaces', icon: 'folder',      label: 'Workspaces' },
    { path: '/analytics',  icon: 'analytics',   label: 'Analytics' },
    { path: '/finances',   icon: 'account_balance', label: 'Finanças' },
    { path: '/logs',       icon: 'article',     label: 'Logs' },
    { path: '/status',     icon: 'monitor_heart', label: 'Status' },
    { path: '/settings',   icon: 'settings',    label: 'Configurações' },
  ],

  render(container) {
    this._el = container;
    container.innerHTML = `
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <span class="sidebar-logo-icon">🎯</span>
          <span class="sidebar-logo-text">AIOS</span>
        </div>
        <button class="sidebar-toggle" aria-label="Toggle sidebar" onclick="Components.Sidebar.toggle()">
          <span class="material-icons">menu</span>
        </button>
      </div>
      <div class="sidebar-user">
        <div class="sidebar-avatar">👤</div>
        <div class="sidebar-user-info">
          <div class="sidebar-user-name">Admin</div>
          <div class="sidebar-user-role">Operador</div>
        </div>
        <div class="sidebar-status-dot" id="sidebar-status" title="Desconectado"></div>
      </div>
      <nav class="sidebar-nav">
        ${this._navItems.map(item => `
          <a class="sidebar-link" href="#${item.path}" data-path="${item.path}">
            <span class="material-icons sidebar-link-icon">${item.icon}</span>
            <span class="sidebar-link-label">${item.label}</span>
          </a>
        `).join('')}
      </nav>
      <div class="sidebar-footer"></div>
    `;
  },

  setActive(path) {
    if (!this._el) return;
    this._el.querySelectorAll('.sidebar-link').forEach(link => {
      link.classList.toggle('active', link.dataset.path === path);
    });
  },

  toggle() {
    if (!this._el) return;
    this._el.classList.toggle('collapsed');
    document.getElementById('app').classList.toggle('sidebar-collapsed');
  },

  updateStatus(status) {
    const dot = document.getElementById('sidebar-status');
    if (dot) {
      dot.className = 'sidebar-status-dot';
      if (status === 'connected') dot.classList.add('online');
    }
  }
};
