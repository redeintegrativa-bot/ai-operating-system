/**
 * AIOS Mission Control - Dashboard Page
 * Real-time dashboard with live data from Kernel API.
 * Shows agents, tasks, queue, memory, CPU, activity, logs, system state, upcoming tasks.
 */
const Pages = window.Pages || {};

Pages.Dashboard = {
  _unsubs: [],

  render() {
    const el = document.createElement('div');
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1>Mission Control</h1>
          <p class="page-subtitle">Real-time system overview</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-sm btn-outline" onclick="Pages.Dashboard.refresh()">
            <span class="btn-icon">↻</span> Refresh
          </button>
          <span class="last-updated" id="lastUpdated"></span>
        </div>
      </div>
      <div class="dashboard-grid" id="dashboardGrid">
        ${this._renderSkeleton()}
      </div>
    `;
    return el;
  },

  async mount() {
    this._bindStore();
    this._renderAll();
    this._updateTimestamp();
  },

  async unmount() {
    this._unsubs.forEach(fn => fn());
    this._unsubs = [];
  },

  _bindStore() {
    this._unsubs.push(
      Store.subscribe('dashboard', () => this._renderAll()),
      Store.subscribe('agents', () => this._renderAgentPanel()),
      Store.subscribe('systemLogs', () => this._renderLogPanel()),
      Store.subscribe('loading', () => {
        const grid = document.getElementById('dashboardGrid');
        if (grid && Store.isLoading()) grid.classList.add('loading');
        else if (grid) grid.classList.remove('loading');
      })
    );
  },

  _updateTimestamp() {
    const el = document.getElementById('lastUpdated');
    if (el) el.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    setTimeout(() => this._updateTimestamp(), 10000);
  },

  _renderAll() {
    this._renderSystemStatusPanel();
    this._renderAgentPanel();
    this._renderMetricPanel();
    this._renderMemoryPanel();
    this._renderQueuePanel();
    this._renderActivityPanel();
    this._renderLogPanel();
    this._renderUpcomingPanel();
    this._renderCpuPanel();
  },

  refresh() {
    Store.stop();
    Promise.all([
      Store.fetchDashboard().catch(() => {}),
      Store.fetchAgents().catch(() => {}),
      Store.fetchSystemLogs().catch(() => {}),
    ]).then(() => {
      Store.start();
      this._updateTimestamp();
    });
  },

  _renderSkeleton() {
    const panels = [
      { span: 3, id: 'systemStatusPanel', title: 'System Status', icon: '⚡' },
      { span: 3, id: 'metricPanel', title: 'Metrics', icon: '📊' },
      { span: 3, id: 'memoryPanel', title: 'Memory', icon: '🧠' },
      { span: 3, id: 'cpuPanel', title: 'CPU', icon: '⚙️' },
      { span: 4, id: 'agentPanel', title: 'Agents', icon: '🤖' },
      { span: 4, id: 'queuePanel', title: 'Task Queue', icon: '📋' },
      { span: 4, id: 'activityPanel', title: 'Recent Activity', icon: '🔄' },
      { span: 6, id: 'logPanel', title: 'System Logs', icon: '📜' },
      { span: 6, id: 'upcomingPanel', title: 'Upcoming Tasks', icon: '📅' },
    ];
    return panels.map(p => `
      <div class="panel col-span-${p.span}" id="${p.id}">
        <div class="panel-header">
          <span class="panel-title"><span class="panel-icon">${p.icon}</span>${p.title}</span>
        </div>
        <div class="panel-body"><div class="empty-state"><div class="empty-icon">⏳</div><div class="empty-text">Loading...</div></div></div>
      </div>
    `).join('');
  },

  /* System Status Panel */
  _renderSystemStatusPanel() {
    const el = document.getElementById('systemStatusPanel');
    if (!el) return;
    const d = Store.get('dashboard');
    if (!d) {
      el.querySelector('.panel-body').innerHTML = `<div class="empty-state"><div class="empty-icon">📡</div><div class="empty-text">Waiting for data...</div></div>`;
      return;
    }
    const statusColors = { operational: '#22c55e', degraded: '#eab308', down: '#ef4444' };
    const color = statusColors[d.status] || '#64748b';
    el.querySelector('.panel-body').innerHTML = `
      <div style="display:flex;flex-direction:column;gap:10px">
        <div style="display:flex;align-items:center;gap:10px">
          <div style="width:12px;height:12px;border-radius:50%;background:${color};box-shadow:0 0 8px ${color}40"></div>
          <span style="font-size:16px;font-weight:600;text-transform:capitalize">${d.status || 'unknown'}</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px">
          <div><span style="color:var(--color-text-muted)">Uptime</span><br><span style="font-weight:600">${d.uptime || '—'}</span></div>
          <div><span style="color:var(--color-text-muted)">Version</span><br><span style="font-weight:600">${d.version || '—'}</span></div>
          <div><span style="color:var(--color-text-muted)">Threads</span><br><span style="font-weight:600">${d.threads ? `${d.threads.active}/${d.threads.idle}` : '—'}</span></div>
          <div><span style="color:var(--color-text-muted)">Started</span><br><span style="font-weight:600;font-size:11px">${d.startedAt ? new Date(d.startedAt).toLocaleString() : '—'}</span></div>
        </div>
      </div>
    `;
  },

  /* Metric Panel - Task Queue Summary */
  _renderMetricPanel() {
    const el = document.getElementById('metricPanel');
    if (!el) return;
    const d = Store.get('dashboard');
    if (!d || !d.taskQueue) {
      el.querySelector('.panel-body').innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><div class="empty-text">—</div></div>`;
      return;
    }
    const q = d.taskQueue;
    el.querySelector('.panel-body').innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">
        <div class="metric-tile">
          <div class="metric-value">${q.pending || 0}</div>
          <div class="metric-label">Pending</div>
        </div>
        <div class="metric-tile">
          <div class="metric-value">${q.running || 0}</div>
          <div class="metric-label">Running</div>
        </div>
        <div class="metric-tile">
          <div class="metric-value">${q.completed || 0}</div>
          <div class="metric-label">Completed</div>
        </div>
      </div>
    `;
  },

  /* Memory Panel */
  _renderMemoryPanel() {
    const el = document.getElementById('memoryPanel');
    if (!el) return;
    const d = Store.get('dashboard');
    if (!d || !d.memory) {
      el.querySelector('.panel-body').innerHTML = `<div class="empty-state"><div class="empty-icon">🧠</div><div class="empty-text">—</div></div>`;
      return;
    }
    const m = d.memory;
    const pct = m.percent || 0;
    const barClass = pct > 80 ? 'warning' : pct === 100 ? 'completed' : '';
    el.querySelector('.panel-body').innerHTML = `
      <div style="display:flex;flex-direction:column;gap:8px">
        <div style="display:flex;justify-content:space-between;font-size:13px">
          <span style="color:var(--color-text-muted)">RAM Usage</span>
          <span style="font-weight:600">${m.used || 0}GB / ${m.total || 0}GB</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill ${barClass}" style="width:${pct}%"></div>
        </div>
        <div style="text-align:right;font-size:11px;color:var(--color-text-muted)">${pct}% used</div>
      </div>
    `;
  },

  /* CPU Panel */
  _renderCpuPanel() {
    const el = document.getElementById('cpuPanel');
    if (!el) return;
    const d = Store.get('dashboard');
    if (!d || d.cpu == null) {
      el.querySelector('.panel-body').innerHTML = `<div class="empty-state"><div class="empty-icon">⚙️</div><div class="empty-text">—</div></div>`;
      return;
    }
    const cpu = d.cpu;
    const pct = cpu.usage || 0;
    const barClass = pct > 80 ? 'warning' : pct === 100 ? 'completed' : '';
    el.querySelector('.panel-body').innerHTML = `
      <div style="display:flex;flex-direction:column;gap:8px">
        <div style="display:flex;justify-content:space-between;font-size:13px">
          <span style="color:var(--color-text-muted)">CPU Load</span>
          <span style="font-weight:600">${pct}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill ${barClass}" style="width:${pct}%"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--color-text-muted)">
          <span>${cpu.cores || '—'} cores</span>
        </div>
      </div>
    `;
  },

  /* Agent Panel */
  _renderAgentPanel() {
    const el = document.getElementById('agentPanel');
    if (!el) return;
    const agents = Store.get('agents');
    if (!agents || agents.length === 0) {
      el.querySelector('.panel-body').innerHTML = `<div class="empty-state"><div class="empty-icon">🤖</div><div class="empty-text">No agents available</div></div>`;
      return;
    }
    const online = agents.filter(a => a.status === 'online').length;
    const busy = agents.filter(a => a.status === 'busy').length;
    const offline = agents.filter(a => a.status === 'offline').length;
    el.querySelector('.panel-body').innerHTML = `
      <div style="display:flex;gap:12px;margin-bottom:10px;flex-wrap:wrap">
        <span class="status-badge online">${online} Online</span>
        <span class="status-badge busy">${busy} Busy</span>
        <span class="status-badge offline">${offline} Offline</span>
      </div>
      <div class="agents-mini-grid">
        ${agents.map(a => `
            <div class="agent-mini-card" onclick="Router.navigate('/agents')">
            <div class="agent-mini-avatar">${a.avatar || '🤖'}</div>
            <div class="agent-mini-info">
              <div class="agent-mini-name">${this._escape(a.name)}</div>
              <div class="agent-mini-status status-badge ${a.status}">${a.status}</div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  },

  /* Task Queue Panel */
  _renderQueuePanel() {
    const el = document.getElementById('queuePanel');
    if (!el) return;
    const d = Store.get('dashboard');
    const q = d && d.taskQueue ? d.taskQueue : { pending: 0, running: 0, completed: 0 };

    API.tasks.queue().then(queueData => {
      if (!queueData) return;
      const pending = queueData.pending || [];
      const running = queueData.running || [];
      const total = pending.length + running.length;

      if (!el) return;
      const body = el.querySelector('.panel-body');
      if (!body) return;

      if (total === 0) {
        body.innerHTML = `<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-text">Queue is empty</div></div>`;
        return;
      }

      let html = `<div class="queue-list">`;
      running.forEach(t => {
        html += `
          <div class="queue-item">
            <div class="queue-item-icon running">▶</div>
            <div class="queue-item-title">${this._escape(t.title)}</div>
            <span class="status-badge in_progress" style="font-size:9px">running</span>
            <div class="queue-item-meta">${t.agent || ''}</div>
          </div>
        `;
      });
      pending.forEach(t => {
        html += `
          <div class="queue-item">
            <div class="queue-item-icon pending">⏳</div>
            <div class="queue-item-title">${this._escape(t.title)}</div>
            <span class="priority-badge ${t.priority || 'medium'}">${t.priority || 'med'}</span>
            <div class="queue-item-meta">${t.agent || ''}</div>
          </div>
        `;
      });
      html += `</div>`;
      body.innerHTML = html;
    }).catch(() => {
      if (!el) return;
      el.querySelector('.panel-body').innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">
          <div class="metric-tile"><div class="metric-value">${q.pending}</div><div class="metric-label">Pending</div></div>
          <div class="metric-tile"><div class="metric-value">${q.running}</div><div class="metric-label">Running</div></div>
          <div class="metric-tile"><div class="metric-value">${q.completed}</div><div class="metric-label">Completed</div></div>
        </div>
      `;
    });
  },

  /* Recent Activity Panel */
  _renderActivityPanel() {
    const el = document.getElementById('activityPanel');
    if (!el) return;
    const d = Store.get('dashboard');
    const actions = d && d.recentActions ? d.recentActions : [];
    if (actions.length === 0) {
      el.querySelector('.panel-body').innerHTML = `<div class="empty-state"><div class="empty-icon">🔄</div><div class="empty-text">No recent activity</div></div>`;
      return;
    }
    el.querySelector('.panel-body').innerHTML = `
      <div class="activity-list">
        ${actions.slice(0, 8).map(a => {
          const agent = Store.get('agents').find(ag => ag.id === a.agent || ag.name === a.agent);
          const avatar = agent ? agent.avatar : null;
          return `
            <div class="activity-item">
              <div class="activity-icon">${avatar || '🤖'}</div>
              <div class="activity-content">
                <div class="activity-text">${this._escape(a.action || a.message || '')}</div>
                <div class="activity-time">${a.time || a.timestamp || ''}</div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  },

  /* System Logs Panel */
  _renderLogPanel() {
    const el = document.getElementById('logPanel');
    if (!el) return;
    const logs = Store.get('systemLogs');
    if (!logs || logs.length === 0) {
      el.querySelector('.panel-body').innerHTML = `<div class="empty-state"><div class="empty-icon">📜</div><div class="empty-text">No logs available</div></div>`;
      return;
    }
    el.querySelector('.panel-body').innerHTML = `
      <div class="log-viewer">
        ${logs.slice(0, 30).map(l => {
          const t = l.timestamp ? new Date(l.timestamp).toLocaleTimeString() : '';
          const level = (l.level || 'info').toLowerCase();
          return `<div class="log-entry">
            <span class="log-time">${t}</span>
            <span class="log-level ${level}">${level}</span>
            <span class="log-message">${this._escape(l.message || '')}</span>
            <span class="log-module">${l.module || ''}</span>
          </div>`;
        }).join('')}
      </div>
    `;
  },

  /* Upcoming Tasks Panel */
  _renderUpcomingPanel() {
    const el = document.getElementById('upcomingPanel');
    if (!el) return;
    const d = Store.get('dashboard');
    const upcoming = d && d.upcomingTasks ? d.upcomingTasks : [];
    if (upcoming.length === 0) {
      el.querySelector('.panel-body').innerHTML = `<div class="empty-state"><div class="empty-icon">📅</div><div class="empty-text">No upcoming tasks</div></div>`;
      return;
    }
    el.querySelector('.panel-body').innerHTML = `
      <div class="queue-list">
        ${upcoming.map(t => `
          <div class="queue-item">
            <div class="queue-item-icon pending">📌</div>
            <div class="queue-item-title">${this._escape(t.title)}</div>
            <span class="priority-badge ${t.priority || 'medium'}">${t.priority || 'med'}</span>
            <div class="queue-item-meta">${t.scheduled || ''}</div>
          </div>
        `).join('')}
      </div>
    `;
  },

  _escape(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};
