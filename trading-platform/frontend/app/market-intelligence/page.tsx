'use client'

import { useState, useEffect } from 'react'
import Navbar from '@/components/Layout/Navbar'
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
  CheckCircle,
  XCircle,
  Clock,
  Users
} from 'lucide-react'

interface RugDetectionResult {
  token_address: string
  symbol: string
  risk_score: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  warning_flags: string[]
  safety_checks: {
    liquidity_locked: boolean
    renounced_ownership: boolean
    verified_contract: boolean
    audit_status: string
    team_doxxed: boolean
    whitepaper_available: boolean
  }
  financial_metrics: {
    liquidity_pool_size: number
    holder_distribution: {
      top_10_percentage: number
      dev_wallet_percentage: number
      locked_tokens_percentage: number
    }
    trading_volume_24h: number
    price_stability_score: number
  }
  recommendations: string[]
}

interface ArbitrageOpportunity {
  id: string
  token_symbol: string
  buy_exchange: string
  sell_exchange: string
  buy_price: number
  sell_price: number
  percentage_profit: number
  potential_profit_usd: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  confidence_score: number
  estimated_execution_time: number
}

interface MarketIntelligenceData {
  social_sentiment: {
    overall_sentiment: number
    confidence: number
    trending_tokens: Array<{
      symbol: string
      sentiment: number
      mentions: number
    }>
  }
  arbitrage_opportunities: ArbitrageOpportunity[]
  high_risk_tokens: RugDetectionResult[]
  market_summary: {
    total_opportunities: number
    average_profit_percentage: number
    market_efficiency_score: number
  }
}

export default function MarketIntelligencePage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'arbitrage' | 'risk' | 'social'>('overview')
  const [marketData, setMarketData] = useState<MarketIntelligenceData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const fetchMarketIntelligence = async () => {
    try {
      setIsLoading(true)
      
      // Fetch all intelligence data in parallel
      const [socialData, arbitrageData, rugData] = await Promise.all([
        fetch('/api/social-intelligence?timeframe=24h').then(r => r.json()),
        fetch('/api/arbitrage?min_profit=1&max_risk=MEDIUM').then(r => r.json()),
        fetch('/api/rug-detection?address=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v').then(r => r.json())
      ])

      const intelligence: MarketIntelligenceData = {
        social_sentiment: {
          overall_sentiment: socialData.data?.market_sentiment?.overall_sentiment || 0.5,
          confidence: socialData.data?.market_sentiment?.confidence || 0.7,
          trending_tokens: Object.entries(socialData.data?.token_sentiments || {})
            .map(([symbol, data]: [string, any]) => ({
              symbol,
              sentiment: data.overall_sentiment,
              mentions: data.total_mentions
            }))
            .slice(0, 5)
        },
        arbitrage_opportunities: arbitrageData.data?.opportunities || [],
        high_risk_tokens: [rugData.data].filter(Boolean),
        market_summary: arbitrageData.data?.market_summary || {
          total_opportunities: 0,
          average_profit_percentage: 0,
          market_efficiency_score: 0
        }
      }

      setMarketData(intelligence)
      setLastUpdate(new Date())
      
    } catch (error) {
      console.error('Failed to fetch market intelligence:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchMarketIntelligence()
    
    // Auto-refresh every 2 minutes
    const interval = setInterval(fetchMarketIntelligence, 2 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'LOW': return 'text-green-400'
      case 'MEDIUM': return 'text-yellow-400'
      case 'HIGH': return 'text-red-400'
      case 'CRITICAL': return 'text-red-600'
      default: return 'text-gray-400'
    }
  }

  const getRiskBgColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'LOW': return 'bg-green-900/30 border-green-700'
      case 'MEDIUM': return 'bg-yellow-900/30 border-yellow-700'
      case 'HIGH': return 'bg-red-900/30 border-red-700'
      case 'CRITICAL': return 'bg-red-900/50 border-red-600'
      default: return 'bg-gray-900/30 border-gray-700'
    }
  }

  if (isLoading && !marketData) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-background p-6 pt-20">
          <div className="max-w-7xl mx-auto">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-text-secondary">Loading market intelligence...</p>
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
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-text-primary mb-2 flex items-center">
              <Brain className="w-8 h-8 mr-3 text-primary" />
              Market Intelligence Dashboard
            </h1>
            <p className="text-text-secondary">
              Comprehensive market analysis powered by AI • Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">Market Sentiment</p>
                  <p className="text-2xl font-bold text-text-primary">
                    {((marketData?.social_sentiment.overall_sentiment || 0) * 100).toFixed(0)}%
                  </p>
                </div>
                <TrendingUp className={`w-8 h-8 ${
                  (marketData?.social_sentiment.overall_sentiment || 0) > 0.5 ? 'text-green-400' : 'text-red-400'
                }`} />
              </div>
            </div>

            <div className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">Arbitrage Opportunities</p>
                  <p className="text-2xl font-bold text-text-primary">
                    {marketData?.arbitrage_opportunities.length || 0}
                  </p>
                </div>
                <ArrowUpDown className="w-8 h-8 text-blue-400" />
              </div>
            </div>

            <div className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">Avg Profit %</p>
                  <p className="text-2xl font-bold text-text-primary">
                    {(marketData?.market_summary.average_profit_percentage || 0).toFixed(2)}%
                  </p>
                </div>
                <DollarSign className="w-8 h-8 text-green-400" />
              </div>
            </div>

            <div className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">Market Efficiency</p>
                  <p className="text-2xl font-bold text-text-primary">
                    {((marketData?.market_summary.market_efficiency_score || 0) * 100).toFixed(0)}%
                  </p>
                </div>
                <BarChart3 className="w-8 h-8 text-purple-400" />
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="mb-8">
            <div className="border-b border-border">
              <nav className="-mb-px flex space-x-8">
                {[
                  { key: 'overview', label: 'Overview', icon: Brain },
                  { key: 'arbitrage', label: 'Arbitrage', icon: ArrowUpDown },
                  { key: 'risk', label: 'Risk Analysis', icon: Shield },
                  { key: 'social', label: 'Social Intelligence', icon: Users }
                ].map(({ key, label, icon: Icon }) => (
                  <button
                    key={key}
                    onClick={() => setActiveTab(key as any)}
                    className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                      activeTab === key
                        ? 'border-primary text-primary'
                        : 'border-transparent text-text-secondary hover:text-text-primary hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {label}
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div className="space-y-8">
              {/* Trending Tokens */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-xl font-semibold text-text-primary mb-4 flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Trending Tokens by Social Sentiment
                </h3>
                <div className="space-y-3">
                  {marketData?.social_sentiment.trending_tokens.map((token, index) => (
                    <div key={token.symbol} className="flex items-center justify-between p-4 bg-surface rounded-lg">
                      <div className="flex items-center">
                        <span className="text-text-secondary text-sm w-8">#{index + 1}</span>
                        <span className="font-medium text-text-primary">${token.symbol}</span>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className="text-text-secondary text-sm">{token.mentions} mentions</span>
                        <span className={`font-medium ${
                          token.sentiment > 0.6 ? 'text-green-400' : 
                          token.sentiment > 0.4 ? 'text-yellow-400' : 'text-red-400'
                        }`}>
                          {(token.sentiment * 100).toFixed(0)}% sentiment
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Arbitrage Opportunities */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-xl font-semibold text-text-primary mb-4 flex items-center">
                  <Zap className="w-5 h-5 mr-2" />
                  Top Arbitrage Opportunities
                </h3>
                <div className="space-y-3">
                  {marketData?.arbitrage_opportunities.slice(0, 3).map((opp) => (
                    <div key={opp.id} className="flex items-center justify-between p-4 bg-surface rounded-lg">
                      <div className="flex items-center space-x-4">
                        <span className="font-medium text-text-primary">${opp.token_symbol}</span>
                        <span className="text-text-secondary text-sm">
                          {opp.buy_exchange} → {opp.sell_exchange}
                        </span>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className="text-green-400 font-medium">
                          +{opp.percentage_profit.toFixed(2)}%
                        </span>
                        <span className="text-text-secondary text-sm">
                          ${opp.potential_profit_usd.toFixed(0)}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs ${getRiskBgColor(opp.risk_level)} ${getRiskColor(opp.risk_level)}`}>
                          {opp.risk_level}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'arbitrage' && (
            <div className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-text-primary flex items-center">
                  <ArrowUpDown className="w-5 h-5 mr-2" />
                  All Arbitrage Opportunities
                </h3>
                <div className="text-xs text-text-secondary">
                  Risk Levels: <span className="text-green-400">LOW</span> = Fast execution, high liquidity • 
                  <span className="text-yellow-400 mx-1">MEDIUM</span> = Moderate complexity • 
                  <span className="text-red-400">HIGH</span> = Higher risk/reward
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-3 px-4 text-text-secondary">Token</th>
                      <th className="text-left py-3 px-4 text-text-secondary">Route</th>
                      <th className="text-left py-3 px-4 text-text-secondary">Profit %</th>
                      <th className="text-left py-3 px-4 text-text-secondary">Est. Profit</th>
                      <th className="text-left py-3 px-4 text-text-secondary">
                        <div className="flex items-center">
                          Risk Level
                          <div className="ml-1 group relative">
                            <AlertTriangle className="w-3 h-3 text-text-secondary cursor-help" />
                            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity z-10 whitespace-nowrap">
                              Based on liquidity, execution complexity, and slippage risk
                            </div>
                          </div>
                        </div>
                      </th>
                      <th className="text-left py-3 px-4 text-text-secondary">Confidence</th>
                      <th className="text-left py-3 px-4 text-text-secondary">Exec Time</th>
                      <th className="text-left py-3 px-4 text-text-secondary">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {marketData?.arbitrage_opportunities.map((opp) => (
                      <tr key={opp.id} className="border-b border-border/50 hover:bg-surface/50">
                        <td className="py-3 px-4 font-medium text-text-primary">${opp.token_symbol}</td>
                        <td className="py-3 px-4 text-text-secondary text-sm">
                          {opp.buy_exchange} → {opp.sell_exchange}
                        </td>
                        <td className="py-3 px-4 text-green-400 font-medium">
                          +{opp.percentage_profit.toFixed(2)}%
                        </td>
                        <td className="py-3 px-4 text-text-primary">
                          ${opp.potential_profit_usd.toFixed(0)}
                        </td>
                        <td className="py-3 px-4">
                          <div className="relative group">
                            <span className={`px-2 py-1 rounded text-xs ${getRiskBgColor(opp.risk_level)} ${getRiskColor(opp.risk_level)}`}>
                              {opp.risk_level}
                            </span>
                            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity z-10 whitespace-nowrap max-w-xs">
                              {opp.risk_level === 'LOW' && (
                                <div>
                                  <div className="font-medium">Low Risk</div>
                                  <div>Fast execution, minimal slippage (&lt;0.5%)</div>
                                  <div>High liquidity on both exchanges</div>
                                </div>
                              )}
                              {opp.risk_level === 'MEDIUM' && (
                                <div>
                                  <div className="font-medium">Medium Risk</div>
                                  <div>Moderate execution time, some slippage (0.5-1%)</div>
                                  <div>Decent liquidity, may require routing</div>
                                </div>
                              )}
                              {opp.risk_level === 'HIGH' && (
                                <div>
                                  <div className="font-medium">High Risk</div>
                                  <div>Slower execution, higher slippage (&gt;1%)</div>
                                  <div>Lower liquidity, complex routing required</div>
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-text-secondary">
                          {(opp.confidence_score * 100).toFixed(0)}%
                        </td>
                        <td className="py-3 px-4 text-text-secondary">
                          {opp.estimated_execution_time}s
                        </td>
                        <td className="py-3 px-4">
                          <button className="text-primary hover:text-primary/80 text-xs">
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'risk' && (
            <div className="space-y-6">
              {marketData?.high_risk_tokens.map((token) => (
                <div key={token.token_address} className="bg-card border border-border rounded-lg p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-semibold text-text-primary flex items-center">
                      <Shield className="w-5 h-5 mr-2" />
                      Risk Analysis: ${token.symbol}
                    </h3>
                    <div className={`px-3 py-1 rounded-lg ${getRiskBgColor(token.risk_level)}`}>
                      <span className={`font-medium ${getRiskColor(token.risk_level)}`}>
                        {token.risk_level} RISK ({token.risk_score}/100)
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Safety Checks */}
                    <div>
                      <h4 className="font-medium text-text-primary mb-3">Safety Checks</h4>
                      <div className="space-y-2">
                        {Object.entries(token.safety_checks).map(([key, value]) => (
                          <div key={key} className="flex items-center justify-between">
                            <span className="text-text-secondary text-sm capitalize">
                              {key.replace(/_/g, ' ')}
                            </span>
                            {typeof value === 'boolean' ? (
                              value ? (
                                <CheckCircle className="w-4 h-4 text-green-400" />
                              ) : (
                                <XCircle className="w-4 h-4 text-red-400" />
                              )
                            ) : (
                              <span className="text-text-primary text-sm">{value}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Financial Metrics */}
                    <div>
                      <h4 className="font-medium text-text-primary mb-3">Financial Metrics</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-text-secondary text-sm">Liquidity Pool</span>
                          <span className="text-text-primary text-sm">
                            ${token.financial_metrics.liquidity_pool_size.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary text-sm">24h Volume</span>
                          <span className="text-text-primary text-sm">
                            ${token.financial_metrics.trading_volume_24h.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary text-sm">Top 10 Holders</span>
                          <span className="text-text-primary text-sm">
                            {token.financial_metrics.holder_distribution.top_10_percentage}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary text-sm">Price Stability</span>
                          <span className="text-text-primary text-sm">
                            {token.financial_metrics.price_stability_score}/100
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Warning Flags */}
                  {token.warning_flags.length > 0 && (
                    <div className="mt-6">
                      <h4 className="font-medium text-text-primary mb-3 flex items-center">
                        <AlertTriangle className="w-4 h-4 mr-2 text-yellow-400" />
                        Warning Flags
                      </h4>
                      <div className="space-y-2">
                        {token.warning_flags.map((flag, index) => (
                          <div key={index} className="flex items-center p-2 bg-yellow-900/20 border border-yellow-700 rounded">
                            <AlertTriangle className="w-4 h-4 mr-2 text-yellow-400 flex-shrink-0" />
                            <span className="text-yellow-200 text-sm">{flag}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  <div className="mt-6">
                    <h4 className="font-medium text-text-primary mb-3">Recommendations</h4>
                    <div className="space-y-1">
                      {token.recommendations.map((rec, index) => (
                        <div key={index} className="text-text-secondary text-sm">
                          • {rec}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'social' && (
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-xl font-semibold text-text-primary mb-4 flex items-center">
                <Users className="w-5 h-5 mr-2" />
                Social Intelligence Overview
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-text-primary mb-3">Market Sentiment</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-text-secondary">Overall Sentiment</span>
                      <span className={`font-medium ${
                        (marketData?.social_sentiment.overall_sentiment || 0) > 0.6 ? 'text-green-400' : 
                        (marketData?.social_sentiment.overall_sentiment || 0) > 0.4 ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {((marketData?.social_sentiment.overall_sentiment || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-text-secondary">Confidence</span>
                      <span className="text-text-primary">
                        {((marketData?.social_sentiment.confidence || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-text-primary mb-3">Platform Activity</h4>
                  <div className="space-y-2">
                    <div className="text-text-secondary text-sm">
                      Monitoring social signals across Twitter, Reddit, Telegram, and news sources for real-time sentiment analysis.
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
