// Market data fetching utilities

export interface MarketData {
  symbol: string
  price: number
  change: number
  volume: string
  high: number
  low: number
}

// Fetch crypto prices from Binance (no API key needed)
export async function getCryptoPrices(): Promise<MarketData[]> {
  try {
    // Binance API for 24hr ticker data
    const symbols = ['SOLUSDT', 'BTCUSDT', 'ETHUSDT', 'BONKUSDT', 'JUPUSDT']
    const promises = symbols.map(symbol => 
      fetch(`https://api.binance.com/api/v3/ticker/24hr?symbol=${symbol}`)
        .then(res => res.json())
    )
    
    const data = await Promise.all(promises)
    
    return data.map((ticker, index) => ({
      symbol: symbols[index].replace('USDT', '/USDC'),
      price: parseFloat(ticker.lastPrice),
      change: parseFloat(ticker.priceChangePercent),
      volume: `$${(parseFloat(ticker.quoteVolume) / 1000000).toFixed(1)}M`,
      high: parseFloat(ticker.highPrice),
      low: parseFloat(ticker.lowPrice)
    }))
  } catch (error) {
    console.error('Error fetching crypto prices:', error)
    // Return mock data as fallback
    return [
      { symbol: 'SOL/USDC', price: 159.23, change: 2.4, volume: '$1.2B', high: 162.50, low: 155.30 },
      { symbol: 'BTC/USDC', price: 98420.50, change: -1.2, volume: '$45.3B', high: 99850, low: 97200 },
      { symbol: 'ETH/USDC', price: 3842.15, change: 3.8, volume: '$18.7B', high: 3920, low: 3710 },
      { symbol: 'BONK/USDC', price: 0.000042, change: 15.2, volume: '$892M', high: 0.000045, low: 0.000038 },
      { symbol: 'JUP/USDC', price: 1.82, change: -0.5, volume: '$125M', high: 1.95, low: 1.78 },
    ]
  }
}

// Fetch stock prices from your backend (which uses Alpaca)
export async function getStockPrices(): Promise<MarketData[]> {
  try {
    const response = await fetch('http://localhost:8000/api/markets/stocks')
    if (!response.ok) throw new Error('Backend not available')
    
    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error fetching stock prices:', error)
    // Return mock data as fallback
    return [
      { symbol: 'AAPL', price: 242.84, change: 1.2, volume: '52.3M', high: 244.20, low: 240.50 },
      { symbol: 'TSLA', price: 412.36, change: -2.8, volume: '98.7M', high: 425.00, low: 408.00 },
      { symbol: 'MSFT', price: 468.25, change: 0.8, volume: '22.1M', high: 470.00, low: 465.30 },
      { symbol: 'NVDA', price: 145.62, change: 4.2, volume: '284M', high: 147.00, low: 140.20 },
      { symbol: 'AMD', price: 182.94, change: 3.1, volume: '68.4M', high: 184.50, low: 178.20 },
    ]
  }
}
