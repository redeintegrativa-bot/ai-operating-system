/**
 * AIOS Dashboard - Client-Side Router
 * Hash-based SPA navigation.
 */
const Router = {
  routes: {},
  currentRoute: null,
  register(path, handler) { this.routes[path] = handler; },
  navigate(path) { if (path === this.currentRoute) return; window.location.hash = path; },
  resolve() {
    const hash = window.location.hash.slice(1) || '/dashboard';
    const handler = this.routes[hash];
    if (handler) { this.currentRoute = hash; handler(hash); this._dispatchRouteChange(hash); }
    else this.navigate('/dashboard');
  },
  _dispatchRouteChange(path) { window.dispatchEvent(new CustomEvent('route:change', { detail: { path } })); },
  init() {
    window.addEventListener('hashchange', () => this.resolve());
    if (!window.location.hash) window.location.hash = '/dashboard';
    else this.resolve();
  },
  getCurrentPath() { return window.location.hash.slice(1) || '/dashboard'; },
  getParam(routePattern, index) {
    const c = this.getCurrentPath().split('/');
    const p = routePattern.split('/');
    if (p.length !== c.length) return null;
    for (let i = 0; i < p.length; i++) if (p[i].startsWith(':') && i === index) return c[i];
    return null;
  }
};
