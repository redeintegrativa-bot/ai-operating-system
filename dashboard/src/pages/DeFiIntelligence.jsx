import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import MetricCard from '../components/MetricCard'
import { Coins, TrendingUp, BarChart3 } from 'lucide-react'

export default function DeFiIntelligence() {
  const [finances, setFinances] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getFinances().then(d => setFinances(d || {})).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader title="DeFi Intelligence" subtitle="Decentralized finance monitoring" actions={<Coins className="w-5 h-5 text-primary-600" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <MetricCard title="Portfolio Value" value={finances.portfolio_value || '--'} icon={Coins} color="green" />
            <MetricCard title="Daily P&L" value={finances.daily_pnl || '--'} icon={TrendingUp} color={finances.daily_pnl?.startsWith('-') ? 'red' : 'green'} />
            <MetricCard title="Active Positions" value={finances.active_positions || '0'} icon={BarChart3} color="blue" />
          </div>
          <div className="card text-center py-12 text-gray-400">DeFi intelligence dashboard</div>
        </div>
      )}
    </div>
  )
}
