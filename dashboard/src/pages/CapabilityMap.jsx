import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { Map, Box, Cpu, Globe, Wrench } from 'lucide-react'

const catIcons = { core: Cpu, agents: Box, api: Globe, utils: Wrench }

export default function CapabilityMap() {
  const [caps, setCaps] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getCapabilities().then(d => setCaps(d)).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const categories = caps?.categories || {}
  const totalCaps = caps?.totalCapabilities || 0

  return (
    <div>
      <PageHeader
        title="Capability Map"
        subtitle={`${totalCaps} capabilities across ${Object.keys(categories).length} categories`}
        actions={<Map className="w-5 h-5 text-primary-600" />}
      />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div className="space-y-6">
          {Object.entries(categories).map(([key, cat]) => {
            const Icon = catIcons[key] || Box
            return (
              <div key={key}>
                <div className="flex items-center gap-2 mb-3">
                  <Icon className="w-5 h-5 text-primary-600" />
                  <h2 className="text-lg font-semibold">{cat.label}</h2>
                  <span className="text-xs text-gray-400 ml-2">{cat.items?.length || 0} items</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {(cat.items || []).map((item) => (
                    <div key={item.id} className="card py-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-medium text-sm">{item.name}</h3>
                          <p className="text-xs text-gray-500 mt-1">{item.description}</p>
                        </div>
                        <StatusBadge status={item.status === 'implementado' ? 'online' : item.status === 'parcial' ? 'warning' : 'offline'} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
          {!Object.keys(categories).length && <p className="text-gray-400 text-center py-12">No capabilities found</p>}
        </div>
      )}
    </div>
  )
}
