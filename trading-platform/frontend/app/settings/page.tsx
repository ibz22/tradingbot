'use client'

import { useState } from 'react'
import Navbar from '@/components/Layout/Navbar'
import BotCreator from '@/components/BotCreator/BotCreator'
import { Save, Key, Bell, Shield, Database, Zap } from 'lucide-react'
import { BotConfig } from '@/lib/types'

export default function SettingsPage() {
  const [isBotCreatorOpen, setIsBotCreatorOpen] = useState(false)
  const [settings, setSettings] = useState({
    alpacaKey: '',
    alpacaSecret: '',
    solanaRpc: 'https://api.mainnet-beta.solana.com',
    slippage: 1,
    gasPrice: 'medium',
    notifications: true,
    autoRestart: false,
    paperTrading: true,
  })

  const handleSave = () => {
    console.log('Saving settings:', settings)
    alert('Settings saved successfully!')
  }

  const handleCreateBot = async (config: BotConfig) => {
    console.log('Creating bot from Settings page:', config)
    setIsBotCreatorOpen(false)
  }

  return (
    <>
      <Navbar onNewBot={() => setIsBotCreatorOpen(true)} />
      <div className="min-h-screen bg-background p-6 pt-20">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-text-primary mb-8">Settings</h1>
          
          <div className="space-y-6">
            {/* API Keys */}
            <div className="card">
              <h2 className="text-xl font-semibold text-text-primary mb-4 flex items-center">
                <Key className="w-5 h-5 mr-2 text-primary" />
                API Configuration
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Alpaca API Key
                  </label>
                  <input
                    type="password"
                    value={settings.alpacaKey}
                    onChange={(e) => setSettings({...settings, alpacaKey: e.target.value})}
                    className="input w-full"
                    placeholder="Enter your Alpaca API key"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Alpaca Secret Key
                  </label>
                  <input
                    type="password"
                    value={settings.alpacaSecret}
                    onChange={(e) => setSettings({...settings, alpacaSecret: e.target.value})}
                    className="input w-full"
                    placeholder="Enter your Alpaca secret key"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Solana RPC URL
                  </label>
                  <input
                    type="text"
                    value={settings.solanaRpc}
                    onChange={(e) => setSettings({...settings, solanaRpc: e.target.value})}
                    className="input w-full"
                  />
                </div>
              </div>
            </div>

            {/* Trading Settings */}
            <div className="card">
              <h2 className="text-xl font-semibold text-text-primary mb-4 flex items-center">
                <Zap className="w-5 h-5 mr-2 text-primary" />
                Trading Preferences
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Slippage Tolerance (%)
                  </label>
                  <input
                    type="number"
                    value={settings.slippage}
                    onChange={(e) => setSettings({...settings, slippage: parseFloat(e.target.value)})}
                    className="input w-full"
                    min="0.1"
                    max="5"
                    step="0.1"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-text-primary font-medium">Paper Trading Mode</div>
                    <div className="text-sm text-text-secondary">Trade with virtual funds</div>
                  </div>
                  <button
                    onClick={() => setSettings({...settings, paperTrading: !settings.paperTrading})}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.paperTrading ? 'bg-primary' : 'bg-gray-600'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.paperTrading ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-text-primary font-medium">Auto-Restart Failed Bots</div>
                    <div className="text-sm text-text-secondary">Automatically restart bots that stop</div>
                  </div>
                  <button
                    onClick={() => setSettings({...settings, autoRestart: !settings.autoRestart})}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.autoRestart ? 'bg-primary' : 'bg-gray-600'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.autoRestart ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>
              </div>
            </div>

            {/* Save Button */}
            <button onClick={handleSave} className="btn-primary flex items-center space-x-2">
              <Save className="w-4 h-4" />
              <span>Save Settings</span>
            </button>
          </div>
        </div>
      </div>
      
      {/* Bot Creator Modal */}
      <BotCreator
        isOpen={isBotCreatorOpen}
        onClose={() => setIsBotCreatorOpen(false)}
        onCreateBot={handleCreateBot}
      />
    </>
  )
}