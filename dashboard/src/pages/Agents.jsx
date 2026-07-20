import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import DataTable from '../components/DataTable'

export default function Agents() {
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getAgents().then(d => setAgents(Array.isArray(d) ? d : d?.agents || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'type', label: 'Type' },
    { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
    { key: 'tasks_completed', label: 'Tasks Done' },
    { key: 'last_active', label: 'Last Active', render: (v) => v ? new Date(v).toLocaleString() : '--' },
  ]

  return (
    <div>
      <PageHeader title="Agents" subtitle="Manage AI agents" />
      {loading ? <p className="text-gray-400">Loading...</p> : <DataTable columns={columns} data={agents} emptyMessage="No agents found" />}
    </div>
  )
}
