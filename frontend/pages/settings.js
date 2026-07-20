/**
 * AIOS Dashboard - Settings Page
 */
const Pages = window.Pages || {};
Pages.Settings = {
  _el: null, _unsubs: [],
  _activeTab: 'system',

  render() {
    const el = document.createElement('div');
    el.className = 'settings-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Configurações</h1>
          <p class="page-subtitle">Gerencie as configurações do AIOS</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-outline btn-sm" onclick="Pages.Settings._reset()"><span class="material-icons">restart_alt</span> Restaurar</button>
          <button class="btn btn-primary btn-sm" onclick="Pages.Settings._save()"><span class="material-icons">save</span> Salvar</button>
        </div>
      </div>
      <div class="settings-layout">
        <aside class="settings-sidebar">
          <nav class="settings-nav" role="tablist">
            <button class="settings-nav-item active" data-tab="system" onclick="Pages.Settings._switchTab('system')"><span class="material-icons">dns</span>Sistema</button>
            <button class="settings-nav-item" data-tab="llm" onclick="Pages.Settings._switchTab('llm')"><span class="material-icons">psychology</span>LLM</button>
            <button class="settings-nav-item" data-tab="agents" onclick="Pages.Settings._switchTab('agents')"><span class="material-icons">smart_toy</span>Agentes</button>
            <button class="settings-nav-item" data-tab="security" onclick="Pages.Settings._switchTab('security')"><span class="material-icons">security</span>Segurança</button>
            <button class="settings-nav-item" data-tab="monitoring" onclick="Pages.Settings._switchTab('monitoring')"><span class="material-icons">monitoring</span>Monitoramento</button>
            <button class="settings-nav-item" data-tab="integrations" onclick="Pages.Settings._switchTab('integrations')"><span class="material-icons">integration_instructions</span>Integrações</button>
          </nav>
        </aside>
        <div class="settings-content card" id="settings-content"><div class="loading-spinner"></div></div>
      </div>
    `;
    this._el = el;
    return el;
  },

  mount() {
    Store.fetchSettings();
    this._unsubs.push(Store.subscribe('settings', data => this._renderTab(this._activeTab, data)));
  },
  unmount() { this._unsubs.forEach(u => u()); },

  _switchTab(tab) {
    this._activeTab = tab;
    document.querySelectorAll('.settings-nav-item').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    this._renderTab(tab, Store.state.settings);
  },

  _renderTab(tab, settings) {
    const content = document.getElementById('settings-content');
    if (!content) return;
    if (!settings) { content.innerHTML = '<div class="empty-state"><span class="empty-icon material-icons">settings</span><p class="empty-text">Configurações não carregadas</p></div>'; return; }

    const tabs = {
      system: `
        <h3 class="settings-section-title">Configurações do Sistema</h3>
        <form class="settings-form" id="settings-form-system">
          <div class="form-group"><label class="form-label">Nome do Sistema</label><input type="text" class="form-input" value="${settings.system?.name||'AIOS'}" data-key="system.name"></div>
          <div class="form-group"><label class="form-label">Ambiente</label><select class="form-select" data-key="system.env">
            ${['development','staging','production'].map(v => `<option value="${v}" ${settings.system?.env===v?'selected':''}>${v}</option>`).join('')}
          </select></div>
          <div class="form-group"><label class="form-label">Log Level</label><select class="form-select" data-key="system.logLevel">
            ${['DEBUG','INFO','WARNING','ERROR'].map(v => `<option value="${v}" ${settings.system?.logLevel===v?'selected':''}>${v}</option>`).join('')}
          </select></div>
          <div class="form-group"><label class="form-label">Host</label><input type="text" class="form-input" value="${settings.system?.host||'0.0.0.0'}" data-key="system.host"></div>
          <div class="form-group"><label class="form-label">Porta</label><input type="number" class="form-input" value="${settings.system?.port||8080}" data-key="system.port"></div>
        </form>
      `,
      llm: `
        <h3 class="settings-section-title">Configurações LLM</h3>
        <form class="settings-form" id="settings-form-llm">
          <div class="form-group"><label class="form-label">Provedor Padrão</label><input type="text" class="form-input" value="${settings.llm?.defaultProvider||'openai'}" data-key="llm.defaultProvider"></div>
          <div class="form-group"><label class="form-label">Modelo Padrão</label><input type="text" class="form-input" value="${settings.llm?.defaultModel||'gpt-4'}" data-key="llm.defaultModel"></div>
          <div class="form-row"><div class="form-group half"><label class="form-label">Temperatura</label><input type="number" step="0.1" min="0" max="2" class="form-input" value="${settings.llm?.temperature||0.7}" data-key="llm.temperature"></div><div class="form-group half"><label class="form-label">Max Tokens</label><input type="number" class="form-input" value="${settings.llm?.maxTokens||4096}" data-key="llm.maxTokens"></div></div>
        </form>
      `,
      agents: `
        <h3 class="settings-section-title">Configurações de Agentes</h3>
        <form class="settings-form" id="settings-form-agents">
          <div class="form-group"><label class="form-label">Max Tarefas Simultâneas</label><input type="number" class="form-input" value="${settings.agents?.maxConcurrentTasks||10}" data-key="agents.maxConcurrentTasks"></div>
          <div class="form-group"><label class="form-label">Timeout (segundos)</label><input type="number" class="form-input" value="${settings.agents?.timeoutSeconds||300}" data-key="agents.timeoutSeconds"></div>
          <div class="form-group"><label class="form-label">Tentativas</label><input type="number" class="form-input" value="${settings.agents?.retryCount||3}" data-key="agents.retryCount"></div>
        </form>
      `,
      security: `
        <h3 class="settings-section-title">Configurações de Segurança</h3>
        <form class="settings-form" id="settings-form-security">
          <div class="form-group"><label class="checkbox-wrapper"><input type="checkbox" ${settings.security?.enableAuth?'checked':''} data-key="security.enableAuth"><span>Autenticação ativa</span></label></div>
          <div class="form-group"><label class="form-label">API Key Header</label><input type="text" class="form-input" value="${settings.security?.apiKeyHeader||'X-API-Key'}" data-key="security.apiKeyHeader"></div>
          <div class="form-group"><label class="form-label">CORS Origins</label><input type="text" class="form-input" value="${(settings.security?.corsOrigins||[]).join(', ')}" data-key="security.corsOrigins"></div>
        </form>
      `,
      monitoring: `
        <h3 class="settings-section-title">Monitoramento</h3>
        <p class="settings-empty">Configurações de monitoramento — em breve</p>
      `,
      integrations: `
        <h3 class="settings-section-title">Integrações</h3>
        <p class="settings-empty">Configurações de integrações — em breve</p>
      `
    };
    content.innerHTML = tabs[tab] || `<p>Selecione uma categoria</p>`;
  },

  _save() {
    const settings = JSON.parse(JSON.stringify(Store.state.settings));
    const form = document.querySelector('#settings-content form');
    if (!form) return Components.Toast.warning('Nada para salvar');
    form.querySelectorAll('[data-key]').forEach(el => {
      const key = el.dataset.key.split('.');
      if (key.length === 2) {
        if (!settings[key[0]]) settings[key[0]] = {};
        const val = el.type === 'checkbox' ? el.checked : el.value;
        if (key[1] === 'corsOrigins') settings[key[0]][key[1]] = val.split(',').map(s => s.trim()).filter(Boolean);
        else settings[key[0]][key[1]] = val;
      }
    });
    Store.update('settings', settings);
    Components.Toast.success('Configurações salvas');
  },
  _reset() {
    if (!confirm('Restaurar configurações padrão?')) return;
    Store.fetchSettings();
    Components.Toast.info('Configurações restauradas');
  }
};
