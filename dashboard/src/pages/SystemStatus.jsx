import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import MetricCard from '../components/MetricCard'
import { Server, Cpu, HardDrive, Activity } from 'lucide-react'

export default function SystemStatus() {
  const [system, setSystem] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([api.getSystem(), api.getHealth()])
      .then(([s, h]) => {
        setSystem(s.status === 'fulfilled' ? s.value : null)
        setHealth(h.status === 'fulfilled' ? h.value : null)
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader title="System Status" subtitle="System health and resource monitoring" actions={<Server className="w-5 h-5 text-primary-600" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <MetricCard title="Health" value={health?.status || 'Unknown'} icon={Activity} color={health?.status === 'healthy' ? 'green' : 'red'} />
            <MetricCard title="CPU" value={system?.cpu || '--'} icon={Cpu} color="blue" />
            <MetricCard title="Memory" value={system?.memory || '--'} icon={HardDrive} color="yellow" />
            <MetricCard title="Disk" value={system?.disk || '--'} icon={Server} color="primary" />
          </div>
          <div className="card">
            <h2 className="font-semibold mb-4">System Information</h2>
            <pre className="text-sm text-gray-600 whitespace-pre-wrap">{JSON.stringify(system || health || {}, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  )
}
