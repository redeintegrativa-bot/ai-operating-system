import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { Users, Zap, Brain } from 'lucide-react'

export default function Agents() {
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getAgents().then(d => setAgents(Array.isArray(d) ? d : d?.agents || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader title="Agents" subtitle={`${agents.length} registered agents`} actions={<Users className="w-5 h-5 text-primary-600" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        agents.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((a, i) => (
              <div key={a.name || a.id || i} className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold capitalize">{(a.name || '').replace(/_/g, ' ')}</h3>
                      <StatusBadge status={a.status} />
                    </div>
                    <div className="mt-2 text-sm text-gray-500">
                      <div className="flex items-center gap-1"><Zap className="w-3 h-3" /> Tasks: {a.tasks_completed || 0}</div>
                    </div>
                  </div>
                  <div className="w-10 h-10 bg-primary-50 rounded-xl flex items-center justify-center">
                    <Brain className="w-5 h-5 text-primary-600" />
                  </div>
                </div>
                {a.capabilities?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-3">
                    {a.capabilities.map((c, j) => <span key={j} className="badge badge-gray">{c}</span>)}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : <p className="text-gray-400 text-center py-12">No agents found</p>
      )}
    </div>
  )
}
