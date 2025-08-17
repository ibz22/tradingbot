import { NextResponse } from 'next/server'

interface ArbitrageOpportunity {
  id: string
  token_symbol: string
  token_address: string
  buy_exchange: string
  sell_exchange: string
  buy_price: number
  sell_price: number
  price_difference: number
  percentage_profit: number
  potential_profit_usd: number
  liquidity_available: number
  estimated_execution_time: number // seconds
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  confidence_score: number
  route_complexity: number
  gas_fees_estimated: number
  minimum_amount: number
  maximum_amount: number
  last_updated: string
  trading_pair: string
  volume_24h: number
  risk_explanation: string
  execution_difficulty: 'Easy' | 'Moderate' | 'Complex'
  slippage_risk: number
}

interface ArbitrageData {
  opportunities: ArbitrageOpportunity[]
  market_summary: {
    total_opportunities: number
    average_profit_percentage: number
    highest_profit_opportunity: ArbitrageOpportunity | null
    market_efficiency_score: number
    active_pairs: number
  }
  exchange_analysis: Array<{
    exchange: string
    opportunities_count: number
    average_spread: number
    liquidity_score: number
    execution_speed: number
  }>
  execution_recommendations: string[]
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const minProfit = parseFloat(searchParams.get('min_profit') || '0.5') // minimum 0.5% profit
    const maxRisk = searchParams.get('max_risk') || 'MEDIUM'
    const exchanges = searchParams.get('exchanges')?.split(',') || ['jupiter', 'orca', 'raydium', 'serum']

    // In production, this would integrate with your arbitrage_strategy.py
    const arbitrageData = await findArbitrageOpportunities(minProfit, maxRisk, exchanges)

    return NextResponse.json({
      success: true,
      data: arbitrageData,
      timestamp: new Date().toISOString(),
      filters: { minProfit, maxRisk, exchanges }
    })

  } catch (error) {
    console.error('Arbitrage API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch arbitrage opportunities' },
      { status: 500 }
    )
  }
}

