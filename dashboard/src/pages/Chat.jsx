import { useState, useRef, useEffect } from 'react'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader'
import ChatMessage from '../components/ChatMessage'
import { Send } from 'lucide-react'

export default function Chat() {
  const [messages, setMessages] = useState([{ role: 'assistant', content: 'Hello! How can I help you today?' }])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async () => {
    if (!input.trim() || sending) return
    const userMsg = { role: 'user', content: input.trim() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setSending(true)
    try {
      const res = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: userMsg.content }) })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response || data.message || 'No response', timestamp: new Date().toISOString() }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error connecting to the AI backend.' }])
    }
    setSending(false)
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="AI Chat" subtitle="Chat with the AI operating system" />
      <div className="flex-1 overflow-y-auto mb-4 space-y-1">
        {messages.map((m, i) => <ChatMessage key={i} {...m} />)}
        {sending && <div className="text-gray-400 text-sm ml-4">Thinking...</div>}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2">
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} className="input" placeholder="Type your message..." disabled={sending} />
        <button onClick={send} className="btn-primary flex items-center gap-2" disabled={sending}><Send className="w-4 h-4" /></button>
      </div>
    </div>
  )
}
