import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export function Header() {
  const { user, logout } = useAuth()
  const [showMenu, setShowMenu] = useState(false)

  return (
    <header style={styles.header}>
      <div style={styles.container}>
        <div style={styles.logo}>
          <Link to="/" style={styles.logoLink}>StockRL Agent</Link>
        </div>
        <nav style={styles.nav}>
          <Link to="/" style={styles.navLink}>Dashboard</Link>
          <Link to="/trades" style={styles.navLink}>Trade Log</Link>
        </nav>
        <div style={styles.userMenu}>
          <button
            style={styles.userButton}
            onClick={() => setShowMenu(!showMenu)}
          >
            {user?.username}
          </button>
          {showMenu && (
            <div style={styles.dropdown}>
              <Link to="/portfolio/settings" style={styles.dropdownItem}>Settings</Link>
              <button onClick={logout} style={styles.dropdownItem}>Logout</button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

const styles: Record<string, React.CSSProperties> = {
  header: {
    backgroundColor: '#1976d2',
    color: 'white',
    height: '60px',
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 1000,
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: '100%',
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '0 20px',
  },
  logo: {
    fontSize: '20px',
    fontWeight: 'bold',
  },
  logoLink: {
    color: 'white',
    textDecoration: 'none',
  },
  nav: {
    display: 'flex',
    gap: '30px',
  },
  navLink: {
    color: 'white',
    textDecoration: 'none',
    fontSize: '16px',
  },
  userMenu: {
    position: 'relative',
  },
  userButton: {
    backgroundColor: 'transparent',
    color: 'white',
    border: 'none',
    fontSize: '16px',
    padding: '8px 16px',
    cursor: 'pointer',
  },
  dropdown: {
    position: 'absolute',
    top: '100%',
    right: 0,
    backgroundColor: 'white',
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
    borderRadius: '4px',
    marginTop: '8px',
    minWidth: '150px',
  },
  dropdownItem: {
    display: 'block',
    width: '100%',
    padding: '12px 16px',
    border: 'none',
    background: 'none',
    textAlign: 'left',
    color: '#333',
    textDecoration: 'none',
    cursor: 'pointer',
  },
}
