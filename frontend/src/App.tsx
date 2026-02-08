import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.PROD ? '/api' : 'http://localhost:8000'

interface Message {
  role: 'user' | 'assistant'
  content: string
  time?: number
}

interface SchemaInfo {
  rows: number
  columns: number
  schema_text: string
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [threadId, setThreadId] = useState<string | null>(null)
  const [schema, setSchema] = useState<SchemaInfo | null>(null)
  const [showSchema, setShowSchema] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const exampleQueries = [
    "How many unique pipelines are there?",
    "Find correlations between capacity columns",
    "Are there outliers in total_scheduled_quantity?",
    "Run a data quality report",
    "Find segments of pipelines by total_scheduled_quantity",
  ]

  useEffect(() => {
    // Fetch schema on mount
    axios.get(`${API_URL}/schema`).then((res) => {
      setSchema(res.data)
    })
  }, [])

  useEffect(() => {
    // Scroll to bottom on new messages
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (message: string) => {
    if (!message.trim() || loading) return

    const userMessage: Message = { role: 'user', content: message }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await axios.post(`${API_URL}/chat`, {
        message,
        thread_id: threadId,
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: res.data.response,
        time: res.data.time_seconds,
      }

      setMessages((prev) => [...prev, assistantMessage])
      setThreadId(res.data.thread_id)
    } catch (error) {
      console.error('Error:', error)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error: Failed to get response' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const clearConversation = async () => {
    if (threadId) {
      const res = await axios.post(`${API_URL}/clear/${threadId}`)
      setThreadId(res.data.new_thread_id)
    }
    setMessages([])
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-72 bg-gray-900 text-white p-4 flex flex-col">
        <h1 className="text-xl font-bold mb-6">Data Analysis Agent</h1>

        {schema && (
          <div className="mb-6">
            <div className="text-sm text-gray-400 mb-2">Dataset</div>
            <div className="text-2xl font-bold">{schema.rows.toLocaleString()}</div>
            <div className="text-sm text-gray-400">rows × {schema.columns} columns</div>

            <button
              onClick={() => setShowSchema(!showSchema)}
              className="mt-2 text-sm text-blue-400 hover:text-blue-300"
            >
              {showSchema ? 'Hide' : 'View'} Schema
            </button>

            {showSchema && (
              <pre className="mt-2 text-xs bg-gray-800 p-2 rounded overflow-auto max-h-64">
                {schema.schema_text}
              </pre>
            )}
          </div>
        )}

        <button
          onClick={clearConversation}
          className="w-full py-2 px-4 bg-gray-700 hover:bg-gray-600 rounded mb-6"
        >
          Clear Conversation
        </button>

        <div className="text-sm text-gray-400 mb-2">Example Queries</div>
        <div className="flex-1 overflow-auto space-y-2">
          {exampleQueries.map((query) => (
            <button
              key={query}
              onClick={() => sendMessage(query)}
              disabled={loading}
              className="w-full text-left text-sm py-2 px-3 bg-gray-800 hover:bg-gray-700 rounded disabled:opacity-50"
            >
              {query}
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-auto p-6">
          {messages.length === 0 ? (
            <div className="text-center text-gray-400 mt-20">
              <div>Welcome</div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-4">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-200 shadow-sm'
                    }`}
                  >
                    {msg.role === 'assistant' ? (
                      <div className="prose prose-sm max-w-none">
                        <div dangerouslySetInnerHTML={{
                          __html: msg.content
                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                            .replace(/### (.*?)(\n|$)/g, '<h3>$1</h3>')
                            .replace(/## (.*?)(\n|$)/g, '<h2>$1</h2>')
                            .replace(/\n/g, '<br />')
                        }} />
                        {msg.time && (
                          <div className="text-xs text-gray-400 mt-2">
                            {msg.time}s
                          </div>
                        )}
                      </div>
                    ) : (
                      <div>{msg.content}</div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 p-4">
          <div className="max-w-4xl mx-auto flex space-x-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about the data..."
              disabled={loading}
              className="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={loading || !input.trim()}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App