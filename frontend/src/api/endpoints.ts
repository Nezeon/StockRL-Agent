import { apiClient } from './client'
import type {
  Portfolio,
  Trade,
  AgentRun,
  Quote,
  OHLCV,
  CreatePortfolioRequest,
  StartAgentRequest,
  TradeQueryParams,
  HistoryParams,
  AuthResponse,
  User,
} from '../types/api'

export const authApi = {
  login: (data: { username: string; password: string }) =>
    apiClient.post<AuthResponse>('/auth/login', data),
  register: (data: { username: string; email: string; password: string }) =>
    apiClient.post<AuthResponse>('/auth/register', data),
  getMe: () => apiClient.get<User>('/auth/me'),
}

export const portfolioApi = {
  list: () =>
    apiClient.get<{ portfolios: Portfolio[] }>('/portfolios'),
  get: (id: string) =>
    apiClient.get<Portfolio>(`/portfolios/${id}`),
  create: (data: CreatePortfolioRequest) =>
    apiClient.post<Portfolio>('/portfolios', data),
  update: (id: string, data: Partial<Portfolio>) =>
    apiClient.patch<Portfolio>(`/portfolios/${id}`, data),
  getPositions: (id: string) =>
    apiClient.get<{
      positions: any[]
      cash: number
      total_nav: number
    }>(`/portfolios/${id}/positions`),
  getTrades: (id: string, params?: TradeQueryParams) =>
    apiClient.get<{
      trades: Trade[]
      total: number
      limit: number
      offset: number
    }>(`/portfolios/${id}/trades`, { params }),
}

export const agentApi = {
  getStatus: () =>
    apiClient.get<{ active_runs: AgentRun[] }>('/agent/status'),
  start: (data: StartAgentRequest) =>
    apiClient.post<{ agent_run: AgentRun }>('/agent/start', data),
  stop: (runId: string) =>
    apiClient.post<{ agent_run: AgentRun }>('/agent/stop', { agent_run_id: runId }),
  getStats: (runId: string, params?: { limit?: number }) =>
    apiClient.get<{
      agent_run: AgentRun
      metrics: any[]
      summary: any
    }>(`/agent/${runId}/stats`, { params }),
}

export const marketApi = {
  getQuote: (ticker: string) =>
    apiClient.get<Quote>(`/market/ticker/${ticker}/quote`),
  getHistory: (ticker: string, params: HistoryParams) =>
    apiClient.get<{
      ticker: string
      interval: string
      data: OHLCV[]
      source: string
    }>(`/market/ticker/${ticker}/history`, { params }),
}
