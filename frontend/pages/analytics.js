/**
 * AIOS Dashboard - Analytics Page
 */
const Pages = window.Pages || {};
Pages.Analytics = {
  _el: null, _unsubs: [],
  _filters: { search: '' },

  render() {
    const el = document.createElement('div');
    el.className = 'analytics-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Analytics</h1>
          <p class="page-subtitle">Análise de uso e desempenho</p>
        </div>
        <div class="header-actions">
          <div class="analytics-date">${new Date().toDateString()}</div>
        </div>
      </div>
      <div class="analytics-overview">
        <div class="an-card card"><span class="an-value" id="an-users">163</span><span class="an-label">Usuários</span></div>
        <div class="an-card card"><span class="an-value" id="an-sessions">24</span><span class="an-label">Sessões ativas</span></div>
        <div class="an-card card"><span class="an-value" id="an-requests">2.4k</span><span class="an-label">Total requests</span></div>
        <div class="an-card card"><span class="an-value" id="an-rate">99.2%</span><span class="an-label">Uptime</span></div>
      </div>
      <div class="analytics-charts-grid">
        <div class="ac-card card">
          <div class="card-header"><h3 class="card-title">Requests</h3></div>
          <div class="card-body"><canvas id="reqChart" width="400" height="200"></canvas></div>
        </div>
        <div class="ac-card card">
          <div class="card-header"><h3 class="card-title">Tarefas / mês</h3></div>
          <div class="card-tasks-progress"><div class="progress-bar"><div class="progress-fill" style="width:73%"></div></div><span>73%</span></div>
          <div class="card-tasks-progress"><div class="progress-bar"><div class="progress-fill" style="width: 45%"></div></div><span>45%</span></div>
        </div>
      </div>
      <div id="analytics-bottom" class="analytics-bottom">
        <div class="card analytics-card"><div class="card-header"><h3 class="card-title">Top habilidades</h3></div><div class="card-body">Skill Analytics</div></div>
        <div class="card analytics-card"><div class="card-header"><h3 class="card-title">Agentes top</h3></div><div class="card-body">Agent Stats</div></div>
        <div class="card analytics-card"><div class="card-header"><h3 class="card-title">Erros</h3></div><div class="card-body">Error logs</div></div>
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchAnalytics();
    Store.subscribe('analytics', d => {

    });
  },
  unmount() {}
};
