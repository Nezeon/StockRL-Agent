import React, { useState, useEffect } from 'react'
import { portfolioApi } from '../api/endpoints'
import { formatCurrency, formatNumber, formatPercent } from '../utils/formatters'
import { useWebSocket } from '../hooks/useWebSocket'

interface HoldingsCardProps {
  portfolioId: string
}

export function HoldingsCard({ portfolioId }: HoldingsCardProps) {
  const [positions, setPositions] = useState<any[]>([])
  const [cash, setCash] = useState(0)
  const [totalNav, setTotalNav] = useState(0)
  const [loading, setLoading] = useState(true)

  const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

  const { subscribe, unsubscribe } = useWebSocket(WS_URL, {
    onMessage: (message) => {
      if (message.type === 'portfolio_update' && message.channel === `portfolio_updates:${portfolioId}`) {
        // Refetch positions on update
        fetchPositions()
      }
    },
  })

  const fetchPositions = async () => {
    try {
      const response = await portfolioApi.getPositions(portfolioId)
      setPositions(response.data.positions)
      setCash(response.data.cash)
      setTotalNav(response.data.total_nav)
    } catch (err) {
      console.error('Failed to fetch positions', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPositions()
    subscribe(`portfolio_updates:${portfolioId}`)

    return () => {
      unsubscribe(`portfolio_updates:${portfolioId}`)
    }
  }, [portfolioId, subscribe, unsubscribe])

  if (loading) {
    return <div style={styles.message}>Loading...</div>
  }

  return (
    <div style={styles.container}>
      <h4 style={styles.title}>Current Holdings</h4>
      <table style={styles.table}>
        <thead>
          <tr style={styles.headerRow}>
            <th style={styles.th}>Ticker</th>
            <th style={styles.th}>Quantity</th>
            <th style={styles.th}>Avg Price</th>
            <th style={styles.th}>Current Price</th>
            <th style={styles.th}>Market Value</th>
            <th style={styles.th}>Unrealized P&L</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((position) => {
            const pnlColor = position.unrealized_pnl >= 0 ? '#4caf50' : '#f44336'
            return (
              <tr key={position.ticker} style={styles.row}>
                <td style={{ ...styles.td, fontWeight: '600' }}>{position.ticker}</td>
                <td style={styles.td}>{formatNumber(position.quantity)}</td>
                <td style={styles.td}>{formatCurrency(position.avg_purchase_price)}</td>
                <td style={styles.td}>{formatCurrency(position.current_price)}</td>
                <td style={styles.td}>{formatCurrency(position.market_value)}</td>
                <td style={{ ...styles.td, color: pnlColor, fontWeight: '600' }}>
                  {formatCurrency(position.unrealized_pnl)} ({formatPercent(position.unrealized_pnl_percent)})
                </td>
              </tr>
            )
          })}
          <tr style={styles.cashRow}>
            <td colSpan={4} style={{ ...styles.td, fontWeight: '600' }}>Cash</td>
            <td colSpan={2} style={{ ...styles.td, fontWeight: '600' }}>{formatCurrency(cash)}</td>
          </tr>
          <tr style={styles.totalRow}>
            <td colSpan={4} style={{ ...styles.td, fontWeight: 'bold', fontSize: '16px' }}>Total NAV</td>
            <td colSpan={2} style={{ ...styles.td, fontWeight: 'bold', fontSize: '16px' }}>
              {formatCurrency(totalNav)}
            </td>
          </tr>
        </tbody>
      </table>
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
    margin: '0 0 16px 0',
    fontSize: '18px',
    fontWeight: '600',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '14px',
  },
  headerRow: {
    borderBottom: '2px solid #e0e0e0',
  },
  th: {
    padding: '8px',
    textAlign: 'left',
    fontWeight: '600',
  },
  row: {},
  td: {
    padding: '8px',
    borderBottom: '1px solid #f0f0f0',
  },
  cashRow: {
    backgroundColor: '#e3f2fd',
  },
  totalRow: {
    borderTop: '2px solid #333',
  },
  message: {
    textAlign: 'center',
    padding: '40px',
    color: '#999',
  },
}
