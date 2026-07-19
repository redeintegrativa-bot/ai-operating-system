/**
 * AIOS Mission Control - DataTable Component
 * Sortable, paginated table with search and row actions.
 */
const Components = window.Components || {};

Components.DataTable = {
  /**
   * Create a data table.
   * @param {Object} options
   * @param {Array} options.columns - [{ key, label, sortable, render }]
   * @param {Array} options.data - Row data
   * @param {Function} [options.onRowClick] - (row, index)
   * @param {boolean} [options.searchable] - Show search input
   * @param {boolean} [options.paginated] - Enable pagination
   * @param {number} [options.pageSize] - Items per page
   * @returns {HTMLElement}
   */
  create(options) {
    const el = document.createElement('div');
    const state = {
      data: [...options.data],
      sortKey: null,
      sortDir: 'asc',
      page: 1,
      pageSize: options.pageSize || 10,
      search: ''
    };

    el.innerHTML = this._buildHTML(options, state);
    this._bindEvents(el, options, state);
    return el;
  },

  /**
   * Build table HTML.
   * @param {Object} options
   * @param {Object} state
   * @returns {string}
   * @private
   */
  _buildHTML(options, state) {
    let filtered = this._getFilteredData(state);

    return `
      ${options.searchable ? `
        <div style="padding: 12px 16px; border-bottom: 1px solid var(--border);">
          <div class="filter-search" style="max-width: none;">
            <span class="filter-search-icon">🔍</span>
            <input type="text" class="table-search" placeholder="Search..." aria-label="Search table">
          </div>
        </div>
      ` : ''}
      <div class="data-table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              ${options.columns.map(col => `
                <th class="${col.sortable ? 'sortable' : ''} ${state.sortKey === col.key ? 'sort-' + state.sortDir : ''}"
                    data-key="${col.key}">${col.label}</th>
              `).join('')}
            </tr>
          </thead>
          <tbody>
            ${this._paginate(filtered, state).map((row, i) => `
              <tr data-index="${i}" class="table-row">
                ${options.columns.map(col => `
                  <td>${col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}</td>
                `).join('')}
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
      ${options.paginated !== false ? this._buildPagination(filtered.length, state) : ''}
    `;
  },

  /**
   * Get filtered and sorted data.
   * @param {Object} state
   * @returns {Array}
   * @private
   */
  _getFilteredData(state) {
    let data = [...state.data];

    if (state.search) {
      const q = state.search.toLowerCase();
      data = data.filter(row =>
        Object.values(row).some(v =>
          String(v).toLowerCase().includes(q)
        )
      );
    }

    if (state.sortKey) {
      data.sort((a, b) => {
        const va = a[state.sortKey];
        const vb = b[state.sortKey];
        const cmp = va < vb ? -1 : va > vb ? 1 : 0;
        return state.sortDir === 'asc' ? cmp : -cmp;
      });
    }

    return data;
  },

  /**
   * Paginate data.
   * @param {Array} data
   * @param {Object} state
   * @returns {Array}
   * @private
   */
  _paginate(data, state) {
    const start = (state.page - 1) * state.pageSize;
    return data.slice(start, start + state.pageSize);
  },

  /**
   * Build pagination HTML.
   * @param {number} total
   * @param {Object} state
   * @returns {string}
   * @private
   */
  _buildPagination(total, state) {
    const pages = Math.ceil(total / state.pageSize);
    const start = (state.page - 1) * state.pageSize + 1;
    const end = Math.min(state.page * state.pageSize, total);

    if (total === 0) return '';

    let buttons = '';
    buttons += `<button class="table-pagination-btn" data-page="prev" ${state.page <= 1 ? 'disabled' : ''}>‹</button>`;
    for (let i = 1; i <= pages; i++) {
      buttons += `<button class="table-pagination-btn${i === state.page ? ' active' : ''}" data-page="${i}">${i}</button>`;
    }
    buttons += `<button class="table-pagination-btn" data-page="next" ${state.page >= pages ? 'disabled' : ''}>›</button>`;

    return `
      <div class="table-pagination">
        <span class="table-pagination-info">Showing ${start}-${end} of ${total}</span>
        <div class="table-pagination-buttons">${buttons}</div>
      </div>
    `;
  },

  /**
   * Bind events.
   * @param {HTMLElement} el
   * @param {Object} options
   * @param {Object} state
   * @private
   */
  _bindEvents(el, options, state) {
    // Sort
    el.querySelectorAll('th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.key;
        if (state.sortKey === key) {
          state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          state.sortKey = key;
          state.sortDir = 'asc';
        }
        this._refresh(el, options, state);
      });
    });

    // Search
    const searchInput = el.querySelector('.table-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        state.search = e.target.value;
        state.page = 1;
        this._refresh(el, options, state);
      });
    }

    // Pagination
    el.addEventListener('click', (e) => {
      const btn = e.target.closest('.table-pagination-btn');
      if (!btn || btn.disabled) return;

      const page = btn.dataset.page;
      const pages = Math.ceil(state.data.length / state.pageSize);

      if (page === 'prev') state.page = Math.max(1, state.page - 1);
      else if (page === 'next') state.page = Math.min(pages, state.page + 1);
      else state.page = parseInt(page);

      this._refresh(el, options, state);
    });

    // Row click
    if (options.onRowClick) {
      el.addEventListener('click', (e) => {
        const row = e.target.closest('.table-row');
        if (row) {
          const index = parseInt(row.dataset.index);
          const start = (state.page - 1) * state.pageSize;
          const filtered = this._getFilteredData(state);
          options.onRowClick(filtered[start + index], start + index);
        }
      });
    }
  },

  /**
   * Refresh table display.
   * @param {HTMLElement} el
   * @param {Object} options
   * @param {Object} state
   * @private
   */
  _refresh(el, options, state) {
    el.innerHTML = this._buildHTML(options, state);
    this._bindEvents(el, options, state);
  }
};
