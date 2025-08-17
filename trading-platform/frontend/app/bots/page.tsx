'use client'

import { useState } from 'react'
import Navbar from '@/components/Layout/Navbar'
import BotTable from '@/components/BotTable/BotTable'
import BotCreator from '@/components/BotCreator/BotCreator'
import { mockData } from '@/lib/api-client'
import { Bot, BotConfig } from '@/lib/types'

export default function BotsPage() {
  const [bots, setBots] = useState<Bot[]>(mockData.bots)
  const [isBotCreatorOpen, setIsBotCreatorOpen] = useState(false)

  const handleControlBot = async (botId: string, action: 'start' | 'pause' | 'stop') => {
    setBots(prev => prev.map(bot => 
      bot.id === botId 
        ? { ...bot, status: action === 'start' ? 'running' : action === 'pause' ? 'paused' : 'stopped' }
        : bot
    ))
  }

  const handleEditBot = (botId: string) => {
    console.log(`Edit bot ${botId}`)
  }

  const handleDeleteBot = (botId: string) => {
    setBots(prev => prev.filter(bot => bot.id !== botId))
  }

  const handleCreateBot = async (config: BotConfig) => {    const newBot: Bot = {
      id: `bot-${Date.now()}`,
      name: config.name,
      type: config.assetType.toLowerCase() as 'solana' | 'stock',
      market: config.market,
      strategy: config.strategy,
      mode: config.paperTrading ? 'paper' : 'live',
      status: 'running',
      runtime: '0m',
      dailyPnl: 0,
      dailyPnlPercent: 0,
    }
    setBots(prev => [...prev, newBot])
    setIsBotCreatorOpen(false)
  }

  return (
    <>
      <Navbar onNewBot={() => setIsBotCreatorOpen(true)} />
      <div className="min-h-screen bg-background p-6 pt-20">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-text-primary mb-8">Bot Management</h1>
          
          <BotTable
            bots={bots}
            onControlBot={handleControlBot}
            onEditBot={handleEditBot}
            onDeleteBot={handleDeleteBot}
            onAddBot={() => setIsBotCreatorOpen(true)}
          />

          <BotCreator
            isOpen={isBotCreatorOpen}
            onClose={() => setIsBotCreatorOpen(false)}
            onCreateBot={handleCreateBot}
          />
        </div>
      </div>
    </>
  )
}