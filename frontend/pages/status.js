/**
 * AIOS Dashboard - System Status Page
 */
const Pages = window.Pages || {};
Pages.Status = {
  _el: null, _unsubs: [],

  render() {
    const el = document.createElement('div');
    el.className = 'status-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Status do Sistema</h1>
          <p class="page-subtitle">Monitoramento completo do AIOS</p>
        </div>
        <div class="header-actions">
          <span class="last-updated" id="status-last-update">Aguardando...</span>
          <button class="btn btn-primary btn-sm" onclick="Pages.Status._refresh()"><span class="material-icons">refresh</span> Atualizar</button>
        </div>
      </div>
      <div class="status-grid" id="status-grid">
        ${this._panel('health-panel','❤️','Health Checks','status-health','<div class="loading-spinner"></div>')}
        ${this._panel('services-panel','⚙️','Serviços','status-services','<div class="loading-spinner"></div>')}
        ${this._panel('metrics-panel','📊','Métricas','status-metrics','<div class="loading-spinner"></div>')}
        ${this._panel('uptime-panel','⏱️','Uptime','status-uptime','<div class="loading-spinner"></div>')}
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    this._unsubs.push(Store.subscribe('dashboard', data => this._update(data)));
    this._refresh();
  },
  unmount() { this._unsubs.forEach(u => u()); },

  _panel(id, icon, title, storeKey, body) {
    return `<div class="card status-panel" id="${id}"><div class="card-header"><span class="card-icon">${icon}</span><h3 class="card-title">${title}</h3></div><div class="card-body">${body}</div></div>`;
  },

  async _refresh() {
    const lu = document.getElementById('status-last-update');
    if (lu) lu.textContent = 'Atualizando...';
    await Store.fetchDashboard().catch(()=>{});
    if (lu) lu.textContent = new Date().toLocaleTimeString();
  },

  _update(data) {
    if (!data) return;
    this._updateHealth(data);
    this._updateServices(data);
    this._updateMetrics(data);
    this._updateUptime(data);
  },

  _updateHealth(data) {
    const el = document.getElementById('status-health');
    if (!el) return;
    const health = data.health || data.health_checks || { status:'healthy', checks:[
      {name:'API Server',status:'healthy'},
      {name:'Kernel',status:'healthy'},
      {name:'WebSocket',status:'healthy'},
      {name:'Database',status:'healthy'}
    ]};
    const isOk = health.status === 'healthy' || health.status === 'ok';
    el.innerHTML = `
      <div class="health-status ${isOk?'health-ok':'health-error'}">
        <span class="health-icon">${isOk?'✅':'❌'}</span>
        <div class="health-info">
          <span class="health-status-text">${isOk?'Sistema Saudável':'Problema Detectado'}</span>
          <span class="health-uptime">${data.uptime||'—'}</span>
        </div>
      </div>
      <div class="health-checks">
        ${(health.checks||[]).map(c => `
          <div class="health-check-item">
            <span class="health-check-dot health-check-${c.status}"></span>
            <span class="health-check-name">${c.name}</span>
          </div>
        `).join('')}
      </div>
    `;
  },

  _updateServices(data) {
    const el = document.getElementById('status-services');
    if (!el) return;
    const services = data.services || [
      {name:'API REST (FastAPI)',status:'online',port:8080},
      {name:'Kernel API (JSON)',status:'online',port:8000},
      {name:'WebSocket Bridge',status:'online',port:8080},
    ];
    el.innerHTML = `<div class="service-list">${services.map(s => `
      <div class="service-item">
        <span class="status-badge status-${s.status||'offline'}">${s.status||'offline'}</span>
        <div class="service-info"><span class="service-name">${s.name}</span><span class="service-port">:${s.port||'—'}</span></div>
      </div>
    `).join('')}</div>`;
  },

  _updateMetrics(data) {
    const el = document.getElementById('status-metrics');
    if (!el) return;
    const m = data.metrics || data;
    el.innerHTML = `
      <div class="metrics-grid">
        <div class="metric-item"><span class="metric-label">CPU</span><span class="metric-value">${m.cpu||0}%</span></div>
        <div class="metric-item"><span class="metric-label">Memória</span><span class="metric-value">${m.memory||0}MB</span></div>
        <div class="metric-item"><span class="metric-label">Agentes Online</span><span class="metric-value">${m.agents_online||m.agents||0}</span></div>
        <div class="metric-item"><span class="metric-label">Tarefas Ativas</span><span class="metric-value">${m.pending_tasks||m.tasks||0}</span></div>
        <div class="metric-item"><span class="metric-label">Sugestões</span><span class="metric-value">${m.suggestions||0}</span></div>
        <div class="metric-item"><span class="metric-label">Memórias</span><span class="metric-value">${m.memories||0}</span></div>
      </div>
    `;
  },

  _updateUptime(data) {
    const el = document.getElementById('status-uptime');
    if (!el) return;
    el.innerHTML = `
      <div class="uptime-display">
        <div class="uptime-main">${data.uptime || '—'}</div>
        <div class="uptime-started">Iniciado: ${data.started_at ? new Date(data.started_at).toLocaleString() : '—'}</div>
        <div class="uptime-version">Versão: ${data.version || '1.0.0'}</div>
      </div>
    `;
  }
};
