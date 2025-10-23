import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Header } from '../components/Header'
import { portfolioApi } from '../api/endpoints'

export function PortfolioSettings() {
  const [name, setName] = useState('')
  const [initialBudget, setInitialBudget] = useState<number>(10000)
  const [tickers, setTickers] = useState<string>('AAPL,GOOGL,MSFT,TSLA')
  const [riskProfile, setRiskProfile] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const portfolioId = searchParams.get('id')

  useEffect(() => {
    if (portfolioId) {
      // Load existing portfolio
      portfolioApi.get(portfolioId).then((response) => {
        const portfolio = response.data
        setName(portfolio.name)
        setInitialBudget(portfolio.initial_budget)
        setTickers(portfolio.tickers.join(','))
        setRiskProfile(portfolio.risk_profile)
      }).catch((err) => {
        console.error('Failed to load portfolio:', err)
        setError('Failed to load portfolio')
      })
    }
  }, [portfolioId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // Validate
    if (name.length < 1 || name.length > 100) {
      setError('Portfolio name must be between 1 and 100 characters')
      setLoading(false)
      return
    }

    if (initialBudget < 0.01) {
      setError('Initial budget must be at least $0.01')
      setLoading(false)
      return
    }

    const tickerList = tickers.split(',').map((t) => t.trim()).filter((t) => t.length > 0)
    if (tickerList.length < 1 || tickerList.length > 20) {
      setError('You must provide between 1 and 20 tickers')
      setLoading(false)
      return
    }

    try {
      if (portfolioId) {
        // Update existing
        await portfolioApi.update(portfolioId, {
          name,
          tickers: tickerList,
          risk_profile: riskProfile,
        })
      } else {
        // Create new
        await portfolioApi.create({
          name,
          initial_budget: initialBudget,
          tickers: tickerList,
          risk_profile: riskProfile,
        })
      }
      navigate('/')
    } catch (err: any) {
      console.error('Failed to create portfolio:', err)
      alert('Failed to create portfolio. Please try again.')
      setError(err.response?.data?.detail || 'Failed to save portfolio')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Header />
      <div style={styles.container}>
        <div style={styles.card}>
          <h2 style={styles.title}>
            {portfolioId ? 'Edit Portfolio' : 'Create Portfolio'}
          </h2>
          <form onSubmit={handleSubmit} style={styles.form}>
            <div style={styles.field}>
              <label style={styles.label}>Portfolio Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                style={styles.input}
                disabled={loading}
              />
            </div>

            {!portfolioId && (
              <div style={styles.field}>
                <label style={styles.label}>Initial Budget ($)</label>
                <input
                  type="number"
                  value={initialBudget}
                  onChange={(e) => setInitialBudget(parseFloat(e.target.value))}
                  required
                  min="0.01"
                  step="0.01"
                  style={styles.input}
                  disabled={loading}
                />
              </div>
            )}

            <div style={styles.field}>
              <label style={styles.label}>Tickers (comma-separated)</label>
              <input
                type="text"
                value={tickers}
                onChange={(e) => setTickers(e.target.value)}
                required
                style={styles.input}
                placeholder="AAPL,GOOGL,MSFT"
                disabled={loading}
              />
              <small style={styles.help}>Enter 1-20 ticker symbols separated by commas</small>
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Risk Profile</label>
              <select
                value={riskProfile}
                onChange={(e) => setRiskProfile(e.target.value as any)}
                style={styles.select}
                disabled={loading}
              >
                <option value="conservative">Conservative (0.1% fees)</option>
                <option value="moderate">Moderate (0.05% fees)</option>
                <option value="aggressive">Aggressive (0.02% fees)</option>
              </select>
            </div>

            {error && <div style={styles.error}>{error}</div>}

            <div style={styles.buttons}>
              <button type="submit" style={styles.saveButton} disabled={loading}>
                {loading ? 'Saving...' : 'Save'}
              </button>
              <button
                type="button"
                onClick={() => navigate('/')}
                style={styles.cancelButton}
                disabled={loading}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginTop: '80px',
    padding: '20px',
    maxWidth: '600px',
    margin: '80px auto 20px',
  },
  card: {
    backgroundColor: 'white',
    padding: '40px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  title: {
    margin: '0 0 30px 0',
    fontSize: '24px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
  },
  field: {
    marginBottom: '20px',
  },
  label: {
    display: 'block',
    marginBottom: '6px',
    fontSize: '14px',
    fontWeight: '500',
  },
  input: {
    width: '100%',
    padding: '10px',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    fontSize: '14px',
  },
  select: {
    width: '100%',
    padding: '10px',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    fontSize: '14px',
  },
  help: {
    display: 'block',
    marginTop: '4px',
    fontSize: '12px',
    color: '#999',
  },
  error: {
    color: '#f44336',
    fontSize: '14px',
    marginBottom: '16px',
  },
  buttons: {
    display: 'flex',
    gap: '12px',
  },
  saveButton: {
    flex: 1,
    padding: '12px',
    backgroundColor: '#1976d2',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  cancelButton: {
    flex: 1,
    padding: '12px',
    backgroundColor: '#999',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
  },
}
