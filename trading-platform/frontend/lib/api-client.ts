import axios from 'axios'
import { Bot, PortfolioStats, CreateBotRequest, ApiResponse } from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
  })

  // Portfolio endpoints
  async getPortfolioStats(): Promise<PortfolioStats> {
    const response = await this.client.get<ApiResponse<PortfolioStats>>('/api/portfolio/stats')
    return response.data.data
  }

  async getPortfolioHistory(): Promise<any[]> {
    const response = await this.client.get<ApiResponse<any[]>>('/api/portfolio/history')
    return response.data.data
  }

  // Bot management endpoints
  async getBots(): Promise<Bot[]> {
    const response = await this.client.get<ApiResponse<Bot[]>>('/api/bot/list')
    return response.data.data
  }

  async createBot(config: CreateBotRequest): Promise<Bot> {
    const response = await this.client.post<ApiResponse<Bot>>('/api/bot/create', config)
    return response.data.data
  }

  async getBotStatus(id: string): Promise<Bot> {
    const response = await this.client.get<ApiResponse<Bot>>(`/api/bot/${id}/status`)
    return response.data.data
  }

  async controlBot(id: string, action: 'start' | 'pause' | 'stop'): Promise<void> {
    await this.client.post(`/api/bot/${id}/control`, { action })
  }

  async deleteBot(id: string): Promise<void> {
    await this.client.delete(`/api/bot/${id}`)
  }

  // WebSocket connection
  createWebSocketConnection(onMessage: (data: any) => void): WebSocket {
    const ws = new WebSocket(`${API_BASE_URL.replace('http', 'ws')}/ws/live-data`)
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      onMessage(data)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    return ws
  }
}

export const apiClient = new ApiClient()

// Mock data for development
export const mockData = {
  portfolioStats: {
    totalValue: 125430.50,
    pnl: 15654.30,
    pnlPercent: 12.4,
    activeBots: 4,
    newBots: 1,
    winRate: 58,
    totalTrades: 200,
    volume24h: 182000,
    sharpeRatio: 1.42
  } as PortfolioStats,

  portfolioHistory: Array.from({ length: 30 }, (_, i) => ({
    timestamp: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString(),
    value: 110000 + Math.random() * 20000 + i * 500,
    pnl: Math.random() * 2000 - 1000
  })),

  bots: [
    {
      id: '1',
      name: 'SOL Momentum v2',
      strategy: 'Momentum + TF 1m',
      type: 'Solana' as const,
      market: 'SOL/USDC',
      mode: 'Paper' as const,
      isConnected: false,
      runtime: '02:14:24',
      dailyPnl: 325.37,
      status: 'running' as const,
      createdAt: '2024-01-15'
    },
    {
      id: '2',
      name: 'SOL Grid Bot',
      strategy: 'Grid + TF 5m',
      type: 'Solana' as const,
      market: 'BONK/USDC',
      mode: 'Live' as const,
      isConnected: true,
      runtime: '12:47:03',
      dailyPnl: -42.10,
      status: 'running' as const,
      createdAt: '2024-01-14'
    },
    {
      id: '3',
      name: 'AAPL MeanRevert',
      strategy: 'Mean Reversion',
      type: 'Stock' as const,
      market: 'AAPL',
      mode: 'Paper' as const,
      isConnected: false,
      runtime: '05:31:13',
      dailyPnl: 80.87,
      status: 'paused' as const,
      createdAt: '2024-01-13'
    }
  ] as Bot[]
}