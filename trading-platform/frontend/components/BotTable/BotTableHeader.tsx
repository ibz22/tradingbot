import { Search, Plus } from 'lucide-react'

interface BotTableHeaderProps {
  filter: 'all' | 'solana' | 'stocks' | 'paper' | 'api'
  onFilterChange: (filter: 'all' | 'solana' | 'stocks' | 'paper' | 'api') => void
  searchQuery: string
  onSearchChange: (query: string) => void
  botCount: number
  onAddBot?: () => void
}

export default function BotTableHeader({ 
  filter, 
  onFilterChange, 
  searchQuery, 
  onSearchChange,
  botCount,
  onAddBot 
}: BotTableHeaderProps) {
  const filters = [
    { key: 'all' as const, label: 'All', count: botCount },
    { key: 'solana' as const, label: 'Solana Bots' },
    { key: 'stocks' as const, label: 'Stocks' },
    { key: 'paper' as const, label: 'Paper Trading' },
    { key: 'api' as const, label: 'API Connected' }
  ]

  return (
    <div className="mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
        {/* Filter Buttons */}
        <div className="flex flex-wrap gap-2">
          {filters.map((filterItem) => (
            <button
              key={filterItem.key}
              onClick={() => onFilterChange(filterItem.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === filterItem.key
                  ? 'bg-primary text-white'
                  : 'bg-background text-text-secondary hover:bg-hover hover:text-text-primary'
              }`}
            >
              {filterItem.label}
              {filterItem.count !== undefined && (
                <span className="ml-2 px-2 py-0.5 bg-card rounded text-xs">
                  {filterItem.count}
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-text-secondary" />
            <input
              type="text"
              placeholder="Search bots..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="input pl-10 pr-4 w-64"
            />
          </div>

          {/* Add Bot Button */}
          <button onClick={onAddBot} className="btn-primary flex items-center space-x-2 hover:bg-primary-dark transition-colors">
            <Plus className="w-4 h-4" />
            <span>Add Bot</span>
          </button>
        </div>
      </div>
    </div>
  )
}