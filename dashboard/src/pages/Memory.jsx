import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { Brain, Search, Plus } from 'lucide-react'

export default function Memory() {
  const [memories, setMemories] = useState([])
  const [agent, setAgent] = useState('main')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ content: '', memory_type: 'episodic', keywords: '', importance: 0.5 })

  const load = () => {
    setLoading(true)
    api.getMemories(agent).then(d => setMemories(Array.isArray(d) ? d : d?.memories || [])).catch(() => setMemories([])).finally(() => setLoading(false))
  }
  useEffect(load, [agent])

  const typeColors = { episodic: 'badge-blue', semantic: 'badge-green', procedural: 'badge-yellow' }

  return (
    <div>
      <PageHeader
        title="Memory"
        subtitle={`${memories.length} memories for "${agent}"`}
        actions={
          <div className="flex items-center gap-2">
            <input value={agent} onChange={e => setAgent(e.target.value)} className="input w-36" placeholder="Agent name" />
            <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-1"><Plus className="w-4 h-4" /> Add</button>
          </div>
        }
      />
      {showForm && (
        <div className="card mb-4">
          <h3 className="font-semibold mb-3">Add Memory</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <textarea className="input" rows={2} placeholder="Content" value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} />
            <div className="space-y-2">
              <select className="input" value={form.memory_type} onChange={e => setForm({ ...form, memory_type: e.target.value })}>
                <option value="episodic">Episodic</option>
                <option value="semantic">Semantic</option>
                <option value="procedural">Procedural</option>
              </select>
              <input className="input" placeholder="Keywords (comma separated)" value={form.keywords} onChange={e => setForm({ ...form, keywords: e.target.value })} />
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            <button className="btn-primary" onClick={() => { setShowForm(false) }}>Save</button>
            <button className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </div>
      )}
      {loading ? <p className="text-gray-400">Loading...</p> : (
        memories.length ? (
          <div className="space-y-3">
            {memories.map((m, i) => (
              <div key={m.id || i} className="card py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`badge ${typeColors[m.memory_type] || 'badge-gray'}`}>{m.memory_type}</span>
                      <span className="text-xs text-gray-400">Importance: {Math.round((m.importance || 0) * 100)}%</span>
                      <span className="text-xs text-gray-400">Accessed: {m.access_count || 0}x</span>
                    </div>
                    <p className="text-sm mt-2">{typeof m.content === 'string' ? m.content : JSON.stringify(m.content)}</p>
                    {m.keywords?.length > 0 && (
                      <div className="flex gap-1 mt-2">{m.keywords.map((k, j) => <span key={j} className="badge badge-gray">{k}</span>)}</div>
                    )}
                  </div>
                  <span className="text-xs text-gray-400 whitespace-nowrap">{m.created_at ? new Date(m.created_at).toLocaleDateString() : ''}</span>
                </div>
              </div>
            ))}
          </div>
        ) : <p className="text-gray-400 text-center py-12">No memories found</p>
      )}
    </div>
  )
}
