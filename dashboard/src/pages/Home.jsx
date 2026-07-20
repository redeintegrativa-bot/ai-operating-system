import { useState, useEffect } from 'react'
import { api } from '../api/client'
import MetricCard from '../components/MetricCard'
import StatusBadge from '../components/StatusBadge'
import { Activity, Users, ListTodo, Brain, Clock, Zap, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

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

  const completed = tasks.filter(t => t.status === 'completed').length
  const running = tasks.filter(t => t.status === 'running' || t.status === 'pending' || t.status === 'assigned').length
  const failed = tasks.filter(t => t.status === 'failed').length
  const activeAgents = agents.filter(a => a.status === 'online' || a.status === 'online')

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="System" value={status?.status || 'Unknown'} icon={Activity} color={status?.status === 'running' ? 'green' : 'red'} />
        <MetricCard title="Agents Online" value={activeAgents.length || agents.length} icon={Users} color="blue" />
        <MetricCard title="Tasks Running" value={running} icon={ListTodo} color="yellow" />
        <MetricCard title="Uptime" value={status?.uptime_human || '--'} icon={Clock} color="primary" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Link to="/tasks" className="card hover:shadow-md transition-shadow group">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Tasks</h2>
            <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-primary-600 transition-colors" />
          </div>
          <div className="mt-3 space-y-1">
            <div className="flex justify-between text-sm"><span className="text-gray-500">Completed</span><span className="text-green-600 font-medium">{completed}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500">Running</span><span className="text-yellow-600 font-medium">{running}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500">Failed</span><span className="text-red-500 font-medium">{failed}</span></div>
          </div>
        </Link>

        <Link to="/agents" className="card hover:shadow-md transition-shadow group">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Agents</h2>
            <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-primary-600 transition-colors" />
          </div>
          <div className="mt-3 space-y-1">
            {agents.slice(0, 4).map(a => (
              <div key={a.name} className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{a.name}</span>
                <StatusBadge status={a.status} />
              </div>
            ))}
          </div>
        </Link>

        <Link to="/system" className="card hover:shadow-md transition-shadow group">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">System</h2>
            <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-primary-600 transition-colors" />
          </div>
          <div className="mt-3 space-y-1">
            <div className="flex justify-between text-sm"><span className="text-gray-500">Version</span><span>{status?.version || '--'}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500">Memories</span><span>{status?.memory_count || 0}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500">Total Tasks</span><span>{tasks.length}</span></div>
          </div>
        </Link>
      </div>
    </div>
  )
}
