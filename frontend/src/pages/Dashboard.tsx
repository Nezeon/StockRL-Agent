import React, { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Header } from '../components/Header'
import { PortfolioCard } from '../components/PortfolioCard'
import { PriceChart } from '../components/PriceChart'
import { RewardChart } from '../components/RewardChart'
import { TradeTable } from '../components/TradeTable'
import { HoldingsCard } from '../components/HoldingsCard'
import { AgentControls } from '../components/AgentControls'
import { portfolioApi } from '../api/endpoints'
import { useAgent } from '../hooks/useAgent'
import { useWebSocket } from '../hooks/useWebSocket'
import type { Portfolio, Trade } from '../types/api'

export function Dashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const { activeRuns, startAgent, stopAgent } = useAgent()

  const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

  const { subscribe } = useWebSocket(WS_URL, {
    onMessage: (message) => {
      if (message.type === 'portfolio_update' && portfolio) {
        // Update portfolio data
        fetchPortfolio()
      }
      if (message.type === 'trade_executed' && portfolio) {
        // Fetch new trades
        fetchTrades()
      }
    },
  })

  const fetchPortfolio = useCallback(async () => {
    try {
      const response = await portfolioApi.list()
      const portfolios = response.data.portfolios
      if (portfolios.length > 0) {
        const firstPortfolio = portfolios[0]
        setPortfolio(firstPortfolio)
        // Subscribe to portfolio updates
        subscribe(`portfolio_updates:${firstPortfolio.id}`)
        subscribe(`trade_executed:${firstPortfolio.id}`)
      }
    } catch (err) {
      console.error('Failed to fetch portfolio', err)
    } finally {
      setLoading(false)
    }
  }, [subscribe])

  const fetchTrades = useCallback(async () => {
    if (!portfolio) return
    try {
      const response = await portfolioApi.getTrades(portfolio.id, { limit: 10 })
      setTrades(response.data.trades)
    } catch (err) {
      console.error('Failed to fetch trades', err)
    }
  }, [portfolio])

  useEffect(() => {
    fetchPortfolio()
  }, [fetchPortfolio])

  useEffect(() => {
    if (portfolio) {
      fetchTrades()
    }
  }, [portfolio, fetchTrades])

  const handleStartAgent = async (config: any) => {
    try {
      await startAgent(config)
      alert('Agent started successfully!')
    } catch (err: any) {
      alert('Failed to start agent: ' + err.message)
    }
  }

  const handleStopAgent = async () => {
    if (activeRuns.length > 0) {
      try {
        await stopAgent(activeRuns[0].id)
        alert('Agent stopped successfully!')
      } catch (err: any) {
        alert('Failed to stop agent: ' + err.message)
      }
    }
  }

  if (loading) {
    return (
      <div>
        <Header />
        <div style={styles.loading}>Loading...</div>
      </div>
    )
  }

  if (!portfolio) {
    return (
      <div>
        <Header />
        <div style={styles.emptyState}>
          <h2>Welcome to StockRL Agent</h2>
          <p>Create your first portfolio to get started.</p>
          <Link to="/portfolio/settings">
            <button style={styles.createButton}>Create Portfolio</button>
          </Link>
        </div>
      </div>
    )
  }

  const activeRun = activeRuns.find((run) => run.portfolio_id === portfolio.id && run.status === 'running')

  return (
    <div>
      <Header />
      <div style={styles.container}>
        <div style={styles.grid}>
          <div style={styles.cardWide}>
            <PortfolioCard portfolio={portfolio} realtime={!!activeRun} />
          </div>
          <div style={styles.card}>
            <PriceChart ticker={portfolio.tickers[0] || 'AAPL'} />
          </div>
          <div style={styles.card}>
            {activeRun ? (
              <RewardChart agentRunId={activeRun.id} />
            ) : (
              <AgentControls
                portfolioId={portfolio.id}
                onStart={handleStartAgent}
                onStop={handleStopAgent}
                agentRunning={false}
              />
            )}
          </div>
          <div style={styles.card}>
            <h4 style={styles.cardTitle}>Recent Trades</h4>
            <TradeTable trades={trades} limit={10} />
          </div>
          <div style={styles.card}>
            <HoldingsCard portfolioId={portfolio.id} />
          </div>
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginTop: '60px',
    padding: '20px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '20px',
    maxWidth: '1400px',
    margin: '0 auto',
  },
  cardWide: {
    gridColumn: '1 / -1',
  },
  card: {},
  cardTitle: {
    margin: '0 0 16px 0',
    fontSize: '18px',
    fontWeight: '600',
  },
  loading: {
    marginTop: '100px',
    textAlign: 'center',
    fontSize: '18px',
    color: '#999',
  },
  emptyState: {
    marginTop: '100px',
    textAlign: 'center',
    padding: '40px',
  },
  createButton: {
    marginTop: '20px',
    padding: '12px 24px',
    backgroundColor: '#1976d2',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
  },
}
