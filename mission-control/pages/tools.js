/**
 * AIOS Mission Control - Tools Page
 * Tool management with category tabs and configuration.
 */
const Pages = window.Pages || {};

Pages.Tools = {
  _activeCategory: 'all',

  _categories: [
    { id: 'all', label: 'All' },
    { id: 'security', label: 'Security' },
    { id: 'performance', label: 'Performance' },
    { id: 'development', label: 'Development' },
    { id: 'testing', label: 'Testing' },
    { id: 'devops', label: 'DevOps' },
    { id: 'data', label: 'Data' },
    { id: 'monitoring', label: 'Monitoring' }
  ],

  render() {
    const el = document.createElement('div');
    el.className = 'tools-page animate-fade-in';

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Tools & Scripts</h1>
          <p class="page-subtitle">${Store.state.tools.length} tools available</p>
        </div>
      </div>
      <div class="tabs" id="tool-tabs">
        ${this._categories.map(c => `
          <button class="tab ${c.id === this._activeCategory ? 'active' : ''}" data-category="${c.id}">${c.label}</button>
        `).join('')}
      </div>
      <div style="margin-top: 16px;">
        <div class="tools-grid" id="tools-grid"></div>
      </div>
    `;

    requestAnimationFrame(() => {
      this._renderGrid(el);
      this._bindEvents(el);
    });

    return el;
  },

  _renderGrid(container) {
    const grid = container.querySelector('#tools-grid');
    if (!grid) return;

    let tools = [...Store.state.tools];
    if (this._activeCategory !== 'all') {
      tools = tools.filter(t => t.category === this._activeCategory);
    }

    if (tools.length === 0) {
      grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🔧</div><div class="empty-state-title">No tools in this category</div></div>';
      return;
    }

    grid.innerHTML = '';
    tools.forEach(tool => {
      const card = Components.Card.create({ type: 'tool', data: tool });
      grid.appendChild(card);
    });
  },

  _bindEvents(container) {
    container.querySelectorAll('#tool-tabs .tab').forEach(tab => {
      tab.addEventListener('click', () => {
        container.querySelectorAll('#tool-tabs .tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this._activeCategory = tab.dataset.category;
        this._renderGrid(container);
      });
    });
  }
};
