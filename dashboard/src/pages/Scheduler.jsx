import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { Clock, Plus, Play, Pause, Trash2 } from 'lucide-react'

export default function Scheduler() {
  const [missions, setMissions] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', agent_name: '', description: '', interval_seconds: 3600 })

  const load = () => {
    setLoading(true)
    api.getMissions().then(d => setMissions(Array.isArray(d) ? d : d?.missions || [])).catch(() => setMissions([])).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const fmtInterval = (s) => {
    if (!s) return '--'
    if (s < 60) return `${s}s`
    if (s < 3600) return `${Math.round(s / 60)}m`
    return `${Math.round(s / 3600)}h`
  }

  return (
    <div>
      <PageHeader
        title="Scheduler"
        subtitle="Task scheduling and cron management"
        actions={
          <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> New Mission
          </button>
        }
      />
      {showForm && (
        <div className="card mb-6">
          <h3 className="font-semibold mb-4">New Scheduled Mission</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input className="input" placeholder="Mission name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
            <input className="input" placeholder="Agent name" value={form.agent_name} onChange={e => setForm({ ...form, agent_name: e.target.value })} />
            <input className="input" placeholder="Description" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
            <select className="input" value={form.interval_seconds} onChange={e => setForm({ ...form, interval_seconds: Number(e.target.value) })}>
              <option value={60}>Every minute</option>
              <option value={300}>Every 5 minutes</option>
              <option value={900}>Every 15 minutes</option>
              <option value={3600}>Every hour</option>
              <option value={86400}>Every day</option>
            </select>
          </div>
          <div className="flex gap-2 mt-4">
            <button className="btn-primary" onClick={() => { setShowForm(false); setForm({ name: '', agent_name: '', description: '', interval_seconds: 3600 }) }}>Create</button>
            <button className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </div>
      )}
      {loading ? <p className="text-gray-400">Loading...</p> : (
        missions.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {missions.map((m, i) => (
              <div key={m.id || i} className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold">{m.name}</h3>
                    <p className="text-sm text-gray-500 mt-1">{m.description || 'No description'}</p>
                    <div className="flex items-center gap-3 mt-3 text-xs text-gray-400">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {fmtInterval(m.interval_seconds)}</span>
                      <span>Agent: {m.agent_name || 'any'}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={m.enabled ? 'online' : 'offline'} />
                    <button className="p-1 hover:bg-gray-100 rounded"><Play className="w-4 h-4 text-green-600" /></button>
                    <button className="p-1 hover:bg-gray-100 rounded"><Pause className="w-4 h-4 text-yellow-600" /></button>
                    <button className="p-1 hover:bg-gray-100 rounded"><Trash2 className="w-4 h-4 text-red-500" /></button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : <div className="card text-center py-12 text-gray-400"><Clock className="w-12 h-12 mx-auto mb-4 opacity-50" /><p>No scheduled missions</p></div>
      )}
    </div>
  )
}
