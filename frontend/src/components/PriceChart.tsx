import React, { useState, useEffect } from 'react'
import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { marketApi } from '../api/endpoints'
import type { OHLCV } from '../types/api'

interface PriceChartProps {
  ticker: string
  interval?: '1m' | '5m' | '1h' | '1d'
}

export function PriceChart({ ticker, interval = '1d' }: PriceChartProps) {
  const [data, setData] = useState<OHLCV[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [range, setRange] = useState('1W')

  useEffect(() => {
    fetchData()
  }, [ticker, range])

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    const endDate = new Date()
    let startDate = new Date()

    switch (range) {
      case '1D':
        startDate.setDate(endDate.getDate() - 1)
        break
      case '1W':
        startDate.setDate(endDate.getDate() - 7)
        break
      case '1M':
        startDate.setMonth(endDate.getMonth() - 1)
        break
      case '3M':
        startDate.setMonth(endDate.getMonth() - 3)
        break
    }

    try {
      const response = await marketApi.getHistory(ticker, {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        interval,
      })
      setData(response.data.data)
    } catch (err: any) {
      setError('Unable to load data')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h4 style={styles.title}>{ticker} Price Chart</h4>
        <div style={styles.rangeSelector}>
          {['1D', '1W', '1M', '3M'].map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              style={{
                ...styles.rangeButton,
                ...(range === r ? styles.rangeButtonActive : {}),
              }}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {loading && <div style={styles.message}>Loading...</div>}
      {error && <div style={styles.message}>{error}</div>}

      {!loading && !error && data.length > 0 && (
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(ts) => new Date(ts).toLocaleDateString()}
            />
            <YAxis yAxisId="price" />
            <YAxis yAxisId="volume" orientation="right" />
            <Tooltip
              labelFormatter={(ts) => new Date(ts).toLocaleString()}
              formatter={(value: any, name: string) =>
                name === 'volume' ? value.toLocaleString() : `$${value.toFixed(2)}`
              }
            />
            <Legend />
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="close"
              stroke="#1976d2"
              strokeWidth={2}
              dot={false}
              name="Price"
            />
            <Bar yAxisId="volume" dataKey="volume" fill="#e0e0e0" opacity={0.5} name="Volume" />
          </ComposedChart>
        </ResponsiveContainer>
      )}

      {!loading && !error && data.length === 0 && (
        <div style={styles.message}>No data available</div>
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
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  title: {
    margin: 0,
    fontSize: '18px',
    fontWeight: '600',
  },
  rangeSelector: {
    display: 'flex',
    gap: '8px',
  },
  rangeButton: {
    padding: '6px 12px',
    border: '1px solid #e0e0e0',
    backgroundColor: 'white',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  rangeButtonActive: {
    backgroundColor: '#1976d2',
    color: 'white',
    borderColor: '#1976d2',
  },
  message: {
    textAlign: 'center',
    padding: '40px',
    color: '#999',
  },
}
