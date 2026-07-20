/**
 * AIOS Dashboard - Workspaces Page
 */
const Pages = window.Pages || {};
Pages.Workspaces = {
  _filter: { search: '', status: 'all' },
  _el: null,

  render() {
    const el = document.createElement('div');
    el.className = 'workspaces-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Workspaces</h1>
          <p class="page-subtitle">Gerencie workspaces de projeto</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary btn-sm" onclick="Pages.Workspaces._create()"><span class="material-icons">add</span> Novo Workspace</button>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="workspaces-search" placeholder="Filtrar workspaces..." oninput="Pages.Workspaces._search(this.value)">
      </div>
      <div class="workspaces-grid" id="workspaces-grid"></div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchWorkspaces();
    Store.subscribe('workspaces', data => this._render(data));
    Store.subscribe('loading', () => {if (Store.loading.workspaces) this._render(null);});
    this._render(Store.state.workspaces);
  },
  _render(w) {
    const grid = document.getElementById('workspaces-grid');
    if (!grid) return;
    if (!w || w.length === 0) { grid.innerHTML = '<div class="empty-state"><span class="empty-icon material-icons">folder_open</span><p class="empty-text">Nenhum workspace. Crie o primeiro!</p></div>'; return; }
    const icons = ['📂','📁','🗂️','📋'];
    grid.innerHTML = w.map((ws, i) => `
      <div class="card workspace-card" onclick="Pages.Workspaces._open('${ws.id}')">
        <div class="card-header">
          <span class="workspace-icon">${icons[i % icons.length]}</span>
          <h3 class="card-title">${ws.name}</h3>
          ${ws.status ? `<span class="status-badge status-${ws.status}">${ws.status}</span>` : ''}
        </div>
        <p class="workspace-desc">${ws.description || 'No description'}</p>
        <div class="workspace-meta">
          <span>📌 ${ws.project_count || ws.projects || 0} projetos</span>
          <span>🧑 ${ws.member_count || ws.members || 0} membros</span>
          ${ws.last_updated || ws.lastUpdated ? `<span>🕐 ${new Date(ws.last_updated || ws.lastUpdated).toLocaleDateString()}</span>` : ''}
        </div>
      </div>
    `).join('');
  },
  _search(val) {
    this._filter.search = val;
    this._render(Store.state.workspaces.filter(w => w.name.toLowerCase().includes(val.toLowerCase())));
  },
  _create() {
    Components.Modal.open({
      title: 'Novo Workspace',
      body: `<div class="form-group"><label class="form-label">Nome</label><input class="form-input" id="workspace-name" placeholder="Workspace name"></div>
<div class="form-group"><label class="form-label">Descrição</label><textarea class="form-input form-textarea" id="workspace-desc" rows="3"></textarea></div>
<button class="btn btn-primary btn-block" onclick="Pages.Workspaces._submitCreate()">Criar</button>`
    });
  },
  _submitCreate() {
    const name = document.getElementById('workspace-name').value;
    const desc = document.getElementById('workspace-desc').value;
    if (!name) return;
    Store.addItem('workspaces', {name, description:desc});
    this._render(Store.state.workspaces);
    Components.Modal.close();
  },
  _open(id) {
    Components.Modal.open({title: `Workspace ${id}`, body: `<p>Detalhes do workspace ${id} — em breve...</p>`});
  }
};
