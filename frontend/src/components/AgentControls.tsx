import React, { useState } from 'react'
import type { StartAgentRequest } from '../types/api'

interface AgentControlsProps {
  portfolioId: string
  onStart: (config: StartAgentRequest) => void
  onStop: () => void
  agentRunning?: boolean
}

export function AgentControls({ portfolioId, onStart, onStop, agentRunning }: AgentControlsProps) {
  const [algorithm, setAlgorithm] = useState<'PPO' | 'DQN' | 'A2C' | 'SB3_PPO' | 'SB3_A2C'>('PPO')
  const [mode, setMode] = useState<'train' | 'live'>('train')
  const [actionSpace, setActionSpace] = useState<'discrete' | 'continuous'>('discrete')
  const [learningRate, setLearningRate] = useState(0.0003)
  const [batchSize, setBatchSize] = useState(64)
  const [gamma, setGamma] = useState(0.99)
  const [episodes, setEpisodes] = useState(100)
  const [showHyperparams, setShowHyperparams] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const handleStart = () => {
    if (mode === 'live') {
      setShowConfirm(true)
      return
    }
    submitStart()
  }

  const submitStart = () => {
    const config: StartAgentRequest = {
      portfolio_id: portfolioId,
      algorithm,
      mode,
      action_space_type: actionSpace,
      hyperparameters: {
        learning_rate: learningRate,
        batch_size: batchSize,
        gamma,
        episodes,
      },
    }
    onStart(config)
    setShowConfirm(false)
  }

  if (agentRunning) {
    return (
      <div style={styles.container}>
        <div style={styles.statusBadge}>Agent Running</div>
        <p style={styles.info}>Algorithm: {algorithm} | Mode: {mode}</p>
        <button onClick={onStop} style={styles.stopButton}>
          Stop Agent
        </button>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <h4 style={styles.title}>Agent Configuration</h4>

      <div style={styles.field}>
        <label style={styles.label}>Algorithm</label>
        <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value as any)} style={styles.select}>
          <option value="PPO">PPO</option>
          <option value="DQN">DQN</option>
          <option value="A2C">A2C</option>
          <option value="SB3_PPO">Stable-Baselines3 PPO</option>
          <option value="SB3_A2C">Stable-Baselines3 A2C</option>
        </select>
      </div>

      <div style={styles.field}>
        <label style={styles.label}>Mode</label>
        <div style={styles.radioGroup}>
          <label style={styles.radioLabel}>
            <input
              type="radio"
              value="train"
              checked={mode === 'train'}
              onChange={(e) => setMode(e.target.value as any)}
            />
            Training
          </label>
          <label style={styles.radioLabel}>
            <input
              type="radio"
              value="live"
              checked={mode === 'live'}
              onChange={(e) => setMode(e.target.value as any)}
            />
            Live
          </label>
        </div>
      </div>

      <div style={styles.field}>
        <label style={styles.label}>Action Space</label>
        <div style={styles.radioGroup}>
          <label style={styles.radioLabel}>
            <input
              type="radio"
              value="discrete"
              checked={actionSpace === 'discrete'}
              onChange={(e) => setActionSpace(e.target.value as any)}
            />
            Discrete
          </label>
          <label style={styles.radioLabel}>
            <input
              type="radio"
              value="continuous"
              checked={actionSpace === 'continuous'}
              onChange={(e) => setActionSpace(e.target.value as any)}
            />
            Continuous
          </label>
        </div>
      </div>

      <button onClick={() => setShowHyperparams(!showHyperparams)} style={styles.toggleButton}>
        {showHyperparams ? 'Hide' : 'Show'} Hyperparameters
      </button>

      {showHyperparams && (
        <div style={styles.hyperparams}>
          <div style={styles.field}>
            <label style={styles.label}>Learning Rate</label>
            <input
              type="number"
              value={learningRate}
              onChange={(e) => setLearningRate(parseFloat(e.target.value))}
              step="0.0001"
              style={styles.input}
            />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Batch Size</label>
            <input
              type="number"
              value={batchSize}
              onChange={(e) => setBatchSize(parseInt(e.target.value))}
              style={styles.input}
            />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Gamma</label>
            <input
              type="number"
              value={gamma}
              onChange={(e) => setGamma(parseFloat(e.target.value))}
              step="0.01"
              style={styles.input}
            />
          </div>
          {mode === 'train' && (
            <div style={styles.field}>
              <label style={styles.label}>Episodes</label>
              <input
                type="number"
                value={episodes}
                onChange={(e) => setEpisodes(parseInt(e.target.value))}
                style={styles.input}
              />
            </div>
          )}
        </div>
      )}

      <button onClick={handleStart} style={styles.startButton}>
        Start Agent
      </button>

      {showConfirm && (
        <div style={styles.modal}>
          <div style={styles.modalContent}>
            <h3>Confirm Live Trading</h3>
            <p>Are you sure you want to start live trading?</p>
            <div style={styles.modalButtons}>
              <button onClick={submitStart} style={styles.confirmButton}>Yes, Start</button>
              <button onClick={() => setShowConfirm(false)} style={styles.cancelButton}>Cancel</button>
            </div>
          </div>
        </div>
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
    fontSize: '18px',
    fontWeight: '600',
  },
  field: {
    marginBottom: '12px',
  },
  label: {
    display: 'block',
    marginBottom: '4px',
    fontSize: '14px',
    fontWeight: '500',
  },
  select: {
    width: '100%',
    padding: '8px',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    fontSize: '14px',
  },
  input: {
    width: '100%',
    padding: '8px',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    fontSize: '14px',
  },
  radioGroup: {
    display: 'flex',
    gap: '16px',
  },
  radioLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '14px',
  },
  toggleButton: {
    padding: '8px 16px',
    border: '1px solid #e0e0e0',
    backgroundColor: 'white',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    marginBottom: '12px',
  },
  hyperparams: {
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    padding: '16px',
    marginBottom: '12px',
    backgroundColor: '#f9f9f9',
  },
  startButton: {
    width: '100%',
    height: '44px',
    backgroundColor: '#4caf50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  stopButton: {
    width: '100%',
    height: '44px',
    backgroundColor: '#f44336',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  statusBadge: {
    display: 'inline-block',
    padding: '8px 16px',
    backgroundColor: '#4caf50',
    color: 'white',
    borderRadius: '16px',
    fontSize: '14px',
    fontWeight: '600',
    marginBottom: '12px',
  },
  info: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '16px',
  },
  modal: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2000,
  },
  modalContent: {
    backgroundColor: 'white',
    padding: '24px',
    borderRadius: '8px',
    maxWidth: '400px',
  },
  modalButtons: {
    display: 'flex',
    gap: '12px',
    marginTop: '20px',
  },
  confirmButton: {
    flex: 1,
    padding: '10px',
    backgroundColor: '#4caf50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  cancelButton: {
    flex: 1,
    padding: '10px',
    backgroundColor: '#999',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
}
