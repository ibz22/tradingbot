'use client'

import { useState, useEffect } from 'react'
import Navbar from '@/components/Layout/Navbar'
import BotCreator from '@/components/BotCreator/BotCreator'
import { 
  Brain, 
  TrendingUp, 
  Shield, 
  Zap, 
  Target, 
  AlertTriangle, 
  DollarSign,
  BarChart3,
  Activity,
  Layers,
  ArrowUpDown,
  Settings,
  Play,
  Pause,
  Eye,
  Plus
} from 'lucide-react'
import { BotConfig } from '@/lib/types'

interface Strategy {
  id: string
  name: string
  type: 'momentum' | 'arbitrage' | 'social' | 'risk_management' | 'multi_strategy'
  status: 'active' | 'paused' | 'stopped'
  description: string
  intelligence_features: string[]
  performance: {
    total_return: number
    win_rate: number
    avg_profit: number
    max_drawdown: number
    sharpe_ratio: number
    total_trades: number
  }
  risk_metrics: {
    risk_score: number
    max_position_size: number
    stop_loss: number
    take_profit: number
  }
  intelligence_settings: {
    social_sentiment_threshold: number
    rug_detection_enabled: boolean
    arbitrage_min_profit: number
    risk_monitoring: boolean
    auto_rebalancing: boolean
  }
}

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [activeStrategy, setActiveStrategy] = useState<Strategy | null>(null)
  const [showBotCreator, setShowBotCreator] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const loadStrategies = async () => {
    try {
      setIsLoading(true)
      
      // In production, this would fetch from your trading engine
      const mockStrategies: Strategy[] = [
        {
          id: 'strategy_001',
          name: 'AI Social Momentum',
          type: 'social',
          status: 'active',
          description: 'Leverages social intelligence and sentiment analysis to identify trending tokens before price movements.',
          intelligence_features: [
            'Real-time Twitter/Reddit sentiment analysis',
            'Telegram alpha signal detection',
            'News sentiment correlation',
            'Influencer impact scoring',
            'Viral trend prediction'
          ],
          performance: {
            total_return: 34.7,
            win_rate: 72,
            avg_profit: 8.2,
            max_drawdown: -12.4,
            sharpe_ratio: 1.8,
            total_trades: 89
          },
          risk_metrics: {
            risk_score: 0.65,
            max_position_size: 5.0,
            stop_loss: 8.0,
            take_profit: 15.0
          },
          intelligence_settings: {
            social_sentiment_threshold: 70,
            rug_detection_enabled: true,
            arbitrage_min_profit: 0,
            risk_monitoring: true,
            auto_rebalancing: false
          }
        },
        {
          id: 'strategy_002',
          name: 'Multi-DEX Arbitrage',
          type: 'arbitrage',
          status: 'active',
          description: 'Automated arbitrage across Jupiter, Orca, Raydium, and Serum with intelligent routing.',
          intelligence_features: [
            'Cross-DEX price monitoring',
            'Liquidity depth analysis',
            'Gas optimization',
            'MEV protection',
            'Route efficiency scoring'
          ],
          performance: {
            total_return: 18.3,
            win_rate: 89,
            avg_profit: 2.1,
            max_drawdown: -3.2,
            sharpe_ratio: 2.4,
            total_trades: 234
          },
          risk_metrics: {
            risk_score: 0.25,
            max_position_size: 15.0,
            stop_loss: 2.0,
            take_profit: 3.5
          },
          intelligence_settings: {
            social_sentiment_threshold: 0,
            rug_detection_enabled: true,
            arbitrage_min_profit: 0.5,
            risk_monitoring: true,
            auto_rebalancing: true
          }
        },
        {
          id: 'strategy_003',
          name: 'Risk-Managed DCA',
          type: 'risk_management',
          status: 'active',
          description: 'Dollar-cost averaging with advanced risk detection and position sizing.',
          intelligence_features: [
            'Dynamic position sizing',
            'Rug pull detection',
            'Liquidity risk assessment',
            'Market sentiment integration',
            'Automated stop-losses'
          ],
          performance: {
            total_return: 22.1,
            win_rate: 84,
            avg_profit: 5.8,
            max_drawdown: -8.1,
            sharpe_ratio: 1.9,
            total_trades: 156
          },
          risk_metrics: {
            risk_score: 0.35,
            max_position_size: 8.0,
            stop_loss: 10.0,
            take_profit: 20.0
          },
          intelligence_settings: {
            social_sentiment_threshold: 50,
            rug_detection_enabled: true,
            arbitrage_min_profit: 0,
            risk_monitoring: true,
            auto_rebalancing: true
          }
        },
        {
          id: 'strategy_004',
          name: 'Unified Intelligence',
          type: 'multi_strategy',
          status: 'paused',
          description: 'Master strategy combining all intelligence systems for optimal decision making.',
          intelligence_features: [
            'All social intelligence systems',
            'Complete arbitrage monitoring',
            'Advanced rug detection',
            'Portfolio rebalancing',
            'Market regime detection',
            'Cross-platform sentiment fusion'
          ],
          performance: {
            total_return: 41.2,
            win_rate: 76,
            avg_profit: 9.8,
            max_drawdown: -15.2,
            sharpe_ratio: 2.1,
            total_trades: 178
          },
          risk_metrics: {
            risk_score: 0.55,
            max_position_size: 10.0,
            stop_loss: 12.0,
            take_profit: 25.0
          },
          intelligence_settings: {
            social_sentiment_threshold: 65,
            rug_detection_enabled: true,
            arbitrage_min_profit: 1.0,
            risk_monitoring: true,
            auto_rebalancing: true
          }
        }
      ]

      setStrategies(mockStrategies)
      
    } catch (error) {
      console.error('Failed to load strategies:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadStrategies()
  }, [])

  const handleStrategyAction = async (strategyId: string, action: 'start' | 'pause' | 'stop') => {
    try {
      // In production, this would call your trading engine API
      setStrategies(prev => prev.map(strategy => 
        strategy.id === strategyId 
          ? { ...strategy, status: action === 'start' ? 'active' : action === 'pause' ? 'paused' : 'stopped' }
          : strategy
      ))
    } catch (error) {
      console.error(`Failed to ${action} strategy:`, error)
    }
  }

  const handleCreateBot = async (config: BotConfig) => {
    console.log('Creating intelligent bot with config:', config)
    setShowBotCreator(false)
    // In production, integrate with your trading engine
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400'
      case 'paused': return 'text-yellow-400'
      case 'stopped': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  const getStatusBgColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-900/30 border-green-700'
      case 'paused': return 'bg-yellow-900/30 border-yellow-700'
      case 'stopped': return 'bg-red-900/30 border-red-700'
      default: return 'bg-gray-900/30 border-gray-700'
    }
  }

  const getRiskColor = (riskScore: number) => {
    if (riskScore <= 0.3) return 'text-green-400'
    if (riskScore <= 0.6) return 'text-yellow-400'
    return 'text-red-400'
  }

  if (isLoading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-background p-6 pt-20">
          <div className="max-w-7xl mx-auto">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-text-secondary">Loading trading strategies...</p>
            </div>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-background p-6 pt-20">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-text-primary mb-2 flex items-center">
                <Brain className="w-8 h-8 mr-3 text-primary" />
                Intelligent Trading Strategies
              </h1>
              <p className="text-text-secondary">
                Advanced strategies powered by complete market intelligence systems
              </p>
            </div>
            <button
              onClick={() => setShowBotCreator(true)}
              className="flex items-center space-x-2 bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Create Strategy</span>
            </button>
          </div>

          {/* Strategy Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {strategies.map((strategy) => (
              <div key={strategy.id} className="bg-card border border-border rounded-lg p-6 hover:border-primary/50 transition-colors">
                {/* Strategy Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center">
                      {strategy.type === 'social' && <Brain className="w-5 h-5 text-primary" />}
                      {strategy.type === 'arbitrage' && <ArrowUpDown className="w-5 h-5 text-primary" />}
                      {strategy.type === 'risk_management' && <Shield className="w-5 h-5 text-primary" />}
                      {strategy.type === 'multi_strategy' && <Layers className="w-5 h-5 text-primary" />}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-text-primary">{strategy.name}</h3>
                      <div className={`px-2 py-1 rounded text-xs ${getStatusBgColor(strategy.status)} ${getStatusColor(strategy.status)}`}>
                        {strategy.status.toUpperCase()}
                      </div>
                    </div>
                  </div>
                  
                  {/* Strategy Controls */}
                  <div className="flex items-center space-x-2">
                    {strategy.status === 'active' ? (
                      <button
                        onClick={() => handleStrategyAction(strategy.id, 'pause')}
                        className="p-2 text-yellow-400 hover:bg-yellow-400/10 rounded transition-colors"
                        title="Pause Strategy"
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStrategyAction(strategy.id, 'start')}
                        className="p-2 text-green-400 hover:bg-green-400/10 rounded transition-colors"
                        title="Start Strategy"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => setActiveStrategy(strategy)}
                      className="p-2 text-text-secondary hover:bg-surface rounded transition-colors"
                      title="View Details"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-text-secondary hover:bg-surface rounded transition-colors">
                      <Settings className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Strategy Description */}
                <p className="text-text-secondary text-sm mb-4">{strategy.description}</p>

                {/* Key Metrics */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-green-400 font-semibold">+{strategy.performance.total_return}%</div>
                    <div className="text-text-secondary text-xs">Total Return</div>
                  </div>
                  <div className="text-center">
                    <div className="text-text-primary font-semibold">{strategy.performance.win_rate}%</div>
                    <div className="text-text-secondary text-xs">Win Rate</div>
                  </div>
                  <div className="text-center">
                    <div className={`font-semibold ${getRiskColor(strategy.risk_metrics.risk_score)}`}>
                      {(strategy.risk_metrics.risk_score * 100).toFixed(0)}%
                    </div>
                    <div className="text-text-secondary text-xs">Risk Score</div>
                  </div>
                </div>

                {/* Intelligence Features Preview */}
                <div className="mb-4">
                  <div className="text-text-primary text-sm font-medium mb-2">Intelligence Features:</div>
                  <div className="flex flex-wrap gap-1">
                    {strategy.intelligence_features.slice(0, 3).map((feature, index) => (
                      <span key={index} className="px-2 py-1 bg-primary/10 text-primary text-xs rounded">
                        {feature}
                      </span>
                    ))}
                    {strategy.intelligence_features.length > 3 && (
                      <span className="px-2 py-1 bg-surface text-text-secondary text-xs rounded">
                        +{strategy.intelligence_features.length - 3} more
                      </span>
                    )}
                  </div>
                </div>

                {/* Performance Bars */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-text-secondary">Sharpe Ratio</span>
                    <span className="text-text-primary">{strategy.performance.sharpe_ratio}</span>
                  </div>
                  <div className="w-full bg-surface rounded-full h-1">
                    <div 
                      className="bg-primary h-1 rounded-full" 
                      style={{ width: `${Math.min(strategy.performance.sharpe_ratio * 20, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Strategy Details Modal */}
          {activeStrategy && (
            <div className="fixed inset-0 z-50 overflow-hidden">
              <div className="absolute inset-0 bg-black/50" onClick={() => setActiveStrategy(null)} />
              
              <div className="absolute right-0 top-0 h-full w-full max-w-2xl bg-card border-l border-border shadow-2xl">
                <div className="flex h-full flex-col p-6">
                  {/* Modal Header */}
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-text-primary">{activeStrategy.name}</h2>
                    <button
                      onClick={() => setActiveStrategy(null)}
                      className="p-2 hover:bg-surface rounded transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Strategy Content */}
                  <div className="flex-1 overflow-y-auto space-y-6">
                    {/* Intelligence Features */}
                    <div>
                      <h3 className="text-lg font-semibold text-text-primary mb-3">Intelligence Features</h3>
                      <div className="space-y-2">
                        {activeStrategy.intelligence_features.map((feature, index) => (
                          <div key={index} className="flex items-center p-3 bg-surface rounded-lg">
                            <Brain className="w-4 h-4 mr-3 text-primary flex-shrink-0" />
                            <span className="text-text-secondary text-sm">{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Performance Metrics */}
                    <div>
                      <h3 className="text-lg font-semibold text-text-primary mb-3">Performance Analytics</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 bg-surface rounded-lg">
                          <div className="text-2xl font-bold text-green-400">+{activeStrategy.performance.total_return}%</div>
                          <div className="text-text-secondary text-sm">Total Return</div>
                        </div>
                        <div className="p-4 bg-surface rounded-lg">
                          <div className="text-2xl font-bold text-text-primary">{activeStrategy.performance.win_rate}%</div>
                          <div className="text-text-secondary text-sm">Win Rate</div>
                        </div>
                        <div className="p-4 bg-surface rounded-lg">
                          <div className="text-2xl font-bold text-text-primary">{activeStrategy.performance.avg_profit}%</div>
                          <div className="text-text-secondary text-sm">Avg Profit</div>
                        </div>
                        <div className="p-4 bg-surface rounded-lg">
                          <div className="text-2xl font-bold text-red-400">{activeStrategy.performance.max_drawdown}%</div>
                          <div className="text-text-secondary text-sm">Max Drawdown</div>
                        </div>
                      </div>
                    </div>

                    {/* Risk Management */}
                    <div>
                      <h3 className="text-lg font-semibold text-text-primary mb-3">Risk Management</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-surface rounded-lg">
                          <span className="text-text-secondary">Risk Score</span>
                          <span className={`font-semibold ${getRiskColor(activeStrategy.risk_metrics.risk_score)}`}>
                            {(activeStrategy.risk_metrics.risk_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-surface rounded-lg">
                          <span className="text-text-secondary">Max Position Size</span>
                          <span className="text-text-primary font-semibold">{activeStrategy.risk_metrics.max_position_size}%</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-surface rounded-lg">
                          <span className="text-text-secondary">Stop Loss</span>
                          <span className="text-red-400 font-semibold">-{activeStrategy.risk_metrics.stop_loss}%</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-surface rounded-lg">
                          <span className="text-text-secondary">Take Profit</span>
                          <span className="text-green-400 font-semibold">+{activeStrategy.risk_metrics.take_profit}%</span>
                        </div>
                      </div>
                    </div>

                    {/* Intelligence Settings */}
                    <div>
                      <h3 className="text-lg font-semibold text-text-primary mb-3">Intelligence Configuration</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-surface rounded-lg">
                          <span className="text-text-secondary">Social Sentiment Threshold</span>
                          <span className="text-text-primary font-semibold">{activeStrategy.intelligence_settings.social_sentiment_threshold}%</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-surface rounded-lg">
                          <span className="text-text-secondary">Rug Detection</span>
                          <span className={`font-semibold ${activeStrategy.intelligence_settings.rug_detection_enabled ? 'text-green-400' : 'text-red-400'}`}>
                            {activeStrategy.intelligence_settings.rug_detection_enabled ? 'Enabled' : 'Disabled'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-surface rounded-lg">
                          <span className="text-text-secondary">Min Arbitrage Profit</span>
                          <span className="text-text-primary font-semibold">{activeStrategy.intelligence_settings.arbitrage_min_profit}%</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-surface rounded-lg">
                          <span className="text-text-secondary">Auto Rebalancing</span>
                          <span className={`font-semibold ${activeStrategy.intelligence_settings.auto_rebalancing ? 'text-green-400' : 'text-red-400'}`}>
                            {activeStrategy.intelligence_settings.auto_rebalancing ? 'Enabled' : 'Disabled'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Bot Creator Modal */}
          <BotCreator
            isOpen={showBotCreator}
            onClose={() => setShowBotCreator(false)}
            onCreateBot={handleCreateBot}
          />
        </div>
      </div>
    </>
  )
}
import { X } from 'lucide-react'