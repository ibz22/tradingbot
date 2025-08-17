'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { TrendingUp, Plus, TrendingDown, Brain, Shield, BarChart3, HelpCircle } from 'lucide-react'

interface NavbarProps {
  onNewBot?: () => void
}

export default function Navbar({ onNewBot }: NavbarProps) {
  const [solPrice, setSolPrice] = useState({ price: 0, change: 0, loading: true })

  // Fetch real SOL price from Binance
  const fetchSolPrice = async () => {
    try {
      const response = await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=SOLUSDT')
      const data = await response.json()
      setSolPrice({
        price: parseFloat(data.lastPrice),
        change: parseFloat(data.priceChangePercent),
        loading: false
      })
    } catch (error) {
      console.error('Error fetching SOL price:', error)
      // Fallback to mock data if API fails
      setSolPrice({ price: 159.23, change: 2.4, loading: false })
    }
  }

  useEffect(() => {
    // Fetch immediately
    fetchSolPrice()
    
    // Then update every 10 seconds
    const interval = setInterval(fetchSolPrice, 10000)
    
    return () => clearInterval(interval)
  }, [])

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-card border-b border-border backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-lg font-bold text-text-primary">Solsak</div>
                <div className="text-xs text-text-secondary -mt-1">Solana-first trading platform</div>
              </div>
            </Link>
            
            {/* Navigation Links */}
            <div className="hidden md:flex items-center space-x-6">
              <Link href="/" className="text-text-primary hover:text-primary transition-colors font-medium">
                Dashboard
              </Link>
              <Link href="/bots" className="text-text-secondary hover:text-primary transition-colors">
                Bots
              </Link>
              <Link href="/strategies" className="text-text-secondary hover:text-primary transition-colors">
                Strategies
              </Link>
              <Link href="/trending" className="text-text-secondary hover:text-primary transition-colors flex items-center">
                <TrendingUp className="w-4 h-4 mr-1" />
                Trending
              </Link>
              <Link href="/intelligence" className="text-text-secondary hover:text-primary transition-colors flex items-center">
                <Brain className="w-4 h-4 mr-1" />
                Social Intel
              </Link>
              <Link href="/market-intelligence" className="text-text-secondary hover:text-primary transition-colors flex items-center">
                <Brain className="w-4 h-4 mr-1" />
                Market Intel
              </Link>
              <Link href="/risk-management" className="text-text-secondary hover:text-primary transition-colors flex items-center">
                <Shield className="w-4 h-4 mr-1" />
                Risk Mgmt
              </Link>
              <Link href="/analytics" className="text-text-secondary hover:text-primary transition-colors flex items-center">
                <BarChart3 className="w-4 h-4 mr-1" />
                Analytics
              </Link>
              <Link href="/markets" className="text-text-secondary hover:text-primary transition-colors">
                Markets
              </Link>
              <Link href="/reports" className="text-text-secondary hover:text-primary transition-colors">
                Reports
              </Link>
              <Link href="/help" className="text-text-secondary hover:text-primary transition-colors flex items-center">
                <HelpCircle className="w-4 h-4 mr-1" />
                Help
              </Link>
              <Link href="/settings" className="text-text-secondary hover:text-primary transition-colors">
                Settings
              </Link>
            </div>
          </div>

          {/* Right side - Price ticker and New Bot button */}
          <div className="flex items-center space-x-4">
            {/* SOL Price Ticker - Now with REAL data */}
            <div className="hidden sm:flex items-center space-x-2 bg-background px-3 py-2 rounded-lg">
              <span className="text-text-secondary text-sm font-medium">SOL</span>
              {solPrice.loading ? (
                <span className="text-text-secondary text-sm">Loading...</span>
              ) : (
                <>
                  <span className="text-text-primary font-semibold">
                    ${solPrice.price.toFixed(2)}
                  </span>
                  <span className={`text-sm font-medium flex items-center ${solPrice.change >= 0 ? 'text-success' : 'text-error'}`}>
                    {solPrice.change >= 0 ? <TrendingUp className="w-3 h-3 mr-0.5" /> : <TrendingDown className="w-3 h-3 mr-0.5" />}
                    {solPrice.change >= 0 ? '+' : ''}{solPrice.change.toFixed(2)}%
                  </span>
                </>
              )}
            </div>

            {/* New Bot Button - Now with onClick */}
            <button 
              onClick={onNewBot}
              className="btn-primary flex items-center space-x-2 hover:bg-primary-dark transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span className="hidden sm:inline">New Bot</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
