/**
 * AIOS Dashboard - Dashboard Page
 * Real-time system dashboard with live panels.
 */
const Pages = window.Pages || {};
Pages.Dashboard = {
  _el: null, _unsubs: [],

  render() {
    const el = document.createElement('div');
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Dashboard</h1>
          <p class="page-subtitle">Visão geral em tempo real do AIOS</p>
        </div>
        <div class="header-actions" id="dash-header-actions">
          <span class="last-updated" id="dash-last-update">Aguardando...</span>
          <button class="btn btn-primary btn-sm" onclick="Pages.Dashboard._refresh()">
            <span class="material-icons">refresh</span> Atualizar
          </button>
        </div>
      </div>
      <div class="dashboard-grid" id="dashboard-grid">
        ${this._renderPanel('cpu-panel', '🧠', 'CPU / Sistema', 'dash-cpu', `
          <div class="metric-grid">
            <div class="metric-item"><span class="metric-label">CPU</span><span class="metric-value" id="cpu-value">0</span><span class="metric-unit">%</span></div>
            <div class="metric-item"><span class="metric-label">Memória</span><span class="metric-value" id="mem-value">0</span><span class="metric-unit">MB</span></div>
            <div class="metric-chart"><canvas id="cpu-chart" width="200" height="100"></canvas></div>
          </div>
        `)}
        ${this._renderPanel('agents-panel', '🤖', 'Agentes', 'dash-agents', '<div id="dash-agents-body" class="dash-agent-list"><div class="loading-spinner"></div><p>Carregando agentes...</p></div>')}
        ${this._renderPanel('tasks-panel', '📋', 'Task Queue', 'dash-tasks', '<div id="dash-tasks-body" class="dash-task-list"><div class="loading-spinner"></div></div>')}
        ${this._renderPanel('recent-panel', '⚡', 'Atividade Recente', 'dash-recent', '<div id="dash-recent-body" class="dash-activity-list"><div class="empty-state"><span class="empty-icon material-icons">inbox</span><p class="empty-text">Nenhuma atividade</p></div></div>')}
        ${this._renderPanel('logs-panel', '📜', 'Logs', 'dash-logs', '<div id="dash-logs-body" class="dash-log-list"><div class="empty-state"><span class="empty-icon material-icons">article</span><p class="empty-text">Nenhum log</p></div></div>', true)}
        ${this._renderPanel('upcoming-panel', '📅', 'Próximas Tarefas', 'dash-upcoming', '<div id="dash-upcoming-body"><div class="empty-state"><span class="empty-icon material-icons">event</span><p class="empty-text">Nenhuma tarefa agendada</p></div></div>')}
      </div>
    `;
    this._el = el;
    return el;
  },

  mount() {
    this._unsubs.push(Store.subscribe('dashboard', data => this._updateDashboard(data)));
    this._unsubs.push(Store.subscribe('agents', data => this._updateAgents(data)));
    this._unsubs.push(Store.subscribe('tasks', data => this._updateTasks(data)));
    this._refresh();
  },
  unmount() { this._unsubs.forEach(u => u()); this._unsubs = []; },

  _renderPanel(id, icon, title, storeKey, body, large = false) {
    return `<div class="card dash-panel ${large?'dash-panel-large':''}" id="${id}"><div class="card-header"><span class="card-icon">${icon}</span><h3 class="card-title">${title}</h3></div><div class="card-body">${body}</div></div>`;
  },

  async _refresh() {
    const lu = document.getElementById('dash-last-update');
    if (lu) lu.textContent = new Date().toLocaleTimeString()+' — atualizando...';
    await Promise.all([
      Store.fetchDashboard().catch(()=>{}),
      Store.fetchAgents().catch(()=>{}),
      Store.fetchTasks().catch(()=>{}),
      Store.fetchSystemLogs().catch(()=>{}),
    ]);
    if (lu) lu.textContent = new Date().toLocaleTimeString();
  },

  _updateDashboard(data) {
    if (!data) return;
    const cpuEl = document.getElementById('cpu-value');
    const memEl = document.getElementById('mem-value');
    if (cpuEl) cpuEl.textContent = data.cpu_usage ?? data.cpu ?? 0;
    if (memEl) memEl.textContent = data.memory_usage ?? data.memory ?? 0;
    const agentCount = data.agents_online ?? data.agents ?? 0;
    const taskCount = data.pending_tasks ?? data.tasks ?? 0;
    this._setMetric('dash-metrics', `
      <div class="stat-card stat-cpu"><span class="stat-value">${data.cpu??0}%</span><span class="stat-label">CPU</span></div>
      <div class="stat-card stat-mem"><span class="stat-value">${data.memory??0}MB</span><span class="stat-label">RAM</span></div>
      <div class="stat-card stat-agents"><span class="stat-value">${agentCount}</span><span class="stat-label">Agentes</span></div>
      <div class="stat-card stat-tasks"><span class="stat-value">${taskCount}</span><span class="stat-label">Tarefas</span></div>
    `);
    this._updateMiniChart(data);
  },

  _setMetric(id, html) {
    let el = document.getElementById(id);
    if (!el) {
      const panel = document.getElementById('cpu-panel')?.querySelector('.card-header');
      if (!panel) return;
      el = document.createElement('div'); el.id = id; el.className = 'metric-strip';
      panel.after(el);
    }
    el.innerHTML = html;
  },

  _updateMiniChart(data) {
    const chartEl = document.getElementById('cpu-chart');
    if (!chartEl) return;
    const ctx = chartEl.getContext('2d');
    const vals = data.cpu_history || [0,5,10,8,12,6,15,14,18,22,20,25,30,28,24,18,15,10,12,8,6,4,10,12,8,5,3];
    const w = chartEl.width, h = chartEl.height;
    ctx.clearRect(0,0,w,h);
    ctx.strokeStyle = '#5b8def';
    ctx.lineWidth = 2;
    ctx.beginPath();
    const step = w / (vals?.length||30);
    vals.forEach((v,i) => { const x=i*step,y=h-(v/100)*h; i===0?ctx.moveTo(x,y):ctx.lineTo(x,y); });
    ctx.stroke();
    const grad = ctx.createLinearGradient(0,h,0,0);
    grad.addColorStop(0,'rgba(91,141,239,0)');
    grad.addColorStop(1,'rgba(91,141,239,0.15)');
    ctx.lineTo(w,h); ctx.lineTo(0,h); ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();
    const latest = vals[vals.length-1]||0;
    ctx.beginPath(); ctx.arc(w-step,(h-(latest/100)*h),3,0,Math.PI*2); ctx.fillStyle='#5b8def'; ctx.fill();
  },

  _updateAgents(agents) {
    const container = document.getElementById('dash-agents-body');
    if (!container) return;
    if (!agents || agents.length === 0) { container.innerHTML = '<div class="empty-state"><span class="empty-icon material-icons">smart_toy</span><p class="empty-text">Nenhum agente disponível</p></div>'; return; }
    container.innerHTML = agents.map(a => `
      <div class="dash-agent-item">
        <span class="dash-avatar">${a.avatar||'🤖'}</span>
        <div class="dash-agent-info">
          <span class="dash-agent-name">${a.name}</span>
          <div class="dash-agent-skills">${(a.capabilities||[]).slice(0,2).join(', ')}</div>
        </div>
        <span class="status-badge status-${a.status||'offline'}">${a.status||'offline'}</span>
      </div>
    `).join('');
  },

  _updateTasks(tasks) {
    const container = document.getElementById('dash-tasks-body');
    if (!container) return;
    if (!tasks || tasks.length === 0) { container.innerHTML = '<div class="empty-state"><span class="empty-icon material-icons">check_circle</span><p class="empty-text">Nenhuma tarefa pendente</p></div>'; return; }
    const active = tasks.filter(t => t.status !== 'done').slice(0,8);
    container.innerHTML = active.map(t => `
      <div class="dash-task-item">
        <span class="task-priority task-priority-${t.priority||'medium'}"></span>
        <div class="dash-task-info">
          <span class="dash-task-title">${t.title}</span>
          <span class="dash-task-assignee">${t.assignee||'sem responsável'}</span>
        </div>
        <span class="task-status task-status-${t.status||'pending'}">${t.status||'pending'}</span>
      </div>
    `).join('');
  },
};
