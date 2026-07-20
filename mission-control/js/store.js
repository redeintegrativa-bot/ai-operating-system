/**
 * AIOS Mission Control - State Management Store
 * LocalStorage persistence with subscription-based reactivity.
 * Fetches real data from Kernel API when backend is available.
 * Supports polling for real-time dashboard updates + WebSocket.
 */
const Store = {
  state: {
    agents: [],
    missions: [],
    tasks: [],
    memories: [],
    workspaces: [],
    tools: [],
    suggestions: [],
    dashboard: null,
    systemLogs: [],
    currentPage: 'dashboard',
    sidebarCollapsed: false,
    notifications: [],
    wsStatus: 'disconnected',
    wsEvents: []
  },

  loading: {
    agents: false,
    missions: false,
    tasks: false,
    memories: false,
    workspaces: false,
    tools: false,
    suggestions: false,
    dashboard: false,
    systemLogs: false,
  },

  errors: {
    agents: null,
    missions: null,
    tasks: null,
    memories: null,
    workspaces: null,
    tools: null,
    suggestions: null,
    dashboard: null,
    systemLogs: null,
  },

  _subscribers: {},
  _storageKey: 'aios_mission_control_state',
  _pollInterval: null,
  _POLL_MS: 3000,

  init() {
    const saved = this.load();
    if (saved && Object.keys(saved).length > 0) {
      Object.assign(this.state, saved);
    } else {
      this._loadMockData();
    }
    this.fetchAll();
    this._startPolling();
    this._startWebSocket();
  },

  start() {
    this._startPolling();
  },

  stop() {
    if (this._pollInterval) {
      clearInterval(this._pollInterval);
      this._pollInterval = null;
    }
  },

  _startPolling() {
    if (this._pollInterval) return;
    this._pollInterval = setInterval(() => this._poll(), this._POLL_MS);
  },

  async _poll() {
    await Promise.all([
      this.fetchAgents().catch(() => {}),
      this.fetchDashboard().catch(() => {}),
    ]);
  },

  _startWebSocket() {
    // Iniciar WebSocket para updates em tempo real
    API.wsConnect();

    API.wsSubscribe('connected', () => {
      this.state.wsStatus = 'connected';
      this._notify('wsStatus');
    });
    API.wsSubscribe('disconnected', () => {
      this.state.wsStatus = 'disconnected';
      this._notify('wsStatus');
    });

    // Escutar eventos de tarefas em tempo real
    API.wsSubscribe('task.created', (event) => {
      this.state.wsEvents.push(event);
      if (this.state.wsEvents.length > 100) this.state.wsEvents.shift();
      this._notify('wsEvents');
      this.fetchTasks().catch(() => {});
    });
    API.wsSubscribe('task.assigned', (event) => {
      this.state.wsEvents.push(event);
      if (this.state.wsEvents.length > 100) this.state.wsEvents.shift();
      this._notify('wsEvents');
      this.fetchTasks().catch(() => {});
    });
    API.wsSubscribe('task.completed', (event) => {
      this.state.wsEvents.push(event);
      if (this.state.wsEvents.length > 100) this.state.wsEvents.shift();
      this._notify('wsEvents');
      this.fetchTasks().catch(() => {});
    });
    API.wsSubscribe('system.startup', (event) => {
      this.state.notifications.push({
        id: Date.now(),
        type: 'info',
        time: new Date().toLocaleTimeString(),
        message: `System status: ${event.data?.status || 'restarted'}`,
        read: false
      });
      if (this.state.notifications.length > 50) this.state.notifications.shift();
      this._notify('notifications');
    });
  },

  load() {
    try {
      const data = localStorage.getItem(this._storageKey);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      return null;
    }
  },
  save() {
    try {
      const toSave = { ...this.state };
      delete toSave.notifications;
      delete toSave.wsEvents;
      localStorage.setItem(this._storageKey, JSON.stringify(toSave));
    } catch (e) {}
  },

  async fetchAll() {
    await Promise.all([
      this.fetchAgents(),
      this.fetchMissions(),
      this.fetchSuggestions(),
      this.fetchDashboard(),
      this.fetchSystemLogs(),
    ]);
  },
  async fetchAgents() {
    this.loading.agents = true; this.errors.agents = null; this._notify('loading');
    try {
      const agents = await API.agents.list();
      this.state.agents = agents; this.save(); this._notify('agents');
    } catch (e) {
      this.errors.agents = e.message || 'Failed to load agents';
      this._notify('errors');
    } finally { this.loading.agents = false; this._notify('loading'); }
  },
  async fetchMissions() {
    this.loading.missions = true; this.errors.missions = null; this._notify('loading');
    try {
      const missions = await API.missions.list();
      if (missions.length > 0) { this.state.missions = missions; this.save(); this._notify('missions'); }
    } catch (e) { this.errors.missions = e.message || 'Failed to load missions'; this._notify('errors');
    } finally { this.loading.missions = false; this._notify('loading'); }
  },
  async fetchSuggestions() {
    this.loading.suggestions = true; this.errors.suggestions = null; this._notify('loading');
    try {
      const data = await API.suggestions();
      if (data && data.suggestions) { this.state.suggestions = data.suggestions; this._notify('suggestions'); }
    } catch (e) { this.errors.suggestions = e.message || 'Failed to load suggestions'; this._notify('errors');
    } finally { this.loading.suggestions = false; this._notify('loading'); }
  },
  async fetchDashboard() {
    this.loading.dashboard = true; this.errors.dashboard = null; this._notify('loading');
    try {
      const data = await API.dashboard();
      if (data) { this.state.dashboard = data; this._notify('dashboard'); }
    } catch (e) { this.errors.dashboard = e.message || 'Failed to load dashboard'; this._notify('errors');
    } finally { this.loading.dashboard = false; this._notify('loading'); }
  },
  async fetchSystemLogs() {
    this.loading.systemLogs = true; this.errors.systemLogs = null; this._notify('loading');
    try {
      const logs = await API.system.logs();
      if (logs) { this.state.systemLogs = logs; this._notify('systemLogs'); }
    } catch (e) { this.errors.systemLogs = e.message || 'Failed to load logs'; this._notify('errors');
    } finally { this.loading.systemLogs = false; this._notify('loading'); }
  },

  isLoading() { return Object.values(this.loading).some(v => v); },
  getFirstError() {
    for (const key of Object.keys(this.errors)) { if (this.errors[key]) return this.errors[key]; }
    return null;
  },

  update(key, data, merge = false) {
    if (merge && typeof data === 'object' && !Array.isArray(data) && this.state[key]) {
      this.state[key] = { ...this.state[key], ...data };
    } else {
      this.state[key] = data;
    }
    this.save(); this._notify(key);
  },
  subscribe(key, callback) {
    if (!this._subscribers[key]) this._subscribers[key] = [];
    this._subscribers[key].push(callback);
    return () => {
      this._subscribers[key] = this._subscribers[key].filter(cb => cb !== callback);
    };
  },
  _notify(key) {
    const cbs = [...(this._subscribers[key] || []), ...(this._subscribers['*'] || [])];
    cbs.forEach(cb => { try { cb(this.state[key], key); } catch (e) { console.error('[Store] Subscriber error:', e); } });
  },
  get(key) { return this.state[key]; },

  findById(collection, id) { return (this.state[collection] || []).find(item => item.id === id); },
  addItem(key, item) {
    const arr = this.state[key] || [];
    const maxId = arr.reduce((max, i) => Math.max(max, i.id || 0), 0);
    item.id = maxId + 1; arr.push(item); this.update(key, arr);
  },
  removeItem(key, id) {
    this.update(key, (this.state[key] || []).filter(item => item.id !== id));
  },
  updateItem(key, id, updates) {
    this.update(key, (this.state[key] || []).map(item =>
      Object.assign({}, item, item.id === id ? updates : {})
    ));
  },

  _loadMockData() {
    this.state.agents = [
      { id: 1, name: 'Orquestrador', status: 'online', capabilities: ['routing', 'coordination'], avatar: '🎯' },
      { id: 2, name: 'Arquiteto', status: 'busy', capabilities: ['architecture', 'design'], avatar: '🏗️' },
      { id: 3, name: 'Engenheiro', status: 'online', capabilities: ['coding', 'testing'], avatar: '⚙️' },
      { id: 4, name: 'Seguranca', status: 'online', capabilities: ['security', 'auth', 'encryption'], avatar: '🛡️' },
      { id: 5, name: 'Analista', status: 'busy', capabilities: ['analysis', 'research', 'data'], avatar: '📊' },
      { id: 6, name: 'Documentador', status: 'offline', capabilities: ['documentation', 'changelog'], avatar: '📝' },
      { id: 7, name: 'Tester', status: 'online', capabilities: ['testing', 'QA', 'debugging'], avatar: '🧪' },
      { id: 8, name: 'DevOps', status: 'busy', capabilities: ['CI/CD', 'deploy', 'monitoring'], avatar: '🚀' }
    ];
    this.state.missions = [
      { id: 1, name: 'Sistema de Autenticacao', status: 'active', progress: 65, agents: [2, 3, 4], priority: 'high', startDate: '2026-07-01', deadline: '2026-07-25', description: 'Complete auth system with OAuth2 and JWT' },
      { id: 2, name: 'API Gateway Redesign', status: 'active', progress: 30, agents: [2, 3], priority: 'high', startDate: '2026-07-10', deadline: '2026-08-05', description: 'Redesign API gateway for microservices' },
      { id: 3, name: 'Performance Optimization', status: 'pending', progress: 0, agents: [5], priority: 'medium', deadline: '2026-08-15' },
      { id: 4, name: 'Security Audit Q3', status: 'completed', progress: 100, agents: [4, 7], priority: 'high', startDate: '2026-06-15', deadline: '2026-07-01' },
      { id: 5, name: 'Documentation Sprint', status: 'pending', progress: 0, agents: [6], priority: 'low', deadline: '2026-08-30' },
      { id: 6, name: 'CI/CD Pipeline v2', status: 'active', progress: 80, agents: [8, 7], priority: 'high', startDate: '2026-06-20', deadline: '2026-07-20' }
    ];
    this.state.tasks = [
      { id: 1, title: 'Implementar login OAuth2', column: 'in_progress', priority: 'high', assignee: 3, tags: ['auth', 'backend'], mission: 1 },
      { id: 2, title: 'Design database schema', column: 'done', priority: 'high', assignee: 2, mission: 1 },
      { id: 3, title: 'Write unit tests', column: 'todo', priority: 'medium', assignee: 7, mission: 1 },
      { id: 4, title: 'Setup rate limiting', column: 'backlog', priority: 'medium', assignee: 4, mission: 2 },
      { id: 5, title: 'API endpoint docs', column: 'todo', priority: 'low', assignee: 6, mission: 2 },
      { id: 6, title: 'Load testing setup', column: 'in_progress', priority: 'high', assignee: 7, mission: 3 },
      { id: 7, title: 'Security scan', column: 'review', priority: 'high', assignee: 4, mission: 6 },
      { id: 8, title: 'Container orchestration', column: 'done', priority: 'high', assignee: 8, mission: 6 },
      { id: 9, title: 'Memory system refactor', column: 'backlog', assignee: 2, mission: null },
      { id: 10, title: 'Dashboard UI improvements', column: 'todo', assignee: 3, mission: null },
      { id: 11, title: 'JWT refresh tokens', column: 'in_progress', priority: 'high', assignee: 3, mission: 1 },
      { id: 12, title: 'Performance profiling', column: 'review', priority: 'medium', assignee: 5, mission: 3 }
    ];
    this.state.memories = [
      { id: 1, type: 'episodic', title: 'Authentication Bug Fix', content: 'Fixed JWT token validation issue.', agent: 4, date: '2026-07-15', tags: ['bugfix', 'auth'] },
      { id: 2, type: 'semantic', title: 'API Design Patterns', content: 'REST API follows OpenAPI 3.0 spec.', agent: 2, date: '2026-07-10', tags: ['architecture', 'API'] },
      { id: 3, type: 'procedural', title: 'Deployment Process', content: '1. Run tests 2. Build 3. Tag release 4. Deploy.', agent: 8, date: '2026-07-08', tags: ['devops'] },
      { id: 4, type: 'episodic', title: 'Performance Optimization', content: 'DB queries 3s -> 200ms.', agent: 5, date: '2026-07-12', tags: ['performance'] },
      { id: 5, type: 'semantic', title: 'Security Practices', content: 'API keys in env vars. Rate limiting.', agent: 4, date: '2026-07-05', tags: ['security'] },
      { id: 6, type: 'procedural', title: 'Code Review Checklist', content: '1. Security 2. Error handling 3. Tests 4. Performance.', agent: 7, date: '2026-07-01', tags: ['process'] }
    ];
    this.state.workspaces = [
      { id: 1, name: 'AIOS Core', agents: [1, 2, 3], status: 'active', progress: 72 },
      { id: 2, name: 'Authentication Service', agents: [2, 3, 4], status: 'active', progress: 65 },
      { id: 3, name: 'API Gateway', agents: [2, 3, 8], status: 'active', progress: 30 },
      { id: 4, name: 'Security Module', agents: [4, 7], status: 'active', progress: 85 },
      { id: 5, name: 'Documentation Hub', agents: [6], status: 'planning', progress: 10 }
    ];
    this.state.tools = [
      { id: 1, name: 'Security Scanner', category: 'security', usageCount: 47, status: 'active' },
      { id: 2, name: 'Performance Profiler', category: 'performance', usageCount: 23, status: 'active' },
      { id: 3, name: 'Code Generator', category: 'development', usageCount: 89, status: 'active' },
      { id: 4, name: 'Test Runner', category: 'testing', usageCount: 156, status: 'active' },
      { id: 5, name: 'Deploy Bot', category: 'devops', usageCount: 34, status: 'active' },
      { id: 6, name: 'Memory Indexer', category: 'data', usageCount: 12, status: 'active' },
      { id: 7, name: 'Log Analyzer', category: 'monitoring', usageCount: 67, status: 'active' },
      { id: 8, name: 'Dependency Auditor', category: 'security', usageCount: 19, status: 'active' }
    ];
    this.state.notifications = [
      { id: 1, type: 'success', message: 'CI/CD Pipeline v2 completed', time: '5 min ago', read: false },
      { id: 2, type: 'warning', message: 'High memory usage', time: '12 min ago', read: false },
      { id: 3, type: 'info', message: 'Security scan: 0 vulnerabilities', time: '1 hour ago', read: true }
    ];
    this.save();
  }
};
