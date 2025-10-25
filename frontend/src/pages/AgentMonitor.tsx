import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Header } from '../components/Header'
import { RewardChart } from '../components/RewardChart'
import { agentApi } from '../api/endpoints'
import { formatDate, formatNumber } from '../utils/formatters'
import { useWebSocket } from '../hooks/useWebSocket'
import type { AgentRun } from '../types/api'

export function AgentMonitor() {
  const { runId } = useParams<{ runId: string }>()
  const [agentRun, setAgentRun] = useState<AgentRun | null>(null)
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

  const { subscribe } = useWebSocket(WS_URL, {
    onMessage: (message) => {
      console.log('WebSocket message:', message)
      if (message.type === 'agent_metric' && message.agent_run_id === runId) {
        // Refresh stats when new metric arrives
        fetchAgentStats()
      }
    },
  })

  const fetchAgentStats = useCallback(async () => {
    if (!runId) return
    setLoading(true)

    try {
      const response = await agentApi.getStats(runId, { limit: 1000 })
      setAgentRun(response.data.agent_run)
      const s = response.data.summary || {}
      // Normalize summary numeric fields to numbers to keep formatters safe
      const normalizedSummary = {
        total_steps: Number(s.total_steps ?? 0),
        total_episodes: Number(s.total_episodes ?? 0),
        avg_episode_reward:
          typeof s.avg_episode_reward === 'number'
            ? s.avg_episode_reward
            : parseFloat(s.avg_episode_reward ?? '0'),
        max_drawdown:
          typeof s.max_drawdown === 'number'
            ? s.max_drawdown
            : parseFloat(s.max_drawdown ?? '0'),
        final_sharpe:
          typeof s.final_sharpe === 'number'
            ? s.final_sharpe
            : parseFloat(s.final_sharpe ?? '0'),
      }
      setSummary(normalizedSummary)
    } catch (err) {
      console.error('Failed to fetch agent stats', err)
    } finally {
      setLoading(false)
    }
  }, [runId])

  useEffect(() => {
    if (runId) {
      fetchAgentStats()
      // Subscribe to agent metrics
      subscribe(`agent_stats:${runId}`)
    }
  }, [runId, fetchAgentStats, subscribe])

  const handleStop = async () => {
    if (!runId) return
    if (!confirm('Are you sure you want to stop this agent?')) return

    try {
      await agentApi.stop(runId)
      alert('Agent stopped successfully!')
      navigate('/')
    } catch (err: any) {
      alert('Failed to stop agent: ' + err.message)
    }
  }

  const handleDownload = () => {
    // Simple CSV download
    alert('CSV download feature coming soon!')
  }

  if (loading) {
    return (
      <div>
        <Header />
        <div style={styles.loading}>Loading...</div>
      </div>
    )
  }

  if (!agentRun) {
    return (
      <div>
        <Header />
        <div style={styles.error}>Agent run not found</div>
      </div>
    )
  }

  return (
    <div>
      <Header />
      <div style={styles.container}>
        <div style={styles.header}>
          <div>
            <h2 style={styles.title}>Agent Monitor</h2>
            <div style={styles.info}>
              <span style={styles.infoItem}>
                <strong>Algorithm:</strong> {agentRun.algorithm}
              </span>
              <span style={styles.infoItem}>
                <strong>Mode:</strong> {agentRun.mode}
              </span>
              <span style={styles.infoItem}>
                <strong>Status:</strong>{' '}
                <span style={{
                  color: agentRun.status === 'running' ? '#4caf50' : '#999',
                  fontWeight: '600',
                }}>
                  {agentRun.status.toUpperCase()}
                </span>
              </span>
              <span style={styles.infoItem}>
                <strong>Started:</strong> {formatDate(agentRun.start_time)}
              </span>
              {agentRun.end_time && (
                <span style={styles.infoItem}>
                  <strong>Ended:</strong> {formatDate(agentRun.end_time)}
                </span>
              )}
            </div>
          </div>
          <div style={styles.controls}>
            {agentRun.status === 'running' && (
              <button onClick={handleStop} style={styles.stopButton}>
                Stop Agent
              </button>
            )}
            <button onClick={handleDownload} style={styles.downloadButton}>
              Download Stats
            </button>
          </div>
        </div>

        <div style={styles.chartContainer}>
          {runId && <RewardChart agentRunId={runId} />}
        </div>

        {summary && (
          <div style={styles.metricsGrid}>
            <div style={styles.metricCard}>
              <div style={styles.metricLabel}>Total Steps</div>
              <div style={styles.metricValue}>{summary.total_steps || 0}</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricLabel}>Total Episodes</div>
              <div style={styles.metricValue}>{summary.total_episodes || 0}</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricLabel}>Avg Episode Reward</div>
              <div style={styles.metricValue}>
                {formatNumber(summary.avg_episode_reward || 0)}
              </div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricLabel}>Max Drawdown</div>
              <div style={styles.metricValue}>
                {formatNumber((summary.max_drawdown || 0) * 100)}%
              </div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricLabel}>Final Sharpe Ratio</div>
              <div style={styles.metricValue}>
                {formatNumber(summary.final_sharpe || 0)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginTop: '80px',
    padding: '20px',
    maxWidth: '1400px',
    margin: '80px auto 20px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '30px',
  },
  title: {
    margin: '0 0 12px 0',
    fontSize: '28px',
  },
  info: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '20px',
    fontSize: '14px',
  },
  infoItem: {},
  controls: {
    display: 'flex',
    gap: '12px',
  },
  stopButton: {
    padding: '10px 20px',
    backgroundColor: '#f44336',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  downloadButton: {
    padding: '10px 20px',
    backgroundColor: '#1976d2',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  chartContainer: {
    marginBottom: '30px',
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
  },
  metricCard: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  metricLabel: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '8px',
  },
  metricValue: {
    fontSize: '24px',
    fontWeight: '600',
  },
  loading: {
    marginTop: '100px',
    textAlign: 'center',
    fontSize: '18px',
    color: '#999',
  },
  error: {
    marginTop: '100px',
    textAlign: 'center',
    fontSize: '18px',
    color: '#f44336',
  },
}
