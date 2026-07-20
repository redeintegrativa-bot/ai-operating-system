import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import MetricCard from '../components/MetricCard'
import { Radio, Target, CheckCircle2, Clock, AlertTriangle } from 'lucide-react'

export default function MissionControl() {
  const [missions, setMissions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getMissions().then(d => setMissions(Array.isArray(d) ? d : d?.missions || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const done = missions.filter(m => m.status === 'terminee' || m.completedTasks === m.totalTasks).length
  const active = missions.filter(m => m.status === 'en_cours').length
  const pending = missions.filter(m => m.status === 'a_venir' || m.status === 'a_faire').length

  const statusColor = (s) => {
    if (s === 'en_cours') return 'running'
    if (s === 'terminee') return 'completed'
    if (s === 'a_venir') return 'info'
    return 'pending'
  }

  return (
    <div>
      <PageHeader title="Mission Control" subtitle="Monitor and manage active missions" actions={<Radio className="w-5 h-5 text-primary-600" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard title="Active" value={active} icon={Target} color="blue" />
            <MetricCard title="Completed" value={done} icon={CheckCircle2} color="green" />
            <MetricCard title="Upcoming" value={pending} icon={Clock} color="yellow" />
          </div>
          <div className="space-y-3">
            {missions.map((m, i) => {
              const pct = m.totalTasks ? Math.round((m.completedTasks / m.totalTasks) * 100) : 0
              return (
                <div key={m.id || i} className="card">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{m.name}</h3>
                        <StatusBadge status={statusColor(m.status)} />
                      </div>
                      <p className="text-sm text-gray-500 mt-1">{m.description}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm font-medium">{m.completedTasks}/{m.totalTasks} tasks</p>
                        <div className="w-24 bg-gray-100 rounded-full h-2 mt-1">
                          <div className={`h-2 rounded-full transition-all ${pct === 100 ? 'bg-green-500' : 'bg-primary-500'}`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
            {!missions.length && <p className="text-gray-400 text-center py-12">No missions</p>}
          </div>
        </div>
      )}
    </div>
  )
}
