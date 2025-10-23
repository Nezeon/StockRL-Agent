import React from 'react'
import type { Trade } from '../types/api'
import { formatCurrency, formatTimeAgo, formatNumber } from '../utils/formatters'

interface TradeTableProps {
  trades: Trade[]
  limit?: number
  showPagination?: boolean
}

export function TradeTable({ trades, limit = 10 }: TradeTableProps) {
  const displayTrades = trades.slice(0, limit)

  if (displayTrades.length === 0) {
    return <div style={styles.noData}>No trades yet</div>
  }

  return (
    <div style={styles.container}>
      <table style={styles.table}>
        <thead>
          <tr style={styles.headerRow}>
            <th style={styles.th}>Time</th>
            <th style={styles.th}>Ticker</th>
            <th style={styles.th}>Side</th>
            <th style={styles.th}>Quantity</th>
            <th style={styles.th}>Price</th>
            <th style={styles.th}>Total Value</th>
            <th style={styles.th}>Fees</th>
          </tr>
        </thead>
        <tbody>
          {displayTrades.map((trade, index) => (
            <tr key={trade.id} style={index % 2 === 0 ? styles.row : styles.rowAlt}>
              <td style={styles.td}>{formatTimeAgo(trade.executed_at)}</td>
              <td style={{ ...styles.td, fontWeight: '600' }}>{trade.ticker}</td>
              <td style={{
                ...styles.td,
                color: trade.side === 'BUY' ? '#4caf50' : '#f44336',
                fontWeight: '600',
              }}>
                {trade.side}
              </td>
              <td style={styles.td}>{formatNumber(trade.quantity)}</td>
              <td style={styles.td}>{formatCurrency(trade.price)}</td>
              <td style={styles.td}>{formatCurrency(trade.total_value)}</td>
              <td style={{ ...styles.td, fontSize: '12px', color: '#999' }}>
                {formatCurrency(trade.fees)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    overflow: 'hidden',
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
    padding: '12px 16px',
    textAlign: 'left',
    fontWeight: '600',
    color: '#333',
  },
  row: {
    backgroundColor: '#ffffff',
  },
  rowAlt: {
    backgroundColor: '#f9f9f9',
  },
  td: {
    padding: '12px 16px',
    borderBottom: '1px solid #f0f0f0',
  },
  noData: {
    textAlign: 'center',
    padding: '40px',
    color: '#999',
  },
}
