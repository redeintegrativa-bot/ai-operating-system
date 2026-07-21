import { useState, useEffect } from 'react'
import { api } from '../api/client'
import {
  X, ExternalLink, TrendingUp, TrendingDown, Droplets, Activity,
  DollarSign, BarChart3, ArrowUpDown, Clock, RefreshCw, Layers
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

function fmtPrice(n) {
  if (n == null || isNaN(n)) return '--'
  const v = Number(n)
  if (v >= 1) return `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  if (v >= 0.01) return `$${v.toFixed(4)}`
  return `$${v.toFixed(8)}`
}

function pct(n) {
  if (n == null || isNaN(n)) return '--'
  const v = Number(n)
  return `${v > 0 ? '+' : ''}${v.toFixed(2)}%`
}

function Sparkline({ data, width = 300, height = 80, color }) {
  if (!data || data.length < 2) return null
  const values = data.map(d => d.c || d)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * width
    const y = height - ((v - min) / range) * (height - 10) - 5
    return `${x},${y}`
  }).join(' ')

  const isUp = values[values.length - 1] >= values[0]
  const lineColor = color || (isUp ? '#16a34a' : '#ef4444')
  const fillColor = isUp ? 'rgba(22,163,74,0.1)' : 'rgba(239,68,68,0.1)'

  const areaPoints = `0,${height} ${points} ${width},${height}`

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
      <defs>
        <linearGradient id={`grad-${isUp ? 'up' : 'down'}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={lineColor} stopOpacity="0.2" />
          <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill={`url(#grad-${isUp ? 'up' : 'down'})`} />
      <polyline points={points} fill="none" stroke={lineColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={(values.length - 1) / (values.length - 1) * width} cy={height - ((values[values.length - 1] - min) / range) * (height - 10) - 5} r="3" fill={lineColor} />
    </svg>
  )
}

function VolumeBar({ data, width = 300, height = 40 }) {
  if (!data || data.length === 0) return null
  const volumes = data.map(d => d.v || 0)
  const maxVol = Math.max(...volumes)
  const barWidth = Math.max(width / volumes.length - 1, 2)

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
      {volumes.map((v, i) => {
        const barH = maxVol > 0 ? (v / maxVol) * (height - 4) : 0
        const x = (i / volumes.length) * width
        return <rect key={i} x={x} y={height - barH} width={barWidth} height={barH} rx="1" fill="rgba(37,99,235,0.4)" />
      })}
    </svg>
  )
}

function Metric({ label, value, icon: Icon, color = 'text-gray-700', sub }) {
  return (
    <div className="flex items-start gap-2">
      {Icon && <Icon className={`w-4 h-4 mt-0.5 ${color}`} />}
      <div>
        <div className="text-xs text-gray-400">{label}</div>
        <div className={`text-sm font-semibold ${color}`}>{value}</div>
        {sub && <div className="text-[10px] text-gray-400">{sub}</div>}
      </div>
    </div>
  )
}

