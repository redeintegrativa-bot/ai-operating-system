import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { FileText } from 'lucide-react'

export default function Logs() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getLogs(100).then(d => setLogs(Array.isArray(d) ? d : d?.logs || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader title="Logs" subtitle="System and agent logs" actions={<FileText className="w-5 h-5 text-primary-600" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div className="card overflow-hidden p-0">
          <div className="overflow-y-auto max-h-[600px]">
            {logs.length ? logs.map((l, i) => (
              <div key={i} className="flex items-start gap-3 px-4 py-2 border-b border-gray-50 last:border-0 text-sm font-mono">
                <StatusBadge status={l.level || 'info'} />
                <span className="text-gray-400 whitespace-nowrap">{l.timestamp ? new Date(l.timestamp).toLocaleTimeString() : ''}</span>
                <span className="flex-1 break-all">{l.message || JSON.stringify(l)}</span>
              </div>
            )) : <p className="text-gray-400 text-center py-12">No logs</p>}
          </div>
        </div>
      )}
    </div>
  )
}
