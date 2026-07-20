import { useEffect, useRef, useState, useCallback } from 'react'
import { getWsUrl } from '../api/client'

export function useWebSocket(events = ['*']) {
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState([])
  const [lastMessage, setLastMessage] = useState(null)
  const wsRef = useRef(null)
  const reconnectRef = useRef(null)

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(getWsUrl())
      wsRef.current = ws
      ws.onopen = () => {
        setConnected(true)
        ws.send(JSON.stringify({ type: 'subscribe', events }))
      }
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          setLastMessage(msg)
          setMessages(prev => [...prev.slice(-200), msg])
        } catch {}
      }
      ws.onclose = () => {
        setConnected(false)
        reconnectRef.current = setTimeout(connect, 3000)
      }
      ws.onerror = () => ws.close()
    } catch {}
  }, [events.join(',')])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((data) => {
    wsRef.current?.send(JSON.stringify(data))
  }, [])

  return { connected, lastMessage, messages, send }
}
