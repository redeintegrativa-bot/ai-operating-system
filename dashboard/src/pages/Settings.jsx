import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import { Settings as SettingsIcon } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getSettings().then(d => setSettings(d || {})).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader title="Settings" subtitle="System configuration" actions={<SettingsIcon className="w-5 h-5 text-primary-600" />} />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div className="card">
          <pre className="text-sm text-gray-600 whitespace-pre-wrap">{JSON.stringify(settings, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
