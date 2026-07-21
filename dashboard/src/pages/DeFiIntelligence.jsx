import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import {
  Coins, TrendingUp, TrendingDown, Droplets, Shield, ExternalLink,
  RefreshCw, Zap, BarChart3, Activity, Search, Layers, Brain,
  Database, ArrowUpDown, AlertCircle, Pause, Play, Filter
} from 'lucide-react'

function fmt(n, decimals = 0) {
  if (n == null || isNaN(n)) return '--'
  const v = Number(n)
  if (v >= 1e12) return `$${(v / 1e12).toFixed(1)}T`
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `$${(v / 1e3).toFixed(1)}K`
  return `$${v.toFixed(decimals)}`
}

function fmtNum(n) {
  if (n == null || isNaN(n)) return '--'
  const v = Number(n)
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K`
  return v.toFixed(0)
}

function pct(n) {
  if (n == null || isNaN(n)) return <span className="text-gray-400">--</span>
  const v = Number(n)
  const color = v > 0 ? 'text-green-600' : v < 0 ? 'text-red-500' : 'text-gray-500'
  return <span className={color}>{v > 0 ? '+' : ''}{v.toFixed(2)}%</span>
}

function ChainBadge({ chain }) {
  const colors = {
    ethereum: 'bg-blue-100 text-blue-700', base: 'bg-blue-50 text-blue-600',
    arbitrum: 'bg-blue-100 text-blue-800', bsc: 'bg-yellow-100 text-yellow-700',
    polygon: 'bg-purple-100 text-purple-700', optimism: 'bg-red-100 text-red-600',
    avalanche: 'bg-red-50 text-red-700', solana: 'bg-green-100 text-green-700',
  }
  const c = colors[chain?.toLowerCase()] || 'bg-gray-100 text-gray-600'
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${c}`}>{chain || '?'}</span>
}

function StatBox({ label, value, icon: Icon, color = 'primary' }) {
  const colors = { primary: 'text-blue-600', green: 'text-green-600', red: 'text-red-500', amber: 'text-amber-600', purple: 'text-purple-600' }
  return (
    <div className="card flex items-center gap-3">
      <div className={`p-2 rounded-lg bg-gray-50 ${colors[color]}`}><Icon className="w-5 h-5" /></div>
      <div>
        <div className="text-xs text-gray-500">{label}</div>
        <div className="text-lg font-bold">{value}</div>
      </div>
    </div>
  )
}

function ErrorBanner({ error, onDismiss }) {
  if (!error) return null
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 flex items-center gap-3 text-sm text-red-700">
      <AlertCircle className="w-4 h-4 flex-shrink-0" />
      <span className="flex-1">{error}</span>
      <button onClick={onDismiss} className="text-red-400 hover:text-red-600">×</button>
    </div>
  )
}

