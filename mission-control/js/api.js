/**
 * AIOS Mission Control - API Layer
 * Prepared for future backend integration.
 * Currently uses Store as data source (mock mode).
 */
const API = {
  /** @type {string} Backend base URL */
  baseURL: '/api',

  /**
   * Generic HTTP request helper (for future backend).
   * @param {string} method
   * @param {string} path
   * @param {*} [body]
   * @returns {Promise<*>}
   */
  async _request(method, path, body) {
    // Placeholder: will use fetch() when backend is ready
    console.log(`[API] ${method} ${path}`, body || '');
    return { ok: true, data: null };
  },

  /** Agents API */
  agents: {
    /**
     * Get all agents.
     * @returns {Promise<Array>}
     */
    list() {
      return Promise.resolve([...Store.state.agents]);
    },

    /**
     * Get agent by ID.
     * @param {number} id
     * @returns {Promise<Object|undefined>}
     */
    get(id) {
      return Promise.resolve(Store.findById('agents', id));
    },

    /**
     * Create a new agent.
     * @param {Object} data
     * @returns {Promise<Object>}
     */
    create(data) {
      const agent = { ...data, id: Date.now() };
      Store.addItem('agents', agent);
      return Promise.resolve(agent);
    },

    /**
     * Update an agent.
     * @param {number} id
     * @param {Object} data
     * @returns {Promise<Object>}
     */
    update(id, data) {
      Store.updateItem('agents', id, data);
      return Promise.resolve(Store.findById('agents', id));
    },

    /**
     * Delete an agent.
     * @param {number} id
     * @returns {Promise<void>}
     */
    delete(id) {
      Store.removeItem('agents', id);
      return Promise.resolve();
    }
  },

  /** Missions API */
  missions: {
    list() {
      return Promise.resolve([...Store.state.missions]);
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
    /**
     * Move task to a different column.
     * @param {number} id
     * @param {string} column
     */
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
  }
};
