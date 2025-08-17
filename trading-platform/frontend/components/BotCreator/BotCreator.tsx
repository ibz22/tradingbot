'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X, Brain, TrendingUp } from 'lucide-react'
import { BotConfig } from '@/lib/types'

const botConfigSchema = z.object({
  name: z.string().min(1, 'Bot name is required'),
  assetType: z.enum(['Solana', 'Stocks']),
  market: z.string().min(1, 'Market is required'),
  strategy: z.enum(['Momentum', 'Grid', 'Mean Reversion', 'AI Social', 'Arbitrage', 'DCA', 'Breakout', 'Scalping', 'Rug Detection', 'Multi-DEX Arbitrage']),
  secondaryStrategy: z.enum(['None', 'AI Social', 'Stop Loss', 'Take Profit', 'DCA', 'Trailing Stop', 'Rug Detection', 'Risk Management']).optional(),
  timeframe: z.enum(['1m', '5m', '15m', '1h', '4h', '1d']),
  paperTrading: z.boolean(),
  connectApi: z.boolean(),
  initialBalance: z.number().min(100, 'Minimum balance is $100'),
  aiEnabled: z.boolean().optional(),
  autoTrade: z.boolean().optional(),
  sentimentThreshold: z.number().min(0).max(100).optional(),
  stopLoss: z.number().min(0).max(100).optional(),
  takeProfit: z.number().min(0).max(1000).optional(),
})

interface BotCreatorProps {
  isOpen: boolean
  onClose: () => void
  onCreateBot: (config: BotConfig) => void
  defaultStrategy?: string | null
}

