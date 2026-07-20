/**
 * AIOS Dashboard - State Management Store
 * LocalStorage persistence, subscription reactivity, polling + WebSocket.
 * All state mutation happens here, never in pages.
 */
const Store = {
  state: {
    agents: [],
    tasks: [],
    taskDetail: null,
    memories: [],
    skills: [],
    plugins: [],
    workspaces: [],
    missions: [],
    tools: [],
    marketplace: [],
    finances: [],
    analytics: [],
    suggestions: [],
    capabilities: null,
    dashboard: null,
    systemLogs: [],
    settings: null,
    user: null,
    currentPage: 'dashboard',
    sidebarCollapsed: false,
    notifications: [],
    wsStatus: 'disconnected',
    wsEvents: []
  },

  loading: {
    agents: false, tasks: false, memories: false, skills: false,
    plugins: false, workspaces: false, missions: false, tools: false,
    marketplace: false, finances: false, analytics: false, suggestions: false,
    dashboard: false, systemLogs: false, settings: false, capabilities: false
  },

  errors: {
    agents: null, tasks: null, memories: null, skills: null,
    plugins: null, workspaces: null, missions: null, tools: null,
    marketplace: null, finances: null, analytics: null, suggestions: null,
    dashboard: null, systemLogs: null, settings: null, capabilities: null
  },

  _subscribers: {},
  _storageKey: 'aios_dashboard_state',
  _pollInterval: null,
  _POLL_MS: 3000,

  init() {
    const saved = this.load();
    if (saved && Object.keys(saved).length > 0) Object.assign(this.state, saved);
    else this._loadMockData();
    this.fetchAll();
    this._startPolling();
    this._startWebSocket();
  },

  start() { this._startPolling(); },
  stop() { if (this._pollInterval) { clearInterval(this._pollInterval); this._pollInterval = null; } },

  _startPolling() {
    if (this._pollInterval) return;
    this._pollInterval = setInterval(() => this._poll(), this._POLL_MS);
  },
  async _poll() {
    await Promise.all([
      this.fetchAgents().catch(() => {}),
      this.fetchDashboard().catch(() => {}),
      this.fetchSystemLogs().catch(() => {}),
    ]);
  },

  _startWebSocket() {
    API.wsConnect();
    API.wsSubscribe('connected', () => { this.state.wsStatus = 'connected'; this._notify('wsStatus'); });
    API.wsSubscribe('disconnected', () => { this.state.wsStatus = 'disconnected'; this._notify('wsStatus'); });
    API.wsSubscribe('task.created', () => this.fetchTasks().catch(() => {}));
    API.wsSubscribe('task.assigned', () => this.fetchTasks().catch(() => {}));
    API.wsSubscribe('task.completed', () => this.fetchTasks().catch(() => {}));
    API.wsSubscribe('system.startup', (ev) => {
      this.state.notifications.push({id:Date.now(), type:'info', time:new Date().toLocaleTimeString(), message:`System: ${ev.data?.status||'restarted'}`, read:false});
      if (this.state.notifications.length > 50) this.state.notifications.shift();
      this._notify('notifications');
    });
  },

  load() { try { const d=localStorage.getItem(this._storageKey); return d?JSON.parse(d):null; } catch(e){return null;} },
  save() {
    try { const ts={...this.state}; delete ts.notifications; delete ts.wsEvents; localStorage.setItem(this._storageKey,JSON.stringify(ts)); } catch(e){} 
  },

  async fetchAll() {
    await Promise.all([
      this.fetchAgents(), this.fetchTasks(), this.fetchMemories(),
      this.fetchSkills(), this.fetchPlugins(), this.fetchWorkspaces(),
      this.fetchMissions(), this.fetchTools(), this.fetchMarketplace(),
      this.fetchFinances(), this.fetchAnalytics(), this.fetchSuggestions(),
      this.fetchDashboard(), this.fetchSystemLogs(), this.fetchSettings(),
      this.fetchCapabilities()
    ]);
  },

  _makeFetcher(key, apiFn) {
    return async () => {
      this.loading[key] = true; this.errors[key] = null; this._notify('loading');
      try {
        const data = await apiFn();
        if (data != null) { this.state[key] = data; this.save(); this._notify(key); }
      } catch(e) { this.errors[key] = e.message||'Erro'; this._notify('errors'); }
      finally { this.loading[key] = false; this._notify('loading'); }
    };
  },

  fetchAgents: null, fetchTasks: null, fetchMemories: null,
  fetchSkills: null, fetchPlugins: null, fetchWorkspaces: null,
  fetchMissions: null, fetchTools: null, fetchMarketplace: null,
  fetchFinances: null, fetchAnalytics: null, fetchSuggestions: null,
  fetchDashboard: null, fetchSystemLogs: null, fetchSettings: null,
  fetchCapabilities: null,

  isLoading() { return Object.values(this.loading).some(v => v); },
  getFirstError() { for(const k of Object.keys(this.errors)) if(this.errors[k]) return this.errors[k]; return null; },

  update(key, data, merge = false) {
    if (merge && typeof data === 'object' && !Array.isArray(data) && this.state[key])
      this.state[key] = { ...this.state[key], ...data };
    else this.state[key] = data;
    this.save(); this._notify(key);
  },
  subscribe(key, callback) {
    if (!this._subscribers[key]) this._subscribers[key] = [];
    this._subscribers[key].push(callback);
    return () => { this._subscribers[key] = this._subscribers[key].filter(cb => cb !== callback); };
  },
  _notify(key) {
    const cbs = [...(this._subscribers[key]||[]), ...(this._subscribers['*']||[])];
    cbs.forEach(cb => { try { cb(this.state[key],key); } catch(e){console.error('[Store]',e);} });
  },
  get(key) { return this.state[key]; },

  findById(collection, id) { return (this.state[collection]||[]).find(item => item.id === id); },
  addItem(key, item) { const a=this.state[key]||[]; item.id=(a.reduce((m,i)=>Math.max(m,i.id||0),0)||0)+1; a.push(item); this.update(key,a); },
  removeItem(key, id) { this.update(key,(this.state[key]||[]).filter(i=>i.id!==id)); },
  updateItem(key, id, updates) { this.update(key,(this.state[key]||[]).map(i=>i.id===id?Object.assign({},i,updates):i)); },

  _loadMockData() { /* mock data omitted - backend handles this */ }
};

