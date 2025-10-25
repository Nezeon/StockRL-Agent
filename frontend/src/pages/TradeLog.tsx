import React, { useState, useEffect, useCallback } from 'react'
import { Header } from '../components/Header'
import { TradeTable } from '../components/TradeTable'
import { portfolioApi } from '../api/endpoints'
import type { Trade } from '../types/api'

export function TradeLog() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [portfolioId, setPortfolioId] = useState<string | null>(null)
  const [ticker, setTicker] = useState<string>('')
  const [side, setSide] = useState<'BUY' | 'SELL' | ''>('')
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)

  const limit = 50

  const fetchPortfolio = useCallback(async () => {
    try {
      const response = await portfolioApi.list()
      const portfolios = response.data.portfolios
      if (portfolios.length > 0) {
        setPortfolioId(portfolios[0].id)
      }
    } catch (err) {
      console.error('Failed to fetch portfolio', err)
    }
  }, [])

  const fetchTrades = useCallback(async () => {
    if (!portfolioId) return
    setLoading(true)

    try {
      const params: any = {
        limit,
        offset: page * limit,
      }
      if (ticker) params.ticker = ticker
      if (side) params.side = side
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate

      const response = await portfolioApi.getTrades(portfolioId, params)
      setTrades(response.data.trades)
      setTotal(response.data.total)
    } catch (err) {
      console.error('Failed to fetch trades', err)
    } finally {
      setLoading(false)
    }
  }, [portfolioId, page, ticker, side, startDate, endDate])

  useEffect(() => {
    fetchPortfolio()
  }, [fetchPortfolio])

  useEffect(() => {
    if (portfolioId) {
      fetchTrades()
    }
  }, [portfolioId, page, fetchTrades])

  const handleApplyFilters = () => {
    setPage(0)
    fetchTrades()
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div>
      <Header />
      <div style={styles.container}>
        <h2 style={styles.title}>Trade History</h2>

        <div style={styles.filters}>
          <div style={styles.filterField}>
            <label style={styles.label}>Ticker</label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              style={styles.input}
              placeholder="e.g., AAPL"
            />
          </div>
          <div style={styles.filterField}>
            <label style={styles.label}>Side</label>
            <select value={side} onChange={(e) => setSide(e.target.value as any)} style={styles.select}>
              <option value="">All</option>
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </div>
          <div style={styles.filterField}>
            <label style={styles.label}>Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={styles.input}
            />
          </div>
          <div style={styles.filterField}>
            <label style={styles.label}>End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={styles.input}
            />
          </div>
          <button onClick={handleApplyFilters} style={styles.applyButton}>
            Apply Filters
          </button>
        </div>

        {loading ? (
          <div style={styles.loading}>Loading...</div>
        ) : (
          <>
            <TradeTable trades={trades} limit={limit} />
            {totalPages > 1 && (
              <div style={styles.pagination}>
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 0}
                  style={styles.pageButton}
                >
                  Previous
                </button>
                <span style={styles.pageInfo}>
                  Page {page + 1} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page >= totalPages - 1}
                  style={styles.pageButton}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginTop: '80px',
    padding: '20px',
    maxWidth: '1200px',
    margin: '80px auto 20px',
  },
  title: {
    margin: '0 0 30px 0',
    fontSize: '28px',
  },
  filters: {
    display: 'flex',
    gap: '12px',
    marginBottom: '30px',
    flexWrap: 'wrap',
    alignItems: 'flex-end',
  },
  filterField: {
    flex: '1 1 200px',
  },
  label: {
    display: 'block',
    marginBottom: '6px',
    fontSize: '14px',
    fontWeight: '500',
  },
  input: {
    width: '100%',
    padding: '8px',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    fontSize: '14px',
  },
  select: {
    width: '100%',
    padding: '8px',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    fontSize: '14px',
  },
  applyButton: {
    padding: '8px 20px',
    backgroundColor: '#1976d2',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    height: '38px',
  },
  loading: {
    textAlign: 'center',
    padding: '40px',
    color: '#999',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '20px',
    marginTop: '30px',
  },
  pageButton: {
    padding: '8px 16px',
    border: '1px solid #e0e0e0',
    backgroundColor: 'white',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  pageInfo: {
    fontSize: '14px',
    color: '#666',
  },
}
