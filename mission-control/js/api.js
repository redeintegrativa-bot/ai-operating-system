/**
 * AIOS Mission Control - API Client
 * HTTP + WebSocket client for the AIOS backend with mock fallback.
 */

const API_URL = 'http://localhost:8000/api';
const WS_URL = `ws://localhost:8000/ws`;
const MOCK_MODE = false;

const API = {
  _ws: null,
  _wsConnected: false,
  _wsSubscribers: {},
  _wsReconnectTimer: null,

  async _fetch(endpoint, options = {}) {
    if (MOCK_MODE) return this._mockResponse(endpoint);

    try {
      const url = `${API_URL}${endpoint}`;
      const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
        signal: AbortSignal.timeout(5000)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data && data.status === 'error') throw new Error(data.message || 'API error');
      return data;
    } catch (e) {
      if (e.name === 'TimeoutError') throw new Error('API timeout');
      const fallback = this._mockResponse(endpoint);
      if (fallback) return fallback;
      throw e;
    }
  },

  // -----------------------------------------------------------------------
  // WebSocket real-time connection
  // -----------------------------------------------------------------------

  wsConnect() {
    if (this._ws && (this._ws.readyState === WebSocket.OPEN || this._ws.readyState === WebSocket.CONNECTING)) return;
    try {
      this._ws = new WebSocket(WS_URL);
      this._ws.onopen = () => {
        this._wsConnected = true;
        console.log('[WS] Connected');
        if (this._wsSubscribers['*']) {
          this._wsSubscribers['*'].forEach(fn => fn({ type: 'connected' }));
        }
      };
      this._ws.onclose = () => {
        this._wsConnected = false;
        console.log('[WS] Disconnected, reconnecting in 5s');
        if (this._wsSubscribers['*']) {
          this._wsSubscribers['*'].forEach(fn => fn({ type: 'disconnected' }));
        }
        this._wsReconnectTimer = setTimeout(() => this.wsConnect(), 5000);
      };
      this._ws.onerror = (err) => {
        console.warn('[WS] Error:', err);
      };
      this._ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data);
          const eventType = data.event_type || data.type;
          if (eventType && this._wsSubscribers[eventType]) {
            this._wsSubscribers[eventType].forEach(fn => fn(data));
          }
          if (eventType && this._wsSubscribers['*']) {
            this._wsSubscribers['*'].forEach(fn => fn(data));
          }
        } catch (e) {}
      };
    } catch (e) {
      console.warn('[WS] Connection failed:', e);
      this._wsReconnectTimer = setTimeout(() => this.wsConnect(), 10000);
    }
  },

  wsDisconnect() {
    if (this._wsReconnectTimer) clearTimeout(this._wsReconnectTimer);
    if (this._ws) {
      this._ws.onclose = null;
      this._ws.close();
      this._ws = null;
    }
    this._wsConnected = false;
  },

  wsSubscribe(eventType, callback) {
    if (!this._wsSubscribers[eventType]) this._wsSubscribers[eventType] = [];
    this._wsSubscribers[eventType].push(callback);
    return () => {
      const arr = this._wsSubscribers[eventType];
      if (arr) this._wsSubscribers[eventType] = arr.filter(cb => cb !== callback);
    };
  },

  wsSend(data) {
    if (this._ws && this._ws.readyState === WebSocket.OPEN) {
      this._ws.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  },

  // -----------------------------------------------------------------------
  // Mock fallback data
  // -----------------------------------------------------------------------

  _mockResponse(endpoint) {
    const baseUrl = (endpoint || '').split('?')[0];
    const data = {
      agents: [
        { id: 'orchestrator', name: 'Orquestrador', status: 'online', role: 'Orchestrator', capabilities: ['routing', 'coordination'], currentTask: null, avatar: '🎯' },
        { id: 'architect', name: 'Arquiteto', status: 'busy', role: 'Architect', capabilities: ['architecture', 'design'], currentTask: 'Design microservices architecture', avatar: '🏗️' },
        { id: 'engineer', name: 'Engenheiro', status: 'online', role: 'Engineer', capabilities: ['coding', 'testing'], currentTask: null, avatar: '⚙️' },
        { id: 'security', name: 'Seguranca', status: 'online', role: 'Security', capabilities: ['security', 'auth', 'encryption'], currentTask: null, avatar: '🛡️' },
        { id: 'analyst', name: 'Analista', status: 'busy', role: 'Analyst', capabilities: ['analysis', 'data', 'research'], currentTask: 'Performance bottleneck analysis', avatar: '📊' },
        { id: 'documenter', name: 'Documentador', status: 'offline', role: 'Documenter', capabilities: ['documentation', 'changelog'], currentTask: null, avatar: '📝' },
        { id: 'tester', name: 'Tester', status: 'online', role: 'Tester', capabilities: ['testing', 'QA', 'debugging'], currentTask: null, avatar: '🧪' },
        { id: 'devops', name: 'DevOps', status: 'busy', role: 'DevOps', capabilities: ['CI/CD', 'deploy', 'monitoring'], currentTask: 'Deploy staging environment', avatar: '🚀' }
      ],
      'system/status': {
        status: 'operational',
        uptime: '72h 34m',
        memory: { used: 3.2, total: 8, percent: 40 },
        cpu: { usage: 34, cores: 8 },
        threads: { active: 12, idle: 28 },
        version: '0.1.0',
        startedAt: '2026-07-17T10:00:00Z',
        taskQueue: { pending: 3, running: 2, completed: 156 },
        recentActions: [
          { agent: 'orchestrator', action: 'Task dispatched to Seguranca', time: '30s ago' },
          { agent: 'analyst', action: 'Analysis completed for Performance Report', time: '2m ago' },
          { agent: 'devops', action: 'Deployment triggered: staging-v2.1', time: '5m ago' },
          { agent: 'engineer', action: 'PR #142 merged: auth module', time: '8m ago' },
          { agent: 'tester', action: 'Test suite passed: 247/247', time: '12m ago' }
        ],
        upcomingTasks: [
          { title: 'Database migration v3', scheduled: '14:30', priority: 'high' },
          { title: 'Security review: auth module', scheduled: '15:00', priority: 'high' },
          { title: 'Performance benchmark run', scheduled: '16:00', priority: 'medium' },
          { title: 'Documentation sync', scheduled: '17:30', priority: 'low' }
        ]
      },
      'system/logs': [
        { level: 'info', timestamp: '2026-07-20T10:30:00Z', message: 'System health check: OK', module: 'health' },
        { level: 'warn', timestamp: '2026-07-20T10:25:00Z', message: 'Memory usage at 75% threshold', module: 'monitor' },
        { level: 'info', timestamp: '2026-07-20T10:20:00Z', message: 'Task #1042 completed: Data export', module: 'tasks' },
        { level: 'info', timestamp: '2026-07-20T10:15:00Z', message: 'Agent Arquiteto started task: API design review', module: 'agents' },
        { level: 'error', timestamp: '2026-07-20T10:10:00Z', message: 'Connection pool exhausted, retrying...', module: 'network' },
        { level: 'warn', timestamp: '2026-07-20T10:05:00Z', message: 'Certificate expiring in 7 days', module: 'security' },
        { level: 'info', timestamp: '2026-07-20T10:00:00Z', message: 'Task #1040 started: Security scan', module: 'tasks' },
        { level: 'info', timestamp: '2026-07-20T09:55:00Z', message: 'Agent Documentador saved 3 new memories', module: 'memory' },
        { level: 'info', timestamp: '2026-07-20T09:50:00Z', message: 'System startup completed', module: 'system' }
      ],
      'tasks/queue': {
        pending: [
          { id: 'T-1045', title: 'Database migration v3', priority: 'high', created: '10:22', agent: 'arquiteto' },
          { id: 'T-1044', title: 'Update API documentation', priority: 'low', created: '10:18', agent: 'documentador' },
          { id: 'T-1043', title: 'Dependency audit', priority: 'medium', created: '10:10', agent: 'seguranca' }
        ],
        running: [
          { id: 'T-1042', title: 'Performance benchmark', priority: 'high', started: '10:05', agent: 'analista' },
          { id: 'T-1041', title: 'Security scan auth module', priority: 'high', started: '10:00', agent: 'seguranca' }
        ]
      }
    };
    return data[baseUrl] || null;
  },

  _normalizeAgents(agents) {
    return (agents || []).map(a => ({
      id: a.id,
      name: a.name,
      status: a.status,
      capabilities: a.capabilities || [],
      currentTask: a.currentTask || a.current_task || null,
      avatar: a.avatar || '🤖'
    }));
  },

  // -----------------------------------------------------------------------
  // API methods
  // -----------------------------------------------------------------------

  agents: {
    async list() {
      const data = await API._fetch('/agents');
      return API._normalizeAgents(data?.agents || data || []);
    }
  },

  missions: {
    async list() {
      const data = await API._fetch('/missions');
      return (data?.missions || data || []).map(m => ({
        id: m.id, name: m.name, status: m.status, progress: m.progress || 0,
        agents: m.agents || [], priority: m.priority || 'medium',
        startDate: m.startDate || m.start_date, deadline: m.deadline,
        description: m.description || ''
      }));
    }
  },

  async suggestions() {
    const data = await API._fetch('/suggestions');
    return data || { suggestions: [] };
  },

  async dashboard() {
    return await API._fetch('/system/status');
  },

  system: {
    async logs(limit = 50) {
      const data = await API._fetch(`/system/logs?limit=${limit}`);
      return data?.logs || data || [];
    },
    async status() {
      return await API._fetch('/system/status');
    }
  },

  tasks: {
    async queue() {
      const data = await API._fetch('/tasks/queue');
      return data || { pending: [], running: [] };
    }
  }
};
