'use client'

import { useState, useEffect } from 'react'
import Navbar from '@/components/Layout/Navbar'
import { 
  BarChart3, 
  TrendingUp, 
  Activity,
  DollarSign,
  Target,
  Clock,
  Zap,
  Users,
  Brain,
  ArrowUpDown,
  Percent
} from 'lucide-react'

interface PerformanceMetrics {
  total_return: number
  annualized_return: number
  sharpe_ratio: number
  sortino_ratio: number
  max_drawdown: number
  win_rate: number
  profit_factor: number
  average_win: number
  average_loss: number
  total_trades: number
  profitable_trades: number
  average_trade_duration: number
  best_trade: number
  worst_trade: number
  consecutive_wins: number
  consecutive_losses: number
}

interface StrategyPerformance {
  strategy_name: string
  performance: PerformanceMetrics
  intelligence_contribution: {
    social_signals_used: number
    arbitrage_opportunities_captured: number
    risk_alerts_triggered: number
    automation_uptime: number
  }
  trades_by_month: Array<{
    month: string
    total_trades: number
    profitable_trades: number
    total_pnl: number
  }>
}

interface MarketImpactAnalysis {
  social_sentiment_correlation: number
  arbitrage_success_rate: number
  risk_detection_accuracy: number
  market_timing_effectiveness: number
  intelligence_system_uptime: number
  total_intelligence_signals: number
  actionable_signals: number
  false_positives: number
}

export default function AnalyticsPage() {
  const [timeframe, setTimeframe] = useState<'7d' | '30d' | '90d' | '1y'>('30d')
  const [strategyPerformance, setStrategyPerformance] = useState<StrategyPerformance[]>([])
  const [marketImpact, setMarketImpact] = useState<MarketImpactAnalysis | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadAnalytics = async () => {
    try {
      setIsLoading(true)
      
      // Mock comprehensive analytics data
      const mockStrategyPerformance: StrategyPerformance[] = [
        {
          strategy_name: 'AI Social Momentum',
          performance: {
            total_return: 34.7,
            annualized_return: 156.8,
            sharpe_ratio: 1.8,
            sortino_ratio: 2.3,
            max_drawdown: -12.4,
            win_rate: 72,
            profit_factor: 2.4,
            average_win: 8.2,
            average_loss: -3.4,
            total_trades: 89,
            profitable_trades: 64,
            average_trade_duration: 4.2,
            best_trade: 45.6,
            worst_trade: -18.3,
            consecutive_wins: 12,
            consecutive_losses: 3
          },
          intelligence_contribution: {
            social_signals_used: 1247,
            arbitrage_opportunities_captured: 23,
            risk_alerts_triggered: 8,
            automation_uptime: 98.5
          },
          trades_by_month: [
            { month: 'Nov', total_trades: 23, profitable_trades: 17, total_pnl: 8.7 },
            { month: 'Dec', total_trades: 31, profitable_trades: 22, total_pnl: 12.3 },
            { month: 'Jan', total_trades: 35, profitable_trades: 25, total_pnl: 13.7 }
          ]
        },
        {
          strategy_name: 'Multi-DEX Arbitrage',
          performance: {
            total_return: 18.3,
            annualized_return: 78.2,
            sharpe_ratio: 2.4,
            sortino_ratio: 3.1,
            max_drawdown: -3.2,
            win_rate: 89,
            profit_factor: 4.2,
            average_win: 2.1,
            average_loss: -0.5,
            total_trades: 234,
            profitable_trades: 208,
            average_trade_duration: 0.3,
            best_trade: 8.9,
            worst_trade: -2.1,
            consecutive_wins: 34,
            consecutive_losses: 2
          },
          intelligence_contribution: {
            social_signals_used: 0,
            arbitrage_opportunities_captured: 156,
            risk_alerts_triggered: 12,
            automation_uptime: 99.2
          },
          trades_by_month: [
            { month: 'Nov', total_trades: 67, profitable_trades: 61, total_pnl: 5.2 },
            { month: 'Dec', total_trades: 89, profitable_trades: 78, total_pnl: 6.8 },
            { month: 'Jan', total_trades: 78, profitable_trades: 69, total_pnl: 6.3 }
          ]
        }
      ]

      const mockMarketImpact: MarketImpactAnalysis = {
        social_sentiment_correlation: 0.78,
        arbitrage_success_rate: 0.89,
        risk_detection_accuracy: 0.94,
        market_timing_effectiveness: 0.72,
        intelligence_system_uptime: 98.7,
        total_intelligence_signals: 2847,
        actionable_signals: 1923,
        false_positives: 156
      }

      setStrategyPerformance(mockStrategyPerformance)
      setMarketImpact(mockMarketImpact)
      
    } catch (error) {
      console.error('Failed to load analytics:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadAnalytics()
  }, [timeframe])

  const getPerformanceColor = (value: number, isPercentage: boolean = true) => {
    if (isPercentage) {
      return value > 0 ? 'text-green-400' : 'text-red-400'
    }
    return value > 1 ? 'text-green-400' : 'text-red-400'
  }

  if (isLoading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-background p-6 pt-20">
          <div className="max-w-7xl mx-auto">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-text-secondary">Loading analytics...</p>
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
                <BarChart3 className="w-8 h-8 mr-3 text-primary" />
                Intelligence Analytics
              </h1>
              <p className="text-text-secondary">
                Comprehensive performance analysis of intelligence-driven trading strategies
              </p>
            </div>
            
            {/* Timeframe Selector */}
            <div className="flex bg-surface rounded-lg p-1">
              {(['7d', '30d', '90d', '1y'] as const).map((period) => (
                <button
                  key={period}
                  onClick={() => setTimeframe(period)}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    timeframe === period
                      ? 'bg-primary text-white'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>

          {/* Intelligence Impact Overview */}
          {marketImpact && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-text-secondary text-sm">Social Correlation</span>
                  <Brain className="w-4 h-4 text-blue-400" />
                </div>
                <div className="text-2xl font-bold text-text-primary">
                  {(marketImpact.social_sentiment_correlation * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-blue-400">Strong correlation</div>
              </div>

              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-text-secondary text-sm">Arbitrage Success</span>
                  <ArrowUpDown className="w-4 h-4 text-green-400" />
                </div>
                <div className="text-2xl font-bold text-text-primary">
                  {(marketImpact.arbitrage_success_rate * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-green-400">High success rate</div>
              </div>

              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-text-secondary text-sm">Risk Detection</span>
                  <Target className="w-4 h-4 text-yellow-400" />
                </div>
                <div className="text-2xl font-bold text-text-primary">
                  {(marketImpact.risk_detection_accuracy * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-yellow-400">Very accurate</div>
              </div>

              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-text-secondary text-sm">System Uptime</span>
                  <Activity className="w-4 h-4 text-purple-400" />
                </div>
                <div className="text-2xl font-bold text-text-primary">
                  {marketImpact.intelligence_system_uptime.toFixed(1)}%
                </div>
                <div className="text-xs text-purple-400">Excellent uptime</div>
              </div>
            </div>
          )}

          {/* Strategy Performance Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {strategyPerformance.map((strategy) => (
              <div key={strategy.strategy_name} className="bg-card border border-border rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-text-primary">{strategy.strategy_name}</h3>
                  <div className={`text-xl font-bold ${getPerformanceColor(strategy.performance.total_return)}`}>
                    +{strategy.performance.total_return}%
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-text-primary font-semibold">
                      {strategy.performance.win_rate}%
                    </div>
                    <div className="text-text-secondary text-xs">Win Rate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-text-primary font-semibold">
                      {strategy.performance.sharpe_ratio}
                    </div>
                    <div className="text-text-secondary text-xs">Sharpe Ratio</div>
                  </div>
                  <div className="text-center">
                    <div className="text-text-primary font-semibold">
                      {strategy.performance.total_trades}
                    </div>
                    <div className="text-text-secondary text-xs">Total Trades</div>
                  </div>
                  <div className="text-center">
                    <div className="text-red-400 font-semibold">
                      {strategy.performance.max_drawdown}%
                    </div>
                    <div className="text-text-secondary text-xs">Max Drawdown</div>
                  </div>
                </div>

                {/* Intelligence Contribution */}
                <div className="border-t border-border pt-4">
                  <h4 className="text-sm font-medium text-text-primary mb-2">Intelligence Impact</h4>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-text-secondary">Social Signals</span>
                      <span className="text-text-primary">{strategy.intelligence_contribution.social_signals_used}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-text-secondary">Arbitrage Captured</span>
                      <span className="text-text-primary">{strategy.intelligence_contribution.arbitrage_opportunities_captured}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-text-secondary">Risk Alerts</span>
                      <span className="text-text-primary">{strategy.intelligence_contribution.risk_alerts_triggered}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-text-secondary">Uptime</span>
                      <span className="text-green-400">{strategy.intelligence_contribution.automation_uptime}%</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Intelligence System Performance */}
          {marketImpact && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-4">Signal Quality Analysis</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-text-secondary">Total Signals Generated</span>
                    <span className="text-text-primary font-semibold">
                      {marketImpact.total_intelligence_signals.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-text-secondary">Actionable Signals</span>
                    <span className="text-green-400 font-semibold">
                      {marketImpact.actionable_signals.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-text-secondary">False Positives</span>
                    <span className="text-red-400 font-semibold">
                      {marketImpact.false_positives.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-text-secondary">Signal Accuracy</span>
                    <span className="text-primary font-semibold">
                      {((marketImpact.actionable_signals / marketImpact.total_intelligence_signals) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-4">System Effectiveness</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-text-secondary">Market Timing</span>
                    <div className="flex items-center">
                      <div className="w-20 bg-surface rounded-full h-2 mr-3">
                        <div 
                          className="bg-blue-400 h-2 rounded-full" 
                          style={{ width: `${marketImpact.market_timing_effectiveness * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-blue-400 font-semibold">
                        {(marketImpact.market_timing_effectiveness * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-text-secondary">Risk Detection</span>
                    <div className="flex items-center">
                      <div className="w-20 bg-surface rounded-full h-2 mr-3">
                        <div 
                          className="bg-yellow-400 h-2 rounded-full" 
                          style={{ width: `${marketImpact.risk_detection_accuracy * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-yellow-400 font-semibold">
                        {(marketImpact.risk_detection_accuracy * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-text-secondary">Arbitrage Success</span>
                    <div className="flex items-center">
                      <div className="w-20 bg-surface rounded-full h-2 mr-3">
                        <div 
                          className="bg-green-400 h-2 rounded-full" 
                          style={{ width: `${marketImpact.arbitrage_success_rate * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-green-400 font-semibold">
                        {(marketImpact.arbitrage_success_rate * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-text-secondary">Social Correlation</span>
                    <div className="flex items-center">
                      <div className="w-20 bg-surface rounded-full h-2 mr-3">
                        <div 
                          className="bg-purple-400 h-2 rounded-full" 
                          style={{ width: `${marketImpact.social_sentiment_correlation * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-purple-400 font-semibold">
                        {(marketImpact.social_sentiment_correlation * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
