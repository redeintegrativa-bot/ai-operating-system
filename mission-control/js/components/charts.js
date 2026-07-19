/**
 * AIOS Mission Control - Charts Component
 * Pure CSS/SVG chart components (no external dependencies).
 */
const Components = window.Components || {};

Components.Charts = {
  /**
   * Create a horizontal bar chart.
   * @param {Object} options
   * @param {Array<number>} options.data - Values
   * @param {Array<string>} options.labels - Label for each bar
   * @param {Array<string>} [options.colors] - Color for each bar
   * @param {number} [options.height] - Chart height
   * @returns {HTMLElement}
   */
  createBarChart(options) {
    const el = document.createElement('div');
    el.className = 'chart bar-chart';
    const maxVal = Math.max(...options.data, 1);
    const colors = options.colors || ['var(--accent-blue)'];

    el.innerHTML = `
      <div class="bar-chart-container" style="display: flex; flex-direction: column; gap: 8px;">
        ${options.data.map((val, i) => `
          <div class="bar-chart-row" style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 0.75rem; color: var(--text-muted); min-width: 80px; text-align: right;">${options.labels[i] || ''}</span>
            <div style="flex: 1; height: 24px; background: var(--bg-input); border-radius: 4px; overflow: hidden;">
              <div class="bar-chart-fill" style="height: 100%; background: ${colors[i % colors.length]}; border-radius: 4px; width: ${(val / maxVal) * 100}%; animation: barGrow 0.8s ease ${i * 0.1}s both;"></div>
            </div>
            <span style="font-size: 0.75rem; color: var(--text-primary); font-weight: 600; min-width: 40px;">${val}</span>
          </div>
        `).join('')}
      </div>
    `;
    return el;
  },

  /**
   * Create an SVG line chart.
   * @param {Object} options
   * @param {Array<number>} options.data - Values
   * @param {Array<string>} [options.labels] - X-axis labels
   * @param {string} [options.color='var(--accent-blue)'] - Line color
   * @param {number} [options.width=400]
   * @param {number} [options.height=200]
   * @returns {HTMLElement}
   */
  createLineChart(options) {
    const el = document.createElement('div');
    el.className = 'chart line-chart';

    const w = options.width || 400;
    const h = options.height || 200;
    const padding = 40;
    const data = options.data || [];
    const labels = options.labels || [];
    const color = options.color || 'var(--accent-blue)';

    if (data.length < 2) {
      el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📈</div><div class="empty-state-text">Not enough data</div></div>';
      return el;
    }

    const maxVal = Math.max(...data);
    const minVal = Math.min(...data);
    const range = maxVal - minVal || 1;

    const points = data.map((val, i) => {
      const x = padding + (i / (data.length - 1)) * (w - padding * 2);
      const y = padding + ((maxVal - val) / range) * (h - padding * 2);
      return { x, y };
    });

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
    const areaD = pathD + ` L ${points[points.length - 1].x} ${h - padding} L ${points[0].x} ${h - padding} Z`;

    // Grid lines
    const gridLines = 4;
    let grid = '';
    for (let i = 0; i <= gridLines; i++) {
      const y = padding + (i / gridLines) * (h - padding * 2);
      const val = Math.round(maxVal - (i / gridLines) * range);
      grid += `<line x1="${padding}" y1="${y}" x2="${w - padding}" y2="${y}" stroke="var(--border)" stroke-width="0.5"/>`;
      grid += `<text x="${padding - 8}" y="${y + 4}" text-anchor="end" fill="var(--text-muted)" font-size="10">${val}</text>`;
    }

    el.innerHTML = `
      <svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" preserveAspectRatio="xMidYMid meet">
        ${grid}
        <defs>
          <linearGradient id="lineGrad-${Date.now()}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${color}" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <path d="${areaD}" fill="url(#lineGrad-${Date.now()})" opacity="0.5"/>
        <path d="${pathD}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"
              stroke-dasharray="1000" stroke-dashoffset="1000" style="animation: drawLine 1.5s ease forwards;"/>
        ${points.map((p, i) => `
          <circle cx="${p.x}" cy="${p.y}" r="4" fill="var(--bg-card)" stroke="${color}" stroke-width="2" opacity="0" style="animation: fadeIn 0.3s ease ${0.8 + i * 0.05}s forwards;"/>
        `).join('')}
        ${labels.map((label, i) => {
          const x = padding + (i / (labels.length - 1)) * (w - padding * 2);
          return `<text x="${x}" y="${h - 10}" text-anchor="middle" fill="var(--text-muted)" font-size="10">${label}</text>`;
        }).join('')}
      </svg>
    `;
    return el;
  },

  /**
   * Create a donut/ring chart.
   * @param {Object} options
   * @param {Array<number>} options.data - Segment values
   * @param {Array<string>} options.labels - Segment labels
   * @param {Array<string>} options.colors - Segment colors
   * @param {number} [options.size=160]
   * @returns {HTMLElement}
   */
  createDonutChart(options) {
    const el = document.createElement('div');
    el.className = 'chart donut-chart';

    const size = options.size || 160;
    const cx = size / 2;
    const cy = size / 2;
    const r = (size - 20) / 2;
    const circumference = 2 * Math.PI * r;
    const total = options.data.reduce((s, v) => s + v, 0) || 1;
    const colors = options.colors || ['var(--accent-blue)', 'var(--accent-purple)', 'var(--accent-green)', 'var(--accent-orange)', 'var(--accent-red)', 'var(--accent-cyan)'];

    let offset = 0;
    const segments = options.data.map((val, i) => {
      const pct = val / total;
      const dashLen = pct * circumference;
      const dashOffset = -offset;
      offset += dashLen;
      return { dashLen, dashOffset, color: colors[i % colors.length], label: options.labels[i], value: val, pct };
    });

    el.innerHTML = `
      <svg viewBox="0 0 ${size} ${size}" width="${size}" height="${size}">
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--bg-input)" stroke-width="14"/>
        ${segments.map((seg, i) => `
          <circle cx="${cx}" cy="${cy}" r="${r}" fill="none"
            stroke="${seg.color}" stroke-width="14"
            stroke-dasharray="${seg.dashLen} ${circumference - seg.dashLen}"
            stroke-dashoffset="${seg.dashOffset}"
            transform="rotate(-90 ${cx} ${cy})"
            stroke-linecap="round"
            style="animation: fadeIn 0.5s ease ${i * 0.1}s both;"/>
        `).join('')}
        <text x="${cx}" y="${cy - 6}" text-anchor="middle" fill="var(--text-primary)" font-size="20" font-weight="700">${total}</text>
        <text x="${cx}" y="${cy + 12}" text-anchor="middle" fill="var(--text-muted)" font-size="10">Total</text>
      </svg>
      <div class="chart-legend" style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 12px;">
        ${segments.map(seg => `
          <div style="display: flex; align-items: center; gap: 6px; font-size: 0.75rem;">
            <span style="width: 8px; height: 8px; border-radius: 50%; background: ${seg.color};"></span>
            <span style="color: var(--text-secondary);">${seg.label}</span>
            <span style="color: var(--text-muted);">${Math.round(seg.pct * 100)}%</span>
          </div>
        `).join('')}
      </div>
    `;
    return el;
  },

  /**
   * Create a mini sparkline chart.
   * @param {Object} options
   * @param {Array<number>} options.data - Values
   * @param {string} [options.color='var(--accent-blue)']
   * @param {number} [options.height=40]
   * @returns {HTMLElement}
   */
  createMiniChart(options) {
    const el = document.createElement('div');
    el.className = 'chart mini-chart';

    const h = options.height || 40;
    const w = 120;
    const data = options.data || [];
    const color = options.color || 'var(--accent-blue)';

    if (data.length < 2) {
      el.innerHTML = `<svg width="${w}" height="${h}"></svg>`;
      return el;
    }

    const maxVal = Math.max(...data);
    const minVal = Math.min(...data);
    const range = maxVal - minVal || 1;

    const points = data.map((val, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = 4 + ((maxVal - val) / range) * (h - 8);
      return `${x},${y}`;
    });

    const pathD = `M ${points.join(' L ')}`;
    const areaD = pathD + ` L ${w} ${h} L 0 ${h} Z`;

    el.innerHTML = `
      <svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}">
        <defs>
          <linearGradient id="miniGrad-${Date.now()}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${color}" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <path d="${areaD}" fill="url(#miniGrad-${Date.now()})"/>
        <path d="${pathD}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
    return el;
  }
};
