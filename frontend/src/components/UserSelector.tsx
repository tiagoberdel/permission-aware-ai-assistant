
import { DEMO_USERS } from '../data/demoUsers'
import type { DemoUserId } from '../services/api'

interface UserSelectorProps {
  selectedUsers: DemoUserId[]
  onAddUser: (userId: DemoUserId) => void
}

export default function UserSelector({
  selectedUsers,
  onAddUser,
}: UserSelectorProps) {
  const availableUsers = DEMO_USERS.filter(
    (user) => !selectedUsers.includes(user.id),
  )

  return (
    <div className="flex items-center gap-3">
      <label
        htmlFor="user-selector"
        className="text-sm font-medium text-slate-300"
      >
        Add demo user
      </label>

      <select
        id="user-selector"
        value=""
        disabled={selectedUsers.length >= 4 || availableUsers.length === 0}
        onChange={(event) => {
          const userId = event.target.value as DemoUserId

          if (userId) {
            onAddUser(userId)
          }
        }}
        className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-blue-500 disabled:opacity-50"
      >
        <option value="" disabled>
          {selectedUsers.length >= 4
            ? 'Maximum of 4 users'
            : 'Select a user...'}
        </option>

        {availableUsers.map((user) => (
          <option key={user.id} value={user.id}>
            {user.name} — {user.jobTitle}
          </option>
        ))}
      </select>

      <span className="text-xs text-slate-500">
        {selectedUsers.length}/4 selected
      </span>
    </div>
  )
}
