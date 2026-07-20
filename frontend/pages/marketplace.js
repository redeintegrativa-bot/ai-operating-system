/**
 * AIOS Dashboard - Marketplace Page
 */
const Pages = window.Pages || {};
Pages.Marketplace = {
  _el: null, _unsubs: [],
  _filters: { search: '', category: 'all', vendor: 'all' },

  render() {
    const categories = ['all','Widget','Analytics','Data', 'Template'];
    const vendors = ['all','AIOS','Acme'];
    const el = document.createElement('div');
    el.className = 'marketplace-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Marketplace</h1>
          <p class="page-subtitle">Descubra integrações e conteúdo para AIOS</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary btn-sm"><span class="material-icons">add</span> Adicionar</button>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="marketplace-search" placeholder="Pesquisar..." oninput="Pages.Marketplace._filter({search:this.value})">
        <div class="search-bar-filters">
          <select class="form-select filter-select" id="marketplace-cat" onchange="Pages.Marketplace._filter({category:this.value})">${categories.map(v => `<option value="${v}">${v}</option>`).join('')}</select>
          <select class="form-select filter-select" id="marketplace-vendor" onchange="Pages.Marketplace._filter({vendor:this.value})">${vendors.map(v => `<option value="${v}">${v}</option>`).join('')}</select>
        </div>
      </div>
      <div class="marketplace-grid grid-3" id="marketplace-grid">
        <div class="loading-spinner"></div>
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchMarketplace();
    this._unsubs.push(Store.subscribe('marketplace', data => this._render(data)));
    this._unsubs.push(Store.subscribe('loading',()=>{if(Store.loading.marketplace) this._loadingMessage();}));
  },
  _loadingMessage() {
    const grid=document.getElementById('marketplace-grid');
    if(grid) grid.innerHTML = '<div class="loading-spinner"></div>';
  },
  _render(data) {
    const grid=document.getElementById('marketplace-grid');
    if(!grid)return;
    if(!data|| data.length===0) {grid.innerHTML='<div class="empty-state"><span class="empty-icon material-icons">store</span><p class="empty-message">Nada disponível</p></div>';return;}
    const cats = {Widget:'📦',Analytics:'📈',Data:'🗄️',Template:'📋',Service:'🔧'};
    const vendors = {AIOS:'🗹',Acme:'A'};
    const catColors = {Widget:'#4ade80',Analytics:'#60a5fa',Data:'#a78bfa',Template:'#f472b6',Service:'#fbbf24'};
    const diffLv = {Easy:'Intermediário',Medium:'Avançado',Hard:'Complexo'};
    grid.innerHTML = data.map(item => {
      const c = item.category || 'Widget';
      return `<div class="card mkt-card" data-cat="${c}" data-vendor="${item.vendor_items||item.vendor||'AIOS'}" data-name="${item.name.toLowerCase()}" onclick="Pages.Marketplace._detail('${item.id||item.name}')">
        <div class="mkt-card-bg" style="background:${catColors[c]||'#6ed7'};opacity:.2"></div>
        <div class="card-header">
          <span class="mkt-icon">${cats[c]||'📦'}</span>
          <div><h3 class="card-title">${item.name}</h3><span class="mkt-vendor">${item.vendor||item.author||'Vendor'}</span></div>
        </div>
        <div class="card-body">
          <p class="mkt-desc">${item.description||''}</p>
          <div class="mkt-footer">
            <span class="tag">${c}</span>
            <span class="mkt-rating">${item.rating? item.likes || 0 : 0} ⭐</span>
          </div>
        </div>
      </div>`;
    }).join('');
  },
  _filter(changes) {
    Object.assign(this._filters, changes);
    const {search,category,vendor} = this._filters;
    const q = search.toLowerCase();
    document.querySelectorAll('.mkt-card').forEach(c => {
      const catMatch = category === 'all' || c.dataset.cat === category;
      const vendorMatch = vendor === 'all' || c.dataset.vendor === vendor;
      const nameMatch = !q || c.dataset.name.includes(q);
      c.classList.toggle('hidden',!(nameMatch && catMatch && vendorMatch));
    });
  },
  _detail(name) {
    Components.Modal.open({title:name, body:`<p>Detalhes de ${name}</p>`});
  }
};
