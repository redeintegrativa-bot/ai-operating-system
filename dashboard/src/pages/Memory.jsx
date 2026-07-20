import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import DataTable from '../components/DataTable'

export default function Memory() {
  const [memories, setMemories] = useState([])
  const [agent, setAgent] = useState('main')
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.getMemories(agent).then(d => setMemories(Array.isArray(d) ? d : d?.memories || [])).catch(() => setMemories([])).finally(() => setLoading(false))
  }

  useEffect(load, [agent])

  const columns = [
    { key: 'content', label: 'Content' },
    { key: 'type', label: 'Type' },
    { key: 'timestamp', label: 'Time', render: (v) => v ? new Date(v).toLocaleString() : '--' },
  ]

  return (
    <div>
      <PageHeader title="Memory" subtitle="Agent memory store" actions={<input value={agent} onChange={e => setAgent(e.target.value)} className="input w-48" placeholder="Agent name" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : <DataTable columns={columns} data={memories} emptyMessage="No memories found" />}
    </div>
  )
}
