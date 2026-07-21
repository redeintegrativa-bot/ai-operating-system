import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import { Coins, TrendingUp, TrendingDown, Droplets, Shield, ExternalLink, RefreshCw, ArrowUpDown, Zap, BarChart3, Activity } from 'lucide-react'

function fmt(n, decimals = 0) {
  if (n == null || isNaN(n)) return '--'
  const v = Number(n)
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `$${(v / 1e3).toFixed(1)}K`
  return `$${v.toFixed(decimals)}`
}

function pct(n) {
  if (n == null || isNaN(n)) return '--'
  const v = Number(n)
  const color = v > 0 ? 'text-green-600' : v < 0 ? 'text-red-500' : 'text-gray-500'
  return <span className={color}>{v > 0 ? '+' : ''}{v.toFixed(2)}%</span>
}

function ChainBadge({ chain }) {
  const colors = {
    ethereum: 'bg-blue-100 text-blue-700',
    base: 'bg-blue-50 text-blue-600',
    arbitrum: 'bg-blue-100 text-blue-800',
    bsc: 'bg-yellow-100 text-yellow-700',
    polygon: 'bg-purple-100 text-purple-700',
    optimism: 'bg-red-100 text-red-600',
    avalanche: 'bg-red-50 text-red-700',
    solana: 'bg-green-100 text-green-700',
  }
  const c = colors[chain?.toLowerCase()] || 'bg-gray-100 text-gray-600'
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${c}`}>{chain || '?'}</span>
}

function IlBadge({ risk }) {
  if (risk === 'yes') return <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 font-medium">IL Risk</span>
  return <span className="text-xs px-1.5 py-0.5 rounded bg-green-50 text-green-600">No IL</span>
}

function StatBox({ label, value, icon: Icon, color = 'primary' }) {
  const colors = { primary: 'text-blue-600', green: 'text-green-600', red: 'text-red-500', amber: 'text-amber-600' }
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

export default function DeFiIntelligence() {
  const [tab, setTab] = useState('trending')
  const [trending, setTrending] = useState([])
  const [yields, setYields] = useState([])
  const [overview, setOverview] = useState({})
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [chain, setChain] = useState('ethereum')
  const [sortBy, setSortBy] = useState('volume')

  const fetchAll = () => {
    setRefreshing(true)
    Promise.allSettled([
      api.request?.('GET', `/api/defi/trending-pools?chain=${chain}`) || fetch(`/api/defi/trending-pools?chain=${chain}`).then(r => r.json()),
      api.request?.('GET', `/api/defi/yields?chain=${chain}&min_tvl=50000`) || fetch(`/api/defi/yields?chain=${chain}&min_tvl=50000`).then(r => r.json()),
      api.request?.('GET', '/api/defi/overview') || fetch('/api/defi/overview').then(r => r.json()),
    ]).then(([t, y, o]) => {
      if (t.status === 'fulfilled') setTrending(t.value?.pools || [])
      if (y.status === 'fulfilled') setYields(y.value?.pools || [])
      if (o.status === 'fulfilled') setOverview(o.value || {})
    }).finally(() => { setLoading(false); setRefreshing(false) })
  }

  useEffect(() => { fetchAll() }, [chain])

  const sortedTrending = [...trending].sort((a, b) => {
    if (sortBy === 'volume') return Number(b.volume_usd_24h || 0) - Number(a.volume_usd_24h || 0)
    if (sortBy === 'tvl') return Number(b.reserve_in_usd || 0) - Number(a.reserve_in_usd || 0)
    if (sortBy === 'change') return Number(b.price_change_24h_pct || 0) - Number(a.price_change_24h_pct || 0)
    return 0
  })

  const sortedYields = [...yields].sort((a, b) => {
    if (sortBy === 'apy') return Number(b.apy_total || 0) - Number(a.apy_total || 0)
    if (sortBy === 'tvl') return Number(b.tvl_usd || 0) - Number(a.tvl_usd || 0)
    return 0
  })

  const stats = overview.stats || {}
  const chains = ['ethereum', 'base', 'arbitrum', 'bsc', 'polygon', 'solana']

  return (
    <div>
      <PageHeader
        title="DeFi Intelligence"
        subtitle="Liquidity pools, yields, and DEX analytics"
        actions={
          <button onClick={fetchAll} className="p-2 rounded-lg hover:bg-gray-100" disabled={refreshing}>
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        }
      />

      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatBox label="Pools Tracked" value={(stats.pool_count || 0).toLocaleString()} icon={Droplets} />
          <StatBox label="Total TVL" value={fmt(stats.total_tvl)} icon={BarChart3} color="green" />
          <StatBox label="Avg APY" value={`${(stats.avg_apy || 0).toFixed(1)}%`} icon={TrendingUp} color="green" />
          <StatBox label="Trending" value={trending.length} icon={Zap} color="amber" />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            {chains.map(c => (
              <button key={c} onClick={() => setChain(c)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition ${chain === c ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}>
                {c.charAt(0).toUpperCase() + c.slice(1)}
              </button>
            ))}
          </div>
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            <button onClick={() => setTab('trending')} className={`px-3 py-1.5 text-xs font-medium rounded-md transition ${tab === 'trending' ? 'bg-white shadow text-gray-900' : 'text-gray-500'}`}>Trending</button>
            <button onClick={() => setTab('yields')} className={`px-3 py-1.5 text-xs font-medium rounded-md transition ${tab === 'yields' ? 'bg-white shadow text-gray-900' : 'text-gray-500'}`}>Yields</button>
          </div>
        </div>

        {tab === 'trending' && (
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-sm">Trending Pools</h3>
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
              <div className="p-8 text-center text-gray-400">No pools found for this chain</div>
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
                          {pool.dex && <span className="text-xs text-gray-400">{pool.dex}</span>}
                        </div>
                        <a href={`https://dexscreener.com/${pool.network || 'ethereum'}/${pool.name?.replace('/', '-')}`}
                           target="_blank" rel="noopener noreferrer"
                           className="text-gray-400 hover:text-blue-500">
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </div>
                      <div className="grid grid-cols-5 gap-2 text-xs">
                        <div>
                          <div className="text-gray-400">Liquidity</div>
                          <div className="font-medium">{fmt(tvl)}</div>
                        </div>
                        <div>
                          <div className="text-gray-400">Volume 24h</div>
                          <div className="font-medium">{fmt(vol)}</div>
                        </div>
                        <div>
                          <div className="text-gray-400">Vol/TVL</div>
                          <div className="font-medium">{volTvlRatio}%</div>
                        </div>
                        <div>
                          <div className="text-gray-400">24h Change</div>
                          <div className="font-medium">{pct(change)}</div>
                        </div>
                        <div>
                          <div className="text-gray-400">Txns 24h</div>
                          <div className="font-medium">{txns.toLocaleString()}</div>
                        </div>
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
              <h3 className="font-semibold text-sm">Top Yield Pools</h3>
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
                  const apyBase = Number(pool.apy_base || 0)
                  const apyReward = Number(pool.apy_reward || 0)
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
                          <IlBadge risk={pool.il_risk} />
                        </div>
                        <div className={`text-lg font-bold ${apyColor}`}>
                          {apy.toFixed(1)}%
                        </div>
                      </div>
                      <div className="grid grid-cols-4 gap-2 text-xs">
                        <div>
                          <div className="text-gray-400">Base APY</div>
                          <div className="font-medium">{apyBase.toFixed(1)}%</div>
                        </div>
                        <div>
                          <div className="text-gray-400">Reward APY</div>
                          <div className="font-medium">{apyReward.toFixed(1)}%</div>
                        </div>
                        <div>
                          <div className="text-gray-400">TVL</div>
                          <div className="font-medium">{fmt(tvl)}</div>
                        </div>
                        <div>
                          <div className="text-gray-400">Pool ID</div>
                          <div className="font-medium text-gray-400 truncate">{pool.pool?.slice(0, 12)}...</div>
                        </div>
                      </div>
                      {apy > 0 && tvl > 0 && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-100 rounded-full h-1.5">
                            <div className="h-1.5 rounded-full transition-all" style={{
                              width: `${Math.min(apy / 2, 100)}%`,
                              backgroundColor: apy > 20 ? '#16a34a' : apy > 5 ? '#2563eb' : '#9ca3af'
                            }} />
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
