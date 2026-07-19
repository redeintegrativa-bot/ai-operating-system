/**
 * AIOS Mission Control - State Management Store
 * LocalStorage persistence with subscription-based reactivity.
 * Fetches real data from Kernel API when backend is available.
 */
const Store = {
  /** @type {Object} Application state */
  state: {
    agents: [],
    missions: [],
    tasks: [],
    memories: [],
    workspaces: [],
    tools: [],
    suggestions: [],
    dashboard: null,
    currentPage: 'dashboard',
    sidebarCollapsed: false,
    notifications: []
  },

  /** @type {Object} Loading flags keyed by data type */
  loading: {
    agents: false,
    missions: false,
    tasks: false,
    memories: false,
    workspaces: false,
    tools: false,
    suggestions: false,
    dashboard: false,
  },

  /** @type {Object|null} Error objects keyed by data type */
  errors: {
    agents: null,
    missions: null,
    tasks: null,
    memories: null,
    workspaces: null,
    tools: null,
    suggestions: null,
    dashboard: null,
  },

  /** @type {Object} Subscriber callbacks keyed by state property */
  _subscribers: {},

  /** @type {string} LocalStorage key */
  _storageKey: 'aios_mission_control_state',

  /**
   * Initialize store with mock data or load from localStorage,
   * then attempt to fetch real data from the Kernel API.
   */
  init() {
    const saved = this.load();
    if (saved && Object.keys(saved).length > 0) {
      Object.assign(this.state, saved);
    } else {
      this._loadMockData();
    }
    this.fetchAll();
  },

  /**
   * Load state from localStorage.
   * @returns {Object|null}
   */
  load() {
    try {
      const data = localStorage.getItem(this._storageKey);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      console.warn('[Store] Failed to load state:', e);
      return null;
    }
  },

  /**
   * Save current state to localStorage.
   */
  save() {
    try {
      const toSave = { ...this.state };
      delete toSave.notifications;
      localStorage.setItem(this._storageKey, JSON.stringify(toSave));
    } catch (e) {
      console.warn('[Store] Failed to save state:', e);
    }
  },

  /**
   * Sync state with backend (placeholder for future API integration).
   * @returns {Promise<void>}
   */
  async sync() {
    // Placeholder: will POST local state and merge remote changes
    console.log('[Store] sync() called — will connect to backend in future version');
  },

  /**
   * Update a state key and notify subscribers.
   * @param {string} key - State property to update
   * @param {*} data - New value (replaces or merges)
   * @param {boolean} [merge=false] - If true and data is object, merge into existing
   */
  update(key, data, merge = false) {
    if (merge && typeof data === 'object' && !Array.isArray(data) && this.state[key]) {
      this.state[key] = { ...this.state[key], ...data };
    } else {
      this.state[key] = data;
    }
    this.save();
    this._notify(key);
  },

  /**
   * Subscribe to changes on a specific state key.
   * @param {string} key - State property to watch
   * @param {Function} callback - Called with (newValue, key) on change
   * @returns {Function} Unsubscribe function
   */
  subscribe(key, callback) {
    if (!this._subscribers[key]) {
      this._subscribers[key] = [];
    }
    this._subscribers[key].push(callback);

    return () => {
      this._subscribers[key] = this._subscribers[key].filter(cb => cb !== callback);
    };
  },

  /**
   * Notify all subscribers of a state key change.
   * @param {string} key
   * @private
   */
  _notify(key) {
    if (this._subscribers[key]) {
      this._subscribers[key].forEach(cb => {
        try {
          cb(this.state[key], key);
        } catch (e) {
          console.error('[Store] Subscriber error:', e);
        }
      });
    }
    // Also notify wildcard subscribers
    if (this._subscribers['*']) {
      this._subscribers['*'].forEach(cb => {
        try {
          cb(this.state[key], key);
        } catch (e) {
          console.error('[Store] Wildcard subscriber error:', e);
        }
      });
    }
  },

  /**
   * Get a state value by key.
   * @param {string} key
   * @returns {*}
   */
  get(key) {
    return this.state[key];
  },

  /**
   * Find an item in a state array by id.
   * @param {string} collection - State key (e.g. 'agents')
   * @param {number} id
   * @returns {Object|undefined}
   */
  findById(collection, id) {
    return (this.state[collection] || []).find(item => item.id === id);
  },

  /**
   * Add an item to a state array.
   * @param {string} key - State array key
   * @param {Object} item - Item to add (will get auto-generated id)
   */
  addItem(key, item) {
    const arr = this.state[key] || [];
    const maxId = arr.reduce((max, i) => Math.max(max, i.id || 0), 0);
    item.id = maxId + 1;
    arr.push(item);
    this.update(key, arr);
  },

  /**
   * Remove an item from a state array by id.
   * @param {string} key
   * @param {number} id
   */
  removeItem(key, id) {
    const arr = (this.state[key] || []).filter(item => item.id !== id);
    this.update(key, arr);
  },

  /**
   * Update an item in a state array by id.
   * @param {string} key
   * @param {number} id
   * @param {Object} updates
   */
  updateItem(key, id, updates) {
    const arr = (this.state[key] || []).map(item =>
      item.id === id ? { ...item, ...updates } : item
    );
    this.update(key, arr);
  },

  /**
   * Load mock data for all collections.
   * @private
   */
  _loadMockData() {
    this.state.agents = [
      { id: 1, name: 'Orquestrador', status: 'online', capabilities: ['routing', 'coordination'], currentTask: null, avatar: '🎯', description: 'Central orchestrator for task routing and agent coordination' },
      { id: 2, name: 'Arquiteto', status: 'busy', capabilities: ['architecture', 'design'], currentTask: 'Design microservices architecture', avatar: '🏗️', description: 'System architecture and design patterns expert' },
      { id: 3, name: 'Engenheiro', status: 'online', capabilities: ['coding', 'testing'], currentTask: null, avatar: '⚙️', description: 'Full-stack engineering and implementation' },
      { id: 4, name: 'Seguranca', status: 'online', capabilities: ['security', 'auth', 'encryption'], currentTask: null, avatar: '🛡️', description: 'Security analysis and vulnerability assessment' },
      { id: 5, name: 'Analista', status: 'busy', capabilities: ['analysis', 'research', 'data'], currentTask: 'Performance bottleneck analysis', avatar: '📊', description: 'Data analysis and research specialist' },
      { id: 6, name: 'Documentador', status: 'offline', capabilities: ['documentation', 'changelog'], currentTask: null, avatar: '📝', description: 'Technical documentation and changelog management' },
      { id: 7, name: 'Tester', status: 'online', capabilities: ['testing', 'QA', 'debugging'], currentTask: null, avatar: '🧪', description: 'Quality assurance and automated testing' },
      { id: 8, name: 'DevOps', status: 'busy', capabilities: ['CI/CD', 'deploy', 'monitoring'], currentTask: 'Deploy staging environment', avatar: '🚀', description: 'Deployment pipeline and infrastructure management' }
    ];

    this.state.missions = [
      { id: 1, name: 'Sistema de Autenticacao', status: 'active', progress: 65, agents: [2, 3, 4], priority: 'high', startDate: '2026-07-01', deadline: '2026-07-25', description: 'Implement complete authentication system with OAuth2 and JWT' },
      { id: 2, name: 'API Gateway Redesign', status: 'active', progress: 30, agents: [2, 3], priority: 'high', startDate: '2026-07-10', deadline: '2026-08-05', description: 'Redesign API gateway for microservices architecture' },
      { id: 3, name: 'Performance Optimization', status: 'pending', progress: 0, agents: [5], priority: 'medium', startDate: null, deadline: '2026-08-15', description: 'Analyze and optimize system performance bottlenecks' },
      { id: 4, name: 'Security Audit Q3', status: 'completed', progress: 100, agents: [4, 7], priority: 'high', startDate: '2026-06-15', deadline: '2026-07-01', description: 'Quarterly security audit and penetration testing' },
      { id: 5, name: 'Documentation Sprint', status: 'pending', progress: 0, agents: [6], priority: 'low', startDate: null, deadline: '2026-08-30', description: 'Complete API documentation and developer guides' },
      { id: 6, name: 'CI/CD Pipeline v2', status: 'active', progress: 80, agents: [8, 7], priority: 'high', startDate: '2026-06-20', deadline: '2026-07-20', description: 'Upgrade CI/CD pipeline with automated testing and deployment' }
    ];

    this.state.tasks = [
      { id: 1, title: 'Implementar login OAuth2', column: 'in_progress', priority: 'high', assignee: 3, tags: ['auth', 'backend'], mission: 1 },
      { id: 2, title: 'Design database schema', column: 'done', priority: 'high', assignee: 2, tags: ['architecture', 'database'], mission: 1 },
      { id: 3, title: 'Write unit tests for auth', column: 'todo', priority: 'medium', assignee: 7, tags: ['testing'], mission: 1 },
      { id: 4, title: 'Setup rate limiting', column: 'backlog', priority: 'medium', assignee: 4, tags: ['security', 'backend'], mission: 2 },
      { id: 5, title: 'API endpoint documentation', column: 'todo', priority: 'low', assignee: 6, tags: ['documentation'], mission: 2 },
      { id: 6, title: 'Load testing setup', column: 'in_progress', priority: 'high', assignee: 7, tags: ['testing', 'performance'], mission: 3 },
      { id: 7, title: 'Security scan automation', column: 'review', priority: 'high', assignee: 4, tags: ['security', 'CI/CD'], mission: 6 },
      { id: 8, title: 'Container orchestration', column: 'done', priority: 'high', assignee: 8, tags: ['devops', 'infrastructure'], mission: 6 },
      { id: 9, title: 'Memory system refactor', column: 'backlog', priority: 'medium', assignee: 2, tags: ['architecture'], mission: null },
      { id: 10, title: 'Dashboard UI improvements', column: 'todo', priority: 'low', assignee: 3, tags: ['frontend', 'UI'], mission: null },
      { id: 11, title: 'Implement JWT refresh tokens', column: 'in_progress', priority: 'high', assignee: 3, tags: ['auth', 'security'], mission: 1 },
      { id: 12, title: 'Performance profiling', column: 'review', priority: 'medium', assignee: 5, tags: ['performance', 'analysis'], mission: 3 }
    ];

    this.state.memories = [
      { id: 1, type: 'episodic', title: 'Authentication Bug Fix', content: 'Fixed JWT token validation issue where expired tokens were not being properly rejected. Root cause: middleware order in Express. Applied fix by reordering middleware chain and adding explicit token expiry check before JWT.verify().', agent: 4, date: '2026-07-15', tags: ['bugfix', 'auth'] },
      { id: 2, type: 'semantic', title: 'API Design Patterns', content: 'REST API follows OpenAPI 3.0 spec. All endpoints use plural nouns. Response format: { data, meta, errors }. Versioning via URL path /api/v1/. Rate limiting: 100 req/min per API key.', agent: 2, date: '2026-07-10', tags: ['architecture', 'API'] },
      { id: 3, type: 'procedural', title: 'Deployment Process', content: '1. Run tests (npm test) 2. Build (npm run build) 3. Tag release (git tag v1.x.x) 4. Push to registry 5. Deploy to staging 6. Run smoke tests 7. Deploy to production after approval.', agent: 8, date: '2026-07-08', tags: ['devops', 'process'] },
      { id: 4, type: 'episodic', title: 'Performance Optimization Session', content: 'Database queries were causing 3s response times. Added compound indexes on users and sessions tables. Response time dropped to 200ms. Key learning: always EXPLAIN ANALYZE before indexing.', agent: 5, date: '2026-07-12', tags: ['performance', 'database'] },
      { id: 5, type: 'semantic', title: 'Security Best Practices', content: 'All API keys stored in environment variables. CORS configured for specific origins only. Rate limiting: 100 req/min per IP. Input validation on all endpoints using Joi schemas. SQL injection prevention via parameterized queries.', agent: 4, date: '2026-07-05', tags: ['security', 'best-practices'] },
      { id: 6, type: 'procedural', title: 'Code Review Checklist', content: '1. Check for security vulnerabilities 2. Verify error handling 3. Review test coverage 4. Check performance implications 5. Validate documentation updates 6. Ensure backwards compatibility.', agent: 7, date: '2026-07-01', tags: ['process', 'quality'] }
    ];

    this.state.workspaces = [
      { id: 1, name: 'AIOS Core', description: 'Core operating system modules and infrastructure', agents: [1, 2, 3], status: 'active', progress: 72, tasks: 24, completedTasks: 17 },
      { id: 2, name: 'Authentication Service', description: 'OAuth2 and JWT authentication system', agents: [2, 3, 4], status: 'active', progress: 65, tasks: 18, completedTasks: 12 },
      { id: 3, name: 'API Gateway', description: 'Microservices API gateway and routing', agents: [2, 3, 8], status: 'active', progress: 30, tasks: 15, completedTasks: 5 },
      { id: 4, name: 'Security Module', description: 'Security scanning and audit tools', agents: [4, 7], status: 'active', progress: 85, tasks: 10, completedTasks: 9 },
      { id: 5, name: 'Documentation Hub', description: 'Central documentation repository', agents: [6], status: 'planning', progress: 10, tasks: 8, completedTasks: 1 }
    ];

    this.state.tools = [
      { id: 1, name: 'Security Scanner', description: 'Automated security vulnerability scanner', category: 'security', usageCount: 47, lastUsed: '2026-07-18', status: 'active' },
      { id: 2, name: 'Performance Profiler', description: 'CPU and memory profiling tool', category: 'performance', usageCount: 23, lastUsed: '2026-07-17', status: 'active' },
      { id: 3, name: 'Code Generator', description: 'Scaffold code from OpenAPI specs', category: 'development', usageCount: 89, lastUsed: '2026-07-19', status: 'active' },
      { id: 4, name: 'Test Runner', description: 'Automated test execution engine', category: 'testing', usageCount: 156, lastUsed: '2026-07-19', status: 'active' },
      { id: 5, name: 'Deploy Bot', description: 'CI/CD deployment automation', category: 'devops', usageCount: 34, lastUsed: '2026-07-18', status: 'active' },
      { id: 6, name: 'Memory Indexer', description: 'Knowledge base indexing and search', category: 'data', usageCount: 12, lastUsed: '2026-07-16', status: 'active' },
      { id: 7, name: 'Log Analyzer', description: 'Intelligent log analysis and alerting', category: 'monitoring', usageCount: 67, lastUsed: '2026-07-19', status: 'active' },
      { id: 8, name: 'Dependency Auditor', description: 'Check dependencies for vulnerabilities', category: 'security', usageCount: 19, lastUsed: '2026-07-14', status: 'active' }
    ];

    this.state.notifications = [
      { id: 1, type: 'success', message: 'CI/CD Pipeline v2 deployment completed', time: '5 min ago', read: false },
      { id: 2, type: 'warning', message: 'High memory usage detected on server', time: '12 min ago', read: false },
      { id: 3, type: 'info', message: 'Security scan completed: 0 vulnerabilities', time: '1 hour ago', read: true }
    ];

    this.save();
  }
};
