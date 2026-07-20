import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import DataTable from '../components/DataTable'

export default function Plugins() {
  const [plugins, setPlugins] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getPlugins().then(d => setPlugins(Array.isArray(d) ? d : d?.plugins || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'version', label: 'Version' },
    { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
    { key: 'description', label: 'Description' },
  ]

  return (
    <div>
      <PageHeader title="Plugins" subtitle="Installed plugins and extensions" />
      {loading ? <p className="text-gray-400">Loading...</p> : <DataTable columns={columns} data={plugins} emptyMessage="No plugins installed" />}
    </div>
  )
}
