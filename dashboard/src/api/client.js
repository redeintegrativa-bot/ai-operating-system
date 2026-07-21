function resolveApiBase() {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('aios_api_url')
    if (saved) return saved
  }
  return ''
}

const API_BASE = resolveApiBase()

export function getApiBase() {
  return API_BASE
}

export function setApiBase(url) {
  localStorage.setItem('aios_api_url', url.replace(/\/+$/, ''))
  window.location.reload()
}

async function request(method, path, data) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } }
  if (data) opts.body = JSON.stringify(data)
  const res = await fetch(`${API_BASE}${path}`, opts)
  if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`)
  return res.json()
}

export const api = {
  getStatus: () => request('GET', '/api/status'),
  getMetrics: () => request('GET', '/api/metrics'),
  getHealth: () => request('GET', '/api/health'),
  getSystem: () => request('GET', '/api/system'),
  getAgents: () => request('GET', '/api/agents'),
  getAgent: (n) => request('GET', `/api/agents/${n}`),
  executeAgent: (n, task) => request('POST', `/api/agents/${n}/execute`, { task }),
  getTasks: (p = {}) => { const q = new URLSearchParams(p).toString(); return request('GET', `/api/tasks${q ? '?' + q : ''}`) },
  createTask: (d) => request('POST', '/api/tasks', d),
  getTask: (id) => request('GET', `/api/tasks/${id}`),
  updateTask: (id, d) => request('PUT', `/api/tasks/${id}`, d),
  deleteTask: (id) => request('DELETE', `/api/tasks/${id}`),
  getMemories: (agent) => request('GET', `/api/memory/${agent}`),
  addMemory: (agent, d) => request('POST', `/api/memory/${agent}`, d),
  getLogs: (n = 50) => request('GET', `/api/logs?limit=${n}`),
  getPlugins: () => request('GET', '/api/plugins'),
  getCapabilities: () => request('GET', '/api/capabilities'),
  getSettings: () => request('GET', '/api/settings'),
  updateSettings: (d) => request('PUT', '/api/settings', d),
  getSkills: () => request('GET', '/api/skills'),
  getSuggestions: () => request('GET', '/api/suggestions'),
  getWorkspaces: () => request('GET', '/api/workspaces'),
  getMissions: () => request('GET', '/api/missions'),
  getTools: () => request('GET', '/api/tools'),
  getMarketplace: () => request('GET', '/api/marketplace'),
  getFinances: () => request('GET', '/api/finances'),
  getAnalytics: () => request('GET', '/api/analytics'),
}

export function getWsUrl() {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL
  if (API_BASE) {
    const url = new URL(API_BASE)
    const proto = url.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${url.host}/ws`
  }
  const loc = window.location
  const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${loc.host}/ws`
}