export default function BotCreator({ isOpen, onClose, onCreateBot, defaultStrategy }: BotCreatorProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [useCustomAddress, setUseCustomAddress] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { errors }
  } = useForm<BotConfig>({
    resolver: zodResolver(botConfigSchema),
    defaultValues: {
      name: '',
      assetType: 'Solana',
      market: '',
      strategy: (defaultStrategy as any) || 'Momentum',
      secondaryStrategy: 'None',
      timeframe: '1m',
      paperTrading: true,
      connectApi: false,
      initialBalance: 5000,
      aiEnabled: false,
      autoTrade: false,
      sentimentThreshold: 70,
      stopLoss: 5,
      takeProfit: 10
    }
  })

  const assetType = watch('assetType')
  const strategy = watch('strategy')
  const secondaryStrategy = watch('secondaryStrategy')
  const aiEnabled = watch('aiEnabled')
  const paperTrading = watch('paperTrading')

  const getSuggestedMarkets = (type: 'Solana' | 'Stocks') => {
    if (type === 'Solana') {
      return ['SOL/USDC', 'RAY/USDC', 'ORCA/USDC', 'BONK/USDC', 'JUP/USDC']
    } else {
      return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'GLD', 'SPY']
    }
  }

  const onSubmit = async (data: BotConfig) => {
    setIsSubmitting(true)
    try {
      await onCreateBot(data)
      reset()
      onClose()
    } catch (error) {
      console.error('Failed to create bot:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      
      <div className="absolute right-0 top-0 h-full w-full max-w-md bg-card border-l border-border shadow-2xl">
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <h2 className="text-xl font-semibold text-text-primary">Create Bot</h2>
            <button
              onClick={onClose}
              className="p-2 text-text-secondary hover:text-text-primary hover:bg-hover rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Form */}
          <div className="flex-1 overflow-y-auto p-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Bot Name */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Bot Name
                </label>
                <input
                  {...register('name')}
                  placeholder="e.g., SOL Momentum v2"
                  className="input w-full"
                />
                {errors.name && (
                  <p className="text-error text-sm mt-1">{errors.name.message}</p>
                )}
              </div>

              {/* Asset Type & Market */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Asset Type
                  </label>
                  <select {...register('assetType')} className="input w-full">
                    <option value="Solana">Solana</option>
                    <option value="Stocks">Stocks</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Market
                  </label>
                  
                  {assetType === 'Solana' && (
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-text-secondary">Select from list or paste contract</span>
                      <button
                        type="button"
                        onClick={() => setUseCustomAddress(!useCustomAddress)}
                        className="text-xs text-primary hover:text-primary-dark transition-colors"
                      >
                        {useCustomAddress ? '← Back to list' : 'Use contract address →'}
                      </button>
                    </div>
                  )}

                  {assetType === 'Solana' ? (
                    useCustomAddress ? (
                      <div className="space-y-2">
                        <input
                          {...register('market')}
                          type="text"
                          className="input w-full font-mono text-sm"
                          placeholder="Paste Solana token address (e.g., HhJpBhRRn4g56VsyLuT8DL5...)"
                        />
                        <div className="text-xs text-text-secondary space-y-1">
                          <p>💡 Tips:</p>
                          <ul className="list-disc list-inside space-y-0.5">
                            <li>Get address from DexScreener or Birdeye</li>
                            <li>Ensure liquidity exists on Raydium/Orca</li>
                            <li>Bot will auto-detect the best DEX</li>
                          </ul>
                        </div>
                      </div>
                    ) : (
                      <select 
                        {...register('market')} 
                        className="input w-full"
                      >
                        <option value="">Select a market</option>
                        <optgroup label="Popular Tokens">
                          <option value="SOL/USDC">SOL/USDC</option>
                          <option value="BONK/USDC">BONK/USDC</option>
                          <option value="WIF/USDC">WIF/USDC</option>
                          <option value="JUP/USDC">JUP/USDC</option>
                          <option value="PYTH/USDC">PYTH/USDC</option>
                        </optgroup>
                        <optgroup label="DeFi Tokens">
                          <option value="RAY/USDC">RAY/USDC</option>
                          <option value="ORCA/USDC">ORCA/USDC</option>
                          <option value="SRM/USDC">SRM/USDC</option>
                          <option value="MNGO/USDC">MNGO/USDC</option>
                        </optgroup>
                        <optgroup label="Meme Coins">
                          <option value="PENGU/USDC">PENGU/USDC</option>
                          <option value="POPCAT/USDC">POPCAT/USDC</option>
                          <option value="MEW/USDC">MEW/USDC</option>
                          <option value="SILLY/USDC">SILLY/USDC</option>
                          <option value="PUMP/USDC">PUMP/USDC</option>
                          <option value="PONKE/USDC">PONKE/USDC</option>
                          <option value="BOME/USDC">BOME/USDC</option>
                          <option value="MYRO/USDC">MYRO/USDC</option>
                        </optgroup>
                      </select>
                    )
                  ) : (
                    <select 
                      {...register('market')} 
                      className="input w-full"
                    >
                      <option value="">Select a stock</option>
                      <optgroup label="Tech Giants">
                        <option value="AAPL">AAPL - Apple Inc.</option>
                        <option value="MSFT">MSFT - Microsoft Corp.</option>
                        <option value="GOOGL">GOOGL - Alphabet Inc.</option>
                        <option value="AMZN">AMZN - Amazon.com Inc.</option>
                        <option value="META">META - Meta Platforms</option>
                        <option value="NVDA">NVDA - NVIDIA Corp.</option>
                      </optgroup>
                      <optgroup label="Growth Stocks">
                        <option value="TSLA">TSLA - Tesla Inc.</option>
                        <option value="AMD">AMD - Advanced Micro Devices</option>
                        <option value="NFLX">NFLX - Netflix Inc.</option>
                      </optgroup>
                      <optgroup label="Blue Chips">
                        <option value="JPM">JPM - JPMorgan Chase</option>
                        <option value="V">V - Visa Inc.</option>
                        <option value="JNJ">JNJ - Johnson & Johnson</option>
                        <option value="WMT">WMT - Walmart Inc.</option>
                        <option value="PG">PG - Procter & Gamble</option>
                        <option value="DIS">DIS - Disney</option>
                      </optgroup>
                    </select>
                  )}
                  {errors.market && (
                    <p className="text-error text-sm mt-1">{errors.market.message}</p>
                  )}
                </div>
              </div>

              {/* Market Suggestions */}
              {!useCustomAddress && (
                <div>
                  <p className="text-sm text-text-secondary mb-2">Quick select:</p>
                  <div className="flex flex-wrap gap-2">
                    {getSuggestedMarkets(assetType).map((market) => (
                      <button
                        key={market}
                        type="button"
                        onClick={() => {
                          setValue('market', market)
                        }}
                        className="px-3 py-1 text-xs bg-background hover:bg-hover text-text-secondary hover:text-text-primary rounded border border-border transition-colors"
                      >
                        {market}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Example addresses for new tokens */}
              {useCustomAddress && assetType === 'Solana' && (
                <div className="p-3 bg-primary/10 rounded-lg border border-primary/30">
                  <p className="text-xs font-medium text-text-primary mb-2">🔥 Recently Launched Tokens:</p>
                  <div className="space-y-1 text-xs text-text-secondary">
                    <button
                      type="button"
                      onClick={() => setValue('market', 'HhJpBhRRn4g56VsyLuT8DL5Bv31HkXqsrahTTUCZeZg4')}
                      className="block hover:text-primary transition-colors"
                    >
                      PENGU: HhJpBhRRn4g56VsyLuT8DL5Bv31HkXqsrahTTUCZeZg4
                    </button>
                    <button
                      type="button"
                      onClick={() => setValue('market', 'EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm')}
                      className="block hover:text-primary transition-colors"
                    >
                      WIF: EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm
                    </button>
                  </div>
                </div>
              )}

              {/* Strategy & Timeframe */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Primary Strategy
                  </label>
                  <select {...register('strategy')} className="input w-full">
                    <option value="Momentum">📈 Momentum</option>
                    <option value="Grid">⚡ Grid Trading</option>
                    <option value="Mean Reversion">📊 Mean Reversion</option>
                    <option value="AI Social">🧠 AI Social Intelligence</option>
                    <option value="Arbitrage">⚡ Arbitrage</option>
                    <option value="DCA">💵 Dollar Cost Averaging</option>
                    <option value="Breakout">🚀 Breakout</option>
                    <option value="Scalping">⚡ Scalping</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Timeframe
                  </label>
                  <select {...register('timeframe')} className="input w-full">
                    <option value="1m">1m</option>
                    <option value="5m">5m</option>
                    <option value="15m">15m</option>
                    <option value="1h">1h</option>
                    <option value="4h">4h</option>
                    <option value="1d">1d</option>
                  </select>
                </div>
              </div>

              {/* Secondary Strategy */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Secondary Strategy (Optional)
                </label>
                <select {...register('secondaryStrategy')} className="input w-full">
                  <option value="None">None</option>
                  <option value="AI Social">🧠 AI Social Filter</option>
                  <option value="Stop Loss">🛡️ Stop Loss Protection</option>
                  <option value="Take Profit">🎯 Take Profit Targets</option>
                  <option value="DCA">💵 DCA on Dips</option>
                  <option value="Trailing Stop">📈 Trailing Stop</option>
                </select>
                <p className="text-xs text-text-secondary mt-1">
                  Combine with primary strategy for enhanced performance
                </p>
              </div>

              {/* Risk Management - Show for Stop Loss or Take Profit */}
              {(secondaryStrategy === 'Stop Loss' || secondaryStrategy === 'Take Profit') && (
                <div className="grid grid-cols-2 gap-4 p-4 bg-error/10 rounded-lg border border-error/30">
                  <div>
                    <label className="text-sm font-medium text-text-primary">Stop Loss %</label>
                    <input
                      {...register('stopLoss', { valueAsNumber: true })}
                      type="number"
                      min="1"
                      max="50"
                      className="input w-full mt-1"
                      placeholder="5"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-text-primary">Take Profit %</label>
                    <input
                      {...register('takeProfit', { valueAsNumber: true })}
                      type="number"
                      min="1"
                      max="100"
                      className="input w-full mt-1"
                      placeholder="10"
                    />
                  </div>
                </div>
              )}

              {/* Trading Mode */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-text-primary">Paper Trading</label>
                    <p className="text-xs text-text-secondary">Trade with virtual money</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      {...register('paperTrading')}
                      type="checkbox"
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-background peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-text-primary">Connect API</label>
                    <p className="text-xs text-text-secondary">Enable live trading</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      {...register('connectApi')}
                      type="checkbox"
                      className="sr-only peer"
                      disabled={paperTrading}
                    />
                    <div className={`w-11 h-6 ${paperTrading ? 'bg-border cursor-not-allowed' : 'bg-background'} peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary`}></div>
                  </label>
                </div>
              </div>

              {/* AI Social Intelligence Settings - Only show for AI Social strategy */}
              {strategy === 'AI Social' && (
                <div className="space-y-4 p-4 bg-gradient-to-r from-primary/10 to-purple-600/10 rounded-lg border border-primary/30">
                  <div className="flex items-center space-x-2 mb-2">
                    <Brain className="w-5 h-5 text-primary" />
                    <h4 className="font-semibold text-text-primary">Social Intelligence Settings</h4>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-text-primary">AI Analysis</label>
                      <p className="text-xs text-text-secondary">Monitor Twitter, Reddit, Telegram</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        {...register('aiEnabled')}
                        type="checkbox"
                        className="sr-only peer"
                        defaultChecked
                      />
                      <div className="w-11 h-6 bg-background peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-text-primary">Auto-Trade New Coins</label>
                      <p className="text-xs text-text-secondary">Buy trending tokens automatically</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        {...register('autoTrade')}
                        type="checkbox"
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-background peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-text-primary">Sentiment Threshold</label>
                    <p className="text-xs text-text-secondary mb-2">Minimum sentiment score to trade</p>
                    <input
                      {...register('sentimentThreshold', { valueAsNumber: true })}
                      type="number"
                      min="0"
                      max="100"
                      className="input w-full"
                      placeholder="70"
                    />
                  </div>
                </div>
              )}

              {/* Initial Balance */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Initial Balance ($)
                </label>
                <input
                  {...register('initialBalance', { valueAsNumber: true })}
                  type="number"
                  min="100"
                  step="100"
                  className="input w-full"
                />
                {errors.initialBalance && (
                  <p className="text-error text-sm mt-1">{errors.initialBalance.message}</p>
                )}
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating Bot...' : 'Create Bot'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}