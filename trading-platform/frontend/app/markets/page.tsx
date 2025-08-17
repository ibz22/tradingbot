'use client'

import { useState, useEffect } from 'react'
import Navbar from '@/components/Layout/Navbar'
import BotCreator from '@/components/BotCreator/BotCreator'
import { TrendingUp, TrendingDown, RefreshCw } from 'lucide-react'
import { getCryptoPrices, getStockPrices, MarketData } from '@/lib/market-data'
import { BotConfig } from '@/lib/types'

export default function MarketsPage() {
  const [cryptoMarkets, setCryptoMarkets] = useState<MarketData[]>([])
  const [stockMarkets, setStockMarkets] = useState<MarketData[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [mounted, setMounted] = useState(false)
  const [isBotCreatorOpen, setIsBotCreatorOpen] = useState(false)

  const fetchMarketData = async () => {
    setLoading(true)
    try {
      const [crypto, stocks] = await Promise.all([
        getCryptoPrices(),
        getStockPrices()
      ])
      setCryptoMarkets(crypto)
      setStockMarkets(stocks)
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Error fetching market data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateBot = async (config: BotConfig) => {
    console.log('Creating bot from Markets page:', config)
    setIsBotCreatorOpen(false)
    // In a real app, this would call the API to create the bot
  }

  useEffect(() => {
    setMounted(true)
    // Fetch immediately
    fetchMarketData()
    
    // Then fetch every 10 seconds
    const interval = setInterval(fetchMarketData, 10000)
    
    return () => clearInterval(interval)
  }, [])
  return (
    <>
      <Navbar onNewBot={() => setIsBotCreatorOpen(true)} />
      <div className="min-h-screen bg-background p-6 pt-20">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-text-primary">Markets Overview</h1>
            <div className="flex items-center gap-4">
              {mounted && lastUpdate && (
                <span className="text-sm text-text-secondary">
                  Last updated: {lastUpdate.toLocaleTimeString()}
                </span>
              )}
              <button 
                onClick={fetchMarketData}
                className="btn-secondary p-2"
                disabled={loading}
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
          
          {/* Solana Markets */}
          <div className="mb-12">
            <h2 className="text-xl font-semibold text-text-primary mb-4">
              Crypto Markets (Live from Binance)
            </h2>
            <div className="card overflow-hidden">
              <table className="w-full">
                <thead className="bg-background border-b border-border">
                  <tr>
                    <th className="text-left p-4 text-text-secondary">Symbol</th>
                    <th className="text-right p-4 text-text-secondary">Price</th>
                    <th className="text-right p-4 text-text-secondary">24h Change</th>
                    <th className="text-right p-4 text-text-secondary">Volume</th>
                    <th className="text-right p-4 text-text-secondary">24h High</th>
                    <th className="text-right p-4 text-text-secondary">24h Low</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && cryptoMarkets.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center p-8 text-text-secondary">
                        Loading real-time data...
                      </td>
                    </tr>
                  ) : (
                    cryptoMarkets.map((market) => (
                      <tr key={market.symbol} className="border-b border-border hover:bg-background transition-colors">
                        <td className="p-4 font-medium text-text-primary">{market.symbol}</td>
                        <td className="p-4 text-right text-text-primary">
                          ${market.price < 1 ? market.price.toFixed(6) : market.price.toLocaleString()}
                        </td>
                        <td className="p-4 text-right">
                          <span className={`flex items-center justify-end ${market.change >= 0 ? 'text-success' : 'text-error'}`}>
                            {market.change >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
                            {Math.abs(market.change).toFixed(2)}%
                          </span>
                        </td>
                        <td className="p-4 text-right text-text-secondary">{market.volume}</td>
                        <td className="p-4 text-right text-text-secondary">
                          ${market.high < 1 ? market.high.toFixed(6) : market.high.toLocaleString()}
                        </td>
                        <td className="p-4 text-right text-text-secondary">
                          ${market.low < 1 ? market.low.toFixed(6) : market.low.toLocaleString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Stock Markets */}
          <div>
            <h2 className="text-xl font-semibold text-text-primary mb-4">
              Stock Markets {stockMarkets[0]?.price ? '(Live from Alpaca)' : '(Demo Data)'}
            </h2>
            <div className="card overflow-hidden">
              <table className="w-full">
                <thead className="bg-background border-b border-border">
                  <tr>
                    <th className="text-left p-4 text-text-secondary">Symbol</th>
                    <th className="text-right p-4 text-text-secondary">Price</th>
                    <th className="text-right p-4 text-text-secondary">Change</th>
                    <th className="text-right p-4 text-text-secondary">Volume</th>
                    <th className="text-right p-4 text-text-secondary">High</th>
                    <th className="text-right p-4 text-text-secondary">Low</th>
                  </tr>
                </thead>
                <tbody>
                  {stockMarkets.map((stock) => (
                    <tr key={stock.symbol} className="border-b border-border hover:bg-background transition-colors">
                      <td className="p-4 font-medium text-text-primary">{stock.symbol}</td>
                      <td className="p-4 text-right text-text-primary">${stock.price.toFixed(2)}</td>
                      <td className="p-4 text-right">
                        <span className={`flex items-center justify-end ${stock.change >= 0 ? 'text-success' : 'text-error'}`}>
                          {stock.change >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
                          {Math.abs(stock.change).toFixed(2)}%
                        </span>
                      </td>
                      <td className="p-4 text-right text-text-secondary">{stock.volume}</td>
                      <td className="p-4 text-right text-text-secondary">${stock.high.toFixed(2)}</td>
                      <td className="p-4 text-right text-text-secondary">${stock.low.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      
      {/* Bot Creator Modal */}
      <BotCreator
        isOpen={isBotCreatorOpen}
        onClose={() => setIsBotCreatorOpen(false)}
        onCreateBot={handleCreateBot}
      />
    </>
  )
}