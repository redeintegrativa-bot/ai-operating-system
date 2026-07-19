/**
 * AIOS Mission Control - Finances Page
 * Financial dashboard with budget, transactions, and charts (placeholder).
 */
const Pages = window.Pages || {};

Pages.Finances = {
  _transactions: [
    { id: 1, date: '2026-07-19', description: 'API Usage — OpenAI GPT-4', type: 'expense', amount: -245.80, status: 'completed' },
    { id: 2, date: '2026-07-18', description: 'Hosting — AWS EC2', type: 'expense', amount: -189.00, status: 'completed' },
    { id: 3, date: '2026-07-17', description: 'Agent Marketplace — SecurityGuard', type: 'expense', amount: -49.99, status: 'completed' },
    { id: 4, date: '2026-07-15', description: 'Budget Allocation — Monthly', type: 'income', amount: 15000.00, status: 'completed' },
    { id: 5, date: '2026-07-14', description: 'API Usage — Anthropic Claude', type: 'expense', amount: -312.50, status: 'completed' },
    { id: 6, date: '2026-2026-07-12', description: 'Database — PostgreSQL Cloud', type: 'expense', amount: -75.00, status: 'completed' },
    { id: 7, date: '2026-07-10', description: 'CDN — CloudFlare Pro', type: 'expense', amount: -20.00, status: 'completed' },
    { id: 8, date: '2026-07-08', description: 'Monitoring — Datadog', type: 'expense', amount: -99.00, status: 'completed' }
  ],

  render() {
    const el = document.createElement('div');
    el.className = 'finances-page animate-fade-in';

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Finances</h1>
          <p class="page-subtitle">Budget tracking and cost management</p>
        </div>
      </div>
      <div class="card finances-balance">
        <div class="finances-balance-amount">$12,450.00</div>
        <div class="finances-balance-label">Available Balance</div>
      </div>
      <div class="finances-stats">
        <div class="card" style="text-align: center;">
          <div class="card-title" style="margin-bottom: 8px;">Monthly Budget</div>
          <div style="font-size: 1.5rem; font-weight: 700; color: var(--accent-blue);">$15,000</div>
        </div>
        <div class="card" style="text-align: center;">
          <div class="card-title" style="margin-bottom: 8px;">Spent This Month</div>
          <div style="font-size: 1.5rem; font-weight: 700; color: var(--accent-orange);">$8,320</div>
        </div>
        <div class="card" style="text-align: center;">
          <div class="card-title" style="margin-bottom: 8px;">Remaining</div>
          <div style="font-size: 1.5rem; font-weight: 700; color: var(--accent-green);">$6,680</div>
        </div>
      </div>
      <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
          <span class="card-title">Transactions</span>
        </div>
        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Type</th>
                <th style="text-align: right;">Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${this._transactions.map(t => `
                <tr>
                  <td style="font-size: 0.8rem;">${t.date}</td>
                  <td>${t.description}</td>
                  <td><span class="badge badge-${t.type === 'income' ? 'completed' : 'pending'}">${t.type}</span></td>
                  <td style="text-align: right; font-weight: 600; color: ${t.amount > 0 ? 'var(--accent-green)' : 'var(--text-primary)'};">${t.amount > 0 ? '+' : ''}$${Math.abs(t.amount).toFixed(2)}</td>
                  <td><span class="badge badge-completed">${t.status}</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
      <div class="finances-charts">
        <div class="card">
          <div class="card-header"><span class="card-title">Budget Allocation</span></div>
          <div id="fin-donut-chart"></div>
        </div>
        <div class="card">
          <div class="card-header"><span class="card-title">Cost per Mission</span></div>
          <div id="fin-bar-chart"></div>
        </div>
      </div>
    `;

    requestAnimationFrame(() => {
      const donut = el.querySelector('#fin-donut-chart');
      if (donut) {
        donut.appendChild(Components.Charts.createDonutChart({
          data: [4200, 2100, 950, 600, 320, 150],
          labels: ['Infrastructure', 'API Costs', 'Tools', 'Personnel', 'Research', 'Other'],
          colors: ['var(--accent-blue)', 'var(--accent-purple)', 'var(--accent-green)', 'var(--accent-orange)', 'var(--accent-pink)', 'var(--accent-cyan)'],
          size: 160
        }));
      }

      const bar = el.querySelector('#fin-bar-chart');
      if (bar) {
        bar.appendChild(Components.Charts.createBarChart({
          data: [3200, 2100, 1800, 900, 320, 120],
          labels: ['Auth System', 'API Gateway', 'CI/CD Pipeline', 'Security Audit', 'Performance', 'Docs'],
          colors: ['var(--accent-blue)', 'var(--accent-purple)', 'var(--accent-green)', 'var(--accent-orange)', 'var(--accent-cyan)', 'var(--accent-pink)']
        }));
      }
    });

    return el;
  }
};
