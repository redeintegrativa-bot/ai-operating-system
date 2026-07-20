import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { Link2 } from 'lucide-react'

export default function Integrations() {
  const [tools, setTools] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getTools().then(d => setTools(Array.isArray(d) ? d : d?.tools || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader title="Integrations" subtitle="External tools and integrations" actions={<Link2 className="w-5 h-5 text-primary-600" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        tools.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tools.map((t, i) => (
              <div key={t.name || i} className="card">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{t.name}</h3>
                  <StatusBadge status={t.status || 'info'} />
                </div>
                <p className="text-sm text-gray-500">{t.description || 'No description'}</p>
              </div>
            ))}
          </div>
        ) : <p className="text-gray-400 text-center py-12">No integrations found</p>
      )}
    </div>
  )
}
