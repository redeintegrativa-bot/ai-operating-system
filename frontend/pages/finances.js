/**
 * AIOS Dashboard - Finances Page
 */
const Pages = window.Pages || {};
Pages.Finances = {
  _el: null, _unsubs: [],
  _filters: { search: '', type: 'all' },
  _types: ['all', 'income', 'expense', 'transfer'],

  render() {
    const el = document.createElement('div');
    el.className = 'finance-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Finanças</h1>
          <p class="page-subtitle">Gestão financeira do AIOS</p>
        </div>
        <div class="header-actions">
          <div class="finance-summary">
            <div class="finance-total">$ <span id="fin-gross">0</span></div>
            <div class="finance-balance" id="fin-balance">Balance: $0</div>
          </div>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="fin-search" placeholder="Pesquisar transações..." oninput="Pages.Finances._filter({search: this.value})">
        <div class="search-bar-filters">
          <select class="form-select" id="fin-type" onchange="Pages.Finances._filter({type: this.value})">${this._types.map(v => `<option value="${v}" ${v === 'all' ? 'selected' : ''}>${v}</option>`).join('')}</select>
        </div>
      </div>
      <div class="finance-chart-box"><canvas id="finChart" width="400" height="220"></canvas></div>
      <div class="table-wrapper">
        <table class="data-table" id="fin-table">
          <thead><tr><th>Descriptor</th><th>Amount</th><th>Category</th><th>Date</th></tr></thead>
          <tbody id="fin-tbody"><tr><td colspan="4">No transactions</td></tr></tbody>
        </table>
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchFinances();
    this._unsubs.push(Store.subscribe('finances', d => this._handleFinances(d)));
  },
  _handleFinances(d) {
    const fin = d || [];
    const total = fin.reduce((s, f) => s + (f.amount || 0) + (f.ammount || 0) + (f.total || 0), 0);
    const balanceEl = document.getElementById('fin-balance');
    const grossEl = document.getElementById('fin-gross');
    if (balanceEl) balanceEl.textContent = `Balance: $${total}`;
    if (grossEl) grossEl.textContent = total;
    this._render(fin);
    const ap = document.getElementById('finChart');
    if (ap && fin.length > 0) {
      const ctx = ap.getContext('2d');
      const amounts = fin.slice(0, Math.min(20, fin.length)).reverse().map(f => f.amount || f.ammount || f.revenue || f.total || 0);
      const w = ap.width;
      const barW = (w / (amounts.length + 2)) - 2;
      const max = Math.max(...amounts, 1);
      const h = ap.height;
      ap.style.width = '100%'; ap.style.height = 'auto';
      ctx.clearRect(0,0,w,h);
      const grd = ctx.createLinearGradient(0,0,0,h);
      grd.addColorStop(0, 'rgba(32,208,128,0.8)');
      grd.addColorStop(1, 'rgba(0,60,30,0.1)');
      amounts.forEach((a, i) => {
        const barH = Math.max(3, (a / max) * (h - 20));
        ctx.fillStyle = i % 2 == 0 ? '#20d080' : '#30e090';
        ctx.fillRect(i * (barW + 2) + 10, h - barH - 10, barW, barH);
        ctx.fillStyle = '#555';
        ctx.font = '9px monospace';
        ctx.fillText(a.toString(), i * (barW + 2) + 10, h - Math.max(barH + 20, 20));
      });
    }
    else if (ap) {
      const ctx = ap.getContext('2d');
      ctx.clearRect(0,0,ap.width,ap.height);
      ctx.fillStyle = '#444';
      ctx.font = '20px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('No data', ap.width/2, ap.height/2);
    }
  },
  _filter(changes) {
    Object.assign(this._filters, changes);
    const {search, type} = this._filters;
    const q = search.toLowerCase();
    const rows = document.querySelectorAll('#fin-tbody tr');
    rows.forEach(row => {
      if (row.cells.length < 4) return;
      const text = row.textContent.toLowerCase();
      const catMatch = type === 'all' || row.cells[2]?.textContent?.trim().toLowerCase() === type.toLowerCase();
      const searchMatch = !q || text.includes(q);
      row.classList.toggle('hidden', !(searchMatch && catMatch));
    });
  },
  _render(fin) {
    const tbody = document.getElementById('fin-tbody');
    if (!tbody) return;
    const data = fin || [];
    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><span class="empty-icon">📊</span><p class="empty-text">Nenhuma transação</p></div></td></tr>';
      return;
    }
    const typeColors = {income:'#16a34a',expense:'#dc2626',deposit:'#2563eb',withdrawal:'#ca8a04'};
    const typeIcons = {income:'📈',deposit:'📈',expense:'📉',withdrawal:'📉',pay:''};
    const t = localStorage.getItem('finance_view_date') || '';
    tbody.innerHTML = data.reverse().slice(0, 100).map(item => {
      const amt = item.ammount || item.amount || 0;
      const desc = item.description || item.descriptor || item.desc || '';
      const category = item.category || item.cat || '-';
      const date = item.date || item.created_at || '';
      return `<tr>
        <td><span class="tx-icon">${typeIcons[category] || '🔄'}</span>${desc}</td>
        <td style="font-weight:500;color:${typeColors[category]||'inherit'}">$${amt}</td>
        <td><span class="tag">${category}</span></td>
        <td>${date}</td>
      </tr>`;
    }).join('');
  }
};
