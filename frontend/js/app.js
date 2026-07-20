/**
 * AIOS Dashboard - App Controller
 * Bootstraps the SPA and registers all routes.
 */
const App = {
  _currentPage: null,

  init() {
    this._registerRoutes();
    Store.init();
    Router.init();
    Components.Sidebar.render(document.getElementById('sidebar'));
    Components.Topbar.render(document.getElementById('topbar'));
  },

  _registerRoutes() {
    const pageMap = {
      '/login': Pages.Login,
      '/dashboard': Pages.Dashboard,
      '/agents': Pages.Agents,
      '/memory': Pages.Memory,
      '/tasks': Pages.Tasks,
      '/skills': Pages.Skills,
      '/plugins': Pages.Plugins,
      '/capability': Pages.Capability,
      '/settings': Pages.Settings,
      '/status': Pages.Status,
      '/workspaces': Pages.Workspaces,
      '/missions': Pages.Missions,
      '/kanban': Pages.Kanban,
      '/tools': Pages.Tools,
      '/marketplace': Pages.Marketplace,
      '/finances': Pages.Finances,
      '/analytics': Pages.Analytics,
      '/logs': Pages.Logs,
    };

    Object.entries(pageMap).forEach(([path, page]) => {
      Router.register(path, () => this._renderPage(page));
    });
  },

  _renderPage(page) {
    if (this._currentPage && this._currentPage.unmount) this._currentPage.unmount();
    const container = document.getElementById('content');
    const el = page.render ? page.render() : document.createElement('div');
    container.innerHTML = '';
    container.appendChild(el);
    this._currentPage = page;
    if (page.mount) page.mount();
    Components.Sidebar.setActive(Router.getCurrentPath());
    Components.Topbar.updatePageTitle(Router.getCurrentPath());
  }
};

document.addEventListener('DOMContentLoaded', () => App.init());
