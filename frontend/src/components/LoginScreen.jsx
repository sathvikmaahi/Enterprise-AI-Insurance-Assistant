import { useState } from 'react'
import { ApiError, login } from '../api'
import { saveSession } from '../auth/session'
import './LoginScreen.css'

export default function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const session = await login(username.trim(), password)
      saveSession(session)
      onLogin(session)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.status === 401 ? 'Invalid credentials' : err.message)
      } else {
        setError('Sign in failed')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login">
      <div className="login__atmosphere" aria-hidden="true" />
      <section className="login__panel">
        <p className="login__brand">Enterprise AI Insurance Assistant</p>
        <h1 className="login__headline">Ask the book of business</h1>
        <p className="login__lede">
          Sign in to query policies and claims through the semantic layer — not raw SQL.
        </p>

        <form className="login__form" onSubmit={handleSubmit}>
          <label className="login__field">
            <span>Username</span>
            <input
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </label>
          <label className="login__field">
            <span>Password</span>
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          {error ? <p className="login__error" role="alert">{error}</p> : null}
          <button className="login__submit" type="submit" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="login__hint">
          Demo users: <code>agent</code> / <code>adjuster</code> / <code>manager</code>
          {' '}(password: username + <code>123</code>)
        </p>
      </section>
    </main>
  )
}
