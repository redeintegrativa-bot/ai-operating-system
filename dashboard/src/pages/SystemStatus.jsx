import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import MetricCard from '../components/MetricCard'
import { Server, Cpu, HardDrive, Activity, RefreshCcw, Wifi } from 'lucide-react'

export default function SystemStatus() {
  const [system, setSystem] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.getSystem().then(d => setSystem(d)).catch(() => {}).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const health = system?.health || {}
  const services = system?.services || []
  const checks = health.checks || []

  return (
    <div>
      <PageHeader
        title="System Status"
        subtitle="System health and resource monitoring"
        actions={
          <button onClick={load} className="btn-secondary flex items-center gap-2">
            <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
        }
      />
      {loading && !system ? <p className="text-gray-400">Loading...</p> : system && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard title="Health" value={health.status || 'Unknown'} icon={Activity} color={health.status === 'healthy' ? 'green' : 'red'} />
            <MetricCard title="CPU" value={`${system.cpu_usage || system.cpu || '--'}%`} icon={Cpu} color="blue" />
            <MetricCard title="Memory" value={`${system.memory_usage || system.memory || '--'} MB`} icon={HardDrive} color="yellow" />
            <MetricCard title="Uptime" value={system.uptime || '--'} icon={Server} color="primary" />
          </div>

          {checks.length > 0 && (
            <div className="card">
              <h3 className="font-semibold mb-3">Health Checks</h3>
              <div className="space-y-2">
                {checks.map((c, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <span className="text-sm">{c.name}</span>
                    <StatusBadge status={c.status} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {services.length > 0 && (
            <div className="card">
              <h3 className="font-semibold mb-3">Services</h3>
              <div className="space-y-2">
                {services.map((s, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <div className="flex items-center gap-3">
                      <Wifi className="w-4 h-4 text-gray-400" />
                      <div>
                        <span className="text-sm font-medium">{s.name}</span>
                        {s.port > 0 && <span className="text-xs text-gray-400 ml-2">:{s.port}</span>}
                      </div>
                    </div>
                    <StatusBadge status={s.status} />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="card">
            <h3 className="font-semibold mb-3">System Info</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div><span className="text-gray-500">Version</span><p className="font-medium">{system.version || '--'}</p></div>
              <div><span className="text-gray-500">Agents</span><p className="font-medium">{system.agents_online || 0}/{system.agents || 0} online</p></div>
              <div><span className="text-gray-500">Tasks</span><p className="font-medium">{system.tasks || 0} total</p></div>
              <div><span className="text-gray-500">Memories</span><p className="font-medium">{system.memories || 0}</p></div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
