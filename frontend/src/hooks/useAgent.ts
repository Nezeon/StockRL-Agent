import { useState, useEffect, useCallback } from 'react'
import { agentApi } from '../api/endpoints'
import type { AgentRun, StartAgentRequest } from '../types/api'

export function useAgent() {
  const [activeRuns, setActiveRuns] = useState<AgentRun[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await agentApi.getStatus()
      setActiveRuns(response.data.active_runs)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch agent status')
    } finally {
      setLoading(false)
    }
  }, [])

  const startAgent = useCallback(async (data: StartAgentRequest) => {
    setError(null)

    try {
      const response = await agentApi.start(data)
      await fetchStatus()
      return response.data.agent_run
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to start agent'
      setError(errorMsg)
      throw new Error(errorMsg)
    }
  }, [fetchStatus])

  const stopAgent = useCallback(async (runId: string) => {
    setError(null)

    try {
      await agentApi.stop(runId)
      await fetchStatus()
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to stop agent'
      setError(errorMsg)
      throw new Error(errorMsg)
    }
  }, [fetchStatus])

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  return { activeRuns, startAgent, stopAgent, fetchStatus, loading, error }
}
