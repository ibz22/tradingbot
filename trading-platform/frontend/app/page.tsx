'use client'

import { useState, useEffect } from 'react'
import { Bot, PortfolioStats, BotConfig } from '@/lib/types'
import { mockData } from '@/lib/api-client'
import Navbar from '@/components/Layout/Navbar'
import WelcomePanel from '@/components/Dashboard/WelcomePanel'
import PortfolioChart from '@/components/Dashboard/PortfolioChart'
import StatsCards from '@/components/Dashboard/StatsCards'
import BotTable from '@/components/BotTable/BotTable'
import BotCreator from '@/components/BotCreator/BotCreator'
import { Brain, TrendingUp, Shield, Zap, AlertTriangle, ArrowUpDown, Activity } from 'lucide-react'

interface IntelligenceAlert {
  id: string
  type: 'arbitrage' | 'social' | 'risk' | 'opportunity'
  title: string
  message: string
  confidence: number
  urgency: 'low' | 'medium' | 'high'
  token?: string
  profit_potential?: number
  timestamp: Date
}

export default function Dashboard() {
  const [portfolioStats, setPortfolioStats] = useState<PortfolioStats>(mockData.portfolioStats)
  const [portfolioHistory, setPortfolioHistory] = useState(mockData.portfolioHistory)
  const [bots, setBots] = useState<Bot[]>(mockData.bots)
  const [isBotCreatorOpen, setIsBotCreatorOpen] = useState(false)
  const [intelligenceAlerts, setIntelligenceAlerts] = useState<IntelligenceAlert[]>([])
  const [marketIntelligence, setMarketIntelligence] = useState({
    sentiment: 0.72,
    arbitrage_opportunities: 8,
    high_risk_tokens: 3,
    trending_tokens: 15
  })

  // Load intelligence alerts
  const loadIntelligenceAlerts = () => {
    const mockAlerts: IntelligenceAlert[] = [
      {
        id: 'alert_001',
        type: 'arbitrage',
        title: 'High-Profit Arbitrage Detected',
        message: 'RAY/USDC showing 2.1% price difference between Serum and Jupiter',
        confidence: 0.89,
        urgency: 'high',
        token: 'RAY',
        profit_potential: 2.1,
        timestamp: new Date(Date.now() - 2 * 60 * 1000)
      },
      {
        id: 'alert_002',
        type: 'social',
        title: 'Viral Social Momentum',
        message: 'TROLL gaining massive social traction with 1000+ mentions in last hour',
        confidence: 0.76,
        urgency: 'medium',
        token: 'TROLL',
        profit_potential: 15.2,
        timestamp: new Date(Date.now() - 5 * 60 * 1000)
      },
      {
        id: 'alert_003',
        type: 'risk',
        title: 'Rug Risk Warning',
        message: 'Unusual wallet activity detected for token with high concentration',
        confidence: 0.82,
        urgency: 'high',
        token: 'UNKNOWN',
        timestamp: new Date(Date.now() - 8 * 60 * 1000)
      },
      {
        id: 'alert_004',
        type: 'opportunity',
        title: 'Technical Breakout Signal',
        message: 'ORCA showing bullish breakout pattern with strong volume',
        confidence: 0.68,
        urgency: 'medium',
        token: 'ORCA',
        profit_potential: 8.5,
        timestamp: new Date(Date.now() - 12 * 60 * 1000)
      }
    ]
    setIntelligenceAlerts(mockAlerts)
  }

  // Simulate real-time updates and load intelligence
  useEffect(() => {
    loadIntelligenceAlerts()
    
    const interval = setInterval(() => {
      setPortfolioStats(prev => ({
        ...prev,
        pnl: prev.pnl + (Math.random() - 0.5) * 100,
        pnlPercent: prev.pnlPercent + (Math.random() - 0.5) * 0.5,
      }))

      setBots(prev => prev.map(bot => ({
        ...bot,
        dailyPnl: bot.dailyPnl + (Math.random() - 0.5) * 10,
      })))

      // Update market intelligence
      setMarketIntelligence(prev => ({
        sentiment: Math.max(0, Math.min(1, prev.sentiment + (Math.random() - 0.5) * 0.05)),
        arbitrage_opportunities: Math.max(0, prev.arbitrage_opportunities + Math.floor((Math.random() - 0.5) * 3)),
        high_risk_tokens: Math.max(0, prev.high_risk_tokens + Math.floor((Math.random() - 0.5) * 2)),
        trending_tokens: Math.max(0, prev.trending_tokens + Math.floor((Math.random() - 0.5) * 5))
      }))
    }, 10000) // Update every 10 seconds

    return () => clearInterval(interval)
  }, [])

  const handleControlBot = async (botId: string, action: 'start' | 'pause' | 'stop') => {
    setBots(prev => prev.map(bot => 
      bot.id === botId 
        ? { ...bot, status: action === 'start' ? 'running' : action === 'pause' ? 'paused' : 'stopped' }
        : bot
    ))
    
    // In a real app, this would call the API
    console.log(`Bot ${botId} action: ${action}`)
  }

  const handleEditBot = (botId: string) => {
    console.log(`Edit bot ${botId}`)
    // In a real app, this would open an edit modal
  }

  const handleDeleteBot = (botId: string) => {
    setBots(prev => prev.filter(bot => bot.id !== botId))
    console.log(`Delete bot ${botId}`)
  }

  const handleCreateBot = async (config: BotConfig) => {
    const newBot: Bot = {
      id: Date.now().toString(),
      name: config.name,
      strategy: config.strategy,
      type: config.assetType,
      market: config.market,
      mode: config.paperTrading ? 'Paper' : 'Live',
      isConnected: config.connectApi,
      runtime: '00:00:00',
      dailyPnl: 0,
      status: 'stopped',
      createdAt: new Date().toISOString().split('T')[0]
    }

    setBots(prev => [...prev, newBot])
    
    // Update stats
    setPortfolioStats(prev => ({
      ...prev,
      activeBots: prev.activeBots + 1,
      newBots: prev.newBots + 1
    }))

    console.log('Created bot:', newBot)
  }

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'arbitrage': return <ArrowUpDown className="w-4 h-4" />
      case 'social': return <Brain className="w-4 h-4" />
      case 'risk': return <Shield className="w-4 h-4" />
      case 'opportunity': return <TrendingUp className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'high': return 'border-red-500 bg-red-500/10 text-red-400'
      case 'medium': return 'border-yellow-500 bg-yellow-500/10 text-yellow-400'
      case 'low': return 'border-blue-500 bg-blue-500/10 text-blue-400'
      default: return 'border-gray-500 bg-gray-500/10 text-gray-400'
    }
  }

  return (
    <>
      <Navbar onNewBot={() => setIsBotCreatorOpen(true)} />
      <div className="min-h-screen bg-background p-6 pt-20">
        <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-8">
          {/* Left Column - Welcome Panel */}
          <div className="xl:col-span-2">
            <WelcomePanel 
              onStartSolanaBot={() => setIsBotCreatorOpen(true)}
            />
          </div>

          {/* Right Column - Portfolio Chart */}
          <div>
            <PortfolioChart 
              data={portfolioHistory}
              pnlPercent={portfolioStats.pnlPercent}
            />
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
          <StatsCards
            activeBots={portfolioStats.activeBots}
            newBots={portfolioStats.newBots}
            winRate={portfolioStats.winRate}
            totalTrades={portfolioStats.totalTrades}
            volume24h={portfolioStats.volume24h}
            sharpeRatio={portfolioStats.sharpeRatio}
          />
        </div>

        {/* Intelligence Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Market Intelligence Overview */}
          <div className="lg:col-span-2">
            <div className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-text-primary flex items-center">
                  <Brain className="w-5 h-5 mr-2" />
                  Live Intelligence Alerts
                </h3>
                <a 
                  href="/market-intelligence" 
                  className="text-primary hover:text-primary/80 text-sm font-medium transition-colors"
                >
                  View All Intelligence →
                </a>
              </div>
              
              <div className="space-y-3">
                {intelligenceAlerts.slice(0, 4).map((alert) => (
                  <div key={alert.id} className={`border rounded-lg p-4 ${getUrgencyColor(alert.urgency)}`}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getAlertIcon(alert.type)}
                        <span className="font-medium text-sm">{alert.title}</span>
                        {alert.token && (
                          <span className="px-2 py-1 bg-primary/20 text-primary text-xs rounded">
                            ${alert.token}
                          </span>
                        )}
                      </div>
                      <div className="text-xs opacity-70">
                        {Math.floor((Date.now() - alert.timestamp.getTime()) / 60000)}m ago
                      </div>
                    </div>
                    <p className="text-sm opacity-80 mb-2">{alert.message}</p>
                    <div className="flex items-center justify-between text-xs">
                      <span>Confidence: {(alert.confidence * 100).toFixed(0)}%</span>
                      {alert.profit_potential && (
                        <span className="text-green-400">+{alert.profit_potential}% potential</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Market Intelligence Stats */}
          <div className="space-y-4">
            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-text-secondary text-sm">Market Sentiment</span>
                <TrendingUp className="w-4 h-4 text-green-400" />
              </div>
              <div className="text-2xl font-bold text-text-primary">
                {(marketIntelligence.sentiment * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-green-400">Bullish momentum</div>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-text-secondary text-sm">Arbitrage Opportunities</span>
                <ArrowUpDown className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-2xl font-bold text-text-primary">
                {marketIntelligence.arbitrage_opportunities}
              </div>
              <div className="text-xs text-blue-400">Active opportunities</div>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-text-secondary text-sm">Risk Alerts</span>
                <AlertTriangle className="w-4 h-4 text-red-400" />
              </div>
              <div className="text-2xl font-bold text-text-primary">
                {marketIntelligence.high_risk_tokens}
              </div>
              <div className="text-xs text-red-400">High-risk tokens detected</div>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-text-secondary text-sm">Trending Tokens</span>
                <Zap className="w-4 h-4 text-yellow-400" />
              </div>
              <div className="text-2xl font-bold text-text-primary">
                {marketIntelligence.trending_tokens}
              </div>
              <div className="text-xs text-yellow-400">Social momentum</div>
            </div>
          </div>
        </div>

        {/* Bot Table */}
        <BotTable
          bots={bots}
          onControlBot={handleControlBot}
          onEditBot={handleEditBot}
          onDeleteBot={handleDeleteBot}
          onAddBot={() => setIsBotCreatorOpen(true)}
        />

        {/* Bot Creator Modal */}
        <BotCreator
          isOpen={isBotCreatorOpen}
          onClose={() => setIsBotCreatorOpen(false)}
          onCreateBot={handleCreateBot}
        />
      </div>
    </div>
    </>
  )
}