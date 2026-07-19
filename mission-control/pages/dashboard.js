/**
 * AIOS Mission Control - Dashboard Page
 * System overview with stats, activity feed, charts, and status.
 * Fetches real data from Kernel API via the Store.
 */
const Pages = window.Pages || {};

Pages.Dashboard = {
  /** @type {Function|null} Store unsubscribe handle */
  _unsubscribe: null,

  render() {
    const el = document.createElement('div');
    el.className = 'dashboard-page animate-fade-in';

    // Show loading state immediately
    el.innerHTML = this._renderLoading();

    // Subscribe to data changes and re-render
    this._unsubscribe = Store.subscribe('*', () => {
      if (this._renderedEl && this._renderedEl.parentNode) {
        this._updateDashboard(this._renderedEl);
      }
    });

    this._renderedEl = el;

    // Populate with current data (may be mock or already fetched)
    this._updateDashboard(el);

    return el;
  },

  destroy() {
    if (this._unsubscribe) {
      this._unsubscribe();
      this._unsubscribe = null;
    }
  },

  _updateDashboard(el) {
    const agents = Store.state.agents;
    const missions = Store.state.missions;
    const tasks = Store.state.tasks;
    const memories = Store.state.memories;
    const dashboard = Store.state.dashboard;
    const isLoading = Store.isLoading();
    const error = Store.getFirstError();

    // Use real API data when available, otherwise derive from collections
    const onlineCount = dashboard
      ? (dashboard.agents ? dashboard.agents.online : 0)
      : agents.filter(a => a.status === 'online').length;
    const totalAgents = dashboard
      ? (dashboard.agents ? dashboard.agents.total : agents.length)
      : agents.length;
    const activeMissions = missions.filter(m => m.status === 'active').length;
    const completedMissions = missions.filter(m => m.status === 'completed').length;
    const inProgressTasks = dashboard
      ? (dashboard.tasks ? dashboard.tasks.pending : 0)
      : tasks.filter(t => t.column === 'in_progress').length;
    const doneTasks = dashboard
      ? (dashboard.tasks ? dashboard.tasks.completed : 0)
      : tasks.filter(t => t.column === 'done').length;

    const statsHtml = `
      <div class="dashboard-stats">
        ${this._statCard('Agents Online', onlineCount + '/' + totalAgents, '🤖', 'blue', error ? 'API unavailable' : '+2 this week')}
        ${this._statCard('Active Missions', activeMissions, '🎯', 'green', completedMissions + ' completed')}
        ${this._statCard('Tasks in Progress', inProgressTasks, '📋', 'orange', doneTasks + ' completed')}
        ${this._statCard('Memory Entries', memories.length, '🧠', 'purple', '3 new this week')}
      </div>
    `;

    const mainHtml = `
      <div class="dashboard-main">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Recent Activity</span>
            ${isLoading ? '<span class="badge badge-active">Syncing...</span>' : ''}
          </div>
          <div class="activity-feed">
            ${this._activityFeed()}
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">Quick Actions</span>
          </div>
          <div class="quick-actions">
            <button class="quick-action-btn" onclick="Router.navigate('/missions')"><span class="quick-action-icon">🎯</span> New Mission</button>
            <button class="quick-action-btn" onclick="Router.navigate('/kanban')"><span class="quick-action-icon">📋</span> New Task</button>
            <button class="quick-action-btn" onclick="Router.navigate('/tools')"><span class="quick-action-icon">🔍</span> Run Scanner</button>
            <button class="quick-action-btn" onclick="Router.navigate('/tools')"><span class="quick-action-icon">🚀</span> Deploy</button>
          </div>
        </div>
      </div>
    `;

    const activeMissionData = missions.filter(m => m.status === 'active');
    const barLabels = activeMissionData.map(m => m.name.length > 15 ? m.name.substring(0, 15) + '...' : m.name);
    const barData = activeMissionData.map(m => m.progress);

    const agentStatusCounts = {
      online: dashboard && dashboard.agents ? dashboard.agents.online : agents.filter(a => a.status === 'online').length,
      busy: dashboard && dashboard.agents ? dashboard.agents.busy : agents.filter(a => a.status === 'busy').length,
      offline: (dashboard && dashboard.agents ? dashboard.agents.total : agents.length)
        - (dashboard && dashboard.agents ? dashboard.agents.online + dashboard.agents.busy : agents.filter(a => a.status === 'online').length + agents.filter(a => a.status === 'busy').length)
    };

    const chartsHtml = `
      <div class="dashboard-charts">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Mission Progress</span>
          </div>
          <div id="mission-progress-chart"></div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">Agent Status</span>
          </div>
          <div id="agent-status-chart"></div>
        </div>
      </div>
    `;

    const statusHtml = `
      <div class="dashboard-status">
        ${this._systemStatus('CPU', 34, 'green')}
        ${this._systemStatus('Memory', 67, 'orange')}
        ${this._systemStatus('Disk', 45, 'green')}
        ${this._systemStatus('Network', 23, 'green')}
      </div>
    `;

    const errorHtml = error ? `
      <div class="dashboard-error-bar">
        <span class="dashboard-error-icon">⚠️</span>
        <span class="dashboard-error-text">API Error: ${error}</span>
        <button class="btn btn-sm btn-secondary" onclick="Store.fetchAll()">Retry</button>
      </div>
    ` : '';

    el.innerHTML = errorHtml + statsHtml + mainHtml + chartsHtml + statusHtml;

    requestAnimationFrame(() => {
      const barContainer = el.querySelector('#mission-progress-chart');
      if (barContainer && barData.length > 0) {
        barContainer.appendChild(Components.Charts.createBarChart({
          data: barData,
          labels: barLabels,
          colors: ['var(--gradient-blue)']
        }));
      } else if (barContainer) {
        barContainer.innerHTML = '<div class="empty-state"><div class="empty-state-text">No active missions</div></div>';
      }

      const donutContainer = el.querySelector('#agent-status-chart');
      if (donutContainer) {
        donutContainer.appendChild(Components.Charts.createDonutChart({
          data: [agentStatusCounts.online, agentStatusCounts.busy, agentStatusCounts.offline],
          labels: ['Online', 'Busy', 'Offline'],
          colors: ['var(--accent-green)', 'var(--accent-orange)', 'var(--text-muted)'],
          size: 150
        }));
      }
    });
  },

  _renderLoading() {
    return `
      <div class="dashboard-loading">
        <div class="loading-spinner"></div>
        <div class="loading-text">Connecting to Kernel API...</div>
      </div>
    `;
  },

  _statCard(title, value, icon, color, subtitle) {
    return `
      <div class="card dashboard-stat-card">
        <div class="card-icon card-stat-icon ${color === 'green' ? 'green' : color === 'orange' ? 'orange' : color === 'purple' ? 'purple' : ''}">${icon}</div>
        <div class="card-title">${title}</div>
        <div class="card-value">${value}</div>
        <div class="card-subtitle">${subtitle}</div>
      </div>
    `;
  },

  _activityFeed() {
    const items = [
      { icon: '🚀', color: 'var(--accent-green)', text: '<strong>DevOps</strong> deployed CI/CD Pipeline v2 to staging', time: '5 min ago' },
      { icon: '🛡️', color: 'var(--accent-blue)', text: '<strong>Seguranca</strong> completed security scan — 0 vulnerabilities', time: '12 min ago' },
      { icon: '⚙️', color: 'var(--accent-orange)', text: '<strong>Arquiteto</strong> updated microservices design document', time: '28 min ago' },
      { icon: '🧪', color: 'var(--accent-purple)', text: '<strong>Tester</strong> ran 847 tests — all passing', time: '1 hour ago' },
      { icon: '📋', color: 'var(--accent-cyan)', text: '<strong>Engenheiro</strong> moved task "JWT refresh tokens" to review', time: '2 hours ago' },
      { icon: '📊', color: 'var(--accent-pink)', text: '<strong>Analista</strong> identified performance bottleneck in DB queries', time: '3 hours ago' },
      { icon: '🎯', color: 'var(--accent-blue)', text: '<strong>Orquestrador</strong> assigned 3 new tasks to Engenheiro', time: '4 hours ago' },
      { icon: '📝', color: 'var(--text-muted)', text: '<strong>Documentador</strong> updated API documentation', time: '5 hours ago' }
    ];

    return items.map(item => `
      <div class="activity-item">
        <div class="activity-icon" style="color: ${item.color};">${item.icon}</div>
        <div class="activity-content">
          <div class="activity-text">${item.text}</div>
          <div class="activity-time">${item.time}</div>
        </div>
      </div>
    `).join('');
  },

  _systemStatus(label, percent, color) {
    const barColor = percent > 80 ? 'orange' : color;
    return `
      <div class="card system-status-card">
        <div class="system-status-item">
          <span class="system-status-label">${label}</span>
          <div class="system-status-bar">
            <div class="progress-bar"><div class="progress-bar-fill ${barColor}" style="width: ${percent}%;"></div></div>
          </div>
          <span class="system-status-value">${percent}%</span>
        </div>
      </div>
    `;
  }
};
