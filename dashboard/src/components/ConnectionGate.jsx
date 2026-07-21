import { useState, useEffect } from 'react'
import { api, getApiBase, setApiBase } from '../api/client'
import { WifiOff, Link, Loader2 } from 'lucide-react'

export default function ConnectionGate({ children }) {
  const [status, setStatus] = useState('checking')
  const [error, setError] = useState('')
  const [url, setUrl] = useState('')

  useEffect(() => {
    api.getHealth()
      .then(() => setStatus('connected'))
      .catch(e => {
        setStatus('disconnected')
        setError(e.message)
      })
  }, [])

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

  const handleConnect = () => {
    if (url.trim()) {
      setApiBase(url.trim())
    }
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
              ? `Cannot reach ${currentBase}`
              : 'No API server found on this host'}
          </p>
          {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
        </div>

        <div className="space-y-3">
          <label className="block">
            <span className="text-sm font-medium text-gray-700">API Server URL</span>
            <input
              type="url"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="https://your-tunnel.trycloudflare.com"
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              onKeyDown={e => e.key === 'Enter' && handleConnect()}
            />
          </label>

          <button
            onClick={handleConnect}
            disabled={!url.trim()}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Link className="w-4 h-4" /> Connect
          </button>

          <button
            onClick={handleLocal}
            className="w-full text-sm text-gray-500 hover:text-gray-700 py-1"
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
