import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { Link2, Star, ShoppingCart } from 'lucide-react'

export default function Integrations() {
  const [tab, setTab] = useState('tools')
  const [tools, setTools] = useState([])
  const [marketplace, setMarketplace] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([api.getTools(), api.getMarketplace()])
      .then(([t, m]) => {
        setTools(t.status === 'fulfilled' ? (Array.isArray(t.value) ? t.value : t.value?.tools || []) : [])
        setMarketplace(m.status === 'fulfilled' ? (Array.isArray(m.value) ? m.value : m.value?.marketplace || []) : [])
      })
      .finally(() => setLoading(false))
  }, [])

  const items = tab === 'tools' ? tools : marketplace

  return (
    <div>
      <PageHeader title="Integrations" subtitle="External tools, services, and marketplace" actions={<Link2 className="w-5 h-5 text-primary-600" />} />
      <div className="flex gap-2 mb-6">
        <button onClick={() => setTab('tools')} className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === 'tools' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>Tools</button>
        <button onClick={() => setTab('marketplace')} className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === 'marketplace' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>Marketplace</button>
      </div>
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((t, i) => (
            <div key={t.id || t.name || i} className="card">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-sm">{t.icon ? `${t.icon} ` : ''}{t.name}</h3>
                  <p className="text-xs text-gray-500 mt-1">{t.description}</p>
                  <div className="flex items-center gap-2 mt-3">
                    {t.category && <span className="badge badge-gray">{t.category}</span>}
                    {t.vendor && <span className="badge badge-blue">{t.vendor}</span>}
                    {t.complexity && <span className="badge badge-yellow">{t.complexity}</span>}
                  </div>
                </div>
                {tab === 'marketplace' ? (
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-yellow-500 text-sm">
                      <Star className="w-3 h-3 fill-current" /> {t.rating}
                    </div>
                    <div className="flex items-center gap-1 text-gray-400 text-xs mt-1">
                      <span>{t.likes} likes</span>
                    </div>
                  </div>
                ) : (
                  <StatusBadge status={t.status || 'info'} />
                )}
              </div>
            </div>
          ))}
          {!items.length && <p className="text-gray-400 text-center py-12 col-span-full">No items found</p>}
        </div>
      )}
    </div>
  )
}
