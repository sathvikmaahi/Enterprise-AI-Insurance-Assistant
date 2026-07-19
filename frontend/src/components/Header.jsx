import './Header.css'

export default function Header({ session, onLogout }) {
  return (
    <header className="header">
      <div className="header__brand-block">
        <p className="header__brand">Enterprise AI Insurance Assistant</p>
        {/* <p className="header__sub">Semantic layer · Bedrock · PostgreSQL</p> */}
      </div>
      <div className="header__meta">
        <span className={`role-badge role-badge--${session.role}`}>
          {session.role}
        </span>
        <span className="header__user">{session.username}</span>
        <button type="button" className="header__logout" onClick={onLogout}>
          Log out
        </button>
      </div>
    </header>
  )
}
