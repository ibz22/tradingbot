'use client'

import { useState } from 'react'
import Navbar from '@/components/Layout/Navbar'
import BotCreator from '@/components/BotCreator/BotCreator'
import { Download, Calendar, TrendingUp, DollarSign } from 'lucide-react'
import { BotConfig } from '@/lib/types'

export default function ReportsPage() {
  const [isBotCreatorOpen, setIsBotCreatorOpen] = useState(false)

  const handleCreateBot = async (config: BotConfig) => {
    console.log('Creating bot from Reports page:', config)
    setIsBotCreatorOpen(false)
  }

  const generateCSVReport = (type: 'monthly' | 'annual' | 'trades') => {
    // Generate sample report data
    const date = new Date()
    let csvContent = ''
    let filename = ''

    if (type === 'monthly') {
      filename = `monthly-report-${date.toISOString().slice(0, 7)}.csv`
      csvContent = `Monthly Trading Report - ${date.toLocaleDateString()}\n\n`
      csvContent += 'Date,Bot Name,Type,Market,PnL,Status\n'
      csvContent += '2024-11-01,SOL Momentum Bot,Solana,SOL/USDC,+325.37,Success\n'
      csvContent += '2024-11-02,AAPL MeanRevert,Stock,AAPL,+80.87,Success\n'
      csvContent += '2024-11-03,SOL Grid Bot,Solana,BONK/USDC,-42.10,Loss\n'
      csvContent += '\nTotal PnL:,+364.14\n'
      csvContent += 'Win Rate:,66.7%\n'
      csvContent += 'Total Trades:,3\n'
    } else if (type === 'annual') {
      filename = `annual-report-${date.getFullYear()}.csv`
      csvContent = `Annual Trading Report - ${date.getFullYear()}\n\n`
      csvContent += 'Month,Total Trades,Win Rate,Total PnL\n'
      csvContent += 'January,142,58%,+2843.50\n'
      csvContent += 'February,189,62%,+3921.23\n'
      csvContent += 'March,201,55%,+1502.87\n'
      csvContent += 'April,167,59%,+2234.91\n'
      csvContent += 'May,194,61%,+3102.45\n'
      csvContent += 'June,178,57%,+1876.32\n'
      csvContent += 'July,203,63%,+4123.78\n'
      csvContent += 'August,186,56%,+1654.21\n'
      csvContent += 'September,171,60%,+2987.44\n'
      csvContent += 'October,195,58%,+2341.90\n'
      csvContent += 'November,156,64%,+3876.52\n'
      csvContent += '\nTotal Annual PnL:,+30465.13\n'
      csvContent += 'Average Win Rate:,59.4%\n'
      csvContent += 'Total Trades:,1982\n'
    } else {
      filename = `trade-history-${date.toISOString().slice(0, 10)}.csv`
      csvContent = 'Trade History Export\n\n'
      csvContent += 'Timestamp,Bot,Type,Market,Side,Quantity,Price,PnL,Status\n'
      csvContent += '2024-11-15 14:23:01,SOL Momentum,Solana,SOL/USDC,BUY,2.5,198.50,0,Open\n'
      csvContent += '2024-11-15 14:45:23,SOL Momentum,Solana,SOL/USDC,SELL,2.5,203.20,+11.75,Closed\n'
      csvContent += '2024-11-15 15:12:45,AAPL MeanRevert,Stock,AAPL,BUY,10,241.50,0,Open\n'
      csvContent += '2024-11-15 15:58:12,AAPL MeanRevert,Stock,AAPL,SELL,10,242.84,+13.40,Closed\n'
      csvContent += '2024-11-15 16:23:34,SOL Grid Bot,Solana,BONK/USDC,BUY,1000000,0.000042,0,Open\n'
      csvContent += '2024-11-15 16:45:56,SOL Grid Bot,Solana,BONK/USDC,SELL,1000000,0.000045,+3.00,Closed\n'
    }

    // Create and download the CSV file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <>
      <Navbar onNewBot={() => setIsBotCreatorOpen(true)} />
      <div className="min-h-screen bg-background p-6 pt-20">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-text-primary mb-8">Performance Reports</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-text-secondary">Total PnL</span>
                <DollarSign className="w-5 h-5 text-primary" />
              </div>
              <div className="text-2xl font-bold text-success">+$12,450.23</div>
              <div className="text-sm text-text-secondary">+18.4% all time</div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-text-secondary">Win Rate</span>
                <TrendingUp className="w-5 h-5 text-primary" />
              </div>
              <div className="text-2xl font-bold text-text-primary">58%</div>
              <div className="text-sm text-text-secondary">Last 200 trades</div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-text-secondary">Best Month</span>
                <Calendar className="w-5 h-5 text-primary" />
              </div>
              <div className="text-2xl font-bold text-success">+$4,823</div>
              <div className="text-sm text-text-secondary">October 2024</div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-text-secondary">Active Days</span>
                <Calendar className="w-5 h-5 text-primary" />
              </div>
              <div className="text-2xl font-bold text-text-primary">142</div>
              <div className="text-sm text-text-secondary">Since Jan 2024</div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-xl font-semibold text-text-primary mb-4">Export Reports</h2>
            <p className="text-text-secondary mb-6">Generate and download detailed performance reports for tax purposes or analysis.</p>
            
            <div className="space-y-4">
              <button 
                onClick={() => generateCSVReport('monthly')}
                className="btn-secondary flex items-center space-x-2 w-full sm:w-auto hover:bg-gray-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Export Monthly Report</span>
              </button>
              <button 
                onClick={() => generateCSVReport('annual')}
                className="btn-secondary flex items-center space-x-2 w-full sm:w-auto hover:bg-gray-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Export Annual Report</span>
              </button>
              <button 
                onClick={() => generateCSVReport('trades')}
                className="btn-secondary flex items-center space-x-2 w-full sm:w-auto hover:bg-gray-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Export Trade History</span>
              </button>
            </div>
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