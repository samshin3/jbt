import { useState } from 'react'
import { login } from '../api/api'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!username.trim()) return
    setLoading(true)
    setError(null)
    try {
      await login(username.trim())
      onLogin(username.trim())
    } catch (err) {
      setError("Login failed. Check your username and try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', background: '#f5f4f0',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: "'DM Sans', sans-serif"
    }}>
      <div style={{
        background: 'white', borderRadius: '16px', padding: '48px',
        width: '380px', boxShadow: '0 4px 24px rgba(0,0,0,0.08)'
      }}>
        <h1 style={{ fontSize: '24px', fontWeight: '700', margin: '0 0 8px', letterSpacing: '-0.5px' }}>
          Japan Budget Tracker
        </h1>
        <p style={{ color: '#888', fontSize: '14px', margin: '0 0 32px' }}>
          Sign in to manage your group expenses (Use username 'Guest' to test)
        </p>

        <form onSubmit={handleSubmit}>
          <label style={{ fontSize: '13px', fontWeight: '500', color: '#444', display: 'block', marginBottom: '6px' }}>
            Username
          </label>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="Enter your username"
            style={{
              width: '100%', padding: '12px', border: '1.5px solid #e5e5e5',
              borderRadius: '10px', fontSize: '14px', outline: 'none',
              boxSizing: 'border-box', marginBottom: '16px', transition: 'border-color 0.2s'
            }}
            onFocus={e => e.target.style.borderColor = '#222'}
            onBlur={e => e.target.style.borderColor = '#e5e5e5'}
          />
          {error && (
            <p style={{ color: '#c62828', fontSize: '13px', marginBottom: '12px' }}>{error}</p>
          )}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '13px', background: loading ? '#888' : '#111',
              color: 'white', border: 'none', borderRadius: '10px',
              fontSize: '14px', fontWeight: '600', cursor: loading ? 'not-allowed' : 'pointer',
              letterSpacing: '0.2px', transition: 'background 0.2s'
            }}
          >
            {loading ? 'Signing in...' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}
