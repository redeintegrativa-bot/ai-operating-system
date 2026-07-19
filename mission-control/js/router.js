/**
 * AIOS Mission Control - Client-Side Router
 * Simple hash-based router for SPA navigation.
 */
const Router = {
  /** @type {Object} Route handlers keyed by path */
  routes: {},

  /** @type {string} Current active route */
  currentRoute: null,

  /**
   * Register a route handler.
   * @param {string} path - Route path (e.g. '/dashboard')
   * @param {Function} handler - Called when route matches
   */
  register(path, handler) {
    this.routes[path] = handler;
  },

  /**
   * Navigate to a route.
   * @param {string} path - Target route path
   */
  navigate(path) {
    if (path === this.currentRoute) return;
    window.location.hash = path;
  },

  /**
   * Resolve the current route and invoke its handler.
   */
  resolve() {
    const hash = window.location.hash.slice(1) || '/dashboard';
    const handler = this.routes[hash];

    if (handler) {
      this.currentRoute = hash;
      handler(hash);
      this._dispatchRouteChange(hash);
    } else {
      // Fallback to dashboard
      this.navigate('/dashboard');
    }
  },

  /**
   * Dispatch a custom event when route changes.
   * @param {string} path
   * @private
   */
  _dispatchRouteChange(path) {
    window.dispatchEvent(new CustomEvent('route:change', { detail: { path } }));
  },

  /**
   * Initialize router — listen for hash changes.
   */
  init() {
    window.addEventListener('hashchange', () => this.resolve());

    // Handle initial load
    if (!window.location.hash) {
      window.location.hash = '/dashboard';
    } else {
      this.resolve();
    }
  },

  /**
   * Get the current route path.
   * @returns {string}
   */
  getCurrentPath() {
    return window.location.hash.slice(1) || '/dashboard';
  },

  /**
   * Get route parameter by index (for dynamic segments).
   * @param {string} routePattern - Pattern like '/agents/:id'
   * @param {number} index - Segment index
   * @returns {string|null}
   */
  getParam(routePattern, index) {
    const current = this.getCurrentPath();
    const patternParts = routePattern.split('/');
    const currentParts = current.split('/');

    if (patternParts.length !== currentParts.length) return null;

    for (let i = 0; i < patternParts.length; i++) {
      if (patternParts[i].startsWith(':') && i === index) {
        return currentParts[i];
      }
    }
    return null;
  }
};
