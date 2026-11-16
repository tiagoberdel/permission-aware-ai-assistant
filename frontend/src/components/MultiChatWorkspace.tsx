
import { useState, type FormEvent } from 'react'
import { DEMO_USERS } from '../data/demoUsers'
import type { DemoUser } from '../data/demoUsers'
import {
  askAgent,
  createDemoSession,
  type DemoUserId,
} from '../services/api'
import ChatWindow, { type ChatMessage } from './ChatWindow'
import UserSelector from './UserSelector'

interface ActiveSession {
  user: DemoUser
  accessToken: string
  conversationId: string
  messages: ChatMessage[]
  loading: boolean
  error: string | null
}

export default function MultiChatWorkspace() {
  const [sessions, setSessions] = useState<ActiveSession[]>([])
  const [creatingUsers, setCreatingUsers] = useState<DemoUserId[]>([])
  const [broadcastQuery, setBroadcastQuery] = useState('')

  const selectedUsers = [
    ...sessions.map((session) => session.user.id),
    ...creatingUsers,
  ]

  async function handleAddUser(userId: DemoUserId) {
    if (selectedUsers.includes(userId) || selectedUsers.length >= 4) return

    setCreatingUsers((current) => [...current, userId])

    try {
      const demoSession = await createDemoSession(userId)
      const user = DEMO_USERS.find((item) => item.id === userId)

      if (!user) return

      setSessions((current) => [
        ...current,
        {
          user,
          accessToken: demoSession.access_token,
          conversationId: demoSession.conversation_id,
          messages: [],
          loading: false,
          error: null,
        },
      ])
    } catch (error) {
      console.error('Could not create demo session:', error)
      alert(
        error instanceof Error
          ? error.message
          : 'Could not create demo session.',
      )
    } finally {
      setCreatingUsers((current) =>
        current.filter((id) => id !== userId),
      )
    }
  }

  function handleCloseUser(userId: DemoUserId) {
    setSessions((current) =>
      current.filter((session) => session.user.id !== userId),
    )
  }

  async function handleSend(userId: DemoUserId, query: string) {
    const session = sessions.find(
      (item) => item.user.id === userId,
    )

    if (!session || session.loading) return

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
    }

    setSessions((current) =>
      current.map((item) =>
        item.user.id === userId
          ? {
              ...item,
              messages: [...item.messages, userMessage],
              loading: true,
              error: null,
            }
          : item,
      ),
    )

    try {
      const result = await askAgent(session.accessToken, query)

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: result.answer,
      }

      setSessions((current) =>
        current.map((item) =>
          item.user.id === userId
            ? {
                ...item,
                messages: [...item.messages, assistantMessage],
                loading: false,
              }
            : item,
        ),
      )
    } catch (error) {
      setSessions((current) =>
        current.map((item) =>
          item.user.id === userId
            ? {
                ...item,
                loading: false,
                error:
                  error instanceof Error
                    ? error.message
                    : 'Something went wrong.',
              }
            : item,
        ),
      )
    }
  }

  async function handleBroadcast(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const query = broadcastQuery.trim()

    if (!query) return

    const availableSessions = sessions.filter(
      (session) => !session.loading,
    )

    if (availableSessions.length === 0) return

    setBroadcastQuery('')

    await Promise.all(
      availableSessions.map((session) =>
        handleSend(session.user.id, query),
      ),
    )
  }

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-white">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8">
          <p className="mb-2 text-sm font-medium uppercase tracking-widest text-blue-400">
            Permission-aware AI assistant
          </p>

          <h1 className="text-3xl font-bold">
            Andino Secure AI
          </h1>

          <p className="mt-2 text-slate-400">
            Compare AI responses across different permission levels.
          </p>
        </header>

        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <UserSelector
            selectedUsers={selectedUsers}
            onAddUser={handleAddUser}
          />

          <span className="text-sm text-slate-500">
            {sessions.length} active sessions
            {creatingUsers.length > 0 && ' · Creating session...'}
          </span>
        </div>

        <form
          onSubmit={handleBroadcast}
          className="mb-8 flex gap-3 rounded-xl border border-slate-700 bg-slate-900 p-4"
        >
          <input
            value={broadcastQuery}
            onChange={(event) => setBroadcastQuery(event.target.value)}
            placeholder="Ask the same question to all active users..."
            disabled={sessions.length === 0}
            className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-blue-500 disabled:opacity-50"
          />

          <button
            type="submit"
            disabled={
              sessions.length === 0 ||
              !broadcastQuery.trim() ||
              sessions.every((session) => session.loading)
            }
            className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Ask all
          </button>
        </form>

        {sessions.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-700 p-12 text-center">
            <h2 className="text-lg font-semibold">
              No active sessions
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Select a demo user to start exploring Andino.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
            {sessions.map((session) => (
              <ChatWindow
                key={session.user.id}
                user={session.user}
                messages={session.messages}
                loading={session.loading}
                error={session.error}
                onSend={(query) =>
                  handleSend(session.user.id, query)
                }
                onClose={() => handleCloseUser(session.user.id)}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
