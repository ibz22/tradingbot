'use client'

import { useState, useEffect } from 'react'
import Navbar from '@/components/Layout/Navbar'
import { 
  Shield, 
  AlertTriangle, 
  TrendingDown, 
  Activity,
  Eye,
  Settings,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
  Users,
  Zap
} from 'lucide-react'

interface RiskAssessment {
  token_address: string
  symbol: string
  risk_score: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  liquidity_risk: number
  volatility_risk: number
  concentration_risk: number
  smart_contract_risk: number
  market_cap: number
  trading_volume_24h: number
  holder_count: number
  top_holders_percentage: number
  last_updated: string
  risk_factors: Array<{
    factor: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    description: string
    recommendation: string
  }>
  safety_checks: {
    liquidity_locked: boolean
    ownership_renounced: boolean
    contract_verified: boolean
    audit_completed: boolean
    team_doxxed: boolean
  }
}

interface PortfolioRisk {
  overall_risk_score: number
  total_portfolio_value: number
  value_at_risk_95: number
  maximum_drawdown_potential: number
  correlation_risk: number
  liquidity_risk: number
  concentration_risk: number
  recommendations: string[]
  positions_by_risk: {
    low: number
    medium: number
    high: number
    critical: number
  }
}

export default function RiskManagementPage() {
  const [portfolioRisk, setPortfolioRisk] = useState<PortfolioRisk | null>(null)
  const [tokenRisks, setTokenRisks] = useState<RiskAssessment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedToken, setSelectedToken] = useState<RiskAssessment | null>(null)
  const [riskThreshold, setRiskThreshold] = useState(70) // Alert threshold

  const loadRiskData = async () => {
    try {
      setRefreshing(true)
      
      // Simulate fetching comprehensive risk data
      const mockPortfolioRisk: PortfolioRisk = {
        overall_risk_score: 42,
        total_portfolio_value: 15420.50,
        value_at_risk_95: 1156.80,
        maximum_drawdown_potential: 28.5,
        correlation_risk: 0.35,
        liquidity_risk: 0.28,
        concentration_risk: 0.45,
        recommendations: [
          'Reduce SOL concentration below 35% of portfolio',
          'Consider adding more established DeFi tokens',
          'Set stop-losses for high-risk meme tokens',
          'Monitor whale movements in BONK positions',
          'Diversify across different market sectors'
        ],
        positions_by_risk: {
          low: 3,
          medium: 2,
          high: 1,
          critical: 0
        }
      }

      const mockTokenRisks: RiskAssessment[] = [
        {
          token_address: 'So11111111111111111111111111111111111111112',
          symbol: 'SOL',
          risk_score: 25,
          risk_level: 'LOW',
          liquidity_risk: 0.05,
          volatility_risk: 0.35,
          concentration_risk: 0.15,
          smart_contract_risk: 0.02,
          market_cap: 45600000000,
          trading_volume_24h: 1200000000,
          holder_count: 850000,
          top_holders_percentage: 12,
          last_updated: new Date().toISOString(),
          risk_factors: [
            {
              factor: 'High Market Volatility',
              severity: 'medium',
              description: 'SOL can experience significant price swings during market stress',
              recommendation: 'Consider position sizing and stop-losses'
            }
          ],
          safety_checks: {
            liquidity_locked: true,
            ownership_renounced: true,
            contract_verified: true,
            audit_completed: true,
            team_doxxed: true
          }
        },
        {
          token_address: 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
          symbol: 'BONK',
          risk_score: 68,
          risk_level: 'MEDIUM',
          liquidity_risk: 0.45,
          volatility_risk: 0.85,
          concentration_risk: 0.72,
          smart_contract_risk: 0.25,
          market_cap: 1200000000,
          trading_volume_24h: 45000000,
          holder_count: 125000,
          top_holders_percentage: 25,
          last_updated: new Date().toISOString(),
          risk_factors: [
            {
              factor: 'High Volatility',
              severity: 'high',
              description: 'Meme token with extreme price volatility',
              recommendation: 'Use small position sizes and tight stop-losses'
            },
            {
              factor: 'Concentration Risk',
              severity: 'medium',
              description: 'Top 10 holders control 25% of supply',
              recommendation: 'Monitor whale movements closely'
            }
          ],
          safety_checks: {
            liquidity_locked: false,
            ownership_renounced: true,
            contract_verified: true,
            audit_completed: false,
            team_doxxed: false
          }
        },
        {
          token_address: 'unknown_risky_token',
          symbol: 'RISKY',
          risk_score: 89,
          risk_level: 'HIGH',
          liquidity_risk: 0.85,
          volatility_risk: 0.95,
          concentration_risk: 0.88,
          smart_contract_risk: 0.75,
          market_cap: 5000000,
          trading_volume_24h: 250000,
          holder_count: 2500,
          top_holders_percentage: 45,
          last_updated: new Date().toISOString(),
          risk_factors: [
            {
              factor: 'Unverified Contract',
              severity: 'critical',
              description: 'Smart contract source code not verified',
              recommendation: 'Exit position immediately'
            },
            {
              factor: 'Low Liquidity',
              severity: 'high',
              description: 'Limited trading liquidity may cause slippage',
              recommendation: 'Consider gradual exit strategy'
            },
            {
              factor: 'Whale Concentration',
              severity: 'critical',
              description: 'Top holders control nearly half of supply',
              recommendation: 'High rug pull risk - exit position'
            }
          ],
          safety_checks: {
            liquidity_locked: false,
            ownership_renounced: false,
            contract_verified: false,
            audit_completed: false,
            team_doxxed: false
          }
        }
      ]

      setPortfolioRisk(mockPortfolioRisk)
      setTokenRisks(mockTokenRisks)
      
    } catch (error) {
      console.error('Failed to load risk data:', error)
    } finally {
      setIsLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadRiskData()
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(loadRiskData, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const getRiskColor = (riskLevel: string | number) => {
    if (typeof riskLevel === 'number') {
      if (riskLevel <= 30) return 'text-green-400'
      if (riskLevel <= 60) return 'text-yellow-400'
      if (riskLevel <= 80) return 'text-orange-400'
      return 'text-red-400'
    }
    
    switch (riskLevel) {
      case 'LOW': return 'text-green-400'
      case 'MEDIUM': return 'text-yellow-400'
      case 'HIGH': return 'text-orange-400'
      case 'CRITICAL': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  const getRiskBgColor = (riskLevel: string | number) => {
    if (typeof riskLevel === 'number') {
      if (riskLevel <= 30) return 'bg-green-900/30 border-green-700'
      if (riskLevel <= 60) return 'bg-yellow-900/30 border-yellow-700'
      if (riskLevel <= 80) return 'bg-orange-900/30 border-orange-700'
      return 'bg-red-900/30 border-red-700'
    }
    
    switch (riskLevel) {
      case 'LOW': return 'bg-green-900/30 border-green-700'
      case 'MEDIUM': return 'bg-yellow-900/30 border-yellow-700'
      case 'HIGH': return 'bg-orange-900/30 border-orange-700'
      case 'CRITICAL': return 'bg-red-900/30 border-red-700'
      default: return 'bg-gray-900/30 border-gray-700'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'text-blue-400'
      case 'medium': return 'text-yellow-400'
      case 'high': return 'text-orange-400'
      case 'critical': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  if (isLoading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-background p-6 pt-20">
          <div className="max-w-7xl mx-auto">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-text-secondary">Loading risk management data...</p>
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
                <Shield className="w-8 h-8 mr-3 text-primary" />
                Risk Management Center
              </h1>
              <p className="text-text-secondary">
                Comprehensive portfolio risk analysis and token safety monitoring
              </p>
            </div>
            <button
              onClick={loadRiskData}
              disabled={refreshing}
              className="flex items-center space-x-2 bg-primary hover:bg-primary/90 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          {/* Portfolio Risk Overview */}
          {portfolioRisk && (
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
              <div className="lg:col-span-1">
                <div className={`border rounded-lg p-6 ${getRiskBgColor(portfolioRisk.overall_risk_score)}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-text-primary">Portfolio Risk</h3>
                    <Shield className="w-5 h-5 text-primary" />
                  </div>
                  <div className={`text-3xl font-bold mb-2 ${getRiskColor(portfolioRisk.overall_risk_score)}`}>
                    {portfolioRisk.overall_risk_score}/100
                  </div>
                  <div className="text-text-secondary text-sm">
                    {portfolioRisk.overall_risk_score <= 30 ? 'Low Risk' :
                     portfolioRisk.overall_risk_score <= 60 ? 'Medium Risk' :
                     portfolioRisk.overall_risk_score <= 80 ? 'High Risk' : 'Critical Risk'}
                  </div>
                </div>
              </div>

              <div className="lg:col-span-3">
                <div className="bg-card border border-border rounded-lg p-6">
                  <h3 className="font-semibold text-text-primary mb-4">Risk Metrics</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-text-primary font-semibold">
                        ${portfolioRisk.value_at_risk_95.toLocaleString()}
                      </div>
                      <div className="text-text-secondary text-xs">Value at Risk (95%)</div>
                    </div>
                    <div className="text-center">
                      <div className="text-red-400 font-semibold">
                        -{portfolioRisk.maximum_drawdown_potential}%
                      </div>
                      <div className="text-text-secondary text-xs">Max Drawdown</div>
                    </div>
                    <div className="text-center">
                      <div className="text-yellow-400 font-semibold">
                        {(portfolioRisk.correlation_risk * 100).toFixed(0)}%
                      </div>
                      <div className="text-text-secondary text-xs">Correlation Risk</div>
                    </div>
                    <div className="text-center">
                      <div className="text-blue-400 font-semibold">
                        {(portfolioRisk.liquidity_risk * 100).toFixed(0)}%
                      </div>
                      <div className="text-text-secondary text-xs">Liquidity Risk</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Risk Distribution */}
          {portfolioRisk && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-4">Risk Distribution</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-green-400 flex items-center">
                      <div className="w-3 h-3 bg-green-400 rounded-full mr-2"></div>
                      Low Risk
                    </span>
                    <span className="text-text-primary font-semibold">
                      {portfolioRisk.positions_by_risk.low} positions
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-yellow-400 flex items-center">
                      <div className="w-3 h-3 bg-yellow-400 rounded-full mr-2"></div>
                      Medium Risk
                    </span>
                    <span className="text-text-primary font-semibold">
                      {portfolioRisk.positions_by_risk.medium} positions
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-orange-400 flex items-center">
                      <div className="w-3 h-3 bg-orange-400 rounded-full mr-2"></div>
                      High Risk
                    </span>
                    <span className="text-text-primary font-semibold">
                      {portfolioRisk.positions_by_risk.high} positions
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-red-400 flex items-center">
                      <div className="w-3 h-3 bg-red-400 rounded-full mr-2"></div>
                      Critical Risk
                    </span>
                    <span className="text-text-primary font-semibold">
                      {portfolioRisk.positions_by_risk.critical} positions
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-4">Risk Recommendations</h3>
                <div className="space-y-2">
                  {portfolioRisk.recommendations.slice(0, 5).map((rec, index) => (
                    <div key={index} className="flex items-start p-2 bg-surface/50 rounded">
                      <AlertTriangle className="w-4 h-4 mr-2 text-yellow-400 flex-shrink-0 mt-0.5" />
                      <span className="text-text-secondary text-sm">{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Token Risk Analysis */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="text-xl font-semibold text-text-primary mb-6">Token Risk Analysis</h3>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-text-secondary">Token</th>
                    <th className="text-left py-3 px-4 text-text-secondary">Risk Score</th>
                    <th className="text-left py-3 px-4 text-text-secondary">Market Cap</th>
                    <th className="text-left py-3 px-4 text-text-secondary">Liquidity</th>
                    <th className="text-left py-3 px-4 text-text-secondary">Safety Checks</th>
                    <th className="text-left py-3 px-4 text-text-secondary">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {tokenRisks.map((token) => (
                    <tr key={token.token_address} className="border-b border-border/50 hover:bg-surface/50">
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            token.risk_level === 'LOW' ? 'bg-green-400' :
                            token.risk_level === 'MEDIUM' ? 'bg-yellow-400' :
                            token.risk_level === 'HIGH' ? 'bg-orange-400' : 'bg-red-400'
                          }`}></div>
                          <div>
                            <div className="font-medium text-text-primary">${token.symbol}</div>
                            <div className="text-text-secondary text-xs">
                              {token.holder_count.toLocaleString()} holders
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className={`font-medium ${getRiskColor(token.risk_score)}`}>
                          {token.risk_score}/100
                        </div>
                        <div className={`text-xs ${getRiskColor(token.risk_level)}`}>
                          {token.risk_level}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-text-primary">
                        ${(token.market_cap / 1000000).toFixed(1)}M
                      </td>
                      <td className="py-3 px-4">
                        <div className={`font-medium ${getRiskColor(token.liquidity_risk * 100)}`}>
                          {((1 - token.liquidity_risk) * 100).toFixed(0)}%
                        </div>
                        <div className="text-text-secondary text-xs">
                          ${(token.trading_volume_24h / 1000000).toFixed(1)}M volume
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-1">
                          {token.safety_checks.contract_verified ? (
                            <CheckCircle className="w-4 h-4 text-green-400" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-400" />
                          )}
                          {token.safety_checks.liquidity_locked ? (
                            <CheckCircle className="w-4 h-4 text-green-400" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-400" />
                          )}
                          {token.safety_checks.audit_completed ? (
                            <CheckCircle className="w-4 h-4 text-green-400" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-400" />
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <button
                          onClick={() => setSelectedToken(token)}
                          className="p-2 text-text-secondary hover:bg-surface rounded transition-colors"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Token Details Modal */}
          {selectedToken && (
            <div className="fixed inset-0 z-50 overflow-hidden">
              <div className="absolute inset-0 bg-black/50" onClick={() => setSelectedToken(null)} />
              
              <div className="absolute right-0 top-0 h-full w-full max-w-2xl bg-card border-l border-border shadow-2xl">
                <div className="flex h-full flex-col p-6">
                  {/* Modal Header */}
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-text-primary">
                      Risk Analysis: ${selectedToken.symbol}
                    </h2>
                    <button
                      onClick={() => setSelectedToken(null)}
                      className="p-2 hover:bg-surface rounded transition-colors"
                    >
                      <XCircle className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Risk Overview */}
                  <div className={`border rounded-lg p-4 mb-6 ${getRiskBgColor(selectedToken.risk_level)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Overall Risk Score</span>
                      <span className={`text-2xl font-bold ${getRiskColor(selectedToken.risk_score)}`}>
                        {selectedToken.risk_score}/100
                      </span>
                    </div>
                    <div className={`text-sm ${getRiskColor(selectedToken.risk_level)}`}>
                      {selectedToken.risk_level} RISK LEVEL
                    </div>
                  </div>

                  {/* Risk Breakdown */}
                  <div className="mb-6">
                    <h3 className="font-semibold text-text-primary mb-3">Risk Breakdown</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary">Liquidity Risk</span>
                        <span className={`font-semibold ${getRiskColor(selectedToken.liquidity_risk * 100)}`}>
                          {(selectedToken.liquidity_risk * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary">Volatility Risk</span>
                        <span className={`font-semibold ${getRiskColor(selectedToken.volatility_risk * 100)}`}>
                          {(selectedToken.volatility_risk * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary">Concentration Risk</span>
                        <span className={`font-semibold ${getRiskColor(selectedToken.concentration_risk * 100)}`}>
                          {(selectedToken.concentration_risk * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary">Smart Contract Risk</span>
                        <span className={`font-semibold ${getRiskColor(selectedToken.smart_contract_risk * 100)}`}>
                          {(selectedToken.smart_contract_risk * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Risk Factors */}
                  <div className="mb-6">
                    <h3 className="font-semibold text-text-primary mb-3">Risk Factors</h3>
                    <div className="space-y-3">
                      {selectedToken.risk_factors.map((factor, index) => (
                        <div key={index} className={`border rounded p-3 ${
                          factor.severity === 'critical' ? 'border-red-500 bg-red-500/10' :
                          factor.severity === 'high' ? 'border-orange-500 bg-orange-500/10' :
                          factor.severity === 'medium' ? 'border-yellow-500 bg-yellow-500/10' :
                          'border-blue-500 bg-blue-500/10'
                        }`}>
                          <div className="flex items-center justify-between mb-2">
                            <span className={`font-medium ${getSeverityColor(factor.severity)}`}>
                              {factor.factor}
                            </span>
                            <span className={`text-xs px-2 py-1 rounded ${
                              factor.severity === 'critical' ? 'bg-red-900 text-red-300' :
                              factor.severity === 'high' ? 'bg-orange-900 text-orange-300' :
                              factor.severity === 'medium' ? 'bg-yellow-900 text-yellow-300' :
                              'bg-blue-900 text-blue-300'
                            }`}>
                              {factor.severity.toUpperCase()}
                            </span>
                          </div>
                          <div className="text-text-secondary text-sm mb-2">
                            {factor.description}
                          </div>
                          <div className="text-text-primary text-sm font-medium">
                            💡 {factor.recommendation}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Safety Checks */}
                  <div>
                    <h3 className="font-semibold text-text-primary mb-3">Safety Checks</h3>
                    <div className="space-y-2">
                      {Object.entries(selectedToken.safety_checks).map(([check, passed]) => (
                        <div key={check} className="flex items-center justify-between p-2 bg-surface rounded">
                          <span className="text-text-secondary capitalize">
                            {check.replace(/_/g, ' ')}
                          </span>
                          {passed ? (
                            <CheckCircle className="w-5 h-5 text-green-400" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-400" />
                          )}
                        </div>
                      ))}
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
