'use client'

import { Area, AreaChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts'

interface PortfolioChartProps {
  data: Array<{
    timestamp: string
    value: number
    pnl: number
  }>
  pnlPercent: number
}

export default function PortfolioChart({ data, pnlPercent }: PortfolioChartProps) {
  const formatValue = (value: number) => `$${(value / 1000).toFixed(1)}k`
  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    })
  }

  return (
    <div className="card">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-text-primary">Portfolio PnL (30d)</h3>
          <div className="flex items-center space-x-2">
            <span className="text-2xl font-bold text-success">+{pnlPercent.toFixed(1)}%</span>
            <span className="text-sm text-text-secondary bg-success/20 px-2 py-1 rounded">Live</span>
          </div>
        </div>
      </div>

      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#5B8DFF" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#5B8DFF" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <XAxis 
              dataKey="timestamp" 
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: '#94A3B8' }}
              tickFormatter={formatDate}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: '#94A3B8' }}
              tickFormatter={formatValue}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1A2332',
                border: '1px solid #2A3441',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              labelStyle={{ color: '#94A3B8' }}
              itemStyle={{ color: '#5B8DFF' }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, 'Portfolio Value']}
              labelFormatter={(timestamp: string) => formatDate(timestamp)}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#5B8DFF"
              strokeWidth={2}
              fill="url(#portfolioGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}