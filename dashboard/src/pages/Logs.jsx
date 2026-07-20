import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { FileText, RefreshCcw, AlertCircle, Info, AlertTriangle } from 'lucide-react'

const levelIcon = { ERROR: AlertCircle, WARNING: AlertTriangle, INFO: Info }

export default function Logs() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [count, setCount] = useState(100)

  const load = () => {
    setLoading(true)
    api.getLogs(count).then(d => setLogs(Array.isArray(d) ? d : d?.logs || [])).catch(() => setLogs([])).finally(() => setLoading(false))
  }
  useEffect(load, [count])

  const filtered = filter === 'all' ? logs : logs.filter(l => l.level?.toLowerCase() === filter)

  return (
    <div>
      <PageHeader
        title="Logs"
        subtitle={`${filtered.length} entries`}
        actions={
          <div className="flex items-center gap-2">
            <select className="input w-32" value={filter} onChange={e => setFilter(e.target.value)}>
              <option value="all">All levels</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
            <select className="input w-28" value={count} onChange={e => setCount(Number(e.target.value))}>
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
              <option value={500}>500</option>
            </select>
            <button onClick={load} className="btn-secondary"><RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /></button>
          </div>
        }
      />
      <div className="card overflow-hidden p-0">
        <div className="overflow-y-auto max-h-[700px]">
          {filtered.length ? filtered.map((l, i) => {
            const Icon = levelIcon[l.level] || Info
            return (
              <div key={i} className={`flex items-start gap-3 px-4 py-2.5 border-b border-gray-50 last:border-0 text-sm font-mono hover:bg-gray-50 ${l.level === 'ERROR' ? 'bg-red-50/50' : ''}`}>
                <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${l.level === 'ERROR' ? 'text-red-500' : l.level === 'WARNING' ? 'text-yellow-500' : 'text-blue-400'}`} />
                <span className="text-gray-400 whitespace-nowrap text-xs mt-0.5">{l.time ? new Date(l.time).toLocaleTimeString() : ''}</span>
                <span className="text-gray-400 whitespace-nowrap text-xs mt-0.5 w-24">{l.source}</span>
                <span className="flex-1 break-all">{l.message}</span>
              </div>
            )
          }) : <p className="text-gray-400 text-center py-12">No logs</p>}
        </div>
      </div>
    </div>
  )
}
