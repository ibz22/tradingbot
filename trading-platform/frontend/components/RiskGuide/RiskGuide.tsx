import { AlertTriangle, Info, CheckCircle, AlertCircle, XCircle } from 'lucide-react'

interface RiskLevelGuideProps {
  type?: 'arbitrage' | 'trading' | 'token' | 'portfolio'
  showTooltip?: boolean
  className?: string
}

export default function RiskLevelGuide({ type = 'arbitrage', showTooltip = true, className = '' }: RiskLevelGuideProps) {
  const getRiskExplanation = () => {
    switch (type) {
      case 'arbitrage':
        return {
          LOW: {
            icon: <CheckCircle className="w-3 h-3" />,
            description: 'Fast execution, minimal slippage, high liquidity pools',
            details: 'Best for beginners. Quick trades with predictable outcomes.',
            bgColor: 'bg-green-900/30 border-green-700',
            textColor: 'text-green-400'
          },
          MEDIUM: {
            icon: <AlertCircle className="w-3 h-3" />,
            description: 'Moderate execution time, some slippage risk, decent liquidity',
            details: 'Requires some experience. Monitor market conditions.',
            bgColor: 'bg-yellow-900/30 border-yellow-700',
            textColor: 'text-yellow-400'
          },
          HIGH: {
            icon: <XCircle className="w-3 h-3" />,
            description: 'Slower execution, higher slippage risk, potential for higher profit',
            details: 'For experienced traders. Higher risk but potentially more reward.',
            bgColor: 'bg-red-900/30 border-red-700',
            textColor: 'text-red-400'
          }
        }

      case 'trading':
        return {
          LOW: {
            icon: <CheckCircle className="w-3 h-3" />,
            description: 'Conservative strategy with stable tokens and established patterns',
            details: 'Ideal for steady growth with minimal risk exposure.',
            bgColor: 'bg-green-900/30 border-green-700',
            textColor: 'text-green-400'
          },
          MEDIUM: {
            icon: <AlertCircle className="w-3 h-3" />,
            description: 'Balanced approach with moderate volatility exposure',
            details: 'Good balance of risk and reward for most traders.',
            bgColor: 'bg-yellow-900/30 border-yellow-700',
            textColor: 'text-yellow-400'
          },
          HIGH: {
            icon: <XCircle className="w-3 h-3" />,
            description: 'Aggressive strategy with high volatility and leverage',
            details: 'Maximum potential returns with significant risk exposure.',
            bgColor: 'bg-red-900/30 border-red-700',
            textColor: 'text-red-400'
          }
        }

      case 'token':
        return {
          LOW: {
            icon: <CheckCircle className="w-3 h-3" />,
            description: 'Verified contracts, audited, high liquidity, established team',
            details: 'Safe for long-term holding and large positions.',
            bgColor: 'bg-green-900/30 border-green-700',
            textColor: 'text-green-400'
          },
          MEDIUM: {
            icon: <AlertCircle className="w-3 h-3" />,
            description: 'Some risk factors present, moderate liquidity',
            details: 'Suitable for smaller positions with proper monitoring.',
            bgColor: 'bg-yellow-900/30 border-yellow-700',
            textColor: 'text-yellow-400'
          },
          HIGH: {
            icon: <XCircle className="w-3 h-3" />,
            description: 'Multiple risk factors, low liquidity, unverified aspects',
            details: 'High risk of loss. Only for experienced traders with small amounts.',
            bgColor: 'bg-red-900/30 border-red-700',
            textColor: 'text-red-400'
          },
          CRITICAL: {
            icon: <XCircle className="w-3 h-3" />,
            description: 'Extreme risk indicators, potential rug pull, immediate exit recommended',
            details: 'Avoid trading. Exit existing positions immediately.',
            bgColor: 'bg-red-900/50 border-red-600',
            textColor: 'text-red-600'
          }
        }

      case 'portfolio':
        return {
          LOW: {
            icon: <CheckCircle className="w-3 h-3" />,
            description: 'Well diversified, low correlation, conservative allocation',
            details: 'Optimal risk management with stable growth potential.',
            bgColor: 'bg-green-900/30 border-green-700',
            textColor: 'text-green-400'
          },
          MEDIUM: {
            icon: <AlertCircle className="w-3 h-3" />,
            description: 'Moderate concentration, some correlation risk',
            details: 'Acceptable risk level with room for optimization.',
            bgColor: 'bg-yellow-900/30 border-yellow-700',
            textColor: 'text-yellow-400'
          },
          HIGH: {
            icon: <XCircle className="w-3 h-3" />,
            description: 'High concentration, significant correlation, potential for large drawdowns',
            details: 'Consider rebalancing to reduce risk exposure.',
            bgColor: 'bg-red-900/30 border-red-700',
            textColor: 'text-red-400'
          }
        }

      default:
        return {}
    }
  }

  const riskLevels = getRiskExplanation()

  if (!showTooltip) {
    return (
      <div className={`text-xs text-text-secondary ${className}`}>
        Risk Levels: {Object.entries(riskLevels).map(([level, data]: [string, any], index) => (
          <span key={level}>
            <span className={data.textColor}>{level}</span>
            {index < Object.keys(riskLevels).length - 1 && ' • '}
          </span>
        ))}
      </div>
    )
  }

  return (
    <div className={`inline-flex items-center space-x-1 ${className}`}>
      <Info className="w-4 h-4 text-text-secondary" />
      <div className="group relative">
        <span className="text-xs text-text-secondary cursor-help">Risk Guide</span>
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity z-50">
          <div className="bg-black border border-gray-700 rounded-lg p-4 w-80 text-xs">
            <h4 className="text-white font-medium mb-3 flex items-center">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Risk Level Explanations
            </h4>
            <div className="space-y-3">
              {Object.entries(riskLevels).map(([level, data]: [string, any]) => (
                <div key={level} className={`p-3 rounded border ${data.bgColor}`}>
                  <div className={`flex items-center mb-1 ${data.textColor}`}>
                    {data.icon}
                    <span className="font-medium ml-2">{level}</span>
                  </div>
                  <div className="text-gray-300 text-xs mb-1">{data.description}</div>
                  <div className="text-gray-400 text-xs">{data.details}</div>
                </div>
              ))}
            </div>
          </div>
          {/* Tooltip arrow */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-700"></div>
        </div>
      </div>
    </div>
  )
}

// Utility function to get risk colors
export const getRiskColors = (riskLevel: string) => {
  const colorMap: Record<string, { bg: string; text: string }> = {
    'LOW': { bg: 'bg-green-900/30 border-green-700', text: 'text-green-400' },
    'MEDIUM': { bg: 'bg-yellow-900/30 border-yellow-700', text: 'text-yellow-400' },
    'HIGH': { bg: 'bg-red-900/30 border-red-700', text: 'text-red-400' },
    'CRITICAL': { bg: 'bg-red-900/50 border-red-600', text: 'text-red-600' }
  }
  return colorMap[riskLevel] || colorMap['MEDIUM']
}

// Quick Risk Badge component
interface RiskBadgeProps {
  riskLevel: string
  type?: 'arbitrage' | 'trading' | 'token' | 'portfolio'
  showTooltip?: boolean
  className?: string
}

export function RiskBadge({ riskLevel, type = 'arbitrage', showTooltip = true, className = '' }: RiskBadgeProps) {
  const colors = getRiskColors(riskLevel)
  const riskData = {
    'arbitrage': {
      'LOW': 'Fast execution, minimal slippage',
      'MEDIUM': 'Moderate complexity, some risk',
      'HIGH': 'Higher risk but more profit potential'
    },
    'token': {
      'LOW': 'Verified, audited, high liquidity',
      'MEDIUM': 'Some risk factors present',
      'HIGH': 'Multiple risk factors detected',
      'CRITICAL': 'Extreme risk - avoid trading'
    }
  }

  const tooltip = riskData[type as keyof typeof riskData]?.[riskLevel] || 'Risk assessment based on multiple factors'

  if (!showTooltip) {
    return (
      <span className={`px-2 py-1 rounded text-xs ${colors.bg} ${colors.text} ${className}`}>
        {riskLevel}
      </span>
    )
  }

  return (
    <div className="relative group">
      <span className={`px-2 py-1 rounded text-xs ${colors.bg} ${colors.text} ${className} cursor-help`}>
        {riskLevel}
      </span>
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity z-10 whitespace-nowrap">
        {tooltip}
      </div>
    </div>
  )
}
