'use client'

import { useState } from 'react'
import Navbar from '@/components/Layout/Navbar'
import { 
  HelpCircle, 
  Book, 
  Shield, 
  ArrowUpDown, 
  Brain, 
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Info,
  TrendingUp,
  Target
} from 'lucide-react'

export default function HelpPage() {
  const [activeSection, setActiveSection] = useState<string>('overview')

  const sections = [
    { id: 'overview', title: 'Platform Overview', icon: Book },
    { id: 'risk-levels', title: 'Risk Level Guide', icon: Shield },
    { id: 'arbitrage', title: 'Arbitrage Trading', icon: ArrowUpDown },
    { id: 'intelligence', title: 'Social Intelligence', icon: Brain },
    { id: 'analytics', title: 'Performance Analytics', icon: BarChart3 },
    { id: 'strategies', title: 'Trading Strategies', icon: Target }
  ]

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-background p-6 pt-20">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-text-primary mb-2 flex items-center">
              <HelpCircle className="w-8 h-8 mr-3 text-primary" />
              Help & Documentation
            </h1>
            <p className="text-text-secondary">
              Complete guide to using the Solsak intelligent trading platform
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Sidebar Navigation */}
            <div className="lg:col-span-1">
              <div className="bg-card border border-border rounded-lg p-4">
                <h3 className="font-semibold text-text-primary mb-4">Documentation</h3>
                <nav className="space-y-2">
                  {sections.map((section) => {
                    const Icon = section.icon
                    return (
                      <button
                        key={section.id}
                        onClick={() => setActiveSection(section.id)}
                        className={`w-full text-left p-3 rounded-lg transition-colors flex items-center ${
                          activeSection === section.id
                            ? 'bg-primary text-white'
                            : 'text-text-secondary hover:text-text-primary hover:bg-surface'
                        }`}
                      >
                        <Icon className="w-4 h-4 mr-3" />
                        {section.title}
                      </button>
                    )
                  })}
                </nav>
              </div>
            </div>

            {/* Content Area */}
            <div className="lg:col-span-3">
              <div className="bg-card border border-border rounded-lg p-8">
                {activeSection === 'overview' && (
                  <div>
                    <h2 className="text-2xl font-bold text-text-primary mb-6">Platform Overview</h2>
                    
                    <div className="space-y-6">
                      <div>
                        <h3 className="text-lg font-semibold text-text-primary mb-3">What is Solsak?</h3>
                        <p className="text-text-secondary mb-4">
                          Solsak is an advanced Solana DeFi trading platform that combines artificial intelligence, 
                          social sentiment analysis, and sophisticated risk management to help you trade smarter and safer.
                        </p>
                      </div>

                      <div>
                        <h3 className="text-lg font-semibold text-text-primary mb-3">Key Features</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="p-4 bg-surface rounded-lg">
                            <div className="flex items-center mb-2">
                              <Brain className="w-5 h-5 mr-2 text-blue-400" />
                              <span className="font-medium">Social Intelligence</span>
                            </div>
                            <p className="text-sm text-text-secondary">
                              Real-time sentiment analysis across Twitter, Reddit, Telegram, and news sources
                            </p>
                          </div>
                          <div className="p-4 bg-surface rounded-lg">
                            <div className="flex items-center mb-2">
                              <ArrowUpDown className="w-5 h-5 mr-2 text-green-400" />
                              <span className="font-medium">Arbitrage Detection</span>
                            </div>
                            <p className="text-sm text-text-secondary">
                              Automated cross-DEX arbitrage opportunities with profit calculations
                            </p>
                          </div>
                          <div className="p-4 bg-surface rounded-lg">
                            <div className="flex items-center mb-2">
                              <Shield className="w-5 h-5 mr-2 text-yellow-400" />
                              <span className="font-medium">Risk Management</span>
                            </div>
                            <p className="text-sm text-text-secondary">
                              Advanced rug detection and comprehensive portfolio risk analysis
                            </p>
                          </div>
                          <div className="p-4 bg-surface rounded-lg">
                            <div className="flex items-center mb-2">
                              <BarChart3 className="w-5 h-5 mr-2 text-purple-400" />
                              <span className="font-medium">Performance Analytics</span>
                            </div>
                            <p className="text-sm text-text-secondary">
                              Detailed performance tracking with intelligence contribution metrics
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeSection === 'risk-levels' && (
                  <div>
                    <h2 className="text-2xl font-bold text-text-primary mb-6">Risk Level Guide</h2>
                    
                    <div className="space-y-8">
                      <div>
                        <h3 className="text-lg font-semibold text-text-primary mb-4">Arbitrage Risk Levels</h3>
                        <div className="space-y-4">
                          <div className="p-4 bg-green-900/30 border border-green-700 rounded-lg">
                            <div className="flex items-center mb-2">
                              <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
                              <span className="font-semibold text-green-400">LOW RISK</span>
                            </div>
                            <ul className="text-sm text-text-secondary space-y-1">
                              <li>• Fast execution (typically less than 15 seconds)</li>
                              <li>• Minimal slippage (less than 0.5%)</li>
                              <li>• High liquidity on both exchanges</li>
                              <li>• Simple direct trading routes</li>
                              <li>• Best for beginners and large trades</li>
                            </ul>
                          </div>

                          <div className="p-4 bg-yellow-900/30 border border-yellow-700 rounded-lg">
                            <div className="flex items-center mb-2">
                              <AlertTriangle className="w-5 h-5 mr-2 text-yellow-400" />
                              <span className="font-semibold text-yellow-400">MEDIUM RISK</span>
                            </div>
                            <ul className="text-sm text-text-secondary space-y-1">
                              <li>• Moderate execution time (15-30 seconds)</li>
                              <li>• Some slippage risk (0.5-1%)</li>
                              <li>• Decent liquidity, may require routing</li>
                              <li>• Multiple transaction steps possible</li>
                              <li>• Suitable for experienced traders</li>
                            </ul>
                          </div>

                          <div className="p-4 bg-red-900/30 border border-red-700 rounded-lg">
                            <div className="flex items-center mb-2">
                              <AlertTriangle className="w-5 h-5 mr-2 text-red-400" />
                              <span className="font-semibold text-red-400">HIGH RISK</span>
                            </div>
                            <ul className="text-sm text-text-secondary space-y-1">
                              <li>• Slower execution (greater than 30 seconds)</li>
                              <li>• Higher slippage risk (greater than 1%)</li>
                              <li>• Lower liquidity, complex routing</li>
                              <li>• Multi-hop trades required</li>
                              <li>• Higher potential profit but significant risk</li>
                            </ul>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-lg font-semibold text-text-primary mb-4">Token Safety Risk Levels</h3>
                        <div className="space-y-4">
                          <div className="p-4 bg-green-900/30 border border-green-700 rounded-lg">
                            <div className="flex items-center mb-2">
                              <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
                              <span className="font-semibold text-green-400">LOW RISK (Score: 0-30)</span>
                            </div>
                            <ul className="text-sm text-text-secondary space-y-1">
                              <li>• Contract verified and audited</li>
                              <li>• Liquidity locked</li>
                              <li>• Ownership renounced</li>
                              <li>• High trading volume</li>
                              <li>• Established team</li>
                            </ul>
                          </div>

                          <div className="p-4 bg-yellow-900/30 border border-yellow-700 rounded-lg">
                            <div className="flex items-center mb-2">
                              <AlertTriangle className="w-5 h-5 mr-2 text-yellow-400" />
                              <span className="font-semibold text-yellow-400">MEDIUM RISK (Score: 31-60)</span>
                            </div>
                            <ul className="text-sm text-text-secondary space-y-1">
                              <li>• Some risk factors present</li>
                              <li>• Moderate liquidity</li>
                              <li>• Limited audit information</li>
                              <li>• Suitable for smaller positions</li>
                            </ul>
                          </div>

                          <div className="p-4 bg-red-900/30 border border-red-700 rounded-lg">
                            <div className="flex items-center mb-2">
                              <AlertTriangle className="w-5 h-5 mr-2 text-red-400" />
                              <span className="font-semibold text-red-400">HIGH RISK (Score: 61-80)</span>
                            </div>
                            <ul className="text-sm text-text-secondary space-y-1">
                              <li>• Multiple risk factors detected</li>
                              <li>• Low liquidity</li>
                              <li>• Unverified contract</li>
                              <li>• High concentration of holdings</li>
                              <li>• Use extreme caution</li>
                            </ul>
                          </div>

                          <div className="p-4 bg-red-900/50 border border-red-600 rounded-lg">
                            <div className="flex items-center mb-2">
                              <AlertTriangle className="w-5 h-5 mr-2 text-red-600" />
                              <span className="font-semibold text-red-600">CRITICAL RISK (Score: 81-100)</span>
                            </div>
                            <ul className="text-sm text-text-secondary space-y-1">
                              <li>• Extreme risk indicators</li>
                              <li>• Potential rug pull detected</li>
                              <li>• Immediate exit recommended</li>
                              <li>• Avoid trading entirely</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeSection === 'arbitrage' && (
                  <div>
                    <h2 className="text-2xl font-bold text-text-primary mb-6">Arbitrage Trading Guide</h2>
                    
                    <div className="space-y-6">
                      <div>
                        <h3 className="text-lg font-semibold text-text-primary mb-3">What is Arbitrage?</h3>
                        <p className="text-text-secondary mb-4">
                          Arbitrage is the practice of buying an asset on one exchange and simultaneously selling it on another 
                          exchange for a profit, taking advantage of price differences between markets.
                        </p>
                      </div>

                      <div>
                        <h3 className="text-lg font-semibold text-text-primary mb-3">How Our System Works</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="p-4 bg-surface rounded-lg">
                            <h4 className="font-medium mb-2">1. Price Monitoring</h4>
                            <p className="text-sm text-text-secondary">
                              Continuously monitors prices across Jupiter, Orca, Raydium, and Serum
                            </p>
                          </div>
                          <div className="p-4 bg-surface rounded-lg">
                            <h4 className="font-medium mb-2">2. Opportunity Detection</h4>
                            <p className="text-sm text-text-secondary">
                              Identifies profitable price differences and calculates potential profits
                            </p>
                          </div>
                          <div className="p-4 bg-surface rounded-lg">
                            <h4 className="font-medium mb-2">3. Risk Assessment</h4>
                            <p className="text-sm text-text-secondary">
                              Evaluates liquidity, slippage risk, and execution complexity
                            </p>
                          </div>
                          <div className="p-4 bg-surface rounded-lg">
                            <h4 className="font-medium mb-2">4. Execution Planning</h4>
                            <p className="text-sm text-text-secondary">
                              Provides optimal routing and timing for maximum profit
                            </p>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-lg font-semibold text-text-primary mb-3">Key Metrics Explained</h3>
                        <div className="space-y-3">
                          <div className="p-3 bg-surface rounded">
                            <span className="font-medium">Profit Percentage:</span>
                            <span className="text-text-secondary ml-2">Expected profit after fees and slippage</span>
                          </div>
                          <div className="p-3 bg-surface rounded">
                            <span className="font-medium">Confidence Score:</span>
                            <span className="text-text-secondary ml-2">Probability of successful execution</span>
                          </div>
                          <div className="p-3 bg-surface rounded">
                            <span className="font-medium">Execution Time:</span>
                            <span className="text-text-secondary ml-2">Estimated time to complete both trades</span>
                          </div>
                          <div className="p-3 bg-surface rounded">
                            <span className="font-medium">Route Complexity:</span>
                            <span className="text-text-secondary ml-2">Number of intermediate steps required</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeSection === 'strategies' && (
                  <div>
                    <h2 className="text-2xl font-bold text-text-primary mb-6">Trading Strategies</h2>
                    
                    <div className="space-y-6">
                      <div>
                        <h3 className="text-lg font-semibold text-text-primary mb-3">Available Strategies</h3>
                        <div className="space-y-4">
                          <div className="p-4 border border-border rounded-lg">
                            <h4 className="font-medium mb-2 text-blue-400">AI Social Momentum</h4>
                            <p className="text-sm text-text-secondary mb-2">
                              Leverages social intelligence to identify tokens gaining viral traction before major price movements.
                            </p>
                            <div className="text-xs text-text-secondary">
                              Best for: Capturing early momentum • Risk Level: Medium • Time Horizon: Short-term
                            </div>
                          </div>

                          <div className="p-4 border border-border rounded-lg">
                            <h4 className="font-medium mb-2 text-green-400">Multi-DEX Arbitrage</h4>
                            <p className="text-sm text-text-secondary mb-2">
                              Automated arbitrage across Jupiter, Orca, Raydium, and Serum with intelligent routing.
                            </p>
                            <div className="text-xs text-text-secondary">
                              Best for: Consistent profits • Risk Level: Low-Medium • Time Horizon: Very short-term
                            </div>
                          </div>

                          <div className="p-4 border border-border rounded-lg">
                            <h4 className="font-medium mb-2 text-yellow-400">Risk-Managed DCA</h4>
                            <p className="text-sm text-text-secondary mb-2">
                              Dollar-cost averaging with advanced risk detection and dynamic position sizing.
                            </p>
                            <div className="text-xs text-text-secondary">
                              Best for: Long-term accumulation • Risk Level: Low • Time Horizon: Long-term
                            </div>
                          </div>

                          <div className="p-4 border border-border rounded-lg">
                            <h4 className="font-medium mb-2 text-purple-400">Unified Intelligence</h4>
                            <p className="text-sm text-text-secondary mb-2">
                              Master strategy combining all intelligence systems for optimal decision making.
                            </p>
                            <div className="text-xs text-text-secondary">
                              Best for: Maximum performance • Risk Level: Medium-High • Time Horizon: Variable
                            </div>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-lg font-semibold text-text-primary mb-3">Strategy Configuration Tips</h3>
                        <div className="space-y-3">
                          <div className="p-3 bg-surface rounded">
                            <span className="font-medium">Start with Paper Trading:</span>
                            <span className="text-text-secondary ml-2">Test strategies without risking real capital</span>
                          </div>
                          <div className="p-3 bg-surface rounded">
                            <span className="font-medium">Set Appropriate Position Sizes:</span>
                            <span className="text-text-secondary ml-2">Never risk more than 1-5% per trade</span>
                          </div>
                          <div className="p-3 bg-surface rounded">
                            <span className="font-medium">Enable Risk Management:</span>
                            <span className="text-text-secondary ml-2">Always use stop-losses and rug detection</span>
                          </div>
                          <div className="p-3 bg-surface rounded">
                            <span className="font-medium">Monitor Performance:</span>
                            <span className="text-text-secondary ml-2">Regularly review analytics and adjust parameters</span>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-lg font-semibold text-text-primary mb-3">Best Practices</h3>
                        <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                          <div className="flex items-start">
                            <Info className="w-5 h-5 mr-3 text-blue-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <h4 className="font-medium text-blue-400 mb-2">Risk Management Guidelines</h4>
                              <ul className="text-sm text-text-secondary space-y-1">
                                <li>• Never invest more than you can afford to lose</li>
                                <li>• Diversify across multiple strategies and tokens</li>
                                <li>• Start with small position sizes and scale up gradually</li>
                                <li>• Always enable rug detection and risk monitoring</li>
                                <li>• Regularly review and adjust your risk parameters</li>
                                <li>• Monitor market conditions and adjust strategies accordingly</li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