function MiniBar({ value, max, color = '#2563eb' }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0
  return (
    <div className="w-full bg-gray-100 rounded-full h-1.5">
      <div className="h-1.5 rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  )
}

const CHAINS = ['ethereum', 'base', 'arbitrum', 'bsc', 'polygon', 'solana']
const TABS = [
  { key: 'trending', label: 'Trending', icon: TrendingUp },
  { key: 'yields', label: 'Yields', icon: Coins },
  { key: 'market', label: 'Market', icon: BarChart3 },
  { key: 'protocols', label: 'Protocols', icon: Database },
  { key: 'l2', label: 'L2', icon: Layers },
  { key: 'intel', label: 'Intelligence', icon: Brain },
]

export default function DeFiIntelligence() {
  const [tab, setTab] = useState('trending')
  const [chain, setChain] = useState('ethereum')
  const [sortBy, setSortBy] = useState('volume')
  const [search, setSearch] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  const [trending, setTrending] = useState([])
  const [yields, setYields] = useState([])
  const [overview, setOverview] = useState({})
  const [market, setMarket] = useState([])
  const [protocols, setProtocols] = useState([])
  const [l2, setL2] = useState([])
  const [intel, setIntel] = useState({})

  const handleErrors = (label, result) => {
    if (result.status === 'rejected') {
      setError(`${label}: ${result.reason?.message || 'request failed'}`)
      return false
    }
    if (result.value?.error) {
      setError(`${label}: ${result.value.error}`)
      return false
    }
    return true
  }

  const fetchAll = useCallback(() => {
    setRefreshing(true)
    setError(null)
    Promise.allSettled([
      api.getDeFiTrending(chain),
      api.getDeFiYields(chain, 50000),
      api.getDeFiOverview(),
      api.getDeFiMarket(50),
      api.getDeFiProtocols(),
      api.getDeFIL2(),
      api.getDeFIIntelligence(),
    ]).then(([t, y, o, m, p, l2r, ir]) => {
      if (handleErrors('Trending', t)) setTrending(t.value?.pools || [])
      if (handleErrors('Yields', y)) setYields(y.value?.pools || [])
      if (o.status === 'fulfilled') setOverview(o.value || {})
      if (handleErrors('Market', m)) setMarket(m.value?.tokens || [])
      if (handleErrors('Protocols', p)) setProtocols(p.value?.top_protocols || [])
      if (handleErrors('L2', l2r)) setL2(l2r.value?.projects || [])
      if (ir.status === 'fulfilled') setIntel(ir.value || {})
    }).finally(() => { setLoading(false); setRefreshing(false) })
  }, [chain])

  useEffect(() => { fetchAll() }, [fetchAll])

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchAll, 60000)
      return () => clearInterval(intervalRef.current)
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
  }, [autoRefresh, fetchAll])

  const searchLower = search.toLowerCase()

  const sortedTrending = useMemo(() => {
    const filtered = searchLower
      ? trending.filter(p => p.name?.toLowerCase().includes(searchLower))
      : trending
    return [...filtered].sort((a, b) => {
      if (sortBy === 'volume') return Number(b.volume_usd_24h || 0) - Number(a.volume_usd_24h || 0)
      if (sortBy === 'tvl') return Number(b.reserve_in_usd || 0) - Number(a.reserve_in_usd || 0)
      if (sortBy === 'change') return Number(b.price_change_24h_pct || 0) - Number(a.price_change_24h_pct || 0)
      return 0
    })
  }, [trending, sortBy, searchLower])

  const sortedYields = useMemo(() => {
    const filtered = searchLower
      ? yields.filter(p => p.symbol?.toLowerCase().includes(searchLower) || p.project?.toLowerCase().includes(searchLower))
      : yields
    return [...filtered].sort((a, b) => {
      if (sortBy === 'apy') return Number(b.apy_total || 0) - Number(a.apy_total || 0)
      if (sortBy === 'tvl') return Number(b.tvl_usd || 0) - Number(a.tvl_usd || 0)
      return 0
    })
  }, [yields, sortBy, searchLower])

  const sortedMarket = useMemo(() => {
    const filtered = searchLower
      ? market.filter(t => t.name?.toLowerCase().includes(searchLower) || t.symbol?.toLowerCase().includes(searchLower))
      : market
    return [...filtered].sort((a, b) => {
      if (sortBy === 'mcap') return Number(b.market_cap_usd || 0) - Number(a.market_cap_usd || 0)
      if (sortBy === 'volume') return Number(b.volume_24h_usd || 0) - Number(a.volume_24h_usd || 0)
      if (sortBy === 'change') return Number(b.price_change_24h_pct || 0) - Number(a.price_change_24h_pct || 0)
      return 0
    })
  }, [market, sortBy, searchLower])

  const sortedProtocols = useMemo(() => {
    const filtered = searchLower
      ? protocols.filter(p => p.name?.toLowerCase().includes(searchLower))
      : protocols
    return [...filtered].sort((a, b) => Number(b.tvl_usd || 0) - Number(a.tvl_usd || 0))
  }, [protocols, searchLower])

  const sortedL2 = useMemo(() => {
    const filtered = searchLower
      ? l2.filter(p => p.name?.toLowerCase().includes(searchLower))
      : l2
    return [...filtered].sort((a, b) => Number(b.tvl_usd || 0) - Number(a.tvl_usd || 0))
  }, [l2, searchLower])

  const stats = overview.stats || {}
  const maxMcap = sortedMarket.length > 0 ? Math.max(...sortedMarket.map(t => Number(t.market_cap_usd || 0))) : 1
  const maxTvl = sortedProtocols.length > 0 ? Math.max(...sortedProtocols.map(p => Number(p.tvl_usd || 0))) : 1
  const maxL2Tvl = sortedL2.length > 0 ? Math.max(...sortedL2.map(p => Number(p.tvl_usd || 0))) : 1

  const actions = (
    <div className="flex items-center gap-2">
      <button onClick={() => setAutoRefresh(!autoRefresh)}
        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition ${autoRefresh ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
        {autoRefresh ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
        {autoRefresh ? 'Auto ON' : 'Auto OFF'}
      </button>
      <button onClick={fetchAll} className="p-2 rounded-lg hover:bg-gray-100" disabled={refreshing}>
        <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
      </button>
    </div>
  )

  return (
    <div>
      <PageHeader
        title="DeFi Intelligence"
        subtitle="Real-time data from GeckoTerminal, DefiLlama, CoinGecko, L2Beat"
        actions={actions}
      />

      <div className="space-y-6">
        <ErrorBanner error={error} onDismiss={() => setError(null)} />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatBox label="Pools Tracked" value={(stats.pool_count || 0).toLocaleString()} icon={Droplets} />
          <StatBox label="Total TVL" value={fmt(stats.total_tvl)} icon={BarChart3} color="green" />
          <StatBox label="Avg APY" value={`${(stats.avg_apy || 0).toFixed(1)}%`} icon={TrendingUp} color="green" />
          <StatBox label="L2 Projects" value={l2.length || '--'} icon={Layers} color="purple" />
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            {TABS.map(t => (
              <button key={t.key} onClick={() => { setTab(t.key); setSortBy(t.key === 'market' ? 'mcap' : t.key === 'trending' ? 'volume' : 'tvl') }}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition ${tab === t.key ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}>
                <t.icon className="w-3 h-3" />
                {t.label}
              </button>
            ))}
          </div>

          {(tab === 'trending' || tab === 'yields') && (
            <div className="flex bg-gray-100 rounded-lg p-0.5">
              {CHAINS.map(c => (
                <button key={c} onClick={() => setChain(c)}
                  className={`px-2.5 py-1.5 text-xs font-medium rounded-md transition ${chain === c ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}>
                  {c.charAt(0).toUpperCase() + c.slice(1)}
                </button>
              ))}
            </div>
          )}

          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search..."
              className="pl-8 pr-3 py-1.5 text-xs border border-gray-200 rounded-lg w-40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {tab === 'trending' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-sm">Trending Pools ({sortedTrending.length})</h3>
              <div className="flex gap-1">
                {[['volume', 'Volume'], ['tvl', 'TVL'], ['change', 'Change']].map(([k, l]) => (
                  <button key={k} onClick={() => setSortBy(k)}
                    className={`text-xs px-2 py-1 rounded ${sortBy === k ? 'bg-blue-100 text-blue-700' : 'text-gray-500 hover:bg-gray-100'}`}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
            {loading ? (
              <div className="p-8 text-center text-gray-400">Loading pools...</div>
            ) : sortedTrending.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No pools found</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {sortedTrending.map((pool, i) => {
                  const tvl = Number(pool.reserve_in_usd || 0)
                  const vol = Number(pool.volume_usd_24h || 0)
                  const change = Number(pool.price_change_24h_pct || 0)
                  const txns = Number(pool.transactions_24h || 0)
                  const volTvlRatio = tvl > 0 ? (vol / tvl * 100).toFixed(1) : 0
                  const name = pool.name || ''
                  const [base, quote] = name.includes('/') ? name.split('/') : [name, '']
                  return (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 transition">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                          <span className="font-medium text-sm">{base}</span>
                          {quote && <span className="text-gray-400 text-sm">/ {quote}</span>}
                          <ChainBadge chain={pool.network || pool.chain} />
                        </div>
                        <a href={`https://www.geckoTerminal.com/${pool.network || 'eth'}/${name?.replace(' / ', '-')}`}
                           target="_blank" rel="noopener noreferrer"
                           className="text-gray-400 hover:text-blue-500">
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </div>
                      <div className="grid grid-cols-5 gap-2 text-xs">
                        <div><div className="text-gray-400">Liquidity</div><div className="font-medium">{fmt(tvl)}</div></div>
                        <div><div className="text-gray-400">Volume 24h</div><div className="font-medium">{fmt(vol)}</div></div>
                        <div><div className="text-gray-400">Vol/TVL</div><div className="font-medium">{volTvlRatio}%</div></div>
                        <div><div className="text-gray-400">24h Change</div><div className="font-medium">{pct(change)}</div></div>
                        <div><div className="text-gray-400">Txns 24h</div><div className="font-medium">{txns.toLocaleString()}</div></div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {tab === 'yields' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-sm">Top Yield Pools ({sortedYields.length})</h3>
              <div className="flex gap-1">
                {[['apy', 'APY'], ['tvl', 'TVL']].map(([k, l]) => (
                  <button key={k} onClick={() => setSortBy(k)}
                    className={`text-xs px-2 py-1 rounded ${sortBy === k ? 'bg-blue-100 text-blue-700' : 'text-gray-500 hover:bg-gray-100'}`}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
            {loading ? (
              <div className="p-8 text-center text-gray-400">Loading yields...</div>
            ) : sortedYields.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No yield pools found</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {sortedYields.map((pool, i) => {
                  const apy = Number(pool.apy_total || 0)
                  const tvl = Number(pool.tvl_usd || 0)
                  const apyColor = apy > 20 ? 'text-green-600' : apy > 5 ? 'text-blue-600' : apy > 0 ? 'text-gray-700' : 'text-red-500'
                  return (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 transition">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                          <span className="font-medium text-sm">{pool.symbol}</span>
                          <ChainBadge chain={pool.chain} />
                          <span className="text-xs text-gray-400">{pool.project}</span>
                          {pool.il_risk === 'yes' && <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 font-medium">IL Risk</span>}
                        </div>
                        <div className={`text-lg font-bold ${apyColor}`}>{apy.toFixed(1)}%</div>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div><div className="text-gray-400">Base APY</div><div className="font-medium">{Number(pool.apy_base || 0).toFixed(1)}%</div></div>
                        <div><div className="text-gray-400">TVL</div><div className="font-medium">{fmt(tvl)}</div></div>
                        <div><div className="text-gray-400">Pool</div><div className="font-medium text-gray-400 truncate">{pool.pool?.slice(0, 12)}...</div></div>
                      </div>
                      {apy > 0 && tvl > 0 && (
                        <div className="mt-2">
                          <MiniBar value={apy} max={30} color={apy > 20 ? '#16a34a' : apy > 5 ? '#2563eb' : '#9ca3af'} />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {tab === 'market' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-sm">Top Tokens by Market Cap ({sortedMarket.length})</h3>
              <div className="flex gap-1">
                {[['mcap', 'Market Cap'], ['volume', 'Volume'], ['change', '24h Change']].map(([k, l]) => (
                  <button key={k} onClick={() => setSortBy(k)}
                    className={`text-xs px-2 py-1 rounded ${sortBy === k ? 'bg-blue-100 text-blue-700' : 'text-gray-500 hover:bg-gray-100'}`}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
            {loading ? (
              <div className="p-8 text-center text-gray-400">Loading market data...</div>
            ) : sortedMarket.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No market data found</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {sortedMarket.map((token, i) => {
                  const mcap = Number(token.market_cap_usd || 0)
                  const vol = Number(token.volume_24h_usd || 0)
                  const change = Number(token.price_change_24h_pct || 0)
                  return (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 transition">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                          <span className="font-medium text-sm">{token.symbol?.toUpperCase()}</span>
                          <span className="text-gray-500 text-xs">{token.name}</span>
                        </div>
                        <div className="text-right">
                          <div className="font-medium text-sm">{fmt(token.current_price_usd, 2)}</div>
                          <div className="text-xs">{pct(change)}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>MCap: {fmt(mcap)}</span>
                        <span>Vol: {fmt(vol)}</span>
                        <div className="flex-1 max-w-[200px]">
                          <MiniBar value={mcap} max={maxMcap} color="#2563eb" />
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {tab === 'protocols' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <h3 className="font-semibold text-sm">Top DeFi Protocols by TVL ({sortedProtocols.length})</h3>
            </div>
            {loading ? (
              <div className="p-8 text-center text-gray-400">Loading protocols...</div>
            ) : sortedProtocols.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No protocol data found</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {sortedProtocols.map((proto, i) => {
                  const tvl = Number(proto.tvl_usd || 0)
                  const change1d = Number(proto.change_1d || 0)
                  const change7d = Number(proto.change_7d || 0)
                  return (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 transition">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                          <span className="font-medium text-sm">{proto.name}</span>
                          <ChainBadge chain={proto.chain} />
                          <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">{proto.category}</span>
                          {proto.symbol && <span className="text-xs text-gray-400">{proto.symbol}</span>}
                        </div>
                        <div className="text-right">
                          <div className="font-medium text-sm">{fmt(tvl)}</div>
                          <div className="text-xs flex gap-2">
                            <span>1d:</span>{pct(change1d)}
                            <span>7d:</span>{pct(change7d)}
                          </div>
                        </div>
                      </div>
                      <div className="mt-1">
                        <MiniBar value={tvl} max={maxTvl} color="#16a34a" />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {tab === 'l2' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <h3 className="font-semibold text-sm">L2 Ecosystem ({sortedL2.length} projects)</h3>
            </div>
            {loading ? (
              <div className="p-8 text-center text-gray-400">Loading L2 data...</div>
            ) : sortedL2.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No L2 data found</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {sortedL2.map((proj, i) => {
                  const tvl = Number(proj.tvl_usd || 0)
                  const share = Number(proj.market_share_pct || 0)
                  const txns = Number(proj.transactions_30d || 0)
                  const change7d = Number(proj.change_7d_tvl_pct || 0)
                  return (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 transition">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                          <span className="font-medium text-sm">{proj.name}</span>
                          <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">{proj.category}</span>
                          {proj.stage && <span className="text-xs px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">Stage {proj.stage}</span>}
                        </div>
                        <div className="text-right">
                          <div className="font-medium text-sm">{fmt(tvl)}</div>
                          <div className="text-xs text-gray-500">{share.toFixed(1)}% share</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>DA: {proj.da_layer || '?'}</span>
                        <span>{fmtNum(txns)} txns/30d</span>
                        <span>7d:</span>{pct(change7d)}
                        <div className="flex-1 max-w-[200px]">
                          <MiniBar value={tvl} max={maxL2Tvl} color="#7c3aed" />
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {tab === 'intel' && (
          <div className="space-y-4">
            {loading ? (
              <div className="card p-8 text-center text-gray-400">Generating intelligence...</div>
            ) : intel.error ? (
              <div className="card p-8 text-center text-red-400">Intelligence unavailable: {intel.error}</div>
            ) : (
              <>
                {intel.sections?.network_overview && (
                  <div className="card">
                    <h3 className="font-semibold text-sm mb-3 flex items-center gap-2"><Database className="w-4 h-4" /> Network Overview</h3>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div><div className="text-gray-400 text-xs">Total TVL</div><div className="font-bold">{intel.sections.network_overview.formatted_tvl}</div></div>
                      <div><div className="text-gray-400 text-xs">Top 3 Dominance</div><div className="font-bold">{intel.sections.network_overview.top_three_dominance_pct}%</div></div>
                      <div><div className="text-gray-400 text-xs">Market Mood</div>
                        <span className={`font-bold ${intel.sections.network_overview.mood === 'bullish' ? 'text-green-600' : 'text-red-500'}`}>
                          {intel.sections.network_overview.mood}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {intel.sections?.price_trends && (
                  <div className="card">
                    <h3 className="font-semibold text-sm mb-3 flex items-center gap-2"><TrendingUp className="w-4 h-4" /> Price Trends</h3>
                    <div className="grid grid-cols-4 gap-4 text-sm mb-3">
                      <div><div className="text-gray-400 text-xs">Tokens</div><div className="font-bold">{intel.sections.price_trends.token_count}</div></div>
                      <div><div className="text-gray-400 text-xs">Gainers</div><div className="font-bold text-green-600">{intel.sections.price_trends.gainers}</div></div>
                      <div><div className="text-gray-400 text-xs">Losers</div><div className="font-bold text-red-500">{intel.sections.price_trends.losers}</div></div>
                      <div><div className="text-gray-400 text-xs">Avg Gain</div><div className="font-bold">{intel.sections.price_trends.average_gain_pct}%</div></div>
                    </div>
                    {intel.sections.price_trends.top_gainers?.length > 0 && (
                      <div className="text-xs">
                        <span className="text-gray-500">Top Gainers:</span>
                        {intel.sections.price_trends.top_gainers.map(([name, change], i) => (
                          <span key={i} className="ml-2 text-green-600">{name} (+{Number(change).toFixed(1)}%)</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {intel.sections?.sector_rotation && (
                  <div className="card">
                    <h3 className="font-semibold text-sm mb-3 flex items-center gap-2"><BarChart3 className="w-4 h-4" /> Sector Rotation</h3>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <div className="text-gray-500 mb-1">Strongest Sectors</div>
                        {intel.sections.sector_rotation.strongest_sectors?.map((s, i) => (
                          <div key={i} className="flex justify-between py-0.5">
                            <span>{s.name}</span>
                            <span className="text-green-600">+{s.change_pct}%</span>
                          </div>
                        ))}
                      </div>
                      <div>
                        <div className="text-gray-500 mb-1">Weakest Sectors</div>
                        {intel.sections.sector_rotation.weakest_sectors?.map((s, i) => (
                          <div key={i} className="flex justify-between py-0.5">
                            <span>{s.name}</span>
                            <span className="text-red-500">{s.change_pct}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {intel.sections?.l2_market && (
                  <div className="card">
                    <h3 className="font-semibold text-sm mb-3 flex items-center gap-2"><Layers className="w-4 h-4" /> L2 Market</h3>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div><div className="text-gray-400 text-xs">Projects</div><div className="font-bold">{intel.sections.l2_market.project_count}</div></div>
                      <div><div className="text-gray-400 text-xs">Total TVL</div><div className="font-bold">{intel.sections.l2_market.formatted_tvl}</div></div>
                      <div><div className="text-gray-400 text-xs">Top 3 Share</div><div className="font-bold">{intel.sections.l2_market.top_three_dominance_pct}%</div></div>
                    </div>
                  </div>
                )}

                {Object.keys(intel.sections || {}).length === 0 && (
                  <div className="card p-8 text-center text-gray-400">
                    <Brain className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No intelligence data available. The system needs data from multiple providers to generate insights.</p>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
