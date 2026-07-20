import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import DataTable from '../components/DataTable'
import { Plus, Trash2 } from 'lucide-react'

export default function Tasks() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ description: '', priority: 'medium' })

  const load = () => {
    setLoading(true)
    const params = filter ? { status: filter } : {}
    api.getTasks(params).then(d => setTasks(Array.isArray(d) ? d : d?.tasks || [])).catch(() => setTasks([])).finally(() => setLoading(false))
  }
  useEffect(load, [filter])

  const create = async () => {
    if (!form.description.trim()) return
    try {
      await api.createTask(form)
      setShowForm(false)
      setForm({ description: '', priority: 'medium' })
      load()
    } catch {}
  }

  const remove = async (id) => {
    try { await api.deleteTask(id); load() } catch {}
  }

  const columns = [
    { key: 'description', label: 'Task', render: (v, row) => (
      <div>
        <p className="text-sm font-medium">{v || row.title || row.id}</p>
        {row.assigned_agent && <p className="text-xs text-gray-400">Agent: {row.assigned_agent}</p>}
      </div>
    )},
    { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
    { key: 'priority', label: 'Priority', render: (v) => {
      const c = { critical: 'text-red-600', high: 'text-orange-500', medium: 'text-blue-600', low: 'text-gray-400' }
      return <span className={`text-sm font-medium ${c[v] || ''}`}>{v}</span>
    }},
    { key: 'created_at', label: 'Created', render: (v) => v ? new Date(v).toLocaleDateString() : '--' },
    { key: 'id', label: '', render: (v) => (
      <button onClick={(e) => { e.stopPropagation(); remove(v) }} className="p-1 hover:bg-red-50 rounded"><Trash2 className="w-4 h-4 text-red-400" /></button>
    )},
  ]

  return (
    <div>
      <PageHeader
        title="Tasks"
        subtitle={`${tasks.length} tasks`}
        actions={
          <div className="flex items-center gap-2">
            <select className="input w-36" value={filter} onChange={e => setFilter(e.target.value)}>
              <option value="">All statuses</option>
              <option value="created">Created</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
            <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-1"><Plus className="w-4 h-4" /> New Task</button>
          </div>
        }
      />
      {showForm && (
        <div className="card mb-4">
          <div className="flex gap-3">
            <input className="input flex-1" placeholder="Task description" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} onKeyDown={e => e.key === 'Enter' && create()} />
            <select className="input w-32" value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
            <button className="btn-primary" onClick={create}>Create</button>
          </div>
        </div>
      )}
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <DataTable columns={columns} data={tasks} emptyMessage="No tasks found" />
      )}
    </div>
  )
}
