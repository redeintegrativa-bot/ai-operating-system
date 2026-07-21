import { useState, useEffect, useCallback, useRef } from 'react'
import { setApiBase } from '../api/client'
import { WifiOff, Link, Loader2, RefreshCw, CheckCircle, XCircle } from 'lucide-react'

function tryConnect(url) {
  return fetch(`${url.replace(/\/+$/, '')}/api/health`, { mode: 'cors' })
    .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
}

export default function ConnectionGate({ children }) {
  const [connected, setConnected] = useState(false)
  const [checking, setChecking] = useState(true)
  const [error, setError] = useState('')
  const [url, setUrl] = useState('')
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const mountedRef = useRef(true)

  useEffect(() => { return () => { mountedRef.current = false } }, [])

  const savedUrl = typeof window !== 'undefined' ? localStorage.getItem('aios_api_url') : null

  const check = useCallback((targetUrl) => {
    if (!targetUrl) {
      setChecking(false)
      setConnected(false)
      return
    }
    setChecking(true)
    tryConnect(targetUrl)
      .then(() => {
        if (mountedRef.current) { setConnected(true); setChecking(false) }
      })
      .catch(e => {
        if (mountedRef.current) { setConnected(false); setChecking(false); setError(e.message) }
      })
  }, [])

  useEffect(() => { check(savedUrl) }, [check, savedUrl])

  useEffect(() => {
    if (!connected) return
    const iv = setInterval(() => {
      const u = localStorage.getItem('aios_api_url')
      if (u) tryConnect(u).catch(() => { if (mountedRef.current) setConnected(false) })
    }, 10000)
    return () => clearInterval(iv)
  }, [connected])

  const handleTest = async () => {
    const testUrl = url.trim()
    if (!testUrl) return
    setTesting(true)
    setTestResult(null)
    try {
      const data = await tryConnect(testUrl)
      setTestResult({ ok: true, msg: `Server healthy (v${data.version})` })
    } catch (e) {
      setTestResult({ ok: false, msg: e.message })
    }
    setTesting(false)
  }

  const handleConnect = async () => {
    const v = url.trim()
    if (!v) return
    setTesting(true)
    setTestResult(null)
    try {
      await tryConnect(v)
      localStorage.setItem('aios_api_url', v.replace(/\/+$/, ''))
      if (mountedRef.current) setConnected(true)
    } catch (e) {
      setTestResult({ ok: false, msg: e.message })
    }
    setTesting(false)
  }

  const handleLocal = () => {
    localStorage.removeItem('aios_api_url')
    window.location.reload()
  }

  const handleDisconnect = () => {
    localStorage.removeItem('aios_api_url')
    if (mountedRef.current) { setConnected(false); setUrl(''); setTestResult(null) }
  }

  if (connected) return children

  if (checking && savedUrl) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-500">Connecting to {savedUrl}...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-6">
          <WifiOff className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <h2 className="text-xl font-bold text-gray-900">Disconnected</h2>
          {error && <p className="text-xs text-red-400 mt-2">Error: {error}</p>}
          {savedUrl && !connected && (
            <p className="text-xs text-gray-400 mt-1">Last: {savedUrl}</p>
          )}
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
              disabled={!url.trim() || testing}
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
