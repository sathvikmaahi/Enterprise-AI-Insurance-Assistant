import { useCallback, useState } from 'react'
import Header from './Header'
import Chat from './Chat'
import LogsPanel from './LogsPanel'
import './AppShell.css'

export default function AppShell({ session, onLogout }) {
  const [refreshKey, setRefreshKey] = useState(0)

  const handleAskSettled = useCallback(() => {
    setRefreshKey((k) => k + 1)
  }, [])

  return (
    <div className="shell">
      <Header session={session} onLogout={onLogout} />
      <div className="shell__body">
        <Chat
          session={session}
          onUnauthorized={onLogout}
          onAskSettled={handleAskSettled}
        />
        <LogsPanel
          session={session}
          refreshKey={refreshKey}
          onUnauthorized={onLogout}
        />
      </div>
    </div>
  )
}