export default function PoolDetail({ pool, chain, onClose }) {
  const [detail, setDetail] = useState(null)
  const [ohlcv, setOhlcv] = useState([])
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState('day')

  const name = pool.name || ''
  const [base, quote] = name.includes('/') ? name.split(' / ').map(s => s.trim()) : [name, '']
  const network = pool.network || chain || 'eth'

  useEffect(() => {
    if (!pool.address) { setLoading(false); return }
    setLoading(true)
    api.getDeFiPoolDetail(network, pool.address, timeframe)
      .then(r => {
        setDetail(r?.info || {})
        setOhlcv(r?.ohlcv || [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [pool.address, network, timeframe])

  const tvl = Number(pool.reserve_in_usd || detail?.reserve_in_usd || 0)
  const vol24 = Number(pool.volume_usd_24h || detail?.volume_usd?.h24 || 0)
  const change24 = Number(pool.price_change_24h_pct || detail?.price_change_percentage?.h24 || 0)
  const change7d = Number(detail?.price_change_percentage?.h7 || 0)
  const change1h = Number(detail?.price_change_percentage?.h1 || 0)
  const txns = pool.transactions_24h || detail?.transactions?.h24 || {}
  const buys = typeof txns === 'object' ? (txns.buys || 0) : 0
  const sells = typeof txns === 'object' ? (txns.sells || 0) : 0
  const totalTxns = buys + sells
  const buyRatio = totalTxns > 0 ? (buys / totalTxns * 100) : 50
  const fdv = Number(detail?.fdv_usd || 0)
  const dex = pool.dex || detail?.dex_id || ''
  const createdAt = detail?.pool_created_at || ''

  const changeColor = change24 > 0 ? 'text-green-600' : change24 < 0 ? 'text-red-500' : 'text-gray-500'

  const timeframes = [
    { key: 'minute', label: '1H' },
    { key: 'hour', label: '1D' },
    { key: 'day', label: '1W' },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto mx-4" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between rounded-t-2xl z-10">
          <div className="flex items-center gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold">{base}</h2>
                {quote && <span className="text-gray-400">/ {quote}</span>}
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <span className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">{network}</span>
                {dex && <span className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">{dex}</span>}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <a href={`https://www.geckoTerminal.com/${network}/${name?.replace(' / ', '-')}`}
               target="_blank" rel="noopener noreferrer"
               className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 transition">
              <ExternalLink className="w-3 h-3" />
              GeckoTerminal
            </a>
            <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 transition">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="px-6 py-5 space-y-6">
          {/* Price + Change */}
          <div className="flex items-end gap-4">
            <div>
              <div className="text-xs text-gray-400 mb-1">Base Price</div>
              <div className="text-2xl font-bold">{fmtPrice(detail?.base_token_price_usd || pool.base_token_price_usd)}</div>
            </div>
            <div className={`text-lg font-bold ${changeColor}`}>
              {pct(change24)}
            </div>
            <div className="text-xs text-gray-400 mb-1">24h</div>
          </div>

          {/* Timeframe Selector + Chart */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-400">Price Chart</span>
              <div className="flex bg-gray-100 rounded-lg p-0.5">
                {timeframes.map(tf => (
                  <button key={tf.key} onClick={() => setTimeframe(tf.key)}
                    className={`text-xs px-2.5 py-1 rounded-md transition ${timeframe === tf.key ? 'bg-white shadow text-gray-900 font-medium' : 'text-gray-500 hover:text-gray-700'}`}>
                    {tf.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="bg-gray-50 rounded-xl p-4" style={{ height: 120 }}>
              {loading ? (
                <div className="flex items-center justify-center h-full text-gray-400 text-xs">
                  <RefreshCw className="w-3 h-3 animate-spin mr-1" /> Loading chart...
                </div>
              ) : ohlcv.length > 1 ? (
                <Sparkline data={ohlcv} width={500} height={100} />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{fmtPrice(pool.base_token_price_usd)}</div>
                    <div className="text-xs text-gray-400">Current price (no chart data available)</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Volume Chart */}
          {ohlcv.length > 1 && (
            <div>
              <div className="text-xs text-gray-400 mb-2">Volume</div>
              <div className="bg-gray-50 rounded-xl p-4" style={{ height: 60 }}>
                <VolumeBar data={ohlcv} width={500} height={50} />
              </div>
            </div>
          )}

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Metric label="Liquidity (TVL)" value={fmt(tvl)} icon={Droplets} color="text-blue-600" />
            <Metric label="Volume 24h" value={fmt(vol24)} icon={BarChart3} color="text-green-600" />
            <Metric label="FDV" value={fmt(fdv)} icon={Layers} color="text-purple-600" />
            <Metric label="Vol/Liq Ratio" value={tvl > 0 ? `${(vol24 / tvl * 100).toFixed(1)}%` : '--'} icon={ArrowUpDown} color="text-amber-600" />
          </div>

          {/* Time Changes */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-xl">
              <div className="text-xs text-gray-400">1h</div>
              <div className={`text-sm font-bold ${change1h > 0 ? 'text-green-600' : change1h < 0 ? 'text-red-500' : 'text-gray-500'}`}>
                {pct(change1h)}
              </div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-xl">
              <div className="text-xs text-gray-400">24h</div>
              <div className={`text-sm font-bold ${change24 > 0 ? 'text-green-600' : change24 < 0 ? 'text-red-500' : 'text-gray-500'}`}>
                {pct(change24)}
              </div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-xl">
              <div className="text-xs text-gray-400">7d</div>
              <div className={`text-sm font-bold ${change7d > 0 ? 'text-green-600' : change7d < 0 ? 'text-red-500' : 'text-gray-500'}`}>
                {pct(change7d)}
              </div>
            </div>
          </div>

          {/* Transactions */}
          {totalTxns > 0 && (
            <div>
              <div className="text-xs text-gray-400 mb-2">24h Transactions</div>
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-green-600 font-medium">Buys: {buys.toLocaleString()}</span>
                  <span className="text-xs text-red-500 font-medium">Sells: {sells.toLocaleString()}</span>
                </div>
                <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden flex">
                  <div className="h-full bg-green-500 rounded-l-full transition-all duration-500"
                       style={{ width: `${buyRatio}%` }} />
                  <div className="h-full bg-red-400 rounded-r-full transition-all duration-500"
                       style={{ width: `${100 - buyRatio}%` }} />
                </div>
                <div className="flex items-center justify-between mt-1.5 text-[10px] text-gray-400">
                  <span>Buy pressure: {buyRatio.toFixed(0)}%</span>
                  <span>{totalTxns.toLocaleString()} total txns</span>
                </div>
              </div>
            </div>
          )}

          {/* Pool Info */}
          {createdAt && (
            <div className="text-xs text-gray-400 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Created: {new Date(createdAt).toLocaleDateString()}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
