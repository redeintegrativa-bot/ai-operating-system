import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import PoolDetail from '../components/PoolDetail'
import {
  Coins, TrendingUp, TrendingDown, Droplets, ExternalLink,
  RefreshCw, Zap, BarChart3, Activity, Search, Layers, Brain,
  Database, ArrowUpDown, AlertCircle, Pause, Play, Flame,
  Clock, DollarSign, Percent, Hash, ArrowRightLeft, Star
} from 'lucide-react'

function fmt(n, decimals = 0) {
  if (n == null || isNaN(n) || n === 0) return '--'
  const v = Number(n)
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`
  if (v >= 1e6) return `$${(v / 1e6).toFixed(2)}M`
  if (v >= 1e3) return `$${(v / 1e3).toFixed(1)}K`
  return `$${v.toFixed(decimals)}`
}

function fmtNum(n) {
  if (n == null || isNaN(n) || n === 0) return '--'
  const v = Number(n)
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K`
  return v.toFixed(0)
}

function fmtPrice(n) {
  if (n == null || isNaN(n)) return '--'
  const v = Number(n)
  if (v >= 1) return `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  if (v >= 0.01) return `$${v.toFixed(4)}`
  return `$${v.toFixed(8)}`
}

function pct(n) {
  if (n == null || isNaN(n)) return <span className="text-gray-400">--</span>
  const v = Number(n)
  const color = v > 0 ? 'text-green-600' : v < 0 ? 'text-red-500' : 'text-gray-500'
  return <span className={color}>{v > 0 ? '+' : ''}{v.toFixed(2)}%</span>
}

function ChainBadge({ chain }) {
  const c = {
    ethereum: 'bg-blue-100 text-blue-700', base: 'bg-blue-50 text-blue-600',
    arbitrum: 'bg-blue-100 text-blue-800', bsc: 'bg-yellow-100 text-yellow-700',
    polygon: 'bg-purple-100 text-purple-700', optimism: 'bg-red-100 text-red-600',
    avalanche: 'bg-red-50 text-red-700', solana: 'bg-green-100 text-green-700',
  }[chain?.toLowerCase()] || 'bg-gray-100 text-gray-600'
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${c}`}>{chain || '?'}</span>
}

function ErrorBanner({ error, onDismiss }) {
  if (!error) return null
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 flex items-center gap-3 text-sm text-red-700">
      <AlertCircle className="w-4 h-4 flex-shrink-0" />
      <span className="flex-1">{error}</span>
      <button onClick={onDismiss} className="text-red-400 hover:text-red-600 text-lg">×</button>
    </div>
  )
}

function MiniBar({ value, max, color = '#2563eb', className = '' }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0
  return (
    <div className={`w-full bg-gray-100 rounded-full h-1.5 ${className}`}>
      <div className="h-1.5 rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  )
}

function PriceTicker({ prices }) {
  if (!prices || prices.length === 0) return null
  return (
    <div className="flex gap-4 overflow-x-auto pb-1 scrollbar-hide">
      {prices.map((p, i) => (
        <div key={i} className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-1.5 flex-shrink-0">
          <span className="text-xs font-bold text-gray-700">{p.symbol?.toUpperCase()}</span>
          <span className="text-sm font-mono">{fmtPrice(p.price_usd)}</span>
          {pct(p.change_24h_pct)}
        </div>
      ))}
    </div>
  )
}

const CHAINS = ['ethereum', 'base', 'arbitrum', 'bsc', 'polygon', 'solana']
const TABS = [
  { key: 'trending', label: 'Trending', icon: Flame },
  { key: 'top', label: 'Top Volume', icon: BarChart3 },
  { key: 'yields', label: 'Yields', icon: Coins },
  { key: 'hot', label: 'Hot Pairs', icon: Zap },
  { key: 'market', label: 'Market', icon: TrendingUp },
  { key: 'protocols', label: 'Protocols', icon: Database },
  { key: 'l2', label: 'L2', icon: Layers },
  { key: 'intel', label: 'Intelligence', icon: Brain },
]

export default function DeFiIntelligence() {
  const [tab, setTab] = useState('trending')
  const [chain, setChain] = useState('ethereum')
  const [sortBy, setSortBy] = useState('volume')
  const [search, setSearch] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const intervalRef = useRef(null)

  const [trending, setTrending] = useState([])
  const [topPools, setTopPools] = useState([])
  const [yields, setYields] = useState([])
  const [hotPairs, setHotPairs] = useState([])
  const [market, setMarket] = useState([])
  const [protocols, setProtocols] = useState([])
  const [l2, setL2] = useState([])
  const [intel, setIntel] = useState({})
  const [prices, setPrices] = useState([])
  const [overview, setOverview] = useState({})
  const [selectedPool, setSelectedPool] = useState(null)

  const fetchAll = useCallback(() => {
    setRefreshing(true)
    setError(null)
    const activeTab = tab

    const fetches = {
      trending: api.getDeFiTrending(chain).then(r => { setTrending(r?.pools || []) }),
      top: api.getDeFITopPools(chain).then(r => { setTopPools(r?.pools || []) }),
      yields: api.getDeFiYields(chain, 10000, sortBy === 'volume' ? 'volume' : 'apy', 100).then(r => { setYields(r?.pools || []) }),
      hot: api.getDeFIHotPairs('USDC').then(r => { setHotPairs(r?.pairs || []) }),
      market: api.getDeFiMarket(50).then(r => { setMarket(r?.tokens || []) }),
      protocols: api.getDeFiProtocols().then(r => { setProtocols(r?.top_protocols || []) }),
      l2: api.getDeFIL2().then(r => { setL2(r?.projects || []) }),
      intel: api.getDeFIIntelligence().then(r => { setIntel(r || {}) }),
      overview: api.getDeFiOverview().then(r => { setOverview(r || {}) }),
      prices: api.getDeFIPrices('bitcoin,ethereum,solana,binancecoin,solana,ripple,dogecoin').then(r => { setPrices(r?.results || []) }),
    }

    Promise.allSettled(Object.values(fetches))
      .then(() => setLastUpdate(new Date()))
      .catch(() => {})
      .finally(() => { setLoading(false); setRefreshing(false) })
  }, [chain, sortBy, tab])

  useEffect(() => { fetchAll() }, [fetchAll])

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchAll, 30000)
      return () => clearInterval(intervalRef.current)
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
  }, [autoRefresh, fetchAll])

  const searchLower = search.toLowerCase()

  const filterByName = (items, nameKey = 'name') => {
    if (!searchLower) return items
    return items.filter(item => {
      const name = item[nameKey] || item.symbol || ''
      return name.toLowerCase().includes(searchLower)
    })
  }

  const sortedTrending = useMemo(() => {
    const filtered = filterByName(trending)
    return [...filtered].sort((a, b) => {
      if (sortBy === 'tvl') return Number(b.reserve_in_usd || 0) - Number(a.reserve_in_usd || 0)
      return Number(b.volume_usd_24h || 0) - Number(a.volume_usd_24h || 0)
    })
  }, [trending, sortBy, searchLower])

  const sortedTopPools = useMemo(() => {
    const filtered = filterByName(topPools)
    return [...filtered].sort((a, b) => {
      if (sortBy === 'tvl') return Number(b.reserve_in_usd || 0) - Number(a.reserve_in_usd || 0)
      return Number(b.volume_usd_24h || 0) - Number(a.volume_usd_24h || 0)
    })
  }, [topPools, sortBy, searchLower])

  const sortedYields = useMemo(() => {
    let filtered = filterByName(yields)
    if (sortBy === 'stable') filtered = filtered.filter(p => p.stablecoin)
    return [...filtered].sort((a, b) => {
      if (sortBy === 'tvl') return Number(b.tvl_usd || 0) - Number(a.tvl_usd || 0)
      if (sortBy === 'volume') return Number(b.volume_usd_1d || 0) - Number(a.volume_usd_1d || 0)
      return Number(b.apy_total || 0) - Number(a.apy_total || 0)
    })
  }, [yields, sortBy, searchLower])

  const sortedHotPairs = useMemo(() => {
    return filterByName(hotPairs, 'baseToken').sort((a, b) => {
      return Number(b.volume?.h24 || 0) - Number(a.volume?.h24 || 0)
    })
  }, [hotPairs, searchLower])

  const sortedMarket = useMemo(() => {
    return filterByName(market, 'name').sort((a, b) => {
      if (sortBy === 'volume') return Number(b.volume_24h_usd || 0) - Number(a.volume_24h_usd || 0)
      if (sortBy === 'change') return Number(b.price_change_24h_pct || 0) - Number(a.price_change_24h_pct || 0)
      return Number(b.market_cap_usd || 0) - Number(a.market_cap_usd || 0)
    })
  }, [market, sortBy, searchLower])

  const sortedProtocols = useMemo(() => {
    return filterByName(protocols).sort((a, b) => Number(b.tvl_usd || 0) - Number(a.tvl_usd || 0))
  }, [protocols, searchLower])

  const sortedL2 = useMemo(() => {
    return filterByName(l2).sort((a, b) => Number(b.tvl_usd || 0) - Number(a.tvl_usd || 0))
  }, [l2, searchLower])

  const stats = overview.stats || {}
  const maxMcap = sortedMarket[0] ? Number(sortedMarket[0].market_cap_usd || 1) : 1
  const maxTvl = sortedProtocols[0] ? Number(sortedProtocols[0].tvl_usd || 1) : 1
  const maxL2Tvl = sortedL2[0] ? Number(sortedL2[0].tvl_usd || 1) : 1

  const sortOptions = {
    trending: [['volume', 'Volume'], ['tvl', 'TVL']],
    top: [['volume', 'Volume'], ['tvl', 'TVL']],
    yields: [['apy', 'APY'], ['tvl', 'TVL'], ['volume', 'Volume'], ['stable', 'Stables Only']],
    hot: [],
    market: [['mcap', 'Market Cap'], ['volume', 'Volume'], ['change', '24h Change']],
    protocols: [],
    l2: [],
    intel: [],
  }

  const actions = (
    <div className="flex items-center gap-3">
      {lastUpdate && (
        <span className="text-xs text-gray-400">
          Updated {lastUpdate.toLocaleTimeString()}
        </span>
      )}
      <button onClick={() => setAutoRefresh(!autoRefresh)}
        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition ${autoRefresh ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
        {autoRefresh ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
        {autoRefresh ? 'Live' : 'Paused'}
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
        subtitle="Real-time liquidity pools, yields, and DEX analytics"
        actions={actions}
      />

      <div className="space-y-5">
        <ErrorBanner error={error} onDismiss={() => setError(null)} />

        <PriceTicker prices={prices} />

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="card flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600"><Droplets className="w-5 h-5" /></div>
            <div>
              <div className="text-xs text-gray-500">Yield Pools</div>
              <div className="text-lg font-bold">{(stats.pool_count || yields.length || 0).toLocaleString()}</div>
            </div>
          </div>
          <div className="card flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-50 text-green-600"><DollarSign className="w-5 h-5" /></div>
            <div>
              <div className="text-xs text-gray-500">Total TVL</div>
              <div className="text-lg font-bold">{fmt(stats.total_tvl || 0)}</div>
            </div>
          </div>
          <div className="card flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-50 text-purple-600"><Percent className="w-5 h-5" /></div>
            <div>
              <div className="text-xs text-gray-500">Avg APY</div>
              <div className="text-lg font-bold">{(stats.avg_apy || 0).toFixed(1)}%</div>
            </div>
          </div>
          <div className="card flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-50 text-amber-600"><Flame className="w-5 h-5" /></div>
            <div>
              <div className="text-xs text-gray-500">Trending</div>
              <div className="text-lg font-bold">{trending.length}</div>
            </div>
          </div>
          <div className="card flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-50 text-red-600"><Layers className="w-5 h-5" /></div>
            <div>
              <div className="text-xs text-gray-500">L2 Projects</div>
              <div className="text-lg font-bold">{l2.length || '--'}</div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            {TABS.map(t => (
              <button key={t.key} onClick={() => { setTab(t.key); setSortBy(t.key === 'yields' ? 'apy' : t.key === 'market' ? 'mcap' : 'volume') }}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition ${tab === t.key ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}>
                <t.icon className="w-3 h-3" />
                {t.label}
              </button>
            ))}
          </div>

          {(tab === 'trending' || tab === 'top' || tab === 'yields') && (
            <div className="flex bg-gray-100 rounded-lg p-0.5">
              {CHAINS.map(c => (
                <button key={c} onClick={() => setChain(c)}
                  className={`px-2.5 py-1.5 text-xs font-medium rounded-md transition ${chain === c ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}>
                  {c.charAt(0).toUpperCase() + c.slice(1)}
                </button>
              ))}
            </div>
          )}

          {sortOptions[tab]?.length > 0 && (
            <div className="flex bg-gray-100 rounded-lg p-0.5">
              {sortOptions[tab].map(([k, l]) => (
                <button key={k} onClick={() => setSortBy(k)}
                  className={`text-xs px-2.5 py-1.5 rounded-md transition ${sortBy === k ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}>
                  {l}
                </button>
              ))}
            </div>
          )}

          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search pools, tokens..."
              className="pl-8 pr-3 py-1.5 text-xs border border-gray-200 rounded-lg w-48 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
          </div>
        </div>

        {tab === 'trending' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Flame className="w-4 h-4 text-orange-500" />
                Trending Pools — {chain.charAt(0).toUpperCase() + chain.slice(1)}
                <span className="text-gray-400 font-normal">({sortedTrending.length} pools)</span>
              </h3>
            </div>
            {loading ? <div className="p-8 text-center text-gray-400">Loading...</div> : sortedTrending.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No pools found</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {sortedTrending.map((pool, i) => {
                  const tvl = Number(pool.reserve_in_usd || 0)
                  const vol = Number(pool.volume_usd_24h || 0)
                  const change = Number(pool.price_change_24h_pct || 0)
                  const txns = Number(pool.transactions_24h || 0)
                  const name = pool.name || ''
                  const [base, quote] = name.includes('/') ? name.split(' / ').map(s => s.trim()) : [name, '']
                  return (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 transition">
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                          <span className="font-semibold text-sm">{base}</span>
                          {quote && <span className="text-gray-400 text-sm">/ {quote}</span>}
                          <ChainBadge chain={pool.network || pool.chain} />
                          {pool.dex && <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{pool.dex}</span>}
                        </div>
                        <a href={`https://www.geckoTerminal.com/${pool.network || 'eth'}/${name?.replace(' / ', '-')}`}
                           target="_blank" rel="noopener noreferrer"
                           className="text-gray-400 hover:text-blue-500 flex items-center gap-1 text-xs">
                          <span className="hidden sm:inline">Chart</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
                        <div>
                          <div className="text-gray-400">Liquidity</div>
                          <div className="font-semibold">{fmt(tvl)}</div>
                          <MiniBar value={tvl} max={sortedTrending[0] ? Number(sortedTrending[0].reserve_in_usd || 1) : 1} color="#2563eb" className="mt-1" />
                        </div>
                        <div>
                          <div className="text-gray-400">Volume 24h</div>
                          <div className="font-semibold">{fmt(vol)}</div>
                          <MiniBar value={vol} max={sortedTrending[0] ? Number(sortedTrending[0].volume_usd_24h || 1) : 1} color="#16a34a" className="mt-1" />
                        </div>
                        <div>
                          <div className="text-gray-400">Vol/Liq</div>
                          <div className="font-semibold">{tvl > 0 ? (vol / tvl * 100).toFixed(1) : 0}%</div>
                        </div>
                        <div>
                          <div className="text-gray-400">24h Change</div>
                          <div className="font-semibold">{pct(change)}</div>
                        </div>
                        <div>
                          <div className="text-gray-400">Txns 24h</div>
                          <div className="font-semibold">{txns > 0 ? txns.toLocaleString() : '--'}</div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {tab === 'top' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-500" />
                Top Pools by Volume — {chain.charAt(0).toUpperCase() + chain.slice(1)}
                <span className="text-gray-400 font-normal">({sortedTopPools.length} pools)</span>
              </h3>
            </div>
            {loading ? <div className="p-8 text-center text-gray-400">Loading...</div> : sortedTopPools.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No pools found</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {sortedTopPools.map((pool, i) => {
                  const tvl = Number(pool.reserve_in_usd || 0)
                  const vol = Number(pool.volume_usd_24h || 0)
                  const change = Number(pool.price_change_24h_pct || 0)
                  const name = pool.name || ''
                  const [base, quote] = name.includes('/') ? name.split(' / ').map(s => s.trim()) : [name, '']
                  return (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 transition flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm">{base}</span>
                            {quote && <span className="text-gray-400 text-sm">/ {quote}</span>}
                            <ChainBadge chain={pool.network} />
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-6 text-xs">
                        <div className="text-right w-24"><div className="text-gray-400">Volume</div><div className="font-semibold">{fmt(vol)}</div></div>
                        <div className="text-right w-24"><div className="text-gray-400">Liquidity</div><div className="font-semibold">{fmt(tvl)}</div></div>
                        <div className="text-right w-16">{pct(change)}</div>
                        <a href={`https://www.geckoTerminal.com/${pool.network || 'eth'}/${name?.replace(' / ', '-')}`}
                           target="_blank" rel="noopener noreferrer"
                           className="text-gray-400 hover:text-blue-500">
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
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
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Coins className="w-4 h-4 text-green-500" />
                Yield Pools
                <span className="text-gray-400 font-normal">({sortedYields.length} pools)</span>
              </h3>
              <div className="text-xs text-gray-400">Min TVL: $10K</div>
            </div>
            {loading ? <div className="p-8 text-center text-gray-400">Loading...</div> : sortedYields.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No yield pools found</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {sortedYields.map((pool, i) => {
                  const apy = Number(pool.apy_total || 0)
                  const tvl = Number(pool.tvl_usd || 0)
                  const vol1d = Number(pool.volume_usd_1d || 0)
                  const apyColor = apy > 20 ? 'text-green-600' : apy > 5 ? 'text-blue-600' : apy > 0 ? 'text-gray-700' : 'text-red-500'
                  const prediction = pool.predictions?.predictedClass || ''
                  return (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 transition">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                          <span className="font-semibold text-sm">{pool.symbol}</span>
                          <ChainBadge chain={pool.chain} />
                          <span className="text-xs text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded">{pool.project}</span>
                          {pool.stablecoin && <span className="text-xs px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 font-medium">Stable</span>}
                          {pool.il_risk === 'yes' && <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 font-medium">IL</span>}
                          {prediction && <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">{prediction}</span>}
                        </div>
                        <div className={`text-lg font-bold ${apyColor}`}>{apy.toFixed(1)}%</div>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
                        <div><div className="text-gray-400">Base APY</div><div className="font-medium">{Number(pool.apy_base || 0).toFixed(1)}%</div></div>
                        <div><div className="text-gray-400">Reward APY</div><div className="font-medium">{Number(pool.apy_reward || 0).toFixed(1)}%</div></div>
                        <div><div className="text-gray-400">TVL</div><div className="font-medium">{fmt(tvl)}</div></div>
                        <div><div className="text-gray-400">Volume 24h</div><div className="font-medium">{fmt(vol1d)}</div></div>
                        <div><div className="text-gray-400">Pool</div><div className="font-medium text-gray-400 truncate font-mono text-[10px]">{pool.pool?.slice(0, 16)}...</div></div>
                      </div>
                      <div className="mt-2 flex items-center gap-3">
                        <MiniBar value={apy} max={30} color={apy > 20 ? '#16a34a' : apy > 5 ? '#2563eb' : '#9ca3af'} className="flex-1" />
                        <span className="text-[10px] text-gray-400 w-12 text-right">7d: {Number(pool.apy_7d || 0).toFixed(1)}%</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {tab === 'hot' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Zap className="w-4 h-4 text-yellow-500" />
                Hot DEX Pairs
                <span className="text-gray-400 font-normal">({sortedHotPairs.length} pairs)</span>
              </h3>
            </div>
            {loading ? <div className="p-8 text-center text-gray-400">Loading...</div> : sortedHotPairs.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No pairs found</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {sortedHotPairs.map((pair, i) => {
                  const vol = Number(pair.volume?.h24 || 0)
                  const liq = Number(pair.liquidity?.usd || 0)
                  const price = Number(pair.priceUsd || 0)
                  const change = Number(pair.priceChange?.h24 || 0)
                  const txns = Number(pair.txns?.h24?.buys || 0) + Number(pair.txns?.h24?.sells || 0)
                  return (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 transition flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm">{pair.baseToken?.symbol}</span>
                            <span className="text-gray-400">/</span>
                            <span className="text-sm">{pair.quoteToken?.symbol}</span>
                            <ChainBadge chain={pair.chainId} />
                            <span className="text-xs text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded">{pair.dexId}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-6 text-xs">
                        <div className="text-right w-20"><div className="text-gray-400">Price</div><div className="font-medium">{fmtPrice(price)}</div></div>
                        <div className="text-right w-20"><div className="text-gray-400">Volume</div><div className="font-medium">{fmt(vol)}</div></div>
                        <div className="text-right w-20"><div className="text-gray-400">Liquidity</div><div className="font-medium">{fmt(liq)}</div></div>
                        <div className="text-right w-16">{pct(change)}</div>
                        <div className="text-right w-16"><div className="text-gray-400">Txns</div><div className="font-medium">{txns > 0 ? fmtNum(txns) : '--'}</div></div>
                        <a href={pair.url} target="_blank" rel="noopener noreferrer"
                           className="text-gray-400 hover:text-blue-500">
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </div>
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
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                Top Tokens by Market Cap
                <span className="text-gray-400 font-normal">({sortedMarket.length} tokens)</span>
              </h3>
            </div>
            {loading ? <div className="p-8 text-center text-gray-400">Loading...</div> : sortedMarket.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No market data</div>
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
                          <span className="font-semibold text-sm">{token.symbol?.toUpperCase()}</span>
                          <span className="text-gray-500 text-xs">{token.name}</span>
                        </div>
                        <div className="text-right">
                          <div className="font-medium text-sm">{fmtPrice(token.current_price_usd)}</div>
                          <div className="text-xs">{pct(change)}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-6 text-xs text-gray-500">
                        <span>MCap: {fmt(mcap)}</span>
                        <span>Vol: {fmt(vol)}</span>
                        <span>ATH: {fmtPrice(token.ath_usd)}</span>
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
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Database className="w-4 h-4 text-purple-500" />
                Top DeFi Protocols
                <span className="text-gray-400 font-normal">({sortedProtocols.length} protocols)</span>
              </h3>
            </div>
            {loading ? <div className="p-8 text-center text-gray-400">Loading...</div> : sortedProtocols.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No protocol data</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {sortedProtocols.map((proto, i) => {
                  const tvl = Number(proto.tvl_usd || 0)
                  return (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 transition flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm">{proto.name}</span>
                            {proto.chain && <ChainBadge chain={proto.chain} />}
                            {proto.category && <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">{proto.category}</span>}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-6 text-xs">
                        <div className="text-right w-24"><div className="text-gray-400">TVL</div><div className="font-semibold">{fmt(tvl)}</div></div>
                        <div className="text-right w-16"><div className="text-gray-400">1d</div>{pct(proto.change_1d)}</div>
                        <div className="text-right w-16"><div className="text-gray-400">7d</div>{pct(proto.change_7d)}</div>
                        <div className="w-32"><MiniBar value={tvl} max={maxTvl} color="#16a34a" /></div>
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
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-500" />
                L2 Ecosystem
                <span className="text-gray-400 font-normal">({sortedL2.length} projects)</span>
              </h3>
            </div>
            {loading ? <div className="p-8 text-center text-gray-400">Loading...</div> : sortedL2.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No L2 data</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {sortedL2.map((proj, i) => {
                  const tvl = Number(proj.tvl_usd || 0)
                  const share = Number(proj.market_share_pct || 0)
                  const change7d = Number(proj.change_7d_tvl_pct || 0)
                  return (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 transition flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm">{proj.name}</span>
                            {proj.category && <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">{proj.category}</span>}
                            {proj.stage && proj.stage !== 'Not applicable' && <span className="text-xs px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">{proj.stage}</span>}
                          </div>
                          {proj.purposes?.length > 0 && (
                            <div className="text-[10px] text-gray-400 mt-0.5">{proj.purposes.join(', ')}</div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-6 text-xs">
                        <div className="text-right w-24"><div className="text-gray-400">TVL</div><div className="font-semibold">{fmt(tvl)}</div></div>
                        <div className="text-right w-16"><div className="text-gray-400">Share</div><div className="font-medium">{share.toFixed(1)}%</div></div>
                        <div className="text-right w-16"><div className="text-gray-400">7d</div>{pct(change7d)}</div>
                        <div className="w-32"><MiniBar value={tvl} max={maxL2Tvl} color="#7c3aed" /></div>
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
                      <div className="text-xs flex flex-wrap gap-2">
                        <span className="text-gray-500">Top Gainers:</span>
                        {intel.sections.price_trends.top_gainers.map(([name, change], i) => (
                          <span key={i} className="text-green-600 bg-green-50 px-2 py-0.5 rounded">{name} (+{Number(change).toFixed(1)}%)</span>
                        ))}
                      </div>
                    )}
                    {intel.sections.price_trends.top_losers?.length > 0 && (
                      <div className="text-xs flex flex-wrap gap-2 mt-2">
                        <span className="text-gray-500">Top Losers:</span>
                        {intel.sections.price_trends.top_losers.map(([name, change], i) => (
                          <span key={i} className="text-red-500 bg-red-50 px-2 py-0.5 rounded">{name} ({Number(change).toFixed(1)}%)</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {intel.sections?.volume_analysis && (
                  <div className="card">
                    <h3 className="font-semibold text-sm mb-3 flex items-center gap-2"><Activity className="w-4 h-4" /> Volume Analysis</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div><div className="text-gray-400 text-xs">Total 24h Volume</div><div className="font-bold">{fmt(intel.sections.volume_analysis.total_volume_usd_24h)}</div></div>
                      <div><div className="text-gray-400 text-xs">Top 5 Concentration</div><div className="font-bold">{intel.sections.volume_analysis.top_five_volume_concentration_pct}%</div></div>
                    </div>
                  </div>
                )}

                {intel.sections?.sector_rotation && (
                  <div className="card">
                    <h3 className="font-semibold text-sm mb-3 flex items-center gap-2"><BarChart3 className="w-4 h-4" /> Sector Rotation</h3>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <div className="text-gray-500 mb-1 font-medium">Strongest Sectors</div>
                        {intel.sections.sector_rotation.strongest_sectors?.length > 0 ? intel.sections.sector_rotation.strongest_sectors.map((s, i) => (
                          <div key={i} className="flex justify-between py-1 border-b border-gray-50">
                            <span>{s.name}</span><span className="text-green-600 font-medium">+{s.change_pct}%</span>
                          </div>
                        )) : <div className="text-gray-400 py-1">None detected</div>}
                      </div>
                      <div>
                        <div className="text-gray-500 mb-1 font-medium">Weakest Sectors</div>
                        {intel.sections.sector_rotation.weakest_sectors?.length > 0 ? intel.sections.sector_rotation.weakest_sectors.map((s, i) => (
                          <div key={i} className="flex justify-between py-1 border-b border-gray-50">
                            <span>{s.name}</span><span className="text-red-500 font-medium">{s.change_pct}%</span>
                          </div>
                        )) : <div className="text-gray-400 py-1">None detected</div>}
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
                    <p>No intelligence data available yet.</p>
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
