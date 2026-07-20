export default function ChatMessage({ role = 'assistant', content, timestamp }) {
  const isUser = role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
        isUser ? 'bg-primary-600 text-white rounded-br-md' : 'bg-gray-100 text-gray-900 rounded-bl-md'
      }`}>
        <p className="text-sm whitespace-pre-wrap">{content}</p>
        {timestamp && (
          <p className={`text-xs mt-1 ${isUser ? 'text-primary-200' : 'text-gray-400'}`}>
            {new Date(timestamp).toLocaleTimeString()}
          </p>
        )}
      </div>
    </div>
  )
}
