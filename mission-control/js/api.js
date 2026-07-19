/**
 * AIOS Mission Control - API Layer
 * Consumes real data from the Kernel API backend.
 * Falls back to Store mock data if the API is unreachable.
 */
const API = {
  /** @type {string} Backend base URL */
  baseURL: '/api',

  /** @type {boolean} Whether the backend is reachable */
  _backendAvailable: null,

  /**
   * Generic HTTP request helper.
   * @param {string} method
   * @param {string} path
   * @param {*} [body]
   * @returns {Promise<{ok: boolean, data: *, status: number}>}
   */
  async _request(method, path, body) {
    try {
      const opts = {
        method,
        headers: { 'Content-Type': 'application/json' },
      };
      if (body) opts.body = JSON.stringify(body);
      const res = await fetch(`${this.baseURL}${path}`, opts);
      if (!res.ok) {
        return { ok: false, data: null, status: res.status };
      }
      const data = await res.json();
      this._backendAvailable = true;
      return { ok: true, data, status: res.status };
    } catch (e) {
      this._backendAvailable = false;
      return { ok: false, data: null, status: 0 };
    }
  },

  /**
   * Check if the backend is reachable.
   * @returns {Promise<boolean>}
   */
  async isAvailable() {
    if (this._backendAvailable !== null) return this._backendAvailable;
    const { ok } = await this._request('GET', '/dashboard');
    return ok;
  },

  /**
   * Normalize KernelAPI agent response to Store agent format.
   * @param {Object} raw
   * @returns {Object}
   */
  _normalizeAgent(raw) {
    return {
      id: raw.id || raw.name,
      name: raw.name || 'Unknown',
      status: (raw.heartbeat && raw.heartbeat.status) || raw.status || 'offline',
      capabilities: raw.capabilities || [],
      currentTask: (raw.heartbeat && raw.heartbeat.active_tasks > 0) ? `Active tasks: ${raw.heartbeat.active_tasks}` : null,
      avatar: raw.avatar || '🤖',
      description: raw.description || '',
      tasks_completed: raw.tasks_completed || 0,
      tasks_failed: raw.tasks_failed || 0,
    };
  },

  /** Agents API */
  agents: {
    /**
     * Get all agents from Kernel API.
     * @returns {Promise<Array>}
     */
    async list() {
      const { ok, data } = await API._request('GET', '/agents');
      if (ok && data && data.agents) {
        return data.agents.map(a => API._normalizeAgent(a));
      }
      return [...Store.state.agents];
    },

    /**
     * Get agent by ID.
     * @param {number|string} id
     * @returns {Promise<Object|undefined>}
     */
    get(id) {
      return Promise.resolve(Store.findById('agents', id));
    },

    create(data) {
      const agent = { ...data, id: Date.now() };
      Store.addItem('agents', agent);
      return Promise.resolve(agent);
    },

    update(id, data) {
      Store.updateItem('agents', id, data);
      return Promise.resolve(Store.findById('agents', id));
    },

    delete(id) {
      Store.removeItem('agents', id);
      return Promise.resolve();
    }
  },

  /** Missions API (maps to Kernel API scheduled missions) */
  missions: {
    /**
     * Get all missions from Kernel API scheduler.
     * @returns {Promise<Array>}
     */
    async list() {
      const { ok, data } = await API._request('GET', '/scheduler/tasks');
      if (ok && data && data.missions) {
        return data.missions.map(m => ({
          id: m.id || m.name,
          name: m.name,
          status: m.enabled ? 'active' : 'pending',
          progress: m.last_run ? 100 : 0,
          agents: m.agent_name ? [m.agent_name] : [],
          priority: 'medium',
          startDate: m.created_at || null,
          deadline: null,
          description: m.description || '',
        }));
      }
      return [...Store.state.missions];
    },
    get(id) {
      return Promise.resolve(Store.findById('missions', id));
    },
    create(data) {
      const mission = { ...data, id: Date.now(), progress: 0, status: 'pending' };
      Store.addItem('missions', mission);
      return Promise.resolve(mission);
    },
    update(id, data) {
      Store.updateItem('missions', id, data);
      return Promise.resolve(Store.findById('missions', id));
    },
    delete(id) {
      Store.removeItem('missions', id);
      return Promise.resolve();
    }
  },

  /** Tasks API */
  tasks: {
    list() {
      return Promise.resolve([...Store.state.tasks]);
    },
    get(id) {
      return Promise.resolve(Store.findById('tasks', id));
    },
    create(data) {
      const task = { ...data, id: Date.now() };
      Store.addItem('tasks', task);
      return Promise.resolve(task);
    },
    update(id, data) {
      Store.updateItem('tasks', id, data);
      return Promise.resolve(Store.findById('tasks', id));
    },
    delete(id) {
      Store.removeItem('tasks', id);
      return Promise.resolve();
    },
    moveTo(id, column) {
      Store.updateItem('tasks', id, { column });
      return Promise.resolve(Store.findById('tasks', id));
    }
  },

  /** Memories API */
  memories: {
    list() {
      return Promise.resolve([...Store.state.memories]);
    },
    get(id) {
      return Promise.resolve(Store.findById('memories', id));
    },
    create(data) {
      const memory = { ...data, id: Date.now() };
      Store.addItem('memories', memory);
      return Promise.resolve(memory);
    },
    search(query) {
      const q = query.toLowerCase();
      const results = Store.state.memories.filter(m =>
        m.title.toLowerCase().includes(q) ||
        m.content.toLowerCase().includes(q) ||
        m.tags.some(t => t.toLowerCase().includes(q))
      );
      return Promise.resolve(results);
    }
  },

  /** Workspaces API */
  workspaces: {
    list() {
      return Promise.resolve([...Store.state.workspaces]);
    },
    get(id) {
      return Promise.resolve(Store.findById('workspaces', id));
    },
    create(data) {
      const ws = { ...data, id: Date.now(), progress: 0, tasks: 0, completedTasks: 0 };
      Store.addItem('workspaces', ws);
      return Promise.resolve(ws);
    }
  },

  /** Tools API */
  tools: {
    list() {
      return Promise.resolve([...Store.state.tools]);
    },
    get(id) {
      return Promise.resolve(Store.findById('tools', id));
    }
  },

  /**
   * Fetch aggregated dashboard data from Kernel API.
   * @returns {Promise<Object|null>}
   */
  async dashboard() {
    const { ok, data } = await API._request('GET', '/dashboard');
    return ok ? data : null;
  },

  /**
   * Fetch suggestions from Kernel API.
   * @returns {Promise<Object|null>}
   */
  async suggestions() {
    const { ok, data } = await API._request('GET', '/suggestions');
    return ok ? data : null;
  }
};
