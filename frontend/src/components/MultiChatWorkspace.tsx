import { useRef, useState, type CSSProperties, type FormEvent } from 'react'
import { DEMO_USERS } from '../data/demoUsers'
import type { DemoUser } from '../data/demoUsers'
import {
  askAgent,
  createDemoSession,
  type DemoUserId,
} from '../services/api'
import ChatWindow, { type ChatMessage } from './ChatWindow'
import UserSelector from './UserSelector'

const MAX_SESSIONS = 4

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

  // Evita crear dos sesiones del mismo usuario con un doble clic rápido.
  const pendingUsersRef = useRef<Set<DemoUserId>>(new Set())

  const selectedUsers = [
    ...sessions.map((session) => session.user.id),
    ...creatingUsers,
  ]

  // Siempre en el mismo orden que DEMO_USERS, sin importar cuál termine primero.
  const orderedSessions = [...sessions].sort(
    (a, b) =>
      DEMO_USERS.findIndex((u) => u.id === a.user.id) -
      DEMO_USERS.findIndex((u) => u.id === b.user.id),
  )

  async function handleAddUser(userId: DemoUserId) {
    if (
      selectedUsers.includes(userId) ||
      pendingUsersRef.current.has(userId) ||
      selectedUsers.length >= MAX_SESSIONS
    ) {
      return
    }

    pendingUsersRef.current.add(userId)
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
      pendingUsersRef.current.delete(userId)
      setCreatingUsers((current) => current.filter((id) => id !== userId))
    }
  }

  function handleCloseUser(userId: DemoUserId) {
    setSessions((current) =>
      current.filter((session) => session.user.id !== userId),
    )
  }

  async function handleSend(userId: DemoUserId, query: string) {
    const session = sessions.find((item) => item.user.id === userId)

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

    const availableSessions = sessions.filter((session) => !session.loading)

    if (availableSessions.length === 0) return

    setBroadcastQuery('')

    await Promise.all(
      availableSessions.map((session) => handleSend(session.user.id, query)),
    )
  }

  return (
    <main className="flex min-h-dvh flex-col gap-3 bg-slate-950 p-3 text-white md:h-screen md:overflow-hidden md:p-4">
      <header className="flex shrink-0 flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest text-blue-400">
            Permission-aware AI assistant
          </p>
          <h1 className="text-xl font-bold">Andino Secure AI</h1>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <UserSelector
            selectedUsers={selectedUsers}
            onAddUser={handleAddUser}
          />
          <span className="text-sm text-slate-500">
            {sessions.length} active sessions
            {creatingUsers.length > 0 && ' \u00b7 Creating session...'}
          </span>
        </div>
      </header>

      <form
        onSubmit={handleBroadcast}
        className="flex shrink-0 gap-3 rounded-xl border border-slate-700 bg-slate-900 p-3"
      >
        <input
          value={broadcastQuery}
          onChange={(event) => setBroadcastQuery(event.target.value)}
          placeholder="Ask the same question to all active users..."
          disabled={sessions.length === 0}
          className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-white outline-none placeholder:text-slate-500 focus:border-blue-500 disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={
            sessions.length === 0 ||
            !broadcastQuery.trim() ||
            sessions.every((session) => session.loading)
          }
          className="cursor-pointer rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Ask all
        </button>
      </form>

      {sessions.length === 0 ? (
        <div className="flex min-h-0 flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 text-center">
          <h2 className="text-lg font-semibold">No active sessions</h2>
          <p className="mt-2 text-sm text-slate-500">
            Select a demo user to start exploring Andino.
          </p>
        </div>
      ) : (
        <div
          className="grid auto-rows-[75dvh] grid-cols-1 gap-4 md:min-h-0 md:flex-1 md:auto-rows-fr md:grid-cols-2 xl:grid-cols-[repeat(var(--cols),minmax(0,1fr))]"
          style={{ '--cols': sessions.length } as CSSProperties}
        >
          {orderedSessions.map((session) => (
            <ChatWindow
              key={session.user.id}
              user={session.user}
              messages={session.messages}
              loading={session.loading}
              error={session.error}
              onSend={(query) => handleSend(session.user.id, query)}
              onClose={() => handleCloseUser(session.user.id)}
            />
          ))}
        </div>
      )}
    </main>
  )
}