'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import Navbar from '@/components/Layout/Navbar'
import BotCreator from '@/components/BotCreator/BotCreator'
import { 
  Brain, 
  TrendingUp, 
  AlertTriangle, 
  Clock, 
  Eye,
  Zap,
  DollarSign,
  BarChart3,
  RefreshCw
} from 'lucide-react'

interface TrendingCoin {
  id: string
  symbol: string
  name: string
  price: number
  price_change_24h: number
  volume_24h: number
  market_cap: number
  sentiment_score: number
  social_volume: number
  mentions_24h: number
  address?: string
  logo_url?: string
}

interface SocialSignal {
  id: string
  type: 'alpha' | 'trending' | 'sentiment' | 'news'
  title: string
  message: string
  confidence: number
  timestamp: string
  tokens_mentioned: string[]
  platform: string
  user_influence: number
  urgency: 'low' | 'medium' | 'high'
}

interface BotConfig {
  name: string
  strategy: string
  tokenSymbol: string
  buyAmount: number
  intelligence: {
    useSocialSignals: boolean
    useRugDetection: boolean
    useArbitrageDetection: boolean
  }
  riskManagement: {
    stopLoss: number
    takeProfit: number
    maxSlippage: number
  }
}

export default function IntelligencePage() {
  const [isBotCreatorOpen, setIsBotCreatorOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'trending' | 'signals' | 'alerts' | 'analytics'>('trending')
  const [allTrendingCoins, setAllTrendingCoins] = useState<TrendingCoin[]>([])
  const [socialSignals, setSocialSignals] = useState<SocialSignal[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedCoin, setSelectedCoin] = useState<TrendingCoin | null>(null)

  // Mock data for demonstration - Extended list of trending coins
  useEffect(() => {
    const mockCoins: TrendingCoin[] = [
      {
        id: '1',
        symbol: 'TROLL',
        name: 'Troll Token',
        price: 0.00234,
        price_change_24h: 45.2,
        volume_24h: 1250000,
        market_cap: 12500000,
        sentiment_score: 0.85,
        social_volume: 1247,
        mentions_24h: 3400,
        address: 'TRoLL5j9z1234567890abcdefghijk'
      },
      {
        id: '2', 
        symbol: 'AURA',
        name: 'Aura Network',
        price: 0.156,
        price_change_24h: 23.8,
        volume_24h: 890000,
        market_cap: 8900000,
        sentiment_score: 0.72,
        social_volume: 892,
        mentions_24h: 2100,
        address: 'AURa5j9z1234567890abcdefghijk'
      },
      {
        id: '3',
        symbol: 'PENGU',
        name: 'Pudgy Penguins',
        price: 0.0342,
        price_change_24h: 127.5,
        volume_24h: 4500000,
        market_cap: 45000000,
        sentiment_score: 0.92,
        social_volume: 5231,
        mentions_24h: 12400,
        address: 'HhJpBhRRn4g56VsyLuT8DL5Bv31HkXqsrahTTUCZeZg4'
      },
      {
        id: '4',
        symbol: 'WIF',
        name: 'dogwifhat',
        price: 2.85,
        price_change_24h: 18.3,
        volume_24h: 23000000,
        market_cap: 2300000000,
        sentiment_score: 0.78,
        social_volume: 3421,
        mentions_24h: 8900,
        address: 'EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm'
      },
      {
        id: '5',
        symbol: 'BONK',
        name: 'Bonk',
        price: 0.00002341,
        price_change_24h: -5.2,
        volume_24h: 12000000,
        market_cap: 1200000000,
        sentiment_score: 0.65,
        social_volume: 2341,
        mentions_24h: 6700,
        address: 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263'
      },
      {
        id: '6',
        symbol: 'POPCAT',
        name: 'Popcat',
        price: 0.892,
        price_change_24h: 34.1,
        volume_24h: 8900000,
        market_cap: 890000000,
        sentiment_score: 0.81,
        social_volume: 1892,
        mentions_24h: 4500,
        address: '7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr'
      },
      {
        id: '7',
        symbol: 'MEW',
        name: 'cat in a dogs world',
        price: 0.00456,
        price_change_24h: 67.8,
        volume_24h: 3400000,
        market_cap: 340000000,
        sentiment_score: 0.88,
        social_volume: 2134,
        mentions_24h: 5600,
        address: 'MEW1gQWJ3nEXg2qgERiKu7FAFj79PHvQVREQUzScn9U'
      },
      {
        id: '8',
        symbol: 'SILLY',
        name: 'Silly Dragon',
        price: 0.0123,
        price_change_24h: 89.2,
        volume_24h: 1200000,
        market_cap: 120000000,
        sentiment_score: 0.76,
        social_volume: 987,
        mentions_24h: 2300,
        address: '7EYnhQoR9YM3N7UoaKRoA44Uy8JeaZV3qyouov87awMs'
      },
      {
        id: '9',
        symbol: 'MYRO',
        name: 'Myro',
        price: 0.0789,
        price_change_24h: 12.3,
        volume_24h: 5600000,
        market_cap: 560000000,
        sentiment_score: 0.69,
        social_volume: 1567,
        mentions_24h: 3400,
        address: 'HhJpBhRRn4g56VsyLuT87DL5Bv31HkXqsrahTTUCZeZg5'
      },
      {
        id: '10',
        symbol: 'PONKE',
        name: 'PONKE',
        price: 0.234,
        price_change_24h: -12.7,
        volume_24h: 7800000,
        market_cap: 780000000,
        sentiment_score: 0.58,
        social_volume: 2345,
        mentions_24h: 5600,
        address: '5z3EqYQo9HiCEs3R84RCDMu2n7anpDMxRhdK8PSWmrRC'
      },
      {
        id: '11',
        symbol: 'BOME',
        name: 'BOOK OF MEME',
        price: 0.00678,
        price_change_24h: 23.4,
        volume_24h: 4500000,
        market_cap: 450000000,
        sentiment_score: 0.73,
        social_volume: 1890,
        mentions_24h: 4200,
        address: 'ukHH6c7mMyiWCf1b9pnWe25TSpkDDt3H5pQZgZ74J82'
      },
      {
        id: '12',
        symbol: 'PUMP',
        name: 'Pump.fun',
        price: 0.000456,
        price_change_24h: 234.5,
        volume_24h: 2300000,
        market_cap: 23000000,
        sentiment_score: 0.91,
        social_volume: 3456,
        mentions_24h: 7800,
        address: 'PUMPkjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr7890abcd'
      },
      {
        id: '13',
        symbol: 'AI16Z',
        name: 'ai16z',
        price: 1.234,
        price_change_24h: 56.7,
        volume_24h: 12000000,
        market_cap: 1200000000,
        sentiment_score: 0.84,
        social_volume: 4321,
        mentions_24h: 9800,
        address: 'AI16z5j9z1234567890abcdefghijk'
      },
      {
        id: '14',
        symbol: 'FWOG',
        name: 'FWOG',
        price: 0.00123,
        price_change_24h: 178.9,
        volume_24h: 890000,
        market_cap: 89000000,
        sentiment_score: 0.79,
        social_volume: 1234,
        mentions_24h: 2900,
        address: 'FWOG5j9z1234567890abcdefghijklm'
      },
      {
        id: '15',
        symbol: 'GIGACHAD',
        name: 'GigaChad',
        price: 0.0456,
        price_change_24h: 89.3,
        volume_24h: 3400000,
        market_cap: 340000000,
        sentiment_score: 0.87,
        social_volume: 2890,
        mentions_24h: 6700,
        address: 'GIGA5j9z1234567890abcdefghijklmn'
      }
    ]

    const mockSignals: SocialSignal[] = [
      {
        id: '1',
        type: 'alpha',
        title: 'TROLL Viral Momentum Building',
        message: 'Major influencer tweet causing viral spread across platforms',
        confidence: 0.89,
        timestamp: new Date().toISOString(),
        tokens_mentioned: ['TROLL'],
        platform: 'Twitter',
        user_influence: 95000,
        urgency: 'high'
      },
      {
        id: '2',
        type: 'trending',
        title: 'PENGU Breaking Out on Social Media',
        message: 'Mentions up 500% in last 4 hours, multiple whale wallets accumulating',
        confidence: 0.92,
        timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
        tokens_mentioned: ['PENGU'],
        platform: 'Reddit',
        user_influence: 45000,
        urgency: 'high'
      },
      {
        id: '3',
        type: 'sentiment',
        title: 'WIF Community Sentiment Shift',
        message: 'Positive sentiment reaching 90% across all platforms',
        confidence: 0.78,
        timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
        tokens_mentioned: ['WIF'],
        platform: 'Telegram',
        user_influence: 23000,
        urgency: 'medium'
      }
    ]

    setAllTrendingCoins(mockCoins)
    setSocialSignals(mockSignals)
  }, [])

  const [tradedCoins, setTradedCoins] = useState<Set<string>>(new Set())

  // Load traded coins from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('tradedCoins')
    if (stored) {
      setTradedCoins(new Set(JSON.parse(stored)))
    }
  }, [])

  const handleCreateBot = async (config: BotConfig) => {
    console.log('Creating AI-powered bot:', config)
    setIsBotCreatorOpen(false)
  }

  const handleQuickTrade = (coin: TrendingCoin) => {
    setSelectedCoin(coin)
    setIsBotCreatorOpen(true)
    
    // Track traded coins
    const newTradedCoins = new Set(tradedCoins)
    newTradedCoins.add(coin.symbol)
    setTradedCoins(newTradedCoins)
    localStorage.setItem('tradedCoins', JSON.stringify(Array.from(newTradedCoins)))
  }

  const handleInstantTrade = async (coin: TrendingCoin) => {
    // Quick trade without opening bot creator
    console.log(`Instant trade initiated for ${coin.symbol}`)
    
    // Track traded coins
    const newTradedCoins = new Set(tradedCoins)
    newTradedCoins.add(coin.symbol)
    setTradedCoins(newTradedCoins)
    localStorage.setItem('tradedCoins', JSON.stringify(Array.from(newTradedCoins)))
    
    // Show success notification (you can enhance this)
    alert(`Trade initiated for ${coin.symbol} at $${coin.price}`)
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
              Social Intelligence Feed
            </h1>
            <p className="text-text-secondary">
              Real-time social sentiment analysis and trading signals from across the crypto ecosystem
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="flex bg-surface rounded-lg p-1 mb-6 w-fit">
            {[
              { id: 'trending', label: 'Trending', icon: TrendingUp },
              { id: 'signals', label: 'Live Signals', icon: Zap },
              { id: 'alerts', label: 'Smart Alerts', icon: AlertTriangle },
              { id: 'analytics', label: 'Analytics', icon: BarChart3 }
            ].map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center ${
                    activeTab === tab.id
                      ? 'bg-primary text-white'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              )
            })}
          </div>

          {/* Trending Tokens Tab */}
          {activeTab === 'trending' && (
            <div className="space-y-6">
              <div className="bg-card border border-border rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold text-text-primary">Trending Social Tokens</h3>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-text-secondary">
                      {allTrendingCoins.length} tokens tracked
                    </span>
                    <button
                      onClick={() => window.location.reload()}
                      className="p-2 hover:bg-surface rounded-lg transition-colors"
                      title="Refresh data"
                    >
                      <RefreshCw className="w-4 h-4 text-text-secondary" />
                    </button>
                  </div>
                </div>
                
                {/* Scrollable container with max height */}
                <div className="max-h-[600px] overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                  {allTrendingCoins.map((coin) => (
                    <div 
                      key={coin.id} 
                      className={`flex items-center justify-between p-4 bg-surface rounded-lg hover:bg-surface/80 transition-all ${
                        tradedCoins.has(coin.symbol) ? 'border-l-4 border-primary' : ''
                      }`}
                    >
                      <div className="flex items-center space-x-4 flex-1">
                        {/* Coin Info */}
                        <div className="min-w-[120px]">
                          <div className="font-medium text-text-primary flex items-center">
                            ${coin.symbol}
                            {tradedCoins.has(coin.symbol) && (
                              <span className="ml-2 text-xs bg-primary/20 text-primary px-2 py-0.5 rounded">
                                Traded
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-text-secondary truncate max-w-[150px]">
                            {coin.name}
                          </div>
                        </div>
                        
                        {/* Price Info */}
                        <div className="text-right min-w-[100px]">
                          <div className="font-mono text-sm text-text-primary">
                            ${coin.price < 0.01 ? coin.price.toFixed(8) : coin.price.toFixed(4)}
                          </div>
                          <div className={`text-sm font-medium ${
                            coin.price_change_24h >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {coin.price_change_24h >= 0 ? '↑' : '↓'} {Math.abs(coin.price_change_24h).toFixed(1)}%
                          </div>
                        </div>
                        
                        {/* Social Metrics */}
                        <div className="flex items-center space-x-4 flex-1">
                          <div className="text-center">
                            <div className="text-sm font-medium text-text-primary">
                              {coin.mentions_24h.toLocaleString()}
                            </div>
                            <div className="text-xs text-text-secondary">mentions</div>
                          </div>
                          <div className="text-center">
                            <div className="text-sm font-medium text-text-primary">
                              {(coin.sentiment_score * 100).toFixed(0)}%
                            </div>
                            <div className="text-xs text-text-secondary">sentiment</div>
                          </div>
                          <div className="text-center">
                            <div className="text-sm font-medium text-text-primary">
                              ${(coin.volume_24h / 1000000).toFixed(1)}M
                            </div>
                            <div className="text-xs text-text-secondary">volume</div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Action Buttons */}
                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => handleInstantTrade(coin)}
                          className="px-3 py-1.5 bg-green-500 text-white rounded text-sm hover:bg-green-600 transition-colors flex items-center"
                          title="Quick Buy"
                        >
                          <DollarSign className="w-3 h-3 mr-1" />
                          Buy
                        </button>
                        <button
                          onClick={() => handleQuickTrade(coin)}
                          className="px-3 py-1.5 bg-primary text-white rounded text-sm hover:bg-primary/80 transition-colors flex items-center"
                          title="Create Bot"
                        >
                          <Brain className="w-3 h-3 mr-1" />
                          Bot
                        </button>
                        <button
                          onClick={() => window.open(`https://dexscreener.com/solana/${coin.address}`, '_blank')}
                          className="p-1.5 hover:bg-surface rounded transition-colors"
                          title="View on DexScreener"
                        >
                          <Eye className="w-4 h-4 text-text-secondary" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Summary Stats */}
                <div className="mt-4 pt-4 border-t border-border flex items-center justify-between text-sm">
                  <div className="text-text-secondary">
                    Average sentiment: {(allTrendingCoins.reduce((acc, coin) => acc + coin.sentiment_score, 0) / allTrendingCoins.length * 100).toFixed(0)}%
                  </div>
                  <div className="text-text-secondary">
                    {tradedCoins.size > 0 && `Trading ${tradedCoins.size} coins`}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Live Signals Tab */}
          {activeTab === 'signals' && (
            <div className="space-y-6">
              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-xl font-semibold text-text-primary mb-4">Live Social Signals</h3>
                <div className="space-y-4">
                  {socialSignals.map((signal) => (
                    <div key={signal.id} className="p-4 border border-border rounded-lg">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Zap className="w-4 h-4 text-yellow-400" />
                          <span className="font-medium text-text-primary">{signal.title}</span>
                          <span className={`px-2 py-1 rounded text-xs ${
                            signal.urgency === 'high' ? 'bg-red-900/30 text-red-400' :
                            signal.urgency === 'medium' ? 'bg-yellow-900/30 text-yellow-400' :
                            'bg-green-900/30 text-green-400'
                          }`}>
                            {signal.urgency.toUpperCase()}
                          </span>
                        </div>
                        <div className="text-xs text-text-secondary">
                          {Math.floor((Date.now() - new Date(signal.timestamp).getTime()) / 60000)}m ago
                        </div>
                      </div>
                      <p className="text-sm text-text-secondary mb-2">{signal.message}</p>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-text-secondary">Confidence: {(signal.confidence * 100).toFixed(0)}%</span>
                        <span className="text-text-secondary">Platform: {signal.platform}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Smart Alerts Tab */}
          {activeTab === 'alerts' && (
            <div className="space-y-6">
              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-xl font-semibold text-text-primary mb-4">Smart Alert Configuration</h3>
                <div className="space-y-4">
                  <div className="p-4 bg-surface rounded-lg">
                    <h4 className="font-medium text-text-primary mb-2">Viral Detection Alerts</h4>
                    <p className="text-sm text-text-secondary mb-3">
                      Get notified when tokens start going viral on social media
                    </p>
                    <button className="px-4 py-2 bg-primary text-white rounded text-sm hover:bg-primary/80">
                      Configure Alerts
                    </button>
                  </div>
                  <div className="p-4 bg-surface rounded-lg">
                    <h4 className="font-medium text-text-primary mb-2">Influencer Signal Alerts</h4>
                    <p className="text-sm text-text-secondary mb-3">
                      Track when major crypto influencers mention specific tokens
                    </p>
                    <button className="px-4 py-2 bg-primary text-white rounded text-sm hover:bg-primary/80">
                      Configure Alerts
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-xl font-semibold text-text-primary mb-4">Intelligence Analytics</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="text-2xl font-bold text-text-primary">1,247</div>
                    <div className="text-sm text-text-secondary">Social signals processed today</div>
                  </div>
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="text-2xl font-bold text-text-primary">89%</div>
                    <div className="text-sm text-text-secondary">Signal accuracy rate</div>
                  </div>
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="text-2xl font-bold text-text-primary">23</div>
                    <div className="text-sm text-text-secondary">Profitable trades triggered</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bot Creator Modal */}
      <BotCreator
        isOpen={isBotCreatorOpen}
        onClose={() => setIsBotCreatorOpen(false)}
        onCreateBot={handleCreateBot}
        defaultStrategy="AI Social"
      />
    </>
  )
}
