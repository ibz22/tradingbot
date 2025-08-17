'use client'

import { useState } from 'react'
import { Bot } from '@/lib/types'
import BotTableHeader from './BotTableHeader'
import BotTableRow from './BotTableRow'

interface BotTableProps {
  bots: Bot[]
  onControlBot: (botId: string, action: 'start' | 'pause' | 'stop') => void
  onEditBot: (botId: string) => void
  onDeleteBot: (botId: string) => void
  onAddBot?: () => void
}

export default function BotTable({ bots, onControlBot, onEditBot, onDeleteBot, onAddBot }: BotTableProps) {
  const [filter, setFilter] = useState<'all' | 'solana' | 'stocks' | 'paper' | 'api'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const filteredBots = bots.filter(bot => {
    // Apply filter
    let matchesFilter = true
    switch (filter) {
      case 'solana':
        matchesFilter = bot.type === 'Solana'
        break
      case 'stocks':
        matchesFilter = bot.type === 'Stock'
        break
      case 'paper':
        matchesFilter = bot.mode === 'Paper'
        break
      case 'api':
        matchesFilter = bot.isConnected
        break
    }

    // Apply search
    const matchesSearch = searchQuery === '' || 
      bot.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      bot.market.toLowerCase().includes(searchQuery.toLowerCase()) ||
      bot.strategy.toLowerCase().includes(searchQuery.toLowerCase())

    return matchesFilter && matchesSearch
  })

  return (
    <div className="card">
      <BotTableHeader 
        filter={filter}
        onFilterChange={setFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        botCount={filteredBots.length}
        onAddBot={onAddBot}
      />

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="table-cell text-left font-medium text-text-secondary">BOT</th>
              <th className="table-cell text-left font-medium text-text-secondary">TYPE</th>
              <th className="table-cell text-left font-medium text-text-secondary">MARKET</th>
              <th className="table-cell text-left font-medium text-text-secondary">MODE</th>
              <th className="table-cell text-left font-medium text-text-secondary">RUNTIME</th>
              <th className="table-cell text-left font-medium text-text-secondary">DAILY PNL</th>
              <th className="table-cell text-left font-medium text-text-secondary">CONTROLS</th>
            </tr>
          </thead>
          <tbody>
            {filteredBots.map((bot) => (
              <BotTableRow 
                key={bot.id} 
                bot={bot}
                onControl={onControlBot}
                onEdit={onEditBot}
                onDelete={onDeleteBot}
              />
            ))}
            {filteredBots.length === 0 && (
              <tr>
                <td colSpan={7} className="table-cell text-center text-text-secondary py-8">
                  No bots found matching your criteria
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}