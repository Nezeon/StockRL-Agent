export interface User {
  id: string
  username: string
  email: string
  created_at: string
}

export interface Portfolio {
  id: string
  name: string
  initial_budget: number
  current_cash: number
  nav: number
  pnl: number
  pnl_percent: number
  tickers: string[]
  allocation_strategy?: Record<string, number>
  risk_profile: 'conservative' | 'moderate' | 'aggressive'
  is_active: boolean
  positions?: Position[]
  created_at: string
  updated_at: string
}

export interface Position {
  ticker: string
  quantity: number
  avg_purchase_price: number
  current_price: number
  market_value: number
  unrealized_pnl: number
  unrealized_pnl_percent: number
}

export interface Trade {
  id: string
  ticker: string
  side: 'BUY' | 'SELL'
  quantity: number
  price: number
  total_value: number
  slippage: number
  fees: number
  executed_at: string
  simulated: boolean
}

export interface AgentRun {
  id: string
  portfolio_id: string
  algorithm: string
  mode: 'train' | 'live'
  action_space_type: 'discrete' | 'continuous'
  status: 'running' | 'stopped' | 'failed' | 'completed'
  start_time: string
  end_time?: string
  final_nav?: number
}

export interface AgentMetric {
  timestamp: string
  step: number
  episode_reward: number | null
  cumulative_reward: number
  loss: number | null
  portfolio_nav: number
  rolling_sharpe: number | null
}

export interface Quote {
  ticker: string
  price: number
  volume: number
  open: number
  high: number
  low: number
  close: number
  timestamp: string
  source: string
}

export interface OHLCV {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface AuthResponse {
  user: User
  access_token: string
  token_type: string
}

export interface CreatePortfolioRequest {
  name: string
  initial_budget: number
  tickers: string[]
  allocation_strategy?: Record<string, number>
  risk_profile?: 'conservative' | 'moderate' | 'aggressive'
}

export interface StartAgentRequest {
  portfolio_id: string
  algorithm: 'PPO' | 'DQN' | 'A2C' | 'SB3_PPO' | 'SB3_A2C'
  mode: 'train' | 'live'
  action_space_type?: 'discrete' | 'continuous'
  hyperparameters?: {
    learning_rate?: number
    batch_size?: number
    gamma?: number
    episodes?: number
  }
}

export interface TradeQueryParams {
  limit?: number
  offset?: number
  ticker?: string
  side?: 'BUY' | 'SELL'
  start_date?: string
  end_date?: string
}

export interface HistoryParams {
  start_date: string
  end_date: string
  interval?: '1m' | '5m' | '15m' | '1h' | '1d'
}

export interface WebSocketMessage {
  type: string
  channel?: string
  data?: any
}
