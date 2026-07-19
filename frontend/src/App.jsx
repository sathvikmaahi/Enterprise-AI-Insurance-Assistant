import { useEffect, useState } from 'react'
import { getHealth } from './api'
import './App.css'

function App() {
  const [health, setHealth] = useState('checking…')

  useEffect(() => {
    let cancelled = false

    getHealth()
      .then((data) => {
        if (!cancelled) {
          setHealth(data.status === 'ok' ? 'API connected' : 'unexpected response')
        }
      })
      .catch(() => {
        if (!cancelled) {
          setHealth('API offline (start FastAPI on :8000)')
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main className="shell">
      <p className="eyebrow">Phase 0 scaffold</p>
      <h1>Enterprise AI Insurance Assistant</h1>
      <p className="lede">
        React · FastAPI · AWS Bedrock Agent · Semantic Layer · PostgreSQL
      </p>
      <p className="status">
        Backend: <span>{health}</span>
      </p>
    </main>
  )
}

export default App
