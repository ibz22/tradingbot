export interface Bot {
  id: string
  name: string
  strategy: string
  type: 'Solana' | 'Stock'
  market: string
  mode: 'Paper' | 'Live'
  isConnected: boolean
  runtime: string
  dailyPnl: number
  status: 'running' | 'paused' | 'stopped'
  createdAt: string
}

export interface PortfolioStats {
  totalValue: number
  pnl: number
  pnlPercent: number
  activeBots: number
  newBots: number
  winRate: number
  totalTrades: number
  volume24h: number
  sharpeRatio: number
}

export interface PnlDataPoint {
  timestamp: string
  value: number
  pnl: number
}

export interface BotConfig {
  name: string
  assetType: 'Solana' | 'Stocks'
  market: string
  strategy: 'Momentum' | 'Grid' | 'Mean Reversion' | 'AI Social' | 'Arbitrage' | 'DCA' | 'Breakout' | 'Scalping'
  secondaryStrategy?: 'None' | 'AI Social' | 'Stop Loss' | 'Take Profit' | 'DCA' | 'Trailing Stop'
  timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d'
  paperTrading: boolean
  connectApi: boolean
  initialBalance: number
  aiEnabled?: boolean
  autoTrade?: boolean
  sentimentThreshold?: number
  stopLoss?: number
  takeProfit?: number
}

export interface CreateBotRequest extends BotConfig {}

export interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
}

export interface WebSocketMessage {
  type: 'portfolio_update' | 'bot_update' | 'price_update'
  data: any
}