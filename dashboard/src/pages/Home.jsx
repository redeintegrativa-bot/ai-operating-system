import { useState, useEffect } from 'react'
import { api } from '../api/client'
import MetricCard from '../components/MetricCard'
import StatusBadge from '../components/StatusBadge'
import { Activity, Users, ListTodo, Brain, Cpu, Zap } from 'lucide-react'

export default function Home() {
  const [status, setStatus] = useState(null)
  const [agents, setAgents] = useState([])
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([api.getStatus(), api.getAgents(), api.getTasks()])
      .then(([s, a, t]) => {
        setStatus(s.status === 'fulfilled' ? s.value : null)
        setAgents(a.status === 'fulfilled' ? (Array.isArray(a.value) ? a.value : a.value?.agents || []) : [])
        setTasks(t.status === 'fulfilled' ? (Array.isArray(t.value) ? t.value : t.value?.tasks || []) : [])
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">Loading...</div>

  const runningTasks = tasks.filter(t => t.status === 'running' || t.status === 'pending')
  const activeAgents = agents.filter(a => a.status === 'online' || a.status === 'running')

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard title="System Status" value={status?.status || 'Unknown'} icon={Activity} color="green" />
        <MetricCard title="Active Agents" value={activeAgents.length} icon={Users} color="blue" />
        <MetricCard title="Running Tasks" value={runningTasks.length} icon={ListTodo} color="yellow" />
        <MetricCard title="Uptime" value={status?.uptime || '--'} icon={Cpu} color="primary" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold mb-4">Recent Tasks</h2>
          {tasks.slice(0, 5).length ? tasks.slice(0, 5).map(t => (
            <div key={t.id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
              <span className="text-sm">{t.title || t.name || t.id}</span>
              <StatusBadge status={t.status} />
            </div>
          )) : <p className="text-gray-400 text-sm">No tasks</p>}
        </div>
        <div className="card">
          <h2 className="font-semibold mb-4">Agents</h2>
          {agents.length ? agents.map(a => (
            <div key={a.name || a.id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
              <span className="text-sm">{a.name || a.id}</span>
              <StatusBadge status={a.status} />
            </div>
          )) : <p className="text-gray-400 text-sm">No agents</p>}
        </div>
      </div>
    </div>
  )
}
