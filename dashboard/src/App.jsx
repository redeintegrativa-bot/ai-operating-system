import { Routes, Route } from 'react-router-dom'
import ConnectionGate from './components/ConnectionGate'
import Layout from './components/Layout'
import Home from './pages/Home'
import MissionControl from './pages/MissionControl'
import CapabilityMap from './pages/CapabilityMap'
import Chat from './pages/Chat'
import Agents from './pages/Agents'
import Tasks from './pages/Tasks'
import Memory from './pages/Memory'
import Scheduler from './pages/Scheduler'
import Plugins from './pages/Plugins'
import Integrations from './pages/Integrations'
import DeFiIntelligence from './pages/DeFiIntelligence'
import Logs from './pages/Logs'
import Settings from './pages/Settings'
import SystemStatus from './pages/SystemStatus'

export default function App() {
  return (
    <ConnectionGate>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/mission-control" element={<MissionControl />} />
          <Route path="/capability-map" element={<CapabilityMap />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/memory" element={<Memory />} />
          <Route path="/scheduler" element={<Scheduler />} />
          <Route path="/plugins" element={<Plugins />} />
          <Route path="/integrations" element={<Integrations />} />
          <Route path="/defi" element={<DeFiIntelligence />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/system" element={<SystemStatus />} />
        </Routes>
      </Layout>
    </ConnectionGate>
  )
}
