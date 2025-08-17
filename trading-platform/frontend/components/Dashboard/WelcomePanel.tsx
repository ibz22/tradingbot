import { Play, Upload } from 'lucide-react'

interface WelcomePanelProps {
  onStartSolanaBot?: () => void
  onImportConfig?: () => void
}

export default function WelcomePanel({ onStartSolanaBot, onImportConfig }: WelcomePanelProps) {
  const handleStartSolanaBot = () => {
    if (onStartSolanaBot) {
      onStartSolanaBot()
    } else {
      console.log('Starting Solana bot...')
    }
  }

  const handleImportConfig = () => {
    if (onImportConfig) {
      onImportConfig()
    } else {
      // Create a file input and trigger it
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.json,.yaml,.yml'
      input.onchange = (e) => {
        const file = (e.target as HTMLInputElement).files?.[0]
        if (file) {
          const reader = new FileReader()
          reader.onload = (event) => {
            console.log('Config file loaded:', event.target?.result)
            // Here you would parse and import the config
            alert(`Config file "${file.name}" loaded! This would import your bot configuration.`)
          }
          reader.readAsText(file)
        }
      }
      input.click()
    }
  }

  return (
    <div className="card">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-text-primary mb-2">
          Welcome back
        </h2>
        <h1 className="text-4xl font-bold text-text-primary mb-4">
          Trade smarter on Solana and Stocks
        </h1>
        <p className="text-text-secondary text-lg leading-relaxed">
          Run multiple bots in parallel across Solana pairs and equities. 
          Paper trade or connect an API. Export performance anytime.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <button 
          onClick={handleStartSolanaBot}
          className="btn-primary flex items-center justify-center space-x-2 px-6 py-3 text-base hover:bg-primary-dark transition-colors"
        >
          <Play className="w-5 h-5" />
          <span>Start Solana Bot</span>
        </button>
        
        <button 
          onClick={handleImportConfig}
          className="btn-secondary flex items-center justify-center space-x-2 px-6 py-3 text-base hover:bg-gray-700 transition-colors"
        >
          <Upload className="w-5 h-5" />
          <span>Import Config</span>
        </button>
      </div>
    </div>
  )
}
