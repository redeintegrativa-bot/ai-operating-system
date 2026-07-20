/**
 * AIOS Dashboard - Tools Page
 */
const Pages = window.Pages || {};
Pages.Tools = {
  _el: null,
  _filters: { search: '' },
  _tools: [
    {name:'Scanner de portas',desc:'Mapeia portas abertas em hosts',category:'network',icon:'📡',complexity:'Medium'},
    {name:'Gerador de hash',desc:'Gera hash MD5/SHA256/SHA512',category:'crypto',icon:'🔐',complexity:'Beginner'},
    {name:'Codifier',desc:'Codifica/decodifica em Base64/URL/Hex',category:'crypto',icon:'🔢',complexity:'Beginner'},
    {name:'Analyzer',desc:'Analisa sentimentos do texto',category:'text',icon:'📊',complexity:'Medium'},
    {name:'Formatador JSON',desc:'Pretty-print e colapsa JSON',category:'utility',icon:'📦',complexity:'Easy'},
    {name:'Extrator CSS',desc:'Extrai CSS inline de HTML',category:'utility',icon:'🎨',complexity:'Medium'},
    {name:'Validador de email',desc:'Valida sintaxe de emails',category:'valid',icon:'✉️',complexity:'Easy'},
    {name:'Generator de QR Code',desc:'Gera QR codes a partir de texto',category:'media',icon:'📱',complexity:'Medium'},
  ],

  render() {
    const el = document.createElement('div');
    el.className = 'tools-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Ferramentas</h1>
          <p class="page-subtitle">Utilitários e ferramentas auxiliares</p>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="tools-search" placeholder="Filtrar ferramentas..." oninput="Pages.Tools._filter(this.value)">
      </div>
      <div class="tools-grid grid-3" id="tools-grid"></div>
    `;
    this._el = el;
    this._renderTools();
    return el;
  },
  _renderTools() {
    const grid = document.getElementById('tools-grid');
    if (!grid) return;
    const tools = this._filterValue ? this._tools.filter(t => t.name.toLowerCase().includes(this._filterValue)||t.category.toLowerCase().includes(this._filterValue)) : this._tools;
    grid.innerHTML = tools.length > 0 ? tools.map(t => `
      <div class="tool-card card" onclick="Pages.Tools._detail('${t.name}')">
        <div class="card-header">
          <span class="tool-icon">${t.icon}</span>
          <div class="tool-info">
            <h3 class="card-title">${t.name}</h3>
            <span class="tool-category">${t.category}</span>
          </div>
        </div>
        <div class="card-body">
          <p class="tool-desc">${t.desc}</p>
          <span class="tool-badge">${t.complexity}</span>
        </div>
      </div>
    `).join('') : '<div class="empty-state big"><span class="empty-icon">🔧</span><p class="empty-text">Nenhuma ferramenta</p></div>';
  },
  _filter(val) {
    this._filterValue = val.toLowerCase();
    this._renderTools();
  },
  _detail(name) {
    Components.Modal.open({title: name, body: `<p>Ferramenta: ${name}</p><p>Em desenvolvimento...</p>`});
  }
};
