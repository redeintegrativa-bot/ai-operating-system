import { useState, useEffect, useCallback } from 'react'
import { getApiBase, setApiBase } from '../api/client'
import { WifiOff, Link, Loader2, RefreshCw, CheckCircle, XCircle } from 'lucide-react'

export default function ConnectionGate({ children }) {
  const [status, setStatus] = useState('checking')
  const [error, setError] = useState('')
  const [url, setUrl] = useState('')
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)

  const check = useCallback(() => {
    const base = getApiBase()
    if (!base) {
      setStatus('disconnected')
      setError('No API URL configured')
      return
    }
    setStatus('checking')
    fetch(`${base}/api/health`, { mode: 'cors' })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(() => setStatus('connected'))
      .catch(e => {
        setStatus('disconnected')
        setError(e.message)
      })
  }, [])

  useEffect(() => {
    check()
    const interval = setInterval(check, 15000)
    return () => clearInterval(interval)
  }, [check])

  if (status === 'connected') return children

  if (status === 'checking') {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-500">Connecting to AIOS...</p>
        </div>
      </div>
    )
  }

  const currentBase = getApiBase()

  const handleTest = async () => {
    const testUrl = url.trim()
    if (!testUrl) return
    setTesting(true)
    setTestResult(null)
    try {
      const res = await fetch(`${testUrl}/api/health`, { mode: 'cors' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setTestResult({ ok: true, msg: `Server healthy (v${data.version})` })
    } catch (e) {
      setTestResult({ ok: false, msg: e.message })
    }
    setTesting(false)
  }

  const handleConnect = () => {
    const v = url.trim()
    if (!v) return
    setApiBase(v)
  }

  const handleLocal = () => {
    setApiBase('')
  }

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-6">
          <WifiOff className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <h2 className="text-xl font-bold text-gray-900">Disconnected</h2>
          <p className="text-sm text-gray-500 mt-1">
            {currentBase
              ? <>Cannot reach <span className="font-mono text-xs break-all">{currentBase}</span></>
              : 'No API server URL configured'}
          </p>
          {error && <p className="text-xs text-red-400 mt-2">Error: {error}</p>}
        </div>

        <div className="space-y-3">
          <label className="block">
            <span className="text-sm font-medium text-gray-700">API Server URL</span>
            <input
              type="url"
              value={url}
              onChange={e => { setUrl(e.target.value); setTestResult(null) }}
              placeholder="https://your-tunnel.trycloudflare.com"
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              onKeyDown={e => e.key === 'Enter' && handleTest()}
            />
          </label>

          <div className="flex gap-2">
            <button
              onClick={handleTest}
              disabled={!url.trim() || testing}
              className="flex-1 flex items-center justify-center gap-1.5 bg-gray-100 text-gray-700 py-2.5 rounded-lg text-sm font-medium hover:bg-gray-200 disabled:opacity-50"
            >
              {testing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
              Test
            </button>
            <button
              onClick={handleConnect}
              disabled={!url.trim()}
              className="flex-1 flex items-center justify-center gap-1.5 bg-blue-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              <Link className="w-4 h-4" /> Connect
            </button>
          </div>

          {testResult && (
            <div className={`flex items-center gap-2 text-sm p-2 rounded-lg ${testResult.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {testResult.ok ? <CheckCircle className="w-4 h-4 flex-shrink-0" /> : <XCircle className="w-4 h-4 flex-shrink-0" />}
              <span>{testResult.msg}</span>
            </div>
          )}

          <button
            onClick={handleLocal}
            className="w-full text-sm text-gray-500 hover:text-gray-700 py-2 border border-gray-200 rounded-lg"
          >
            Use local server (localhost:8080)
          </button>
        </div>

        <p className="text-xs text-gray-400 mt-4 text-center">
          Start tunnel: <code className="bg-gray-100 px-1 rounded">aios serve</code>
        </p>
      </div>
    </div>
  )
}
