/**
 * AIOS Mission Control - Analytics Page
 * Performance analytics with charts and metrics (placeholder).
 */
const Pages = window.Pages || {};

Pages.Analytics = {
  _dateRange: 'month',

  render() {
    const el = document.createElement('div');
    el.className = 'analytics-page animate-fade-in';

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Analytics</h1>
          <p class="page-subtitle">Performance metrics and insights</p>
        </div>
        <div class="page-actions">
          <div class="date-range" id="date-range">
            <button class="date-range-btn" data-range="today">Today</button>
            <button class="date-range-btn" data-range="week">This Week</button>
            <button class="date-range-btn active" data-range="month">This Month</button>
            <button class="date-range-btn" data-range="quarter">This Quarter</button>
          </div>
        </div>
      </div>
      <div class="analytics-stats">
        ${this._statCard('Task Completion Rate', '87%', '+5%', 'up')}
        ${this._statCard('Avg Mission Duration', '4.2 days', '-0.3', 'down')}
        ${this._statCard('Agent Utilization', '78%', '+12%', 'up')}
        ${this._statCard('Memory Growth', '156 entries', '+23', 'up')}
      </div>
      <div class="analytics-charts">
        <div class="card">
          <div class="card-header"><span class="card-title">Task Completion Over Time</span></div>
          <div id="an-line-chart"></div>
        </div>
        <div class="card">
          <div class="card-header"><span class="card-title">Agent Performance</span></div>
          <div id="an-agent-chart"></div>
        </div>
      </div>
      <div class="analytics-charts">
        <div class="card">
          <div class="card-header"><span class="card-title">Mission Success Rate</span></div>
          <div id="an-donut-chart"></div>
        </div>
        <div class="card">
          <div class="card-header"><span class="card-title">System Resource Usage</span></div>
          <div id="an-resource-chart"></div>
        </div>
      </div>
      <div class="card" style="margin-top: 24px;">
        <div class="card-header"><span class="card-title">Activity Heatmap (Last 4 Weeks)</span></div>
        <div id="an-heatmap" style="display: flex; flex-direction: column; gap: 4px;"></div>
      </div>
    `;

    requestAnimationFrame(() => {
      this._renderCharts(el);
      this._renderHeatmap(el);
      this._bindEvents(el);
    });

    return el;
  },

  _statCard(title, value, change, direction) {
    return `
      <div class="card" style="text-align: center; padding: 20px;">
        <div class="card-title" style="margin-bottom: 8px;">${title}</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">${value}</div>
        <div class="card-trend ${direction}">${direction === 'up' ? '↑' : '↓'} ${change}</div>
      </div>
    `;
  },

  _renderCharts(el) {
    // Line chart: task completion over months
    const lineChart = el.querySelector('#an-line-chart');
    if (lineChart) {
      lineChart.appendChild(Components.Charts.createLineChart({
        data: [65, 72, 68, 80, 75, 85, 78, 90, 87, 92, 88, 95],
        labels: ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
        color: 'var(--accent-blue)',
        height: 220
      }));
    }

    // Agent performance bar chart
    const agentChart = el.querySelector('#an-agent-chart');
    if (agentChart) {
      agentChart.appendChild(Components.Charts.createBarChart({
        data: [95, 88, 92, 85, 78, 70, 90, 82],
        labels: Store.state.agents.map(a => a.name),
        colors: ['var(--accent-blue)', 'var(--accent-purple)', 'var(--accent-green)', 'var(--accent-orange)', 'var(--accent-cyan)', 'var(--accent-pink)', 'var(--accent-yellow)', 'var(--accent-red)']
      }));
    }

    // Mission success donut
    const donutChart = el.querySelector('#an-donut-chart');
    if (donutChart) {
      donutChart.appendChild(Components.Charts.createDonutChart({
        data: [4, 1, 1],
        labels: ['Completed', 'Active', 'Failed'],
        colors: ['var(--accent-green)', 'var(--accent-blue)', 'var(--accent-red)'],
        size: 150
      }));
    }

    // Resource usage
    const resourceChart = el.querySelector('#an-resource-chart');
    if (resourceChart) {
      resourceChart.appendChild(Components.Charts.createBarChart({
        data: [34, 67, 45, 23],
        labels: ['CPU', 'Memory', 'Disk', 'Network'],
        colors: ['var(--accent-green)', 'var(--accent-orange)', 'var(--accent-blue)', 'var(--accent-purple)']
      }));
    }
  },

  _renderHeatmap(el) {
    const container = el.querySelector('#an-heatmap');
    if (!container) return;

    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const weeks = 4;

    // Header
    container.innerHTML = `
      <div style="display: grid; grid-template-columns: 40px repeat(7, 1fr); gap: 4px; margin-bottom: 4px;">
        <div></div>
        ${days.map(d => `<div style="font-size: 0.65rem; color: var(--text-muted); text-align: center;">${d}</div>`).join('')}
      </div>
    `;

    for (let w = 0; w < weeks; w++) {
      let row = `<div style="display: grid; grid-template-columns: 40px repeat(7, 1fr); gap: 4px;">`;
      row += `<div style="font-size: 0.65rem; color: var(--text-muted); display: flex; align-items: center;">W${w + 1}</div>`;
      for (let d = 0; d < 7; d++) {
        const level = Math.floor(Math.random() * 5);
        row += `<div class="heatmap-cell ${level > 0 ? 'level-' + level : ''}" style="aspect-ratio: 1; border-radius: 3px;"></div>`;
      }
      row += '</div>';
      container.innerHTML += row;
    }
  },

  _bindEvents(el) {
    el.querySelectorAll('.date-range-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        el.querySelectorAll('.date-range-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this._dateRange = btn.dataset.range;
        App.showToast(`Date range: ${btn.textContent}`, 'info');
      });
    });
  }
};
