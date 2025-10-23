import { useState, useEffect, useCallback } from 'react'
import { portfolioApi } from '../api/endpoints'
import type { Portfolio } from '../types/api'

export function usePortfolio(portfolioId: string | null) {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPortfolio = useCallback(async () => {
    if (!portfolioId) {
      setPortfolio(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await portfolioApi.get(portfolioId)
      setPortfolio(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch portfolio')
    } finally {
      setLoading(false)
    }
  }, [portfolioId])

  useEffect(() => {
    fetchPortfolio()
  }, [fetchPortfolio])

  const refetch = useCallback(() => {
    fetchPortfolio()
  }, [fetchPortfolio])

  return { portfolio, loading, error, refetch }
}
