/**
 * AIOS Mission Control - Dashboard Page
 * System overview with stats, activity feed, charts, and status.
 */
const Pages = window.Pages || {};

Pages.Dashboard = {
  render() {
    const agents = Store.state.agents;
    const missions = Store.state.missions;
    const tasks = Store.state.tasks;
    const memories = Store.state.memories;

    const onlineCount = agents.filter(a => a.status === 'online').length;
    const activeMissions = missions.filter(m => m.status === 'active').length;
    const inProgressTasks = tasks.filter(t => t.column === 'in_progress').length;

    const el = document.createElement('div');
    el.className = 'dashboard-page animate-fade-in';

    // Row 1: Stat cards
    const statsHtml = `
      <div class="dashboard-stats">
        ${this._statCard('Agents Online', onlineCount + '/' + agents.length, '🤖', 'blue', '+2 this week')}
        ${this._statCard('Active Missions', activeMissions, '🎯', 'green', missions.filter(m => m.status === 'completed').length + ' completed')}
        ${this._statCard('Tasks in Progress', inProgressTasks, '📋', 'orange', tasks.filter(t => t.column === 'done').length + ' completed')}
        ${this._statCard('Memory Entries', memories.length, '🧠', 'purple', '3 new this week')}
      </div>
    `;

    // Row 2: Activity + Quick Actions
    const mainHtml = `
      <div class="dashboard-main">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Recent Activity</span>
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

    // Row 3: Charts
    const activeMissionData = missions.filter(m => m.status === 'active');
    const barLabels = activeMissionData.map(m => m.name.length > 15 ? m.name.substring(0, 15) + '...' : m.name);
    const barData = activeMissionData.map(m => m.progress);

    const agentStatusCounts = {
      online: agents.filter(a => a.status === 'online').length,
      busy: agents.filter(a => a.status === 'busy').length,
      offline: agents.filter(a => a.status === 'offline').length
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

    // Row 4: System Status
    const statusHtml = `
      <div class="dashboard-status">
        ${this._systemStatus('CPU', 34, 'green')}
        ${this._systemStatus('Memory', 67, 'orange')}
        ${this._systemStatus('Disk', 45, 'green')}
        ${this._systemStatus('Network', 23, 'green')}
      </div>
    `;

    el.innerHTML = statsHtml + mainHtml + chartsHtml + statusHtml;

    // Render charts after DOM insert
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

    return el;
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
