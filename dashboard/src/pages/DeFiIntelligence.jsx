import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import MetricCard from '../components/MetricCard'
import DataTable from '../components/DataTable'
import { Coins, TrendingUp, TrendingDown, DollarSign, Wallet, ArrowUpRight, ArrowDownRight } from 'lucide-react'

export default function DeFiIntelligence() {
  const [finances, setFinances] = useState({})
  const [analytics, setAnalytics] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([api.getFinances(), api.getAnalytics()])
      .then(([f, a]) => {
        setFinances(f.status === 'fulfilled' ? f.value : {})
        setAnalytics(a.status === 'fulfilled' ? a.value : {})
      })
      .finally(() => setLoading(false))
  }, [])

  const txColumns = [
    { key: 'description', label: 'Description' },
    { key: 'amount', label: 'Amount', render: (v, row) => (
      <span className={`font-medium ${row.category === 'income' ? 'text-green-600' : 'text-red-500'}`}>
        {row.category === 'income' ? '+' : '-'}${v?.toLocaleString()}
      </span>
    )},
    { key: 'category', label: 'Type', render: (v) => (
      <span className={`badge ${v === 'income' ? 'badge-green' : 'badge-red'}`}>{v}</span>
    )},
    { key: 'date', label: 'Date', render: (v) => v ? new Date(v).toLocaleDateString() : '--' },
  ]

  return (
    <div>
      <PageHeader title="DeFi Intelligence" subtitle="Decentralized finance monitoring and analytics" actions={<Coins className="w-5 h-5 text-primary-600" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard title="Total Income" value={`$${(finances.total_income || 0).toLocaleString()}`} icon={TrendingUp} color="green" trend="up" />
            <MetricCard title="Total Expenses" value={`$${(finances.total_expense || 0).toLocaleString()}`} icon={TrendingDown} color="red" trend="down" />
            <MetricCard title="Balance" value={`$${(finances.balance || 0).toLocaleString()}`} icon={Wallet} color="primary" />
            <MetricCard title="Active Sessions" value={analytics.active_sessions || 0} icon={DollarSign} color="blue" />
          </div>
          <div className="card">
            <h3 className="font-semibold mb-4">Recent Transactions</h3>
            <DataTable columns={txColumns} data={finances.transactions || []} emptyMessage="No transactions" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="font-semibold mb-3">Daily Requests (30d)</h3>
              <div className="flex items-end gap-1 h-32">
                {(analytics.daily_requests || []).map((v, i) => {
                  const max = Math.max(...(analytics.daily_requests || [1]))
                  return <div key={i} className="flex-1 bg-primary-200 rounded-t" style={{ height: `${(v / max) * 100}%` }} />
                })}
              </div>
            </div>
            <div className="card">
              <h3 className="font-semibold mb-3">Top Activities</h3>
              <div className="space-y-2">
                {(analytics.top_habits || []).map((h, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-sm">{h}</span>
                    <div className="w-24 bg-gray-100 rounded-full h-2">
                      <div className="bg-primary-500 h-2 rounded-full" style={{ width: `${100 - i * 20}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
