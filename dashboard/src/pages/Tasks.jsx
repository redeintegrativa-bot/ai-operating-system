import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import DataTable from '../components/DataTable'

export default function Tasks() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getTasks().then(d => setTasks(Array.isArray(d) ? d : d?.tasks || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const columns = [
    { key: 'title', label: 'Title', render: (v, row) => v || row.name || row.id },
    { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
    { key: 'priority', label: 'Priority' },
    { key: 'assigned_to', label: 'Assigned To' },
    { key: 'created_at', label: 'Created', render: (v) => v ? new Date(v).toLocaleString() : '--' },
  ]

  return (
    <div>
      <PageHeader title="Tasks" subtitle="Manage and track tasks" />
      {loading ? <p className="text-gray-400">Loading...</p> : <DataTable columns={columns} data={tasks} emptyMessage="No tasks found" />}
    </div>
  )
}
