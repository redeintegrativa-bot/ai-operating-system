/**
 * AIOS Dashboard - Skills Manager Page
 */
const Pages = window.Pages || {};
Pages.Skills = {
  _el: null, _unsubs: [],

  render() {
    const el = document.createElement('div');
    el.className = 'skills-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Skills Manager</h1>
          <p class="page-subtitle">Gerencie as habilidades e capacidades dos agentes</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary btn-sm">
            <span class="material-icons">add</span> Nova Skill
          </button>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="skills-search" placeholder="Filtrar skills..." oninput="Pages.Skills._filter(this.value)">
      </div>
      <div class="skills-grid grid-3" id="skills-grid">
        <div class="loading-spinner"></div>
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchSkills();
    this._unsubs.push(Store.subscribe('skills', data => this._renderGrid(data)));
    this._unsubs.push(Store.subscribe('loading', () => {
      if (Store.loading.skills && document.getElementById('skills-grid'))
        document.getElementById('skills-grid').innerHTML = '<div class="loading-spinner"></div>';
    }));
    this._unsubs.push(Store.subscribe('errors', () => {
      if (Store.errors.skills && document.getElementById('skills-grid'))
        document.getElementById('skills-grid').innerHTML = `<div class="empty-state"><span class="empty-icon material-icons">error_outline</span><p class="empty-text">${Store.errors.skills}</p></div>`;
    }));
  },
  unmount() { this._unsubs.forEach(u => u()); },
  _renderGrid(skills) {
    const grid = document.getElementById('skills-grid');
    if (!grid) return;
    if (!skills || skills.length === 0) { grid.innerHTML = '<div class="empty-state"><span class="empty-icon material-icons">school</span><p class="empty-text">Nenhuma skill registrada</p></div>'; return; }
    const maxUsage = Math.max(...skills.map(s => s.usage||0), 1);
    const levelOrder = {basico:1,intermediario:2,avancado:3,especialista:4};
    const levelBadge = {basico:'offline',intermediario:'busy',avancado:'online',especialista:'online'};
    const catIcons = {ia:'🧠',automacao:'⚡',banco:'🗄️',seguranca:'🛡️',desenvolvimento:'💻',devops:'🚀'};
    grid.innerHTML = skills.sort((a,b) => (b.usage||0)-(a.usage||0)).map(s => {
      const pct = Math.round((s.usage||0)/maxUsage*100);
      const level = s.level||'intermediario';
      return `
        <div class="skill-card card" data-skill-name="${s.name.toLowerCase()}" data-skill-level="${level}">
          <div class="card-header">
            <span class="skill-icon">${catIcons[s.category]||'📚'}</span>
            <div class="skill-info">
              <h3 class="card-title">${s.name}</h3>
              <span class="status-badge status-${levelBadge[level]||'offline'} skill-level">${level}</span>
            </div>
          </div>
          <div class="card-body">
            <div class="skill-meta"><span class="skill-category-tag">${s.category||'geral'}</span>${s.agent?`<span class="skill-agent-tag">${s.agent}</span>`:''}</div>
            <div class="skill-stat-bar"><div class="skill-stat-fill" style="width:${pct}%"></div><span>${s.usage||0} usos</span></div>
          </div>
        </div>
      `;
    }).join('');
  },
  _filter(val) {
    const q = val.toLowerCase();
    document.querySelectorAll('.skill-card').forEach(c => {
      const name = c.dataset.skillName;
      const level = c.dataset.skillLevel;
      c.classList.toggle('hidden', !name.includes(q) && !level.includes(q));
    });
  }
};
