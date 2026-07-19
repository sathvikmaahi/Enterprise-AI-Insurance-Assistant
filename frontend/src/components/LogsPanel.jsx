import { useCallback, useEffect, useState } from 'react'
import { ApiError, getLogs } from '../api'
import './LogsPanel.css'

function formatTime(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return iso
  }
}

export default function LogsPanel({
  session,
  refreshKey,
  onUnauthorized,
}) {
  const [entries, setEntries] = useState([])
  const [error, setError] = useState(null)
  const [flash, setFlash] = useState(false)

  const load = useCallback(async () => {
    try {
      const data = await getLogs(session.access_token, 50)
      setEntries(data.entries || [])
      setError(null)
      setFlash(true)
      window.setTimeout(() => setFlash(false), 600)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        onUnauthorized()
        return
      }
      setError(err instanceof ApiError ? err.message : 'Failed to load logs')
    }
  }, [session.access_token, onUnauthorized])

  useEffect(() => {
    load()
  }, [load, refreshKey])

  return (
    <aside className={`logs ${flash ? 'logs--flash' : ''}`} aria-label="Audit logs">
      <div className="logs__head">
        <h2>Audit log</h2>
        <button type="button" className="logs__refresh" onClick={load}>
          Refresh
        </button>
      </div>
      {error ? <p className="logs__error">{error}</p> : null}
      <div className="logs__table-wrap">
        <table className="logs__table">
          <thead>
            <tr>
              <th>Time</th>
              <th>User</th>
              <th>Role</th>
              <th>Decision</th>
              <th>Concept</th>
              <th>ms</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {entries.length === 0 ? (
              <tr>
                <td colSpan={7} className="logs__empty">
                  No entries yet
                </td>
              </tr>
            ) : (
              entries.map((entry, index) => (
                <tr key={`${entry.timestamp}-${index}`}>
                  <td>{formatTime(entry.timestamp)}</td>
                  <td>{entry.username}</td>
                  <td>{entry.role}</td>
                  <td>
                    <span className={`decision decision--${entry.decision}`}>
                      {entry.decision}
                    </span>
                  </td>
                  <td>{entry.concept || '—'}</td>
                  <td>{entry.latency_ms}</td>
                  <td className="logs__reason" title={entry.reason || ''}>
                    {entry.reason || '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </aside>
  )
}
