/**
 * AIOS Dashboard - Capability Map Page
 */
const Pages = window.Pages || {};
Pages.Capability = {
  _el: null, _unsubs: [],

  render() {
    const el = document.createElement('div');
    el.className = 'capability-page animate-fade-in';
    el.innerHTML = Statistics.render() + `
      <div class="page-header">
        <div>
          <h1 class="page-title">Capability Map</h1>
          <p class="page-subtitle">Mapeamento completo dos módulos, agentes e endpoints do AIOS</p>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="cap-search" placeholder="Filtrar capacidades..." oninput="Pages.Capability._filter(this.value)">
      </div>
      <div class="capability-grid" id="capability-grid">
        <div class="loading-spinner"></div>
      </div>
    `;
    this._el = el;
    return el;
  },

  mount() {
    Store.fetchCapabilities();
    this._unsubs.push(Store.subscribe('capabilities', data => this._renderGrid(data)));
    this._unsubs.push(Store.subscribe('loading', () => {
      if (Store.loading.capabilities && document.getElementById('capability-grid'))
        document.getElementById('capability-grid').innerHTML = '<div class="loading-spinner"></div>';
    }));
  },
  unmount() { this._unsubs.forEach(u => u()); },

  _renderGrid(data) {
    const grid = document.getElementById('capability-grid');
    if (!grid) return;
    if (!data || !data.categories) { grid.innerHTML = '<div class="empty-state"><span class="empty-icon material-icons">psychology</span><p class="empty-text">Nenhum dado de capabilities disponível</p></div>'; return; }

    const total = data.totalCapabilities || Object.values(data.categories).reduce((s,c) => s + c.items.length, 0);
    const implemented = Object.values(data.categories).reduce((s,c) => s + c.items.filter(i => i.status === 'implementado').length, 0);

    grid.innerHTML = Statistics.render(total, implemented) + Object.entries(data.categories).map(([key, cat]) => {
      const progress = Math.round((cat.items.filter(i => i.status === 'implementado').length / cat.items.length) * 100);
      return `
        <div class="capability-category card">
          <div class="card-header">
            <h3 class="card-title">${cat.label}</h3>
            <div class="cap-progress-sm"><div class="cap-progress-bar" style="width:${progress}%"></div><span>${progress}%</span></div>
          </div>
          <div class="card-body">
            ${cat.items.map(item => `
              <div class="capability-item ${item.status === 'implementado' ? '' : 'capability-item-partial'}" data-cap-name="${item.name.toLowerCase()}" data-cap-status="${item.status}">
                <div class="cap-item-header">
                  <span class="cap-item-name">${item.name}</span>
                  <span class="status-badge status-${item.status === 'implementado' ? 'online' : item.status === 'parcial' ? 'busy' : 'offline'}">${item.status}</span>
                </div>
                <p class="cap-item-desc">${item.description}</p>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }).join('') + Store.state.capabilities?.totalCapabilities ?
    `<div class="capability-summary card"><div class="cap-summary-header">Resumo</div><div class="cap-summary-grid"><div class="cap-summary-item"><span class="cap-summary-value">${total}</span><span class="cap-summary-label">Total</span></div><div class="cap-summary-item cap-summary-implemented"><span class="cap-summary-value">${implemented}</span><span class="cap-summary-label">Implementados</span></div><div class="cap-summary-item cap-summary-pending"><span class="cap-summary-value">${total - implemented}</span><span class="cap-summary-label">Restantes</span></div></div></div>` : '';
  },

  _filter(val) {
    const items = document.querySelectorAll('.capability-item');
    const q = val.toLowerCase();
    items.forEach(item => {
      const name = item.dataset.capName || '';
      const status = item.dataset.capStatus || '';
      item.classList.toggle('hidden', !name.includes(q) && !status.includes(q));
    });
  }
};

const Statistics = {
  render(total, implemented) {
    return `<div class="cap-statistics card"></div>`;
  }
}
