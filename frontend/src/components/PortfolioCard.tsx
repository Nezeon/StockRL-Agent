import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { agentApi } from '../api/endpoints'
import type { Portfolio } from '../types/api'
import { formatCurrency, formatPercent } from '../utils/formatters'

interface PortfolioCardProps {
  portfolio: Portfolio
  realtime?: boolean
}

export function PortfolioCard({ portfolio, realtime }: PortfolioCardProps) {
  const [navHistory, setNavHistory] = useState<any[]>([])

  useEffect(() => {
    // Fetch agent metrics to get NAV history
    if (portfolio) {
      // Find active agent run for this portfolio
      agentApi.getStatus().then((response) => {
        const activeRun = response.data.active_runs.find(
          (run) => run.portfolio_id === portfolio.id && run.status === 'running'
        )
        if (activeRun) {
          agentApi.getStats(activeRun.id, { limit: 100 }).then((statsResponse) => {
            const metrics = statsResponse.data.metrics || []
            const historyData = metrics.map((m: any) => ({
              timestamp: new Date(m.timestamp).getTime(),
              nav: m.portfolio_nav,
            }))
            setNavHistory(historyData)
          }).catch(() => {
            // No metrics yet
            setNavHistory([])
          })
        }
      }).catch(() => {
        // No active runs
        setNavHistory([])
      })
    }
  }, [portfolio])

  const pnlColor = portfolio.pnl >= 0 ? '#4caf50' : '#f44336'

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>{portfolio.name}</h2>
      <div style={styles.metricsGrid}>
        <div style={styles.metric}>
          <div style={styles.metricLabel}>NAV</div>
          <div style={styles.metricValue}>{formatCurrency(portfolio.nav)}</div>
        </div>
        <div style={styles.metric}>
          <div style={styles.metricLabel}>P&L</div>
          <div style={{ ...styles.metricValue, color: pnlColor }}>
            {formatCurrency(portfolio.pnl)} ({formatPercent(portfolio.pnl_percent)})
          </div>
        </div>
        <div style={styles.metric}>
          <div style={styles.metricLabel}>Cash</div>
          <div style={styles.metricValue}>{formatCurrency(portfolio.current_cash)}</div>
        </div>
        <div style={styles.metric}>
          <div style={styles.metricLabel}>Agent Status</div>
          <div style={styles.badge}>
            {realtime ? 'Running' : 'Stopped'}
          </div>
        </div>
      </div>
      {navHistory.length > 0 ? (
        <div style={styles.chartContainer}>
          <h4 style={styles.chartTitle}>NAV History</h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={navHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(ts) => new Date(ts).toLocaleTimeString()}
              />
              <YAxis domain={['auto', 'auto']} />
              <Tooltip
                labelFormatter={(ts) => new Date(ts).toLocaleString()}
                formatter={(value: any) => formatCurrency(value)}
              />
              <Line type="monotone" dataKey="nav" stroke="#1976d2" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div style={styles.noData}>No historical data available</div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  title: {
    margin: '0 0 20px 0',
    fontSize: '24px',
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '20px',
    marginBottom: '30px',
  },
  metric: {},
  metricLabel: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '4px',
  },
  metricValue: {
    fontSize: '24px',
    fontWeight: '600',
  },
  badge: {
    display: 'inline-block',
    padding: '4px 12px',
    backgroundColor: '#4caf50',
    color: 'white',
    borderRadius: '12px',
    fontSize: '14px',
    fontWeight: '500',
  },
  chartContainer: {
    marginTop: '20px',
  },
  chartTitle: {
    margin: '0 0 16px 0',
    fontSize: '16px',
    fontWeight: '600',
  },
  noData: {
    textAlign: 'center',
    padding: '40px',
    color: '#999',
  },
}
