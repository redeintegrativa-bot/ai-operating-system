import { NavLink } from 'react-router-dom'
import { Home, Radio, Map, MessageSquare, Users, ListTodo, Brain, Clock, Puzzle, Link2, Coins, FileText, Settings, Server, Bot } from 'lucide-react'

const links = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/mission-control', label: 'Mission Control', icon: Radio },
  { to: '/capability-map', label: 'Capability Map', icon: Map },
  { to: '/chat', label: 'AI Chat', icon: MessageSquare },
  { to: '/agents', label: 'Agents', icon: Users },
  { to: '/tasks', label: 'Tasks', icon: ListTodo },
  { to: '/memory', label: 'Memory', icon: Brain },
  { to: '/scheduler', label: 'Scheduler', icon: Clock },
  { to: '/plugins', label: 'Plugins', icon: Puzzle },
  { to: '/integrations', label: 'Integrations', icon: Link2 },
  { to: '/defi', label: 'DeFi Intelligence', icon: Coins },
  { to: '/logs', label: 'Logs', icon: FileText },
  { to: '/settings', label: 'Settings', icon: Settings },
  { to: '/system', label: 'System Status', icon: Server },
]

export default function Sidebar({ onNavigate }) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold">AIOS</h1>
            <p className="text-xs text-gray-400">Dashboard</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive ? 'bg-primary-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <Icon className="w-5 h-5 flex-shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-800 text-xs text-gray-500">AIOS v2.1.0</div>
    </div>
  )
}
