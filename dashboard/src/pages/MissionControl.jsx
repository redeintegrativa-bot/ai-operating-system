import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { Radio } from 'lucide-react'

export default function MissionControl() {
  const [missions, setMissions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getMissions().then(d => setMissions(Array.isArray(d) ? d : d?.missions || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader title="Mission Control" subtitle="Monitor and manage active missions" actions={<Radio className="w-5 h-5 text-primary-600" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        missions.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {missions.map((m, i) => (
              <div key={m.id || i} className="card">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{m.name || m.title || `Mission ${i + 1}`}</h3>
                  <StatusBadge status={m.status} />
                </div>
                <p className="text-sm text-gray-500">{m.description || 'No description'}</p>
              </div>
            ))}
          </div>
        ) : <p className="text-gray-400 text-center py-12">No active missions</p>
      )}
    </div>
  )
}
