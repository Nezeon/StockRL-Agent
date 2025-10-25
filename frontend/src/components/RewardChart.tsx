import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { agentApi } from '../api/endpoints'
import { useWebSocket } from '../hooks/useWebSocket'

interface RewardChartProps {
  agentRunId: string
}

export function RewardChart({ agentRunId }: RewardChartProps) {
  const [metrics, setMetrics] = useState<any[]>([])
  const [latestMetrics, setLatestMetrics] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

  const { subscribe, unsubscribe } = useWebSocket(WS_URL, {
    onMessage: (message) => {
      console.log('RewardChart received message:', message)
      if (message.type === 'agent_metric' && message.agent_run_id === agentRunId) {
        const newMetric = message.metric
        setLatestMetrics(newMetric)
        setMetrics((prev) => {
          const updated = [...prev, {
            step: newMetric.step,
            reward: newMetric.cumulative_reward,
            loss: newMetric.loss,
            nav: newMetric.portfolio_nav,
          }]
          // Keep last 100 points
          return updated.slice(-100)
        })
      }
    },
  })

  useEffect(() => {
    // Fetch initial data
    agentApi.getStats(agentRunId, { limit: 100 })
      .then((response) => {
        const metricsData = response.data.metrics || []
        const chartData = metricsData.map((m: any) => ({
          step: m.step,
          reward: m.cumulative_reward,
          loss: m.loss,
          nav: m.portfolio_nav,
        }))
        setMetrics(chartData)
        if (metricsData.length > 0) {
          setLatestMetrics(metricsData[metricsData.length - 1])
        }
      })
      .catch(() => {
        // No metrics yet
      })
      .finally(() => {
        setLoading(false)
      })

    // Subscribe to WebSocket updates
    subscribe(`agent_stats:${agentRunId}`)

    return () => {
      unsubscribe(`agent_stats:${agentRunId}`)
    }
  }, [agentRunId, subscribe, unsubscribe])

  if (loading) {
    return <div style={styles.message}>Loading...</div>
  }

  if (metrics.length === 0) {
    return <div style={styles.message}>Training starting...</div>
  }

  return (
    <div style={styles.container}>
      <div style={styles.metricsRow}>
        <div style={styles.metricBox}>
          <div style={styles.metricLabel}>Step</div>
          <div style={styles.metricValue}>{latestMetrics?.step || 0}</div>
        </div>
        <div style={styles.metricBox}>
          <div style={styles.metricLabel}>Reward</div>
          <div style={styles.metricValue}>{latestMetrics?.cumulative_reward?.toFixed(2) || 0}</div>
        </div>
        <div style={styles.metricBox}>
          <div style={styles.metricLabel}>Loss</div>
          <div style={styles.metricValue}>{latestMetrics?.loss?.toFixed(4) || 'N/A'}</div>
        </div>
        <div style={styles.metricBox}>
          <div style={styles.metricLabel}>NAV</div>
          <div style={styles.metricValue}>${latestMetrics?.portfolio_nav?.toFixed(2) || 0}</div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={metrics}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="step" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <Tooltip />
          <Legend />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="reward"
            stroke="#1976d2"
            strokeWidth={2}
            dot={false}
            name="Cumulative Reward"
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="loss"
            stroke="#f44336"
            strokeWidth={2}
            dot={false}
            name="Loss"
          />
        </LineChart>
      </ResponsiveContainer>
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
  metricsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '16px',
    marginBottom: '20px',
  },
  metricBox: {},
  metricLabel: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '4px',
  },
  metricValue: {
    fontSize: '20px',
    fontWeight: '600',
  },
  message: {
    textAlign: 'center',
    padding: '40px',
    color: '#999',
  },
}