async function findArbitrageOpportunities(
  minProfit: number, 
  maxRisk: string, 
  exchanges: string[]
): Promise<ArbitrageData> {
  // This simulates your actual arbitrage detection system
  // In production, this would call your Python arbitrage_strategy.py
  
  const currentTime = new Date()
  
  const opportunities: ArbitrageOpportunity[] = [
    {
      id: 'arb_001',
      token_symbol: 'RAY',
      token_address: '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R',
      buy_exchange: 'Serum',
      sell_exchange: 'Jupiter',
      buy_price: 2.1450,
      sell_price: 2.1890,
      price_difference: 0.0440,
      percentage_profit: 2.05,
      potential_profit_usd: 220.50,
      liquidity_available: 150000,
      estimated_execution_time: 15,
      risk_level: 'LOW',
      confidence_score: 0.89,
      route_complexity: 2,
      gas_fees_estimated: 0.008,
      minimum_amount: 1000,
      maximum_amount: 25000,
      last_updated: new Date(currentTime.getTime() - 30000).toISOString(),
      trading_pair: 'RAY/USDC',
      volume_24h: 2500000,
      risk_explanation: 'Low risk due to high liquidity and fast execution between major DEXs',
      execution_difficulty: 'Easy',
      slippage_risk: 0.1
    },
    {
      id: 'arb_002',
      token_symbol: 'ORCA',
      token_address: 'orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE',
      buy_exchange: 'Orca',
      sell_exchange: 'Raydium',
      buy_price: 3.8920,
      sell_price: 3.9670,
      price_difference: 0.0750,
      percentage_profit: 1.93,
      potential_profit_usd: 386.50,
      liquidity_available: 89000,
      estimated_execution_time: 12,
      risk_level: 'LOW',
      confidence_score: 0.92,
      route_complexity: 1,
      gas_fees_estimated: 0.006,
      minimum_amount: 2000,
      maximum_amount: 15000,
      last_updated: new Date(currentTime.getTime() - 45000).toISOString(),
      trading_pair: 'ORCA/USDC',
      volume_24h: 1800000,
      risk_explanation: 'Low risk with excellent liquidity on both exchanges',
      execution_difficulty: 'Easy',
      slippage_risk: 0.2
    },
    {
      id: 'arb_003',
      token_symbol: 'MNGO',
      token_address: 'MangoCzJ36AjZyKwVj3VnYU4GTonjfVEnJmvvWaxLac',
      buy_exchange: 'Jupiter',
      sell_exchange: 'Orca',
      buy_price: 0.0895,
      sell_price: 0.0932,
      price_difference: 0.0037,
      percentage_profit: 4.13,
      potential_profit_usd: 185.50,
      liquidity_available: 45000,
      estimated_execution_time: 20,
      risk_level: 'MEDIUM',
      confidence_score: 0.74,
      route_complexity: 3,
      gas_fees_estimated: 0.012,
      minimum_amount: 500,
      maximum_amount: 8000,
      last_updated: new Date(currentTime.getTime() - 75000).toISOString(),
      trading_pair: 'MNGO/USDC',
      volume_24h: 450000,
      risk_explanation: 'Medium risk due to multi-hop routing and moderate liquidity',
      execution_difficulty: 'Moderate',
      slippage_risk: 0.8
    },
    {
      id: 'arb_004',
      token_symbol: 'SBR',
      token_address: 'Saber2gLauYim4Mvftnrasomsv6NvAuncvMEZwcLpD1',
      buy_exchange: 'Raydium',
      sell_exchange: 'Serum',
      buy_price: 0.0134,
      sell_price: 0.0141,
      price_difference: 0.0007,
      percentage_profit: 5.22,
      potential_profit_usd: 78.30,
      liquidity_available: 25000,
      estimated_execution_time: 25,
      risk_level: 'HIGH',
      confidence_score: 0.68,
      route_complexity: 4,
      gas_fees_estimated: 0.018,
      minimum_amount: 200,
      maximum_amount: 3000,
      last_updated: new Date(currentTime.getTime() - 120000).toISOString(),
      trading_pair: 'SBR/USDC',
      volume_24h: 180000,
      risk_explanation: 'High risk due to low liquidity and complex routing requirements',
      execution_difficulty: 'Complex',
      slippage_risk: 2.1
    }
  ]

  // Filter by minimum profit and max risk
  const filteredOpportunities = opportunities.filter(opp => 
    opp.percentage_profit >= minProfit &&
    (maxRisk === 'HIGH' || 
     (maxRisk === 'MEDIUM' && opp.risk_level !== 'HIGH') ||
     (maxRisk === 'LOW' && opp.risk_level === 'LOW'))
  )

  const highestProfit = filteredOpportunities.reduce((max, opp) => 
    opp.percentage_profit > max.percentage_profit ? opp : max, 
    filteredOpportunities[0]
  )

  const marketSummary = {
    total_opportunities: filteredOpportunities.length,
    average_profit_percentage: filteredOpportunities.reduce((sum, opp) => 
      sum + opp.percentage_profit, 0) / filteredOpportunities.length,
    highest_profit_opportunity: highestProfit,
    market_efficiency_score: 0.78, // Market efficiency (lower = more opportunities)
    active_pairs: new Set(filteredOpportunities.map(opp => opp.trading_pair)).size
  }

  const exchangeAnalysis = [
    {
      exchange: 'Jupiter',
      opportunities_count: 15,
      average_spread: 1.8,
      liquidity_score: 0.92,
      execution_speed: 8
    },
    {
      exchange: 'Orca',
      opportunities_count: 12,
      average_spread: 2.1,
      liquidity_score: 0.88,
      execution_speed: 6
    },
    {
      exchange: 'Raydium',
      opportunities_count: 18,
      average_spread: 2.4,
      liquidity_score: 0.85,
      execution_speed: 10
    },
    {
      exchange: 'Serum',
      opportunities_count: 8,
      average_spread: 3.2,
      liquidity_score: 0.76,
      execution_speed: 15
    }
  ]

  const executionRecommendations = [
    `${filteredOpportunities.length} arbitrage opportunities detected`,
    `Best opportunity: ${highestProfit?.token_symbol} with ${highestProfit?.percentage_profit.toFixed(2)}% profit`,
    'Monitor gas fees - current network congestion is low',
    'Jupiter offers best liquidity for large trades',
    'Orca provides fastest execution times',
    'Consider position sizing based on liquidity depth'
  ]

  return {
    opportunities: filteredOpportunities,
    market_summary: marketSummary,
    exchange_analysis: exchangeAnalysis,
    execution_recommendations: executionRecommendations
  }
}
