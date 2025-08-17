'use client'

import { useState, useEffect } from 'react'
import Navbar from '@/components/Layout/Navbar'
import BotCreator from '@/components/BotCreator/BotCreator'
import { 
  TrendingUp, 
  RefreshCw, 
  Rss, 
  Twitter,
  MessageCircle,
  Globe,
  AlertCircle,
  Clock,
  ExternalLink,
  DollarSign,
  Brain
} from 'lucide-react'

interface RSSFeedItem {
  id: string
  title: string
  description: string
  link: string
  pubDate: string
  source: string
  tokens: string[]
  sentiment: 'bullish' | 'bearish' | 'neutral'
}

interface TrendingToken {
  symbol: string
  name: string
  mentions: number
  sentiment: number
  sources: string[]
  lastMention: string
  price?: number
  priceChange?: number
}

export default function TrendingPage() {
  const [isBotCreatorOpen, setIsBotCreatorOpen] = useState(false)
  const [feedItems, setFeedItems] = useState<RSSFeedItem[]>([])
  const [trendingTokens, setTrendingTokens] = useState<TrendingToken[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedSource, setSelectedSource] = useState<'all' | 'twitter' | 'reddit' | 'telegram' | 'news'>('all')
  const [autoRefresh, setAutoRefresh] = useState(true)

  // RSS feed sources
  const rssSources = [
    { name: 'CoinDesk', url: '/api/rss/coindesk', icon: Globe },
    { name: 'CryptoNews', url: '/api/rss/cryptonews', icon: Globe },
    { name: 'Twitter Trends', url: '/api/rss/twitter', icon: Twitter },
    { name: 'Reddit Crypto', url: '/api/rss/reddit', icon: MessageCircle },
    { name: 'Telegram Channels', url: '/api/rss/telegram', icon: MessageCircle }
  ]

  // Fetch RSS feeds
  const fetchRSSFeeds = async () => {
    setIsLoading(true)
    try {
      // In production, this would call your actual RSS API endpoints
      const response = await fetch('/api/trending-tokens')
      if (response.ok) {
        const data = await response.json()
        setFeedItems(data.feeds || mockFeedItems)
        setTrendingTokens(data.tokens || mockTrendingTokens)
      } else {
        // Use mock data as fallback
        setFeedItems(mockFeedItems)
        setTrendingTokens(mockTrendingTokens)
      }
    } catch (error) {
      console.error('Error fetching RSS feeds:', error)
      // Use mock data as fallback
      setFeedItems(mockFeedItems)
      setTrendingTokens(mockTrendingTokens)
    } finally {
      setIsLoading(false)
    }
  }

  // Mock data for demonstration
  const mockFeedItems: RSSFeedItem[] = [
    {
      id: '1',
      title: 'PENGU Token Surges 200% After Major Exchange Listing',
      description: 'Pudgy Penguins token PENGU sees massive volume after Binance listing announcement',
      link: 'https://example.com/news/1',
      pubDate: new Date(Date.now() - 30 * 60000).toISOString(),
      source: 'CoinDesk',
      tokens: ['PENGU'],
      sentiment: 'bullish'
    },
    {
      id: '2',
      title: 'AI Meme Coins Take Over: AI16Z Leads the Charge',
      description: 'New wave of AI-themed meme coins gaining traction on social media',
      link: 'https://example.com/news/2',
      pubDate: new Date(Date.now() - 60 * 60000).toISOString(),
      source: 'Twitter',
      tokens: ['AI16Z', 'GOAT'],
      sentiment: 'bullish'
    },
    {
      id: '3',
      title: 'Reddit Community Discovers Next 100x Gem: FWOG',
      description: 'r/CryptoMoonShots highlights FWOG as potential breakout star',
      link: 'https://reddit.com/r/cryptomoonshots',
      pubDate: new Date(Date.now() - 90 * 60000).toISOString(),
      source: 'Reddit',
      tokens: ['FWOG'],
      sentiment: 'bullish'
    },
    {
      id: '4',
      title: 'Whale Alert: Massive WIF Accumulation Detected',
      description: 'Large wallets accumulating dogwifhat tokens, social sentiment turning bullish',
      link: 'https://example.com/news/4',
      pubDate: new Date(Date.now() - 120 * 60000).toISOString(),
      source: 'Telegram',
      tokens: ['WIF'],
      sentiment: 'bullish'
    },
    {
      id: '5',
      title: 'Warning: Potential Rug Pull Detected in SCAM Token',
      description: 'Community warns about suspicious activity in newly launched token',
      link: 'https://example.com/news/5',
      pubDate: new Date(Date.now() - 150 * 60000).toISOString(),
      source: 'Twitter',
      tokens: ['SCAM'],
      sentiment: 'bearish'
    }
  ]

  const mockTrendingTokens: TrendingToken[] = [
    {
      symbol: 'PENGU',
      name: 'Pudgy Penguins',
      mentions: 12453,
      sentiment: 0.92,
      sources: ['Twitter', 'Reddit', 'Telegram'],
      lastMention: '2 minutes ago',
      price: 0.0342,
      priceChange: 127.5
    },
    {
      symbol: 'AI16Z',
      name: 'ai16z',
      mentions: 8921,
      sentiment: 0.84,
      sources: ['Twitter', 'CoinDesk'],
      lastMention: '5 minutes ago',
      price: 1.234,
      priceChange: 56.7
    },
    {
      symbol: 'WIF',
      name: 'dogwifhat',
      mentions: 7234,
      sentiment: 0.78,
      sources: ['Reddit', 'Telegram'],
      lastMention: '8 minutes ago',
      price: 2.85,
      priceChange: 18.3
    },
    {
      symbol: 'FWOG',
      name: 'FWOG',
      mentions: 5432,
      sentiment: 0.79,
      sources: ['Reddit', 'Twitter'],
      lastMention: '12 minutes ago',
      price: 0.00123,
      priceChange: 178.9
    },
    {
      symbol: 'BONK',
      name: 'Bonk',
      mentions: 4321,
      sentiment: 0.65,
      sources: ['Twitter', 'News'],
      lastMention: '15 minutes ago',
      price: 0.00002341,
      priceChange: -5.2
    }
  ]

  useEffect(() => {
    fetchRSSFeeds()
    
    // Auto-refresh every 30 seconds if enabled
    const interval = autoRefresh ? setInterval(fetchRSSFeeds, 30000) : null
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh])

  const handleCreateBot = async (config: any) => {
    console.log('Creating bot from trending page:', config)
    setIsBotCreatorOpen(false)
  }

  const handleQuickTrade = (symbol: string) => {
    console.log(`Quick trade for ${symbol}`)
    setIsBotCreatorOpen(true)
  }

  const getSentimentColor = (sentiment: string | number) => {
    if (typeof sentiment === 'number') {
      if (sentiment >= 0.7) return 'text-green-400'
      if (sentiment >= 0.4) return 'text-yellow-400'
      return 'text-red-400'
    }
    switch (sentiment) {
      case 'bullish': return 'text-green-400'
      case 'bearish': return 'text-red-400'
      default: return 'text-yellow-400'
    }
  }

  const getSourceIcon = (source: string) => {
    switch (source.toLowerCase()) {
      case 'twitter': return <Twitter className="w-4 h-4" />
      case 'reddit': return <MessageCircle className="w-4 h-4" />
      case 'telegram': return <MessageCircle className="w-4 h-4" />
      default: return <Globe className="w-4 h-4" />
    }
  }

  return (
    <>
      <Navbar onNewBot={() => setIsBotCreatorOpen(true)} />
      <div className="min-h-screen bg-background p-6 pt-20">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-text-primary mb-2 flex items-center">
              <TrendingUp className="w-8 h-8 mr-3 text-primary" />
              Trending Tokens from Social Media
            </h1>
            <p className="text-text-secondary">
              Real-time trending cryptocurrencies aggregated from RSS feeds, Twitter, Reddit, and Telegram
            </p>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-2">
              {['all', 'twitter', 'reddit', 'telegram', 'news'].map((source) => (
                <button
                  key={source}
                  onClick={() => setSelectedSource(source as any)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedSource === source
                      ? 'bg-primary text-white'
                      : 'bg-surface text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {source.charAt(0).toUpperCase() + source.slice(1)}
                </button>
              ))}
            </div>
            
            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded"
                />
                <span className="text-text-secondary">Auto-refresh</span>
              </label>
              
              <button
                onClick={fetchRSSFeeds}
                disabled={isLoading}
                className="p-2 hover:bg-surface rounded-lg transition-colors"
                title="Refresh feeds"
              >
                <RefreshCw className={`w-4 h-4 text-text-secondary ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Trending Tokens List */}
            <div className="lg:col-span-1">
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-text-primary mb-4 flex items-center">
                  <Rss className="w-5 h-5 mr-2 text-primary" />
                  Top Trending Tokens
                </h2>
                
                <div className="space-y-3 max-h-[600px] overflow-y-auto custom-scrollbar pr-2">
                  {trendingTokens.map((token, index) => (
                    <div key={token.symbol} className="p-3 bg-surface rounded-lg hover:bg-surface/80 transition-all">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-lg font-bold text-text-primary">#{index + 1}</span>
                            <span className="font-medium text-text-primary">${token.symbol}</span>
                          </div>
                          <div className="text-sm text-text-secondary">{token.name}</div>
                        </div>
                        {token.priceChange !== undefined && (
                          <div className={`text-sm font-medium ${token.priceChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {token.priceChange >= 0 ? '+' : ''}{token.priceChange.toFixed(1)}%
                          </div>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                        <div>
                          <span className="text-text-secondary">Mentions: </span>
                          <span className="text-text-primary font-medium">{token.mentions.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-text-secondary">Sentiment: </span>
                          <span className={`font-medium ${getSentimentColor(token.sentiment)}`}>
                            {(token.sentiment * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-1">
                          {token.sources.map((source) => (
                            <span key={source} title={source}>
                              {getSourceIcon(source)}
                            </span>
                          ))}
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleQuickTrade(token.symbol)}
                            className="px-2 py-1 bg-green-500 text-white rounded text-xs hover:bg-green-600 transition-colors"
                          >
                            <DollarSign className="w-3 h-3 inline mr-1" />
                            Buy
                          </button>
                          <button
                            onClick={() => setIsBotCreatorOpen(true)}
                            className="px-2 py-1 bg-primary text-white rounded text-xs hover:bg-primary/80 transition-colors"
                          >
                            <Brain className="w-3 h-3 inline mr-1" />
                            Bot
                          </button>
                        </div>
                      </div>
                      
                      <div className="mt-2 text-xs text-text-secondary flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        Last mention: {token.lastMention}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* RSS Feed Items */}
            <div className="lg:col-span-2">
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-text-primary mb-4">
                  Latest Social Media & News Feed
                </h2>
                
                <div className="space-y-4 max-h-[600px] overflow-y-auto custom-scrollbar pr-2">
                  {feedItems
                    .filter(item => selectedSource === 'all' || item.source.toLowerCase() === selectedSource)
                    .map((item) => (
                    <div key={item.id} className="p-4 bg-surface rounded-lg hover:bg-surface/80 transition-all">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h3 className="font-medium text-text-primary mb-1">{item.title}</h3>
                          <p className="text-sm text-text-secondary line-clamp-2">{item.description}</p>
                        </div>
                        <span className={`ml-4 px-2 py-1 rounded text-xs font-medium ${
                          item.sentiment === 'bullish' ? 'bg-green-900/30 text-green-400' :
                          item.sentiment === 'bearish' ? 'bg-red-900/30 text-red-400' :
                          'bg-yellow-900/30 text-yellow-400'
                        }`}>
                          {item.sentiment}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between mt-3">
                        <div className="flex items-center space-x-3 text-xs text-text-secondary">
                          <span className="flex items-center">
                            {getSourceIcon(item.source)}
                            <span className="ml-1">{item.source}</span>
                          </span>
                          <span className="flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            {new Date(item.pubDate).toLocaleTimeString()}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {item.tokens.map((token) => (
                            <button
                              key={token}
                              onClick={() => handleQuickTrade(token)}
                              className="px-2 py-1 bg-primary/20 text-primary rounded text-xs hover:bg-primary/30 transition-colors"
                            >
                              ${token}
                            </button>
                          ))}
                          <a
                            href={item.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1 hover:bg-surface rounded transition-colors"
                            title="Read more"
                          >
                            <ExternalLink className="w-3 h-3 text-text-secondary" />
                          </a>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {feedItems.length === 0 && !isLoading && (
                  <div className="text-center py-8 text-text-secondary">
                    <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No feed items available</p>
                    <button
                      onClick={fetchRSSFeeds}
                      className="mt-3 px-4 py-2 bg-primary text-white rounded text-sm hover:bg-primary/80"
                    >
                      Refresh Feeds
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* RSS Sources Status */}
          <div className="mt-6 bg-card border border-border rounded-lg p-4">
            <h3 className="text-sm font-medium text-text-primary mb-3">Connected RSS Sources</h3>
            <div className="flex flex-wrap gap-3">
              {rssSources.map((source) => {
                const Icon = source.icon
                return (
                  <div key={source.name} className="flex items-center space-x-2 px-3 py-1 bg-surface rounded-lg">
                    <Icon className="w-4 h-4 text-primary" />
                    <span className="text-sm text-text-secondary">{source.name}</span>
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  </div>
                )
              })}
            </div>
          </div>
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