import PageHeader from '../components/PageHeader'
import { Clock } from 'lucide-react'

export default function Scheduler() {
  return (
    <div>
      <PageHeader title="Scheduler" subtitle="Task scheduling and cron management" actions={<Clock className="w-5 h-5 text-primary-600" />} />
      <div className="card text-center py-12 text-gray-400">
        <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>Scheduler interface coming soon</p>
      </div>
    </div>
  )
}
