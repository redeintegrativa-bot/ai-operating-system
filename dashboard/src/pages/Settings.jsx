import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import { Save, RotateCcw } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState({})
  const [original, setOriginal] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.getSettings().then(d => { setSettings(d || {}); setOriginal(d || {}) }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const update = (path, value) => {
    const keys = path.split('.')
    const next = { ...settings }
    let obj = next
    for (let i = 0; i < keys.length - 1; i++) { obj[keys[i]] = { ...obj[keys[i]] }; obj = obj[keys[i]] }
    obj[keys[keys.length - 1]] = value
    setSettings(next)
  }

  const save = async () => {
    setSaving(true)
    try { await api.updateSettings(settings) } catch {}
    setSaving(false)
  }

  const Section = ({ title, children }) => (
    <div className="card mb-4">
      <h3 className="font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="space-y-3">{children}</div>
    </div>
  )

  const Field = ({ label, path, type = 'text' }) => {
    const keys = path.split('.')
    let value = settings
    for (const k of keys) value = value?.[k]
    return (
      <div className="flex flex-col sm:flex-row sm:items-center gap-2">
        <label className="text-sm font-medium text-gray-600 w-48">{label}</label>
        {type === 'toggle' ? (
          <button onClick={() => update(path, !value)} className={`w-12 h-6 rounded-full transition-colors ${value ? 'bg-primary-600' : 'bg-gray-300'}`}>
            <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${value ? 'translate-x-6' : 'translate-x-0.5'}`} />
          </button>
        ) : (
          <input type={type} className="input flex-1" value={value ?? ''} onChange={e => update(path, type === 'number' ? Number(e.target.value) : e.target.value)} />
        )}
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="System configuration"
        actions={
          <div className="flex gap-2">
            <button onClick={() => setSettings({ ...original })} className="btn-secondary flex items-center gap-2"><RotateCcw className="w-4 h-4" /> Reset</button>
            <button onClick={save} disabled={saving} className="btn-primary flex items-center gap-2"><Save className="w-4 h-4" /> {saving ? 'Saving...' : 'Save'}</button>
          </div>
        }
      />
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <>
          <Section title="System">
            <Field label="Name" path="system.name" />
            <Field label="Environment" path="system.env" />
            <Field label="Log Level" path="system.logLevel" />
            <Field label="Host" path="system.host" />
            <Field label="Port" path="system.port" type="number" />
          </Section>
          <Section title="LLM">
            <Field label="Default Provider" path="llm.defaultProvider" />
            <Field label="Default Model" path="llm.defaultModel" />
            <Field label="Temperature" path="llm.temperature" type="number" />
            <Field label="Max Tokens" path="llm.maxTokens" type="number" />
          </Section>
          <Section title="Security">
            <Field label="Enable Auth" path="security.enableAuth" type="toggle" />
            <Field label="API Key Header" path="security.apiKeyHeader" />
          </Section>
          <Section title="Agents">
            <Field label="Max Concurrent Tasks" path="agents.maxConcurrentTasks" type="number" />
            <Field label="Timeout (seconds)" path="agents.timeoutSeconds" type="number" />
            <Field label="Retry Count" path="agents.retryCount" type="number" />
          </Section>
        </>
      )}
    </div>
  )
}
