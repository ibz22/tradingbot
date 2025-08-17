import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const addresses = searchParams.get('addresses')
    
    if (!addresses) {
      // Return trending pairs if no specific addresses
      const response = await fetch('https://api.dexscreener.com/latest/dex/tokens/solana')
      const data = await response.json()
      
      return NextResponse.json(data)
    }
    
    // Fetch specific token data
    const addressList = addresses.split(',')
    const promises = addressList.map(async (address) => {
      try {
        const response = await fetch(`https://api.dexscreener.com/latest/dex/tokens/${address}`)
        const data = await response.json()
        return data.pairs?.[0] || null
      } catch (error) {
        console.error(`Error fetching data for ${address}:`, error)
        return null
      }
    })
    
    const results = await Promise.all(promises)
    const validPairs = results.filter(Boolean)
    
    // Format the response
    const formattedData = validPairs.map(pair => ({
      symbol: pair.baseToken.symbol,
      name: pair.baseToken.name,
      address: pair.baseToken.address,
      priceUsd: pair.priceUsd,
      priceChange24h: pair.priceChange?.h24 || 0,
      volume24h: pair.volume?.h24 || 0,
      liquidity: pair.liquidity?.usd || 0,
      marketCap: pair.fdv || 0,
      pairAddress: pair.pairAddress,
      dexId: pair.dexId,
      url: pair.url
    }))
    
    return NextResponse.json({
      success: true,
      data: formattedData
    })
    
  } catch (error) {
    console.error('DexScreener API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch price data' },
      { status: 500 }
    )
  }
}