import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { Puzzle, Power, ExternalLink } from 'lucide-react'

export default function Plugins() {
  const [plugins, setPlugins] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getPlugins().then(d => setPlugins(Array.isArray(d) ? d : d?.plugins || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader title="Plugins" subtitle={`${plugins.length} installed plugins and extensions`} actions={<Puzzle className="w-5 h-5 text-primary-600" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        plugins.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {plugins.map((p, i) => (
              <div key={p.id || i} className="card">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{p.name}</h3>
                      <span className="text-xs text-gray-400">v{p.version}</span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{p.description}</p>
                    <div className="flex items-center gap-3 mt-3">
                      <span className="badge badge-gray">{p.vendor}</span>
                      <StatusBadge status={p.enabled ? 'online' : 'offline'} />
                    </div>
                  </div>
                  <button className={`p-2 rounded-lg transition-colors ${p.enabled ? 'bg-green-50 text-green-600 hover:bg-green-100' : 'bg-gray-50 text-gray-400 hover:bg-gray-100'}`}>
                    <Power className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : <p className="text-gray-400 text-center py-12">No plugins installed</p>
      )}
    </div>
  )
}