// Wire fetchers to API
Store.fetchAgents = Store._makeFetcher('agents', () => API.agents.list());
Store.fetchTasks = Store._makeFetcher('tasks', () => API.tasks.list());
Store.fetchMemories = Store._makeFetcher('memories', () => API.memories.list());
Store.fetchSkills = Store._makeFetcher('skills', () => API.skills.list());
Store.fetchPlugins = Store._makeFetcher('plugins', () => API.plugins.list());
Store.fetchWorkspaces = Store._makeFetcher('workspaces', () => API.workspaces.list());
Store.fetchMissions = Store._makeFetcher('missions', () => API.missions.list());
Store.fetchTools = Store._makeFetcher('tools', () => API.tools.list());
Store.fetchMarketplace = Store._makeFetcher('marketplace', () => API.marketplace.list());
Store.fetchFinances = Store._makeFetcher('finances', () => API.finances.list());
Store.fetchAnalytics = Store._makeFetcher('analytics', () => API.analytics.get());
Store.fetchSuggestions = Store._makeFetcher('suggestions', () => API.suggestions());
Store.fetchDashboard = Store._makeFetcher('dashboard', () => API.system.status());
Store.fetchSystemLogs = Store._makeFetcher('systemLogs', () => API.system.logs());
Store.fetchSettings = Store._makeFetcher('settings', () => API.settings.get());
Store.fetchCapabilities = Store._makeFetcher('capabilities', () => API.capabilities.get());
