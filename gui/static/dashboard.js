// React Dashboard for Trading Bot Management
const { useState, useEffect, useCallback } = React;

// API Base URL - adjust for your server
const API_BASE = window.location.origin + '/api';

// WebSocket connection for real-time updates
let ws = null;

// Predefined popular assets for dropdown
const POPULAR_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 
    'AMD', 'INTC', 'CRM', 'ADBE', 'PYPL', 'ORCL', 'IBM', 'CSCO',
    'DIS', 'V', 'MA', 'JPM', 'BAC', 'WMT', 'PG', 'JNJ', 'UNH', 'HD'
];

const POPULAR_CRYPTO = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'XRP/USDT', 
    'SOL/USDT', 'DOT/USDT', 'DOGE/USDT', 'AVAX/USDT', 'MATIC/USDT',
    'ATOM/USDT', 'LINK/USDT', 'UNI/USDT', 'ALGO/USDT', 'VET/USDT'
];

const PRECIOUS_METALS = ['GLD', 'SLV', 'GOLD', 'SILVER', 'PALL', 'PPLT'];

// Main Dashboard Component
function TradingBotDashboard() {
    const [bots, setBots] = useState([]);
    const [summary, setSummary] = useState({});
    const [selectedBot, setSelectedBot] = useState(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [recentActivity, setRecentActivity] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [refreshSettings, setRefreshSettings] = useState({
        interval: 30000, // 30 seconds default
        isPaused: false
    });
    const [tradingAccounts, setTradingAccounts] = useState({});

    // Initialize WebSocket connection
    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        ws = new WebSocket(wsUrl);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'dashboard_update') {
                setSummary(data.data);
            }
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setTimeout(() => {
                window.location.reload();
            }, 5000);
        };
        
        return () => {
            if (ws) ws.close();
        };
    }, []);

    // Load initial data
    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            
            const [botsResponse, summaryResponse, activityResponse] = await Promise.all([
                fetch(`${API_BASE}/bots`),
                fetch(`${API_BASE}/dashboard/summary`),
                fetch(`${API_BASE}/dashboard/recent-activity`)
            ]);
            
            const botsData = await botsResponse.json();
            const summaryData = await summaryResponse.json();
            const activityData = await activityResponse.json();
            
            setBots(botsData);
            setSummary(summaryData);
            setRecentActivity(activityData);
            setError(null);
            
        } catch (err) {
            console.error('Failed to load data:', err);
            setError('Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    }, []);

    // Fixed refresh logic with proper pause functionality and Manual Only support
    useEffect(() => {
        loadData();
        
        if (!refreshSettings.isPaused && refreshSettings.interval > 0) {
            const intervalId = setInterval(loadData, refreshSettings.interval);
            return () => clearInterval(intervalId);
        }
    }, [refreshSettings.isPaused, refreshSettings.interval]);

    const toggleRefresh = () => {
        setRefreshSettings(prev => ({
            ...prev,
            isPaused: !prev.isPaused
        }));
    };

    const changeRefreshInterval = (newInterval) => {
        setRefreshSettings(prev => ({
            ...prev,
            interval: newInterval
        }));
    };

    // Bot control functions
    const startBot = async (botId, dryRun = true) => {
        try {
            const response = await fetch(`${API_BASE}/bots/${botId}/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: 'live', dry_run: dryRun })
            });
            
            if (response.ok) {
                loadData();
            } else {
                const error = await response.json();
                alert(`Failed to start bot: ${error.detail}`);
            }
        } catch (err) {
            alert(`Failed to start bot: ${err.message}`);
        }
    };

    const stopBot = async (botId) => {
        try {
            const response = await fetch(`${API_BASE}/bots/${botId}/stop`, {
                method: 'POST'
            });
            
            if (response.ok) {
                loadData();
            } else {
                const error = await response.json();
                alert(`Failed to stop bot: ${error.detail}`);
            }
        } catch (err) {
            alert(`Failed to stop bot: ${err.message}`);
        }
    };

    const deleteBot = async (botId) => {
        if (!confirm('Are you sure you want to delete this bot?')) return;
        
        try {
            const response = await fetch(`${API_BASE}/bots/${botId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                loadData();
            } else {
                const error = await response.json();
                alert(`Failed to delete bot: ${error.detail}`);
            }
        } catch (err) {
            alert(`Failed to delete bot: ${err.message}`);
        }
    };

    const exportResults = async (botId, format) => {
        try {
            const response = await fetch(`${API_BASE}/bots/${botId}/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format })
            });
            
            if (response.ok) {
                alert(`Export started for ${format.toUpperCase()} format`);
            } else {
                const error = await response.json();
                alert(`Failed to export: ${error.detail}`);
            }
        } catch (err) {
            alert(`Failed to export: ${err.message}`);
        }
    };

    if (loading) {
        return (
            <div className="d-flex justify-content-center mt-5">
                <div className="spinner-border" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="alert alert-danger m-3" role="alert">
                {error}
                <button className="btn btn-link" onClick={loadData}>Retry</button>
            </div>
        );
    }

    return (
        <div className="container-fluid">
            <Header summary={summary} />
            
            <div className="row mb-3">
                <div className="col-12">
                    <ControlPanel
                        refreshSettings={refreshSettings}
                        onToggleRefresh={toggleRefresh}
                        onChangeInterval={changeRefreshInterval}
                        onShowLogin={() => setShowLoginModal(true)}
                        onRefresh={loadData}
                        tradingAccounts={tradingAccounts}
                    />
                </div>
            </div>
            
            <div className="row">
                <div className="col-md-8">
                    <BotsList 
                        bots={bots}
                        onStart={startBot}
                        onStop={stopBot}
                        onDelete={deleteBot}
                        onExport={exportResults}
                        onSelect={setSelectedBot}
                    />
                </div>
                <div className="col-md-4">
                    <RecentActivity activity={recentActivity} />
                </div>
            </div>
            
            <div className="row mt-4">
                <div className="col-12">
                    <QuickActions 
                        onCreateBot={() => setShowCreateModal(true)}
                        onRefresh={loadData}
                    />
                </div>
            </div>
            
            {showCreateModal && (
                <CreateBotModal 
                    onClose={() => setShowCreateModal(false)}
                    onCreated={loadData}
                />
            )}
            
            {showLoginModal && (
                <TradingAccountModal
                    onClose={() => setShowLoginModal(false)}
                    onSave={(accounts) => {
                        setTradingAccounts(accounts);
                        setShowLoginModal(false);
                    }}
                    currentAccounts={tradingAccounts}
                />
            )}
            
            {selectedBot && (
                <BotDetailsModal
                    bot={selectedBot}
                    onClose={() => setSelectedBot(null)}
                />
            )}
        </div>
    );
}

// Header component
function Header({ summary }) {
    return (
        <div className="row mb-4 mt-3">
            <div className="col-12">
                <h1 className="h2">🕌 Halal Trading Bot Dashboard</h1>
                <div className="row">
                    <div className="col-md-2">
                        <div className="card bg-primary text-white">
                            <div className="card-body">
                                <h5 className="card-title">Total Bots</h5>
                                <h3>{summary.total_bots || 0}</h3>
                            </div>
                        </div>
                    </div>
                    <div className="col-md-2">
                        <div className="card bg-success text-white">
                            <div className="card-body">
                                <h5 className="card-title">Running</h5>
                                <h3>{summary.running_bots || 0}</h3>
                            </div>
                        </div>
                    </div>
                    <div className="col-md-2">
                        <div className="card bg-info text-white">
                            <div className="card-body">
                                <h5 className="card-title">Total Equity</h5>
                                <h4>${(summary.total_equity || 0).toLocaleString()}</h4>
                            </div>
                        </div>
                    </div>
                    <div className="col-md-2">
                        <div className="card bg-warning text-dark">
                            <div className="card-body">
                                <h5 className="card-title">Overall Return</h5>
                                <h4>{((summary.overall_return || 0) * 100).toFixed(1)}%</h4>
                            </div>
                        </div>
                    </div>
                    <div className="col-md-2">
                        <div className="card bg-secondary text-white">
                            <div className="card-body">
                                <h5 className="card-title">Total Trades</h5>
                                <h4>{summary.total_trades || 0}</h4>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Control Panel with fixed refresh logic
function ControlPanel({ refreshSettings, onToggleRefresh, onChangeInterval, onShowLogin, onRefresh, tradingAccounts }) {
    const connectedAccounts = Object.keys(tradingAccounts).filter(key => tradingAccounts[key].connected).length;

    return (
        <div className="card">
            <div className="card-body">
                <div className="row align-items-center">
                    <div className="col-md-4">
                        <h6>Refresh Settings</h6>
                        <div className="btn-group">
                            <button 
                                className={`btn ${refreshSettings.isPaused ? 'btn-warning' : 'btn-success'} btn-sm`}
                                onClick={onToggleRefresh}
                            >
                                {refreshSettings.isPaused ? '▶️ Resume' : '⏸️ Pause'} Refresh
                            </button>
                            <button className="btn btn-outline-secondary btn-sm" onClick={onRefresh}>
                                🔄 Manual Refresh
                            </button>
                        </div>
                        <div className="mt-2">
                            <label className="form-label small">Interval:</label>
                            <select 
                                className="form-select form-select-sm"
                                value={refreshSettings.interval}
                                onChange={(e) => onChangeInterval(Number(e.target.value))}
                            >
                                <option value={5000}>5 seconds</option>
                                <option value={10000}>10 seconds</option>
                                <option value={30000}>30 seconds</option>
                                <option value={60000}>1 minute</option>
                                <option value={300000}>5 minutes</option>
                                <option value={0}>Manual only</option>
                            </select>
                        </div>
                    </div>
                    <div className="col-md-4">
                        <h6>Trading Accounts</h6>
                        <div className="d-flex align-items-center">
                            <span className="badge bg-info me-2">{connectedAccounts} Connected</span>
                            <button className="btn btn-outline-primary btn-sm" onClick={onShowLogin}>
                                🔐 Manage Accounts
                            </button>
                        </div>
                    </div>
                    <div className="col-md-4">
                        <div className="small text-muted">
                            <div>Status: {refreshSettings.isPaused ? '⏸️ Paused' : '🟢 Active'}</div>
                            <div>Next refresh: {refreshSettings.isPaused ? 'Manual' : refreshSettings.interval === 0 ? 'Manual' : `${refreshSettings.interval/1000}s`}</div>
                            <div>Last updated: {new Date().toLocaleTimeString()}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Simplified components
function BotsList({ bots, onStart, onStop, onDelete, onSelect }) {
    return (
        <div className="card">
            <div className="card-header">
                <h5>Bot Instances</h5>
            </div>
            <div className="card-body">
                {bots.length === 0 ? (
                    <p className="text-muted">No bots created yet. Create your first bot to get started.</p>
                ) : (
                    <div className="table-responsive">
                        <table className="table table-hover">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {bots.map(bot => (
                                    <tr key={bot.id}>
                                        <td>{bot.name}</td>
                                        <td><span className="badge bg-secondary">STOPPED</span></td>
                                        <td>
                                            <button className="btn btn-success btn-sm me-1" onClick={() => onStart(bot.id)}>
                                                Start
                                            </button>
                                            <button className="btn btn-danger btn-sm" onClick={() => onDelete(bot.id)}>
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

function RecentActivity({ activity }) {
    return (
        <div className="card">
            <div className="card-header">
                <h5>Recent Activity</h5>
            </div>
            <div className="card-body">
                <p className="text-muted">No recent activity</p>
            </div>
        </div>
    );
}

function QuickActions({ onCreateBot, onRefresh }) {
    return (
        <div className="card">
            <div className="card-body">
                <h5>Quick Actions</h5>
                <div className="btn-group">
                    <button className="btn btn-primary" onClick={onCreateBot}>
                        Create New Bot
                    </button>
                    <button className="btn btn-outline-secondary" onClick={onRefresh}>
                        Refresh Data
                    </button>
                </div>
            </div>
        </div>
    );
}

function TradingAccountModal({ onClose, onSave }) {
    return (
        <div className="modal show d-block" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
            <div className="modal-dialog">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">Trading Account Management</h5>
                        <button type="button" className="btn-close" onClick={onClose}></button>
                    </div>
                    <div className="modal-body">
                        <p>Account management coming soon...</p>
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-secondary" onClick={onClose}>
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function CreateBotModal({ onClose, onCreated }) {
    const [name, setName] = useState('');
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        if (name) {
            onCreated();
            onClose();
        }
    };

    return (
        <div className="modal show d-block" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
            <div className="modal-dialog">
                <div className="modal-content">
                    <form onSubmit={handleSubmit}>
                        <div className="modal-header">
                            <h5 className="modal-title">Create New Trading Bot</h5>
                            <button type="button" className="btn-close" onClick={onClose}></button>
                        </div>
                        <div className="modal-body">
                            <div className="mb-3">
                                <label className="form-label">Bot Name</label>
                                <input 
                                    type="text" 
                                    className="form-control"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button type="button" className="btn btn-secondary" onClick={onClose}>
                                Cancel
                            </button>
                            <button type="submit" className="btn btn-primary">
                                Create Bot
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}

function BotDetailsModal({ bot, onClose }) {
    return (
        <div className="modal show d-block" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
            <div className="modal-dialog">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">Bot Details: {bot.name}</h5>
                        <button type="button" className="btn-close" onClick={onClose}></button>
                    </div>
                    <div className="modal-body">
                        <p>Bot details coming soon...</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Render the main component
ReactDOM.render(<TradingBotDashboard />, document.getElementById('root'));