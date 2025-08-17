import { Bot } from '@/lib/types'
import { Play, Pause, Square, Edit, Trash2, Wifi, WifiOff } from 'lucide-react'

interface BotTableRowProps {
  bot: Bot
  onControl: (botId: string, action: 'start' | 'pause' | 'stop') => void
  onEdit: (botId: string) => void
  onDelete: (botId: string) => void
}

export default function BotTableRow({ bot, onControl, onEdit, onDelete }: BotTableRowProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-success'
      case 'paused':
        return 'text-yellow-500'
      case 'stopped':
        return 'text-text-secondary'
      default:
        return 'text-text-secondary'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
      case 'paused':
        return <div className="w-2 h-2 bg-yellow-500 rounded-full" />
      case 'stopped':
        return <div className="w-2 h-2 bg-text-secondary rounded-full" />
      default:
        return <div className="w-2 h-2 bg-text-secondary rounded-full" />
    }
  }

  const formatPnl = (pnl: number) => {
    const isPositive = pnl >= 0
    return (
      <span className={isPositive ? 'text-success' : 'text-error'}>
        {isPositive ? '+' : ''}{pnl.toFixed(2)}
      </span>
    )
  }

  return (
    <tr className="border-b border-border hover:bg-hover/50 transition-colors">
      {/* Bot Name & Strategy */}
      <td className="table-cell">
        <div className="flex items-center space-x-3">
          {getStatusIcon(bot.status)}
          <div>
            <div className="font-medium text-text-primary">{bot.name}</div>
            <div className="text-sm text-text-secondary">{bot.strategy}</div>
          </div>
        </div>
      </td>

      {/* Type */}
      <td className="table-cell">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          bot.type === 'Solana' 
            ? 'bg-primary/20 text-primary' 
            : 'bg-success/20 text-success'
        }`}>
          {bot.type}
        </span>
      </td>

      {/* Market */}
      <td className="table-cell">
        <span className="font-mono text-text-primary">{bot.market}</span>
      </td>

      {/* Mode */}
      <td className="table-cell">
        <div className="flex items-center space-x-2">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            bot.mode === 'Paper' 
              ? 'bg-blue-500/20 text-blue-400' 
              : 'bg-success/20 text-success'
          }`}>
            {bot.mode}
          </span>
          {bot.mode === 'Live' && (
            bot.isConnected ? (
              <Wifi className="w-4 h-4 text-success" />
            ) : (
              <WifiOff className="w-4 h-4 text-error" />
            )
          )}
        </div>
      </td>

      {/* Runtime */}
      <td className="table-cell">
        <span className="font-mono text-text-secondary">{bot.runtime}</span>
      </td>

      {/* Daily PnL */}
      <td className="table-cell">
        <div className="font-mono font-medium">
          {formatPnl(bot.dailyPnl)}
        </div>
      </td>

      {/* Controls */}
      <td className="table-cell">
        <div className="flex items-center space-x-2">
          {bot.status === 'running' ? (
            <button
              onClick={() => onControl(bot.id, 'pause')}
              className="p-2 text-text-secondary hover:text-yellow-500 hover:bg-hover rounded-lg transition-colors"
              title="Pause"
            >
              <Pause className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => onControl(bot.id, 'start')}
              className="p-2 text-text-secondary hover:text-success hover:bg-hover rounded-lg transition-colors"
              title="Start"
            >
              <Play className="w-4 h-4" />
            </button>
          )}
          
          <button
            onClick={() => onEdit(bot.id)}
            className="p-2 text-text-secondary hover:text-primary hover:bg-hover rounded-lg transition-colors"
            title="Edit"
          >
            <Edit className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => onControl(bot.id, 'stop')}
            className="p-2 text-text-secondary hover:text-error hover:bg-hover rounded-lg transition-colors"
            title="Stop"
          >
            <Square className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => onDelete(bot.id)}
            className="p-2 text-text-secondary hover:text-error hover:bg-hover rounded-lg transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </td>
    </tr>
  )
}