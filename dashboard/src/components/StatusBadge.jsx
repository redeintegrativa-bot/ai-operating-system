const colors = {
  online: 'bg-green-100 text-green-800',
  success: 'bg-green-100 text-green-800',
  healthy: 'bg-green-100 text-green-800',
  completed: 'bg-green-100 text-green-800',
  offline: 'bg-red-100 text-red-800',
  error: 'bg-red-100 text-red-800',
  failed: 'bg-red-100 text-red-800',
  warning: 'bg-yellow-100 text-yellow-800',
  pending: 'bg-yellow-100 text-yellow-800',
  starting: 'bg-yellow-100 text-yellow-800',
  info: 'bg-blue-100 text-blue-800',
  running: 'bg-blue-100 text-blue-800',
}

export default function StatusBadge({ status, size = 'sm' }) {
  const s = (status || 'unknown').toLowerCase()
  const cls = colors[s] || 'bg-gray-100 text-gray-600'
  const sz = size === 'lg' ? 'px-3 py-1 text-sm' : size === 'md' ? 'px-2.5 py-0.5 text-xs' : 'px-2 py-0.5 text-xs'
  return <span className={`badge ${cls} ${sz}`}>{status}</span>
}
