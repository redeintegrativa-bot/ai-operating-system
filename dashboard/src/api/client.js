const API_BASE = ''

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
  getDeFiTrending: (chain = 'ethereum') => request('GET', `/api/defi/trending-pools?chain=${chain}`),
  getDeFITopPools: (chain = 'ethereum') => request('GET', `/api/defi/top-pools?chain=${chain}`),
  getDeFiPoolDetail: (chain = 'eth', poolAddress, timeframe = 'day') => request('GET', `/api/defi/pool-detail?chain=${chain}&pool_address=${poolAddress}&timeframe=${timeframe}`),
  getDeFiYields: (chain = 'ethereum', minTvl = 10000, sort = 'apy', limit = 100) => request('GET', `/api/defi/yields?chain=${chain}&min_tvl=${minTvl}&sort=${sort}&limit=${limit}`),
  getDeFIHotPairs: (query = 'USDC') => request('GET', `/api/defi/hot-pairs?query=${query}`),
  getDeFiProtocols: () => request('GET', '/api/defi/top-protocols'),
  getDeFiOverview: () => request('GET', '/api/defi/overview'),
  getDeFiMarket: (limit = 50) => request('GET', `/api/defi/market?limit=${limit}`),
  getDeFIL2: () => request('GET', '/api/defi/l2-overview'),
  getDeFIIntelligence: () => request('GET', '/api/defi/intelligence'),
  getDeFIPairs: (chain = 'ethereum', query = 'USDC') => request('GET', `/api/defi/pairs?chain=${chain}&query=${query}`),
  getDeFITrendingCoins: () => request('GET', '/api/defi/trending-coins'),
  getDeFIPrices: (ids = 'bitcoin,ethereum,solana') => request('GET', `/api/defi/prices?coin_ids=${ids}`),
  getDeFiStatus: () => request('GET', '/api/defi/status'),
}

export function getWsUrl() {
  const loc = window.location
  const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${loc.host}/ws`
}
