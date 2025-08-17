import { TrendingUp, Users, Target, BarChart3 } from 'lucide-react'

interface StatsCardsProps {
  activeBots: number
  newBots: number
  winRate: number
  totalTrades: number
  volume24h: number
  sharpeRatio: number
}

export default function StatsCards({ 
  activeBots, 
  newBots, 
  winRate, 
  totalTrades, 
  volume24h, 
  sharpeRatio 
}: StatsCardsProps) {
  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}k`
    }
    return `$${value.toFixed(0)}`
  }

  const cards = [
    {
      title: 'Active Bots',
      value: activeBots.toString(),
      subtitle: `+${newBots} today`,
      icon: Users,
      color: 'text-primary'
    },
    {
      title: 'Win Rate',
      value: `${winRate}%`,
      subtitle: `Last ${totalTrades} trades`,
      icon: Target,
      color: 'text-success'
    },
    {
      title: '24h Volume',
      value: formatCurrency(volume24h),
      subtitle: 'Across all bots',
      icon: BarChart3,
      color: 'text-primary'
    },
    {
      title: 'Sharpe Ratio',
      value: sharpeRatio.toFixed(2),
      subtitle: '30d rolling',
      icon: TrendingUp,
      color: 'text-success'
    }
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
      {cards.map((card, index) => (
        <div key={index} className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm font-medium mb-1">{card.title}</p>
              <p className="text-3xl font-bold text-text-primary mb-1">{card.value}</p>
              <p className="text-text-secondary text-sm">{card.subtitle}</p>
            </div>
            <div className={`${card.color} opacity-80`}>
              <card.icon className="w-8 h-8" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}