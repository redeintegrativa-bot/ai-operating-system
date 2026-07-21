import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import PoolDetail from '../components/PoolDetail'
import {
  Coins, TrendingUp, TrendingDown, Droplets, ExternalLink,
  RefreshCw, Zap, BarChart3, Activity, Search, Layers, Brain,
  Database, ArrowUpDown, AlertCircle, Pause, Play, Flame,
  Clock, DollarSign, Percent, Hash, ArrowRightLeft, Star,
  ArrowUpRight, ArrowDownRight, Filter, X, ChevronDown
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
  return <span className={`font-semibold ${color}`}>{v > 0 ? '+' : ''}{v.toFixed(2)}%</span>
}

function pctText(n) {
  if (n == null || isNaN(n)) return '--'
  const v = Number(n)
  return `${v > 0 ? '+' : ''}${v.toFixed(2)}%`
}

function pctColor(n) {
  const v = Number(n || 0)
  return v > 0 ? 'text-green-600' : v < 0 ? 'text-red-500' : 'text-gray-500'
}

function pctBg(n) {
  const v = Number(n || 0)
  return v > 0 ? 'bg-green-50 text-green-700' : v < 0 ? 'bg-red-50 text-red-600' : 'bg-gray-50 text-gray-500'
}

const CHAIN_META = {
  ethereum: { label: 'Ethereum', color: 'bg-blue-500', text: 'text-blue-700', bg: 'bg-blue-50' },
  base: { label: 'Base', color: 'bg-blue-400', text: 'text-blue-600', bg: 'bg-blue-50' },
  arbitrum: { label: 'Arbitrum', color: 'bg-blue-600', text: 'text-blue-800', bg: 'bg-blue-50' },
  bsc: { label: 'BSC', color: 'bg-yellow-500', text: 'text-yellow-700', bg: 'bg-yellow-50' },
  polygon: { label: 'Polygon', color: 'bg-purple-500', text: 'text-purple-700', bg: 'bg-purple-50' },
  solana: { label: 'Solana', color: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50' },
  optimism: { label: 'Optimism', color: 'bg-red-500', text: 'text-red-600', bg: 'bg-red-50' },
  avalanche: { label: 'Avalanche', color: 'bg-red-400', text: 'text-red-700', bg: 'bg-red-50' },
}

function ChainBadge({ chain, size = 'sm' }) {
  const meta = CHAIN_META[chain?.toLowerCase()] || { label: chain || '?', color: 'bg-gray-400', text: 'text-gray-600', bg: 'bg-gray-50' }
  if (size === 'xs') {
    return (
      <span className={`inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full font-medium ${meta.text} ${meta.bg}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${meta.color}`} />
        {meta.label}
      </span>
    )
  }
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full font-medium ${meta.text} ${meta.bg}`}>
      <span className={`w-2 h-2 rounded-full ${meta.color}`} />
      {meta.label}
    </span>
  )
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
  const p = max > 0 ? Math.min((value / max) * 100, 100) : 0
  return (
    <div className={`w-full bg-gray-100 rounded-full h-1 ${className}`}>
      <div className="h-1 rounded-full transition-all duration-500" style={{ width: `${p}%`, backgroundColor: color }} />
    </div>
  )
}

function PriceTicker({ prices }) {
  if (!prices || prices.length === 0) return null
  return (
    <div className="flex gap-4 overflow-x-auto pb-1 scrollbar-hide">
      {prices.map((p, i) => (
        <div key={i} className="flex items-center gap-2 bg-white border border-gray-100 rounded-lg px-3 py-2 flex-shrink-0 shadow-sm">
          <span className="text-xs font-bold text-gray-700 uppercase">{p.symbol || p.coin_id}</span>
          <span className="text-sm font-mono">{fmtPrice(p.price_usd)}</span>
          {pct(p.change_24h_pct)}
        </div>
      ))}
    </div>
  )
}

function PoolCard({ pool, index, maxTvl, maxVol, onClick }) {
  const name = pool.name || ''
  const [base, quote] = name.includes('/') ? name.split(' / ').map(s => s.trim()) : [name, '']
  const tvl = Number(pool.reserve_in_usd || 0)
  const vol = Number(pool.volume_usd_24h || 0)
  const change = Number(pool.price_change_24h_pct || 0)
  const txns = pool.transactions_24h || {}
  const buys = typeof txns === 'object' ? (txns.buys || 0) : 0
  const sells = typeof txns === 'object' ? (txns.sells || 0) : 0
  const totalTxns = buys + sells
  const buyRatio = totalTxns > 0 ? (buys / totalTxns * 100) : 50
  const volLiqRatio = tvl > 0 ? (vol / tvl * 100) : 0

  return (
    <div onClick={onClick}
      className="bg-white border border-gray-100 rounded-xl p-4 hover:border-blue-200 hover:shadow-md transition-all duration-200 cursor-pointer group">
      {/* Header: rank + pair + chain */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-gray-300 font-mono">#{index + 1}</span>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-base text-gray-900">{base}</span>
              {quote && <span className="text-gray-300 text-sm">/</span>}
              {quote && <span className="text-gray-500 text-sm font-medium">{quote}</span>}
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <ChainBadge chain={pool.network || pool.chain} size="xs" />
              {pool.dex && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 font-medium uppercase">
                  {pool.dex.replace(/_/g, ' ')}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className={`text-right px-2 py-1 rounded-lg ${pctBg(change)}`}>
          <div className={`text-sm font-bold ${pctColor(change)}`}>{pctText(change)}</div>
        </div>
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div>
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-0.5">Liquidity</div>
          <div className="text-sm font-bold text-gray-900">{fmt(tvl)}</div>
          <MiniBar value={tvl} max={maxTvl} color="#3b82f6" className="mt-1" />
        </div>
        <div>
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-0.5">Volume 24h</div>
          <div className="text-sm font-bold text-gray-900">{fmt(vol)}</div>
          <MiniBar value={vol} max={maxVol} color="#22c55e" className="mt-1" />
        </div>
        <div>
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-0.5">Vol/Liq</div>
          <div className={`text-sm font-bold ${volLiqRatio > 50 ? 'text-orange-600' : volLiqRatio > 10 ? 'text-blue-600' : 'text-gray-600'}`}>
            {volLiqRatio.toFixed(1)}%
          </div>
          <div className="text-[10px] text-gray-400 mt-1">
            {totalTxns > 0 ? `${fmtNum(totalTxns)} txns` : ''}
          </div>
        </div>
      </div>

      {/* Footer: buy/sell bar */}
      {totalTxns > 0 && (
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden flex">
            <div className="h-full bg-green-400 rounded-l-full transition-all duration-500"
                 style={{ width: `${buyRatio}%` }} />
            <div className="h-full bg-red-300 rounded-r-full transition-all duration-500"
                 style={{ width: `${100 - buyRatio}%` }} />
          </div>
          <span className="text-[10px] text-gray-400 flex-shrink-0">
            {buyRatio > 55 ? 'Buy pressure' : buyRatio < 45 ? 'Sell pressure' : 'Balanced'}
          </span>
        </div>
      )}
    </div>
  )
}

function YieldCard({ pool, index, onClick }) {
  const apy = Number(pool.apy_total || 0)
  const tvl = Number(pool.tvl_usd || 0)
  const vol1d = Number(pool.volume_usd_1d || 0)
  const apyColor = apy > 20 ? 'text-green-600' : apy > 5 ? 'text-blue-600' : apy > 0 ? 'text-gray-700' : 'text-red-500'
  const prediction = pool.predictions?.predictedClass || ''

  return (
    <div onClick={onClick}
      className="bg-white border border-gray-100 rounded-xl p-4 hover:border-green-200 hover:shadow-md transition-all duration-200 cursor-pointer group">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold text-base text-gray-900">{pool.symbol}</span>
            <ChainBadge chain={pool.chain} size="xs" />
          </div>
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 font-medium">{pool.project}</span>
            {pool.stablecoin && <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 font-medium">Stable</span>}
            {pool.il_risk === 'yes' && <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-600 font-medium">IL Risk</span>}
            {prediction && <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-50 text-gray-400">{prediction}</span>}
          </div>
        </div>
        <div className={`text-right px-3 py-2 rounded-lg ${apy > 20 ? 'bg-green-50' : apy > 5 ? 'bg-blue-50' : 'bg-gray-50'}`}>
          <div className={`text-xl font-bold ${apyColor}`}>{apy.toFixed(1)}%</div>
          <div className="text-[10px] text-gray-400">APY</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-3">
        <div>
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-0.5">Base APY</div>
          <div className="text-sm font-bold text-gray-900">{Number(pool.apy_base || 0).toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-0.5">TVL</div>
          <div className="text-sm font-bold text-gray-900">{fmt(tvl)}</div>
        </div>
        <div>
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-0.5">Volume 24h</div>
          <div className="text-sm font-bold text-gray-900">{fmt(vol1d)}</div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <MiniBar value={apy} max={30} color={apy > 20 ? '#16a34a' : apy > 5 ? '#2563eb' : '#9ca3af'} className="flex-1" />
        <span className="text-[10px] text-gray-400 flex-shrink-0">7d: {Number(pool.apy_7d || 0).toFixed(1)}%</span>
      </div>
    </div>
  )
}

function HotPairCard({ pair, index, onClick }) {
  const vol = Number(pair.volume_24h_usd || 0)
  const liq = Number(pair.liquidity_usd || 0)
  const price = Number(pair.price_usd || 0)
  const change = Number(pair.price_change_24h_pct || 0)
  const buys = Number(pair.txns_24h?.buys || 0)
  const sells = Number(pair.txns_24h?.sells || 0)
  const txns = buys + sells

  return (
    <div onClick={onClick}
      className="bg-white border border-gray-100 rounded-xl p-4 hover:border-yellow-200 hover:shadow-md transition-all duration-200 cursor-pointer group">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-1.5 mb-1">
            <span className="font-bold text-base text-gray-900">{pair.base_token?.symbol}</span>
            <span className="text-gray-300">/</span>
            <span className="text-gray-500 font-medium">{pair.quote_token?.symbol}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <ChainBadge chain={pair.chain_id} size="xs" />
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 font-medium uppercase">{pair.dex_id}</span>
          </div>
        </div>
        <div className={`text-right px-2 py-1 rounded-lg ${pctBg(change)}`}>
          <div className={`text-sm font-bold ${pctColor(change)}`}>{pctText(change)}</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-0.5">Price</div>
          <div className="text-sm font-bold text-gray-900">{fmtPrice(price)}</div>
        </div>
        <div>
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-0.5">Volume</div>
          <div className="text-sm font-bold text-gray-900">{fmt(vol)}</div>
        </div>
        <div>
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-0.5">Liquidity</div>
          <div className="text-sm font-bold text-gray-900">{fmt(liq)}</div>
        </div>
      </div>

      {txns > 0 && (
        <div className="mt-2 flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden flex">
            <div className="h-full bg-green-400 rounded-l-full transition-all duration-500"
                 style={{ width: `${buys + sells > 0 ? (buys / (buys + sells) * 100) : 50}%` }} />
            <div className="h-full bg-red-300 rounded-r-full transition-all duration-500"
                 style={{ width: `${buys + sells > 0 ? (sells / (buys + sells) * 100) : 50}%` }} />
          </div>
          <span className="text-[10px] text-gray-400 flex-shrink-0">{fmtNum(txns)} txns</span>
        </div>
      )}
    </div>
  )
}

const CHAINS = ['ethereum', 'base', 'arbitrum', 'bsc', 'polygon', 'solana']
const TABS = [
  { key: 'trending', label: 'Trending', icon: Flame, accent: 'orange' },
  { key: 'top', label: 'Top Volume', icon: BarChart3, accent: 'blue' },
  { key: 'yields', label: 'Yields', icon: Coins, accent: 'green' },
  { key: 'hot', label: 'Hot Pairs', icon: Zap, accent: 'yellow' },
  { key: 'market', label: 'Market', icon: TrendingUp, accent: 'emerald' },
  { key: 'protocols', label: 'Protocols', icon: Database, accent: 'purple' },
  { key: 'l2', label: 'L2', icon: Layers, accent: 'indigo' },
  { key: 'intel', label: 'Intelligence', icon: Brain, accent: 'pink' },
]

export default function DeFiIntelligence() {
  const [tab, setTab] = useState('trending')
  const [chain, setChain] = useState('ethereum')
  const [sortBy, setSortBy] = useState('volume')
  const [search, setSearch] = useState('')
  const [minTvlFilter, setMinTvlFilter] = useState(0)
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
      prices: api.getDeFIPrices('bitcoin,ethereum,solana,binancecoin,ripple,dogecoin').then(r => { setPrices(r?.results || []) }),
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

  const filterByTvl = (items, tvlKey = 'reserve_in_usd') => {
    if (minTvlFilter <= 0) return items
    return items.filter(item => Number(item[tvlKey] || 0) >= minTvlFilter)
  }

  const sortedTrending = useMemo(() => {
    let filtered = filterByName(trending)
    filtered = filterByTvl(filtered)
    return [...filtered].sort((a, b) => {
      if (sortBy === 'tvl') return Number(b.reserve_in_usd || 0) - Number(a.reserve_in_usd || 0)
      return Number(b.volume_usd_24h || 0) - Number(a.volume_usd_24h || 0)
    })
  }, [trending, sortBy, searchLower, minTvlFilter])

  const sortedTopPools = useMemo(() => {
    let filtered = filterByName(topPools)
    filtered = filterByTvl(filtered)
    return [...filtered].sort((a, b) => {
      if (sortBy === 'tvl') return Number(b.reserve_in_usd || 0) - Number(a.reserve_in_usd || 0)
      return Number(b.volume_usd_24h || 0) - Number(a.volume_usd_24h || 0)
    })
  }, [topPools, sortBy, searchLower, minTvlFilter])

  const sortedYields = useMemo(() => {
    let filtered = filterByName(yields)
    filtered = filterByTvl(filtered, 'tvl_usd')
    if (sortBy === 'stable') filtered = filtered.filter(p => p.stablecoin)
    return [...filtered].sort((a, b) => {
      if (sortBy === 'tvl') return Number(b.tvl_usd || 0) - Number(a.tvl_usd || 0)
      if (sortBy === 'volume') return Number(b.volume_usd_1d || 0) - Number(a.volume_usd_1d || 0)
      return Number(b.apy_total || 0) - Number(a.apy_total || 0)
    })
  }, [yields, sortBy, searchLower, minTvlFilter])

  const sortedHotPairs = useMemo(() => {
    return filterByName(hotPairs, 'base_token').sort((a, b) => {
      return Number(b.volume_24h_usd || 0) - Number(a.volume_24h_usd || 0)
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
  const maxTvl = Math.max(...sortedTrending.map(p => Number(p.reserve_in_usd || 0)), ...sortedTopPools.map(p => Number(p.reserve_in_usd || 0)), 1)
  const maxVol = Math.max(...sortedTrending.map(p => Number(p.volume_usd_24h || 0)), ...sortedTopPools.map(p => Number(p.volume_usd_24h || 0)), 1)
  const maxMcap = sortedMarket[0] ? Number(sortedMarket[0].market_cap_usd || 1) : 1
  const maxProtTvl = sortedProtocols[0] ? Number(sortedProtocols[0].tvl_usd || 1) : 1
  const maxL2Tvl = sortedL2[0] ? Number(sortedL2[0].tvl_usd || 1) : 1

  const showChainFilter = ['trending', 'top', 'yields'].includes(tab)
  const showSortOptions = ['trending', 'top', 'yields', 'market'].includes(tab)
  const showTvlFilter = ['trending', 'top', 'yields'].includes(tab)

  const sortOptions = {
    trending: [['volume', 'Volume'], ['tvl', 'TVL']],
    top: [['volume', 'Volume'], ['tvl', 'TVL']],
    yields: [['apy', 'APY'], ['tvl', 'TVL'], ['volume', 'Volume'], ['stable', 'Stables']],
    market: [['mcap', 'Market Cap'], ['volume', 'Volume'], ['change', '24h Change']],
  }

  const tvlPresets = [
    { label: 'All', value: 0 },
    { label: '>$10K', value: 10000 },
    { label: '>$100K', value: 100000 },
    { label: '>$1M', value: 1000000 },
    { label: '>$10M', value: 10000000 },
  ]

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

      <div className="space-y-4">
        <ErrorBanner error={error} onDismiss={() => setError(null)} />

        <PriceTicker prices={prices} />

        {/* Stats bar */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="card flex items-center gap-3 py-3">
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600"><Droplets className="w-4 h-4" /></div>
            <div>
              <div className="text-[10px] text-gray-400 uppercase tracking-wider">Yield Pools</div>
              <div className="text-base font-bold">{(stats.pool_count || yields.length || 0).toLocaleString()}</div>
            </div>
          </div>
          <div className="card flex items-center gap-3 py-3">
            <div className="p-2 rounded-lg bg-green-50 text-green-600"><DollarSign className="w-4 h-4" /></div>
            <div>
              <div className="text-[10px] text-gray-400 uppercase tracking-wider">Total TVL</div>
              <div className="text-base font-bold">{fmt(stats.total_tvl || 0)}</div>
            </div>
          </div>
          <div className="card flex items-center gap-3 py-3">
            <div className="p-2 rounded-lg bg-purple-50 text-purple-600"><Percent className="w-4 h-4" /></div>
            <div>
              <div className="text-[10px] text-gray-400 uppercase tracking-wider">Avg APY</div>
              <div className="text-base font-bold">{(stats.avg_apy || 0).toFixed(1)}%</div>
            </div>
          </div>
          <div className="card flex items-center gap-3 py-3">
            <div className="p-2 rounded-lg bg-amber-50 text-amber-600"><Flame className="w-4 h-4" /></div>
            <div>
              <div className="text-[10px] text-gray-400 uppercase tracking-wider">Trending</div>
              <div className="text-base font-bold">{trending.length}</div>
            </div>
          </div>
          <div className="card flex items-center gap-3 py-3">
            <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600"><Layers className="w-4 h-4" /></div>
            <div>
              <div className="text-[10px] text-gray-400 uppercase tracking-wider">L2 Projects</div>
              <div className="text-base font-bold">{l2.length || '--'}</div>
            </div>
          </div>
        </div>

        {/* Filter bar */}
        <div className="bg-white border border-gray-100 rounded-xl p-3 space-y-3">
          {/* Row 1: Tabs */}
          <div className="flex items-center gap-2 flex-wrap">
            {TABS.map(t => (
              <button key={t.key} onClick={() => {
                setTab(t.key)
                setSortBy(t.key === 'yields' ? 'apy' : t.key === 'market' ? 'mcap' : 'volume')
                setMinTvlFilter(0)
              }}
                className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg transition ${
                  tab === t.key
                    ? 'bg-gray-900 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}>
                <t.icon className="w-3.5 h-3.5" />
                {t.label}
              </button>
            ))}

            <div className="flex-1" />

            {/* Search */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input type="text" value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search pools, tokens..."
                className="pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg w-56 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50" />
              {search && (
                <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>

          {/* Row 2: Chain + Sort + TVL filter */}
          {(showChainFilter || showSortOptions || showTvlFilter) && (
            <div className="flex items-center gap-3 flex-wrap pt-1 border-t border-gray-50">
              {/* Chain filter */}
              {showChainFilter && (
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-gray-400 uppercase tracking-wider mr-1">Chain</span>
                  {CHAINS.map(c => {
                    const meta = CHAIN_META[c] || {}
                    return (
                      <button key={c} onClick={() => setChain(c)}
                        className={`flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-lg transition ${
                          chain === c
                            ? `${meta.bg || 'bg-gray-100'} ${meta.text || 'text-gray-900'} ring-1 ring-offset-1 ring-gray-200`
                            : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
                        }`}>
                        <span className={`w-2 h-2 rounded-full ${meta.color || 'bg-gray-400'} ${chain === c ? 'opacity-100' : 'opacity-30'}`} />
                        {meta.label || c}
                      </button>
                    )
                  })}
                </div>
              )}

              {showChainFilter && showSortOptions && <div className="w-px h-5 bg-gray-200" />}

              {/* Sort */}
              {showSortOptions && sortOptions[tab]?.length > 0 && (
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-gray-400 uppercase tracking-wider mr-1">Sort</span>
                  {sortOptions[tab].map(([k, l]) => (
                    <button key={k} onClick={() => setSortBy(k)}
                      className={`text-xs px-2.5 py-1.5 rounded-lg transition font-medium ${
                        sortBy === k
                          ? 'bg-blue-50 text-blue-700 ring-1 ring-blue-200'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                      }`}>
                      {l}
                    </button>
                  ))}
                </div>
              )}

              {(showChainFilter || showSortOptions) && showTvlFilter && <div className="w-px h-5 bg-gray-200" />}

              {/* TVL filter */}
              {showTvlFilter && (
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-gray-400 uppercase tracking-wider mr-1">Min TVL</span>
                  {tvlPresets.map(p => (
                    <button key={p.value} onClick={() => setMinTvlFilter(p.value)}
                      className={`text-xs px-2.5 py-1.5 rounded-lg transition font-medium ${
                        minTvlFilter === p.value
                          ? 'bg-purple-50 text-purple-700 ring-1 ring-purple-200'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                      }`}>
                      {p.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Trending tab - Card Grid */}
        {tab === 'trending' && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Flame className="w-4 h-4 text-orange-500" />
                Trending Pools
                <span className="text-gray-400 font-normal">({sortedTrending.length})</span>
              </h3>
            </div>
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[1,2,3,4].map(i => (
                  <div key={i} className="bg-white border border-gray-100 rounded-xl p-4 animate-pulse">
                    <div className="h-4 bg-gray-100 rounded w-1/3 mb-3" />
                    <div className="grid grid-cols-3 gap-3">
                      <div className="h-8 bg-gray-100 rounded" />
                      <div className="h-8 bg-gray-100 rounded" />
                      <div className="h-8 bg-gray-100 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : sortedTrending.length === 0 ? (
              <div className="card p-8 text-center text-gray-400">No pools found</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sortedTrending.map((pool, i) => (
                  <PoolCard key={i} pool={pool} index={i} maxTvl={maxTvl} maxVol={maxVol}
                    onClick={() => setSelectedPool({ ...pool, network: pool.network || chain })} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Top Pools tab - Card Grid */}
        {tab === 'top' && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-500" />
                Top Pools by Volume
                <span className="text-gray-400 font-normal">({sortedTopPools.length})</span>
              </h3>
            </div>
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[1,2,3,4].map(i => (
                  <div key={i} className="bg-white border border-gray-100 rounded-xl p-4 animate-pulse">
                    <div className="h-4 bg-gray-100 rounded w-1/3 mb-3" />
                    <div className="grid grid-cols-3 gap-3">
                      <div className="h-8 bg-gray-100 rounded" />
                      <div className="h-8 bg-gray-100 rounded" />
                      <div className="h-8 bg-gray-100 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : sortedTopPools.length === 0 ? (
              <div className="card p-8 text-center text-gray-400">No pools found</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sortedTopPools.map((pool, i) => (
                  <PoolCard key={i} pool={pool} index={i} maxTvl={maxTvl} maxVol={maxVol}
                    onClick={() => setSelectedPool({ ...pool, network: pool.network || chain })} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Yields tab - Card Grid */}
        {tab === 'yields' && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Coins className="w-4 h-4 text-green-500" />
                Yield Pools
                <span className="text-gray-400 font-normal">({sortedYields.length})</span>
              </h3>
              <div className="text-xs text-gray-400">Min TVL: {minTvlFilter > 0 ? fmt(minTvlFilter) : '$0'}</div>
            </div>
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[1,2,3,4].map(i => (
                  <div key={i} className="bg-white border border-gray-100 rounded-xl p-4 animate-pulse">
                    <div className="h-4 bg-gray-100 rounded w-1/3 mb-3" />
                    <div className="grid grid-cols-3 gap-3">
                      <div className="h-8 bg-gray-100 rounded" />
                      <div className="h-8 bg-gray-100 rounded" />
                      <div className="h-8 bg-gray-100 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : sortedYields.length === 0 ? (
              <div className="card p-8 text-center text-gray-400">No yield pools found</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sortedYields.map((pool, i) => (
                  <YieldCard key={i} pool={pool} index={i}
                    onClick={() => setSelectedPool({ ...pool, network: pool.chain, name: pool.symbol })} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Hot Pairs tab - Card Grid */}
        {tab === 'hot' && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Zap className="w-4 h-4 text-yellow-500" />
                Hot DEX Pairs
                <span className="text-gray-400 font-normal">({sortedHotPairs.length})</span>
              </h3>
            </div>
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[1,2,3,4].map(i => (
                  <div key={i} className="bg-white border border-gray-100 rounded-xl p-4 animate-pulse">
                    <div className="h-4 bg-gray-100 rounded w-1/3 mb-3" />
                    <div className="grid grid-cols-3 gap-3">
                      <div className="h-8 bg-gray-100 rounded" />
                      <div className="h-8 bg-gray-100 rounded" />
                      <div className="h-8 bg-gray-100 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : sortedHotPairs.length === 0 ? (
              <div className="card p-8 text-center text-gray-400">No pairs found</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sortedHotPairs.map((pair, i) => (
                  <HotPairCard key={i} pair={pair} index={i} onClick={() => {}} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Market tab - Table (keeps original layout) */}
        {tab === 'market' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-500" />
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

        {/* Protocols tab - Table */}
        {tab === 'protocols' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Database className="w-4 h-4 text-purple-500" />
                Top DeFi Protocols
                <span className="text-gray-400 font-normal">({sortedProtocols.length})</span>
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
                        <div className="w-32"><MiniBar value={tvl} max={maxProtTvl} color="#16a34a" /></div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* L2 tab - Table */}
        {tab === 'l2' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-500" />
                L2 Ecosystem
                <span className="text-gray-400 font-normal">({sortedL2.length})</span>
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

        {/* Intelligence tab */}
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
      {selectedPool && (
        <PoolDetail pool={selectedPool} chain={selectedPool.network || chain} onClose={() => setSelectedPool(null)} />
      )}
    </div>
  )
}
