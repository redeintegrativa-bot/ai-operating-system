/**
 * AIOS Dashboard - Missions Page
 */
const Pages = window.Pages || {};
Pages.Missions = {
  _el: null,
  _filters: { search: '' },

  render() {
    const el = document.createElement('div');
    el.className = 'missions-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Missões</h1>
          <p class="page-subtitle">Gerencie missões e objetivos estratégicos</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary btn-sm"><span class="material-icons">flag</span> Nova Missão</button>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="missions-search" placeholder="Filtrar missões..." oninput="Pages.Missions._filter(this.value)">
      </div>
      <div id="missions-content" class="missions-content">
        <div class="loading-spinner"></div>
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchMissions();
    const h = (key) => Store.subscribe(key, () => this._reload());
    h('missions');
    h('loading');
  },
  _reload() {
    if (Store.loading.missions) {
      const c = document.getElementById('missions-content');
      if (c) c.innerHTML = '<div class="loading-spinner"></div>';
      return;
    }
    this._render(Store.state.missions);
  },
  _render(missions) {
    const container = document.getElementById('missions-content');
    if (!container) return;
    if (!missions || missions.length === 0) {
      container.innerHTML = '<div class="empty-state"><span class="empty-icon material-icons">flag</span><p class="empty-text">Nenhuma missão cadastrada</p></div>';
      return;
    }
    const progressColors = { a_faire:'#6b7280', bloquee:'#ef4444', a_venir:'#3b82f6', en_cours:'#eab308', terminee:'#22c55e' };
    const statusLabels = { a_faire:'À faire', bloqueé:'Bloquée', a_venir:'À venir', en_cours:'En cours', terminee:'Terminée' };
    const statusClasses = { a_faire:'offline', bloqueé:'offline', a_venir:'offline',  en_cours:'busy', terminee:'online' };
    const statusMarks = { a_faire:'○', bloqueé:'✕', a_venir:'◎',  en_cours:'●', terminee:'✓'};
    const statusColors = { a_faire:'#888', bloqueé:'#e22', a_venir:'#08f', en_cours:'#ea0', terminee:'#0b8'};

    // Group by status
    const grouped = {};
    missions.forEach(m => { const s = m.status || 'a_faire'; if (!grouped[s]) grouped[s] = []; grouped[s].push(m); });
    const order = ['a_faire','bloquee','a_venir','en_cours','terminee'];

    container.innerHTML = `<div class="missions-kanban">${order.map(st => {
      const items = grouped[st] || [];
      const pct = ((st) => { return items.length/missions.length*100; })(st);
      return `<div class="mission-column">
        <div class="mission-column-head" style="background:${statusColors[st]||'#666'}">
          <span>${statusMarks[st]||'?'}</span> ${statusLabels[st]||st}
          <span class="mission-count">${items.length}</span>
        </div>
        <div class="mission-column-body" data-mission-status="${st}">
          ${items.map(n => {
            const totalT = n.total_tasks || n.totalTasks || 0;
            const compT = n.completed_tasks || n.completedTasks || 0;
            const progress = totalT > 0 ? Math.round(compT / totalT * 100) : 0;
            return `<div class="card mission-card" data-name="${n.name.toLowerCase()}" onclick="Pages.Missions._detail('${n.id||n.name}')">
              <div class="card-body">
                <div class="mission-card-title">${n.name}</div>
                <div class="mission-card-desc">${n.description||n.desc||''}</div>
                <div class="mission-progress-bar">
                  <div class="mission-progress-fill" style="width:${progress}%; background:${progressColors[n.status]||'#22c55e'};"></div>
                  <span>${progress}%</span>
                </div>
              </div>
            </div>`;
          }).join('')}
        </div>
      </div>`;
    }).join('')}</div>`;
  },
  _filter(val) {
    const q = val.toLowerCase();
    document.querySelectorAll('.mission-column').forEach(col => {
      let hasVisible = false;
      col.querySelectorAll('.mission-card').forEach(card => {
        const name = (card.dataset.name || '').toLowerCase();
        card.classList.toggle('hidden', !name.includes(q));
        if (!card.classList.contains('hidden')) hasVisible = true;
      });
      col.classList.toggle('hidden', !hasVisible && q !== '');
    });
  },
  _detail(id) {
    Components.Modal.open({title: id, body: `Detalhes da missão ${id} — em breve.`});
  }
};
