/**
 * Real-time WebSocket client for live trading intelligence
 * Connects to the backend WebSocket for real-time updates
 */

export interface IntelligenceUpdate {
  type: 'arbitrage' | 'social' | 'risk' | 'portfolio' | 'market'
  data: any
  timestamp: number
}

export interface ArbitrageUpdate {
  opportunity_id: string
  token_symbol: string
  profit_percentage: number
  confidence: number
  execution_time: number
  status: 'active' | 'expired' | 'executed'
}

export interface SocialUpdate {
  signal_id: string
  platform: string
  token: string
  sentiment_score: number
  hype_level: number
  mentions_count: number
  influence_score: number
}

export interface RiskAlert {
  alert_id: string
  token_address: string
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  risk_factors: string[]
  confidence: number
  action_required: boolean
}

export class IntelligenceWebSocket {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private pingInterval: NodeJS.Timeout | null = null
  
  // Event handlers
  private onArbitrageUpdate: ((update: ArbitrageUpdate) => void) | null = null
  private onSocialUpdate: ((update: SocialUpdate) => void) | null = null
  private onRiskAlert: ((alert: RiskAlert) => void) | null = null
  private onMarketUpdate: ((data: any) => void) | null = null
  private onConnectionChange: ((connected: boolean) => void) | null = null

  constructor() {
    this.connect()
  }

  private connect() {
    try {
      // In production, use wss:// for secure WebSocket
      const wsUrl = process.env.NODE_ENV === 'production' 
        ? 'wss://your-api-domain.com/ws/intelligence'
        : 'ws://localhost:8000/ws/intelligence'
      
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = () => {
        console.log('🔗 Intelligence WebSocket connected')
        this.reconnectAttempts = 0
        this.onConnectionChange?.(true)
        this.startPing()
      }
      
      this.ws.onmessage = (event) => {
        try {
          const update: IntelligenceUpdate = JSON.parse(event.data)
          this.handleIntelligenceUpdate(update)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
      
      this.ws.onclose = () => {
        console.log('🔌 Intelligence WebSocket disconnected')
        this.onConnectionChange?.(false)
        this.stopPing()
        this.attemptReconnect()
      }
      
      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
      }
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.attemptReconnect()
    }
  }

  private handleIntelligenceUpdate(update: IntelligenceUpdate) {
    switch (update.type) {
      case 'arbitrage':
        this.onArbitrageUpdate?.(update.data as ArbitrageUpdate)
        break
      case 'social':
        this.onSocialUpdate?.(update.data as SocialUpdate)
        break
      case 'risk':
        this.onRiskAlert?.(update.data as RiskAlert)
        break
      case 'market':
        this.onMarketUpdate?.(update.data)
        break
      default:
        console.log('Unknown intelligence update type:', update.type)
    }
  }

  private startPing() {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000) // Ping every 30 seconds
  }

  private stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      
      setTimeout(() => {
        this.connect()
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.error('❌ Max reconnection attempts reached')
    }
  }

  // Subscription methods
  onArbitrage(callback: (update: ArbitrageUpdate) => void) {
    this.onArbitrageUpdate = callback
    return this
  }

  onSocial(callback: (update: SocialUpdate) => void) {
    this.onSocialUpdate = callback
    return this
  }

  onRisk(callback: (alert: RiskAlert) => void) {
    this.onRiskAlert = callback
    return this
  }

  onMarket(callback: (data: any) => void) {
    this.onMarketUpdate = callback
    return this
  }

  onConnection(callback: (connected: boolean) => void) {
    this.onConnectionChange = callback
    return this
  }

  // Send methods
  subscribeToToken(tokenAddress: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        data: { token: tokenAddress }
      }))
    }
  }

  unsubscribeFromToken(tokenAddress: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        data: { token: tokenAddress }
      }))
    }
  }

  requestArbitrageUpdate() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'request_arbitrage'
      }))
    }
  }

  // Utility methods
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  disconnect() {
    this.stopPing()
    this.ws?.close()
    this.ws = null
  }
}

// Singleton instance
let intelligenceWS: IntelligenceWebSocket | null = null

export function getIntelligenceWebSocket(): IntelligenceWebSocket {
  if (!intelligenceWS) {
    intelligenceWS = new IntelligenceWebSocket()
  }
  return intelligenceWS
}

// React hook for WebSocket integration
export function useIntelligenceWebSocket() {
  const [connected, setConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<IntelligenceUpdate | null>(null)
  
  useEffect(() => {
    const ws = getIntelligenceWebSocket()
    
    ws.onConnection(setConnected)
    ws.onArbitrage((update) => {
      setLastUpdate({ type: 'arbitrage', data: update, timestamp: Date.now() })
    })
    ws.onSocial((update) => {
      setLastUpdate({ type: 'social', data: update, timestamp: Date.now() })
    })
    ws.onRisk((alert) => {
      setLastUpdate({ type: 'risk', data: alert, timestamp: Date.now() })
    })
    ws.onMarket((data) => {
      setLastUpdate({ type: 'market', data, timestamp: Date.now() })
    })
    
    return () => {
      // Don't disconnect on unmount, keep connection alive
    }
  }, [])
  
  return {
    connected,
    lastUpdate,
    subscribe: (token: string) => getIntelligenceWebSocket().subscribeToToken(token),
    unsubscribe: (token: string) => getIntelligenceWebSocket().unsubscribeFromToken(token),
    requestUpdate: () => getIntelligenceWebSocket().requestArbitrageUpdate()
  }
}
