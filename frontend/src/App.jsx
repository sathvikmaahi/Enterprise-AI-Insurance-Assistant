import { useCallback, useState } from 'react'
import { clearSession, loadSession } from './auth/session'
import LoginScreen from './components/LoginScreen'
import AppShell from './components/AppShell'

export default function App() {
  const [session, setSession] = useState(() => loadSession())

  const handleLogout = useCallback(() => {
    clearSession()
    setSession(null)
  }, [])

  if (!session) {
    return <LoginScreen onLogin={setSession} />
  }

  return <AppShell session={session} onLogout={handleLogout} />
}
