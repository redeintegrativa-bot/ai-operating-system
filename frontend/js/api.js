/**
 * AIOS Dashboard - API Client
 * HTTP + WebSocket client. Pure interface to the AIOS backend.
 * All endpoints are defined here. MOCK_MODE=true uses fallback.
 */
const API_URL = window.AIOS_API_URL || 'http://localhost:8000/api';
const WS_URL = window.AIOS_WS_URL || `ws://localhost:8000/ws`;
const MOCK_MODE = window.AIOS_MOCK_MODE === true;

const API = {
  _ws: null,
  _wsConnected: false,
  _wsSubscribers: {},
  _wsReconnectTimer: null,

  async _fetch(endpoint, options = {}) {
    if (MOCK_MODE) return this._mockResponse(endpoint);
    try {
      const url = `${API_URL}${endpoint}`;
      const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
        signal: AbortSignal.timeout(8000)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data && data.status === 'error') throw new Error(data.message || 'API error');
      return data;
    } catch (e) {
      if (e.name === 'TimeoutError') throw new Error('Timeout');
      const fallback = this._mockResponse(endpoint);
      if (fallback) return fallback;
      throw e;
    }
  },

  wsConnect() {
    if (this._ws && (this._ws.readyState === WebSocket.OPEN || this._ws.readyState === WebSocket.CONNECTING)) return;
    try {
      this._ws = new WebSocket(WS_URL);
      this._ws.onopen = () => { this._wsConnected = true;  if(this._wsSubscribers['*']) this._wsSubscribers['*'].forEach(f=>f({type:'connected'})); };
      this._ws.onclose = () => { this._wsConnected = false; if(this._wsSubscribers['*']) this._wsSubscribers['*'].forEach(f=>f({type:'disconnected'})); this._wsReconnectTimer = setTimeout(()=>this.wsConnect(),5000); };
      this._ws.onerror = () => {};
      this._ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data);
          const et = data.event_type || data.type;
          if (et && this._wsSubscribers[et]) this._wsSubscribers[et].forEach(f => f(data));
          if (et && this._wsSubscribers['*']) this._wsSubscribers['*'].forEach(f => f(data));
        } catch(e) {}
      };
    } catch(e) { this._wsReconnectTimer = setTimeout(()=>this.wsConnect(),10000); }
  },
  wsDisconnect() {
    if(this._wsReconnectTimer) clearTimeout(this._wsReconnectTimer);
    if(this._ws) { this._ws.onclose=null; this._ws.close(); this._ws=null; }
    this._wsConnected=false;
  },
  wsSubscribe(eventType, callback) {
    if(!this._wsSubscribers[eventType]) this._wsSubscribers[eventType]=[];
    this._wsSubscribers[eventType].push(callback);
    return ()=>{ const a=this._wsSubscribers[eventType]; if(a) this._wsSubscribers[eventType]=a.filter(c=>c!==callback); };
  },
  wsSend(data) { if(this._ws&&this._ws.readyState===WebSocket.OPEN) this._ws.send(typeof data==='string'?data:JSON.stringify(data)); },

  _mockResponse(endpoint) {
    const base = (endpoint||'').split('?')[0];
    const m = {
      agents: [
        {id:'orch',name:'Osculador',status:'online',capabilities:['routing','coordenação'],avatar:'🎯'},
        {id:'arch',name:'Arquiteto',status:'busy',capabilities:['arquitetura','design'],avatar:'🏗️'},
        {id:'eng',name:'Engenheiro',status:'online',capabilities:['codificação','testes'],avatar:'⚙️'},
        {id:'sec',name:'Segurança',status:'online',capabilities:['auth','criptografia'],avatar:'🛡️'},
        {id:'anal',name:'Analista',status:'busy',capabilities:['análise','pesquisa'],avatar:'📊'},
        {id:'doc',name:'Documentador',status:'offline',capabilities:['docs','changelog'],avatar:'📝'},
        {id:'tester',name:'Tester',status:'online',capabilities:['QA','debug'],avatar:'🧪'},
        {id:'devops',name:'DevOps',status:'busy',capabilities:['CI/CD','deploy'],avatar:'🚀'}
      ],
      tasks: [
        {id:'T-1',title:'Login OAuth2',status:'in_progress',priority:'high',assignee:'Engenheiro'},
        {id:'T-2',title:'Schema DB',status:'done',priority:'high',assignee:'Arquiteto'}
      ]
    };
    const more = {
      skills: [
        {id:'sk-1',name:'Prompt Engineering',category:'ia',level:'avancado',usage:89},
        {id:'sk-2',name:'Web Scraping',category:'automacao',level:'intermediario',usage:45},
        {id:'sk-3',name:'SQL Tuning',category:'banco',level:'avancado',usage:67},
        {id:'sk-4',name:'Security Audit',category:'seguranca',level:'especialista',usage:23},
        {id:'sk-5',name:'API Design',category:'desenvolvimento',level:'avancado',usage:120},
        {id:'sk-6',name:'DevOps Pipeline',category:'devops',level:'avancado',usage:56}
      ],
      plugins: [
        {id:'pl-1',name:'GitHub Sync',description:'Sincroniza com repositórios',vendor:'aios',version:'1.2.0',enabled:true},
        {id:'pl-2',name:'Slack Notifier',description:'Notificações no Slack',vendor:'community',version:'0.9.0',enabled:false},
        {id:'pl-3',name:'Jira Connector',description:'Integração com Jira',vendor:'aios',version:'2.0.0',enabled:true},
        {id:'pl-4',name:'Discord Bot',description:'Bot para Discord',vendor:'community',version:'0.5.0',enabled:false},
        {id:'pl-5',name:'Telegram Gateway',description:'Gateway Telegram',vendor:'aios',version:'1.0.0',enabled:true}
      ],
      capabilities: {
        generated: new Date().toISOString(),
        totalCapabilities: 34,
        categories: {
          core: {label:'Módulos Core', items:[
            {id:'system',name:'AIOS Entrypoint',status:'implementado',description:'Inicializa todos os subsistemas'},
            {id:'events',name:'EventBus',status:'implementado',description:'Barramento pub/sub de eventos'},
            {id:'orchestrator',name:'Orquestrador',status:'implementado',description:'Roteamento baseado em palavras-chave'},
            {id:'task_manager',name:'TaskManager',status:'implementado',description:'Gerenciamento persistente de tarefas'},
            {id:'memory',name:'Memória',status:'implementado',description:'Memórias episódica, semântica e procedural'},
            {id:'monitoring',name:'Monitor',status:'implementado',description:'Métricas e health checks'},
            {id:'suggestions',name:'Sugestões',status:'parcial',description:'Gerador de sugestões'}
          ]},
          agents: {label:'Agentes', items:[
            {id:'orchestrator',name:'Osculador',status:'implementado',description:'Roteamento central'},
            {id:'architect',name:'Arquiteto',status:'implementado',description:'Design de sistemas'},
            {id:'engineer',name:'Engenheiro',status:'implementado',description:'Geração de código'},
            {id:'security',name:'Segurança',status:'implementado',description:'Auditoria'},
            {id:'researcher',name:'Pesquisador',status:'implementado',description:'Coleta de conhecimento'}
          ]},
          api: {label:'API Layer', items:[
            {id:'server',name:'FastAPI Server',status:'implementado',description:'API REST + WebSocket na porta 8080'},
            {id:'kernel_api',name:'Kernel API',status:'implementado',description:'API JSON na porta 8000'},
            {id:'client',name:'HTTP Client',status:'implementado',description:'Cliente Python para APIs'}
          ]},
          utils: {label:'Utilitários', items:[
            {id:'config',name:'ConfigManager',status:'implementado',description:'JSON + env vars'},
            {id:'logger',name:'Logger',status:'implementado',description:'JSON logging rotativo'}
          ]}
        }
      },
      settings: {
        system: {name:'AIOS',env:'development',logLevel:'INFO',host:'0.0.0.0',port:8080},
        llm: {defaultProvider:'openai',defaultModel:'gpt-4',temperature:0.7,maxTokens:4096},
        security: {enableAuth:false,apiKeyHeader:'X-API-Key',corsOrigins:['http://localhost:3000']},
        agents: {maxConcurrentTasks:10,timeoutSeconds:300,retryCount:3}
      }
    };
    Object.assign(m, more);
    return m[base] || null;
  },
  _normalizeAgents(a) {
    return (a||[]).map(x => ({id:x.id,name:x.name,status:x.status,capabilities:x.capabilities||[],currentTask:x.currentTask||x.current_task||null,avatar:x.avatar||'🤖'}));
  },
  _normalizeTasks(t) {
    return (t||[]).map(x => ({id:x.id,title:x.title||x.description,status:x.status,priority:x.priority,assignee:x.assignee||x.assigned_agent,tags:x.tags||[],mission:x.mission||null}));
  },

  agents: { async list() { const d=await API._fetch('/agents'); return API._normalizeAgents(d?.agents||d||[]); } },
  tasks: {
    async list() { const d=await API._fetch('/tasks'); return API._normalizeTasks(d?.tasks||d||[]); },
    async get(id) { return API._fetch(`/tasks/${id}`); },
    async create(opts) { return API._fetch('/tasks', {method:'POST',body:JSON.stringify(opts)}); },
    async update(id,opts) { return API._fetch(`/tasks/${id}`, {method:'PUT',body:JSON.stringify(opts)}); },
    async delete(id) { return API._fetch(`/tasks/${id}`, {method:'DELETE'}); }
  },
  memories: {
    async list(agent='system',type=null) { let url=`/memory/${agent}`; if(type) url+=`?memory_type=${type}`; return API._fetch(url); }
  },
  skills: { async list() { return API._fetch('/skills'); } },
  plugins: { async list() { return API._fetch('/plugins'); } },
  workspaces: { async list() { const d=await API._fetch('/workspaces'); return d?.workspaces||d||[]; } },
  missions: { async list() { const d=await API._fetch('/missions'); return d?.missions||d||[]; } },
  tools: { async list() { const d=await API._fetch('/tools'); return d?.tools||[]; } },
  marketplace: { async list() { const d=await API._fetch('/marketplace'); return d?.items||d||[]; } },
  finances: { async list() { const d=await API._fetch('/finances'); return d?.transactions||d||[]; } },
  analytics: { async get() { return API._fetch('/analytics'); } },
  async suggestions() { const d=await API._fetch('/suggestions'); return d||{suggestions:[]}; },
  system: {
    async status() { return API._fetch('/system'); },
    async logs(limit=50) { const d=await API._fetch(`/logs?limit=${limit}`); return d?.logs||d||[]; },
    async health() { return API._fetch('/health'); }
  },
  settings: { async get() { return API._fetch('/settings'); }, async update(opts) { return API._fetch('/settings',{method:'PUT',body:JSON.stringify(opts)}); } },
  capabilities: { async get() { return API._fetch('/capabilities'); } },

  // Task Center endpoints (extended)
  taskCenter: {
    async list(params) {
      const q = params ? '?'+new URLSearchParams(params) : '';
      const d=await API._fetch(`/taskcenter${q}`);
      return d?.tasks||d||[];
    },
    async get(id) { return API._fetch(`/taskcenter/${id}`); },
    async create(opts) { return API._fetch('/taskcenter', {method:'POST',body:JSON.stringify(opts)}); },
    async update(id,opts) { return API._fetch(`/taskcenter/${id}`, {method:'PUT',body:JSON.stringify(opts)}); },
    async delete(id) { return API._fetch(`/taskcenter/${id}`); }
  }
};
