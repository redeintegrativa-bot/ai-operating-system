/**
 * AIOS Mission Control - Marketplace Page
 * Agent marketplace with featured agents, ratings, and categories.
 */
const Pages = window.Pages || {};

Pages.Marketplace = {
  _activeCategory: 'all',
  _sortBy: 'popular',

  _marketplaceAgents: [
    { id: 101, name: 'CodeReviewer Pro', description: 'Automated code review with AI-powered suggestions for improvements, security issues, and best practices.', category: 'development', rating: 4.8, installs: 1240, version: '2.3.1' },
    { id: 102, name: 'DataAnalyzer X', description: 'Advanced data analysis with statistical modeling, trend detection, and automated report generation.', category: 'analysis', rating: 4.6, installs: 890, version: '1.8.0' },
    { id: 103, name: 'SecurityGuard', description: 'Continuous security monitoring with real-time threat detection and vulnerability assessment.', category: 'security', rating: 4.9, installs: 2100, version: '3.1.0' },
    { id: 104, name: 'DeployMaster', description: 'One-click deployment to any cloud provider with rollback support and health checks.', category: 'operations', rating: 4.5, installs: 670, version: '2.0.3' },
    { id: 105, name: 'TestWizard', description: 'Intelligent test generation covering unit, integration, and end-to-end scenarios.', category: 'development', rating: 4.7, installs: 1560, version: '1.5.2' },
    { id: 106, name: 'DocWriter AI', description: 'Automatic documentation generation from code analysis and API specifications.', category: 'creative', rating: 4.3, installs: 430, version: '1.2.0' },
    { id: 107, name: 'PerfOptimizer', description: 'Performance profiling with bottleneck identification and optimization recommendations.', category: 'operations', rating: 4.6, installs: 780, version: '2.1.0' },
    { id: 108, name: 'APIInspector', description: 'API testing and monitoring with automated endpoint validation and performance tracking.', category: 'operations', rating: 4.4, installs: 560, version: '1.7.1' },
    { id: 109, name: 'LogScout', description: 'Intelligent log aggregation and analysis with anomaly detection and alerting.', category: 'operations', rating: 4.2, installs: 340, version: '1.3.0' },
    { id: 110, name: 'DBAdmin', description: 'Database administration with schema migration, query optimization, and backup management.', category: 'development', rating: 4.7, installs: 920, version: '2.4.0' },
    { id: 111, name: 'CloudNinja', description: 'Multi-cloud resource management with cost optimization and infrastructure as code.', category: 'operations', rating: 4.8, installs: 1800, version: '3.0.1' },
    { id: 112, name: 'PromptCraft', description: 'Advanced prompt engineering toolkit for optimizing LLM interactions and outputs.', category: 'creative', rating: 4.5, installs: 2300, version: '1.9.0' }
  ],

  _categories: [
    { id: 'all', label: 'All' },
    { id: 'development', label: 'Development' },
    { id: 'security', label: 'Security' },
    { id: 'analysis', label: 'Analysis' },
    { id: 'operations', label: 'Operations' },
    { id: 'creative', label: 'Creative' }
  ],

  _featured: [103, 101, 112],

  render() {
    const el = document.createElement('div');
    el.className = 'marketplace-page animate-fade-in';

    const featured = this._featured.map(id => this._marketplaceAgents.find(a => a.id === id)).filter(Boolean);

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Agent Marketplace</h1>
          <p class="page-subtitle">Discover and install powerful AI agents</p>
        </div>
      </div>
      <div class="marketplace-featured" id="mp-featured">
        ${featured.map(agent => `
          <div class="card marketplace-featured-card">
            <div style="position: relative; z-index: 1;">
              <div class="marketplace-featured-name">${agent.name}</div>
              <div class="marketplace-featured-desc">${agent.description}</div>
              <div class="flex items-center gap-2" style="margin-bottom: 12px;">
                ${this._renderStars(agent.rating)}
                <span style="font-size: 0.8rem; color: var(--text-secondary);">${agent.rating}</span>
              </div>
              <button class="btn btn-primary btn-sm" onclick="App.showToast('${agent.name} installation placeholder', 'info')">Install</button>
            </div>
          </div>
        `).join('')}
      </div>
      <div class="filter-bar">
        <div class="tabs" style="border-bottom: none; margin-bottom: 0;">
          ${this._categories.map(c => `
            <button class="tab ${c.id === this._activeCategory ? 'active' : ''}" data-category="${c.id}">${c.label}</button>
          `).join('')}
        </div>
        <div style="margin-left: auto;">
          <select class="filter-select" id="mp-sort">
            <option value="popular">Most Popular</option>
            <option value="rating">Highest Rated</option>
            <option value="name">Name A-Z</option>
          </select>
        </div>
      </div>
      <div class="marketplace-grid" id="mp-grid"></div>
    `;

    requestAnimationFrame(() => {
      this._renderGrid(el);
      this._bindEvents(el);
    });

    return el;
  },

  _renderGrid(container) {
    const grid = container.querySelector('#mp-grid');
    if (!grid) return;

    let agents = [...this._marketplaceAgents];

    if (this._activeCategory !== 'all') {
      agents = agents.filter(a => a.category === this._activeCategory);
    }

    if (this._sortBy === 'rating') agents.sort((a, b) => b.rating - a.rating);
    else if (this._sortBy === 'name') agents.sort((a, b) => a.name.localeCompare(b.name));
    else agents.sort((a, b) => b.installs - a.installs);

    grid.innerHTML = agents.map(agent => `
      <div class="card marketplace-card card-clickable">
        <div class="marketplace-card-rating">${this._renderStars(agent.rating)} <span style="color: var(--text-secondary); font-size: 0.8rem;">${agent.rating}</span></div>
        <div class="marketplace-card-name">${agent.name}</div>
        <div class="marketplace-card-desc">${agent.description}</div>
        <div class="marketplace-card-meta">
          <span>📦 ${agent.installs.toLocaleString()} installs</span>
          <span>v${agent.version}</span>
          <span class="badge badge-tag">${agent.category}</span>
        </div>
        <div class="marketplace-card-actions">
          <button class="btn btn-primary btn-sm w-full" onclick="App.showToast('${agent.name} installation placeholder', 'info')">Install</button>
        </div>
      </div>
    `).join('');
  },

  _renderStars(rating) {
    const full = Math.floor(rating);
    const hasHalf = rating % 1 >= 0.5;
    let html = '';
    for (let i = 0; i < 5; i++) {
      if (i < full) html += '<span class="marketplace-star">★</span>';
      else if (i === full && hasHalf) html += '<span class="marketplace-star">★</span>';
      else html += '<span class="marketplace-star empty">★</span>';
    }
    return html;
  },

  _bindEvents(container) {
    container.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        container.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this._activeCategory = tab.dataset.category;
        this._renderGrid(container);
      });
    });

    container.querySelector('#mp-sort')?.addEventListener('change', (e) => {
      this._sortBy = e.target.value;
      this._renderGrid(container);
    });
  }
};
