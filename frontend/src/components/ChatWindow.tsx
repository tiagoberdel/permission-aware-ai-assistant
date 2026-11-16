import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useState, type FormEvent } from 'react'
import type { DemoUser } from '../data/demoUsers'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

interface ChatWindowProps {
  user: DemoUser
  messages: ChatMessage[]
  loading: boolean
  error: string | null
  onSend: (query: string) => void
  onClose: () => void
}

export default function ChatWindow({
  user,
  messages,
  loading,
  error,
  onSend,
  onClose,
}: ChatWindowProps) {
  const [query, setQuery] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedQuery = query.trim()

    if (!trimmedQuery || loading) return

    onSend(trimmedQuery)
    setQuery('')
  }

  return (
    <section className="flex min-h-[420px] flex-col overflow-hidden rounded-xl border border-slate-700 bg-slate-900">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-700 p-4">
        <div>
          <h2 className="font-semibold text-white">{user.name}</h2>
          <p className="text-xs text-slate-400">{user.jobTitle}</p>

          <div className="mt-2 flex flex-wrap gap-1">
            {user.roles.length > 0 ? (
              user.roles.map((role) => (
                <span
                  key={role}
                  className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-300"
                >
                  {role}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-500">
                No internal roles
              </span>
            )}
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          aria-label={`Close ${user.name} chat`}
          className="rounded-lg px-3 py-2 text-slate-400 hover:bg-slate-800 hover:text-white cursor-pointer"
        >
          ×
        </button>
      </header>

      {/* Messages */}
      <div className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="m-auto max-w-xs text-center text-sm text-slate-500">
            Ask Andino a question as {user.name}.
          </p>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`max-w-[90%] rounded-xl p-3 text-sm ${
              message.role === 'user'
                ? 'ml-auto whitespace-pre-wrap bg-blue-600 text-white'
                : 'mr-auto bg-slate-800 text-slate-200'
            }`}
          >
            {message.role === 'user' ? (
              message.content
            ) : (
              <div className="markdown-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <p className="mr-auto rounded-xl bg-slate-800 p-3 text-sm text-slate-400">
            Andino is thinking...
          </p>
        )}

        {error && (
          <p className="rounded-lg border border-red-900 bg-red-950/50 p-3 text-sm text-red-300">
            {error}
          </p>
        )}
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-slate-700 p-3"
      >
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask a question..."
          disabled={loading}
          className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none placeholder:text-slate-500 focus:border-blue-500 disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </section>
  )
}
