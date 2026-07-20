import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { Map } from 'lucide-react'

export default function CapabilityMap() {
  const [capabilities, setCapabilities] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getCapabilities().then(d => setCapabilities(Array.isArray(d) ? d : d?.capabilities || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader title="Capability Map" subtitle="System capabilities and their status" actions={<Map className="w-5 h-5 text-primary-600" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        capabilities.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {capabilities.map((c, i) => (
              <div key={c.name || i} className="card">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{c.name || c.title}</h3>
                  <StatusBadge status={c.status || 'info'} />
                </div>
                <p className="text-sm text-gray-500">{c.description || 'No description'}</p>
              </div>
            ))}
          </div>
        ) : <p className="text-gray-400 text-center py-12">No capabilities found</p>
      )}
    </div>
  )
}
