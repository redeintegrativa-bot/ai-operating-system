/**
 * AIOS Dashboard - Plugins Manager Page
 */
const Pages = window.Pages || {};
Pages.Plugins = {
  _el: null, _unsubs: [],
  _filterVal: {search:'',vendor:'all',status:'all'},

  render() {
    const el = document.createElement('div');
    el.className = 'plugins-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Plugins Manager</h1>
          <p class="page-subtitle">Gerencie plugins e extensões do AIOS</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-outline btn-sm"><span class="material-icons">cloud_download</span> Instalar</button>
          <button class="btn btn-primary btn-sm"><span class="material-icons">add</span> Plugin custom</button>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="plugins-search" placeholder="Filtrar plugins..." oninput="Pages.Plugins._filter({search: this.value})">
        <div class="search-bar-filters">
          <select class="form-select filter-select" id="plugins-vendor" onchange="Pages.Plugins._filter({vendor: this.value})">
            <option value="all">Todos fornecedores</option>
            <option value="aios">AIOS</option>
            <option value="community">Community</option>
          </select>
          <select class="form-select filter-select" id="plugins-status" onchange="Pages.Plugins._filter({status: this.value})">
            <option value="all">Todos status</option>
            <option value="enabled">Ativos</option>
            <option value="disabled">Desativados</option>
          </select>
        </div>
      </div>
      <div class="plugins-grid grid-3" id="plugins-grid">
        <div class="loading-spinner"></div>
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchPlugins();
    this._unsubs.push(Store.subscribe('plugins', data => this._renderGrid(data)));
    this._unsubs.push(Store.subscribe('loading', () => {
      if (Store.loading.plugins && document.getElementById('plugins-grid'))
        this._setLoading();
    }));
    this._unsubs.push(Store.subscribe('errors', () => {
      if (Store.errors.plugins && document.getElementById('plugins-grid'))
        document.getElementById('plugins-grid').innerHTML = `<div class="empty-state"><span class="empty-icon material-icons">error_outline</span><p class="empty-text">${Store.errors.plugins}</p></div>`;
    }));
  },
  unmount() { this._unsubs.forEach(u => u()); },
  _setLoading() {
    const grid = document.getElementById('plugins-grid');
    if (grid) grid.innerHTML = '<div class="loading-spinner"></div>';
  },
  _renderGrid(plugins) {
    const grid = document.getElementById('plugins-grid');
    if (!grid) return;
    if (!plugins || plugins.length === 0) { grid.innerHTML = '<div class="empty-state"><span class="empty-icon material-icons">extension</span><p class="empty-text">Nenhum plugin instalado</p></div>'; return; }
    grid.innerHTML = plugins.map(p => `
      <div class="plugin-card card" data-plugin-name="${p.name.toLowerCase()}" data-plugin-vendor="${p.vendor||'unknown'}" data-plugin-status="${p.enabled?'enabled':'disabled'}">
        <div class="card-header">
          <span class="plugin-icon">🧩</span>
          <div class="plugin-info">
            <h3 class="card-title">${p.name}</h3>
            <span class="plugin-vendor">${p.vendor||'unknown'} v${p.version||'0.0.0'}</span>
          </div>
        </div>
        <div class="card-body">
          <p class="plugin-desc">${p.description||'Sem descrição'}</p>
          <div class="plugin-actions">
            <label class="toggle-switch">
              <input type="checkbox" ${p.enabled?'checked':''} onchange="Pages.Plugins._toggle('${p.id}', this.checked)">
              <span class="toggle-slider"></span>
            </label>
            <div class="plugin-action-btns">
              <button class="btn-icon" title="Configurar" onclick="Pages.Plugins._configure('${p.id}')"><span class="material-icons">settings</span></button>
              <button class="btn-icon btn-icon-danger" title="Desinstalar" onclick="Pages.Plugins._uninstall('${p.id}')"><span class="material-icons">delete</span></button>
            </div>
          </div>
        </div>
      </div>
    `).join('');
  },
  _filter(changes) {
    Object.assign(this._filterVal, changes);
    const {search, vendor, status} = this._filterVal;
    const q = search.toLowerCase();
    document.querySelectorAll('.plugin-card').forEach(c => {
      const name = c.dataset.pluginName;
      const pv = c.dataset.pluginVendor;
      const ps = c.dataset.pluginStatus;
      const matchSearch = !q || name.includes(q);
      const matchVendor = vendor === 'all' || pv === vendor;
      const matchStatus = status === 'all' || ps === status;
      c.classList.toggle('hidden', !(matchSearch && matchVendor && matchStatus));
    });
  },
  _toggle(id, enabled) {
    Store.updateItem('plugins', id, {enabled});
    Components.Toast.success(`Plugin ${enabled?'ativado':'desativado'}`);
  },
  _configure(id) {
    Components.Modal.open({title:'Configurar Plugin', body:`<p>Configurações do plugin <strong>${id}</strong></p><p>Em desenvolvimento...</p>`});
  },
  _uninstall(id) {
    if (!confirm(`Desinstalar plugin ${id}?`)) return;
    Store.removeItem('plugins', id);
    this._renderGrid(Store.state.plugins);
    Components.Toast.success('Plugin removido');
  }
};
