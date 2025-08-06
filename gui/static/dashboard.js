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
            // Attempt to reconnect after 5 seconds
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

    // Configurable refresh with pause functionality
    useEffect(() => {
        loadData();
        
        if (!refreshSettings.isPaused) {
            const interval = setInterval(loadData, refreshSettings.interval);
            return () => clearInterval(interval);
        }
    }, [loadData, refreshSettings]);

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
                loadData(); // Refresh data
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
                loadData(); // Refresh data
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
                loadData(); // Refresh data
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
            
            {/* Control Panel */}
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

// Header component with summary stats
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

// Bots list component
function BotsList({ bots, onStart, onStop, onDelete, onExport, onSelect }) {
    const getStatusBadge = (status) => {
        const statusClasses = {
            running: 'bg-success',
            stopped: 'bg-secondary',
            starting: 'bg-warning',
            stopping: 'bg-warning', 
            error: 'bg-danger',
            backtesting: 'bg-info'
        };
        
        return (
            <span className={`badge ${statusClasses[status] || 'bg-secondary'}`}>
                {status.toUpperCase()}
            </span>
        );
    };

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
                                    <th>Equity</th>
                                    <th>Return</th>
                                    <th>Trades</th>
                                    <th>Win Rate</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {bots.map(bot => (
                                    <tr key={bot.id}>
                                        <td>
                                            <button 
                                                className="btn btn-link p-0 text-start"
                                                onClick={() => onSelect(bot)}
                                            >
                                                {bot.name}
                                            </button>
                                        </td>
                                        <td>{getStatusBadge(bot.status)}</td>
                                        <td>${bot.current_equity.toLocaleString()}</td>
                                        <td className={bot.total_return >= 0 ? 'text-success' : 'text-danger'}>
                                            {(bot.total_return * 100).toFixed(2)}%
                                        </td>
                                        <td>{bot.total_trades}</td>
                                        <td>{(bot.win_rate * 100).toFixed(1)}%</td>
                                        <td>
                                            <div className="btn-group btn-group-sm">
                                                {bot.status === 'stopped' ? (
                                                    <>
                                                        <button 
                                                            className="btn btn-success btn-sm"
                                                            onClick={() => onStart(bot.id, true)}
                                                        >
                                                            Start (Dry)
                                                        </button>
                                                        <button 
                                                            className="btn btn-warning btn-sm"
                                                            onClick={() => onStart(bot.id, false)}
                                                        >
                                                            Start (Live)
                                                        </button>
                                                    </>
                                                ) : (
                                                    <button 
                                                        className="btn btn-danger btn-sm"
                                                        onClick={() => onStop(bot.id)}
                                                    >
                                                        Stop
                                                    </button>
                                                )}
                                                <div className="dropdown">
                                                    <button 
                                                        className="btn btn-outline-secondary btn-sm dropdown-toggle"
                                                        type="button"
                                                        data-bs-toggle="dropdown"
                                                    >
                                                        Export
                                                    </button>
                                                    <ul className="dropdown-menu">
                                                        <li>
                                                            <button 
                                                                className="dropdown-item"
                                                                onClick={() => onExport(bot.id, 'csv')}
                                                            >
                                                                Export CSV
                                                            </button>
                                                        </li>
                                                        <li>
                                                            <button 
                                                                className="dropdown-item"
                                                                onClick={() => onExport(bot.id, 'google_sheets')}
                                                            >
                                                                Export to Google Sheets
                                                            </button>
                                                        </li>
                                                    </ul>
                                                </div>
                                                <button 
                                                    className="btn btn-outline-danger btn-sm"
                                                    onClick={() => onDelete(bot.id)}
                                                >
                                                    Delete
                                                </button>
                                            </div>
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

// Recent activity component
function RecentActivity({ activity }) {
    return (
        <div className="card">
            <div className="card-header">
                <h5>Recent Activity</h5>
            </div>
            <div className="card-body">
                {activity.length === 0 ? (
                    <p className="text-muted">No recent activity</p>
                ) : (
                    <div className="list-group list-group-flush">
                        {activity.slice(0, 10).map((item, index) => (
                            <div key={index} className="list-group-item border-0 px-0">
                                <div className="d-flex justify-content-between">
                                    <div>
                                        <strong>{item.bot_name}</strong>
                                        <span className={`badge ms-2 ${item.side === 'buy' ? 'bg-success' : 'bg-danger'}`}>
                                            {item.side.toUpperCase()}
                                        </span>
                                    </div>
                                    <small className="text-muted">
                                        {new Date(item.timestamp).toLocaleTimeString()}
                                    </small>
                                </div>
                                <div className="text-muted small">
                                    {item.symbol} - {item.quantity} @ ${item.price}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

// Quick actions component
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
                    <button 
                        className="btn btn-outline-info"
                        onClick={() => window.open(`${API_BASE}/export/summary?format=csv`, '_blank')}
                    >
                        Export All Results
                    </button>
                </div>
            </div>
        </div>
    );
}

// Control Panel Component with refresh settings and account management
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
                        {connectedAccounts > 0 && (
                            <div className="small text-muted mt-1">
                                {Object.keys(tradingAccounts)
                                    .filter(key => tradingAccounts[key].connected)
                                    .map(key => `${key.charAt(0).toUpperCase() + key.slice(1)}`)
                                    .join(', ')} ready
                            </div>
                        )}
                    </div>
                    <div className="col-md-4">
                        <div className="small text-muted">
                            <div>Status: {refreshSettings.isPaused ? '⏸️ Paused' : '🟢 Active'}</div>
                            <div>Next refresh: {refreshSettings.isPaused ? 'Manual' : `${refreshSettings.interval/1000}s`}</div>
                            <div>Last updated: {new Date().toLocaleTimeString()}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Trading Account Management Modal
function TradingAccountModal({ onClose, onSave, currentAccounts = {} }) {
    const [accounts, setAccounts] = useState({
        alpaca: {
            connected: false,
            apiKey: '',
            secretKey: '',
            paper: true,
            ...currentAccounts.alpaca
        },
        binance: {
            connected: false,
            apiKey: '',
            secretKey: '',
            testnet: true,
            ...currentAccounts.binance
        },
        coinbase: {
            connected: false,
            apiKey: '',
            secretKey: '',
            passphrase: '',
            sandbox: true,
            ...currentAccounts.coinbase
        }
    });

    const [activeTab, setActiveTab] = useState('alpaca');

    const handleAccountChange = (provider, field, value) => {
        setAccounts(prev => ({
            ...prev,
            [provider]: {
                ...prev[provider],
                [field]: value
            }
        }));
    };

    const toggleConnection = (provider) => {
        setAccounts(prev => ({
            ...prev,
            [provider]: {
                ...prev[provider],
                connected: !prev[provider].connected
            }
        }));
    };

    return (
        <div className="modal show d-block" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
            <div className="modal-dialog modal-lg">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">Trading Account Management</h5>
                        <button type="button" className="btn-close" onClick={onClose}></button>
                    </div>
                    <div className="modal-body">
                        <ul className="nav nav-tabs">
                            {['alpaca', 'binance', 'coinbase'].map(provider => (
                                <li key={provider} className="nav-item">
                                    <button 
                                        className={`nav-link ${activeTab === provider ? 'active' : ''}`}
                                        onClick={() => setActiveTab(provider)}
                                    >
                                        {provider.charAt(0).toUpperCase() + provider.slice(1)}
                                        {accounts[provider].connected && <span className="badge bg-success ms-1">✓</span>}
                                    </button>
                                </li>
                            ))}
                        </ul>
                        
                        <div className="tab-content mt-3">
                            {activeTab === 'alpaca' && (
                                <div>
                                    <div className="form-check mb-3">
                                        <input 
                                            className="form-check-input" 
                                            type="checkbox"
                                            checked={accounts.alpaca.connected}
                                            onChange={() => toggleConnection('alpaca')}
                                        />
                                        <label className="form-check-label">Enable Alpaca Trading</label>
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label">API Key</label>
                                        <input 
                                            type="text" 
                                            className="form-control"
                                            value={accounts.alpaca.apiKey}
                                            onChange={(e) => handleAccountChange('alpaca', 'apiKey', e.target.value)}
                                            disabled={!accounts.alpaca.connected}
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label">Secret Key</label>
                                        <input 
                                            type="password" 
                                            className="form-control"
                                            value={accounts.alpaca.secretKey}
                                            onChange={(e) => handleAccountChange('alpaca', 'secretKey', e.target.value)}
                                            disabled={!accounts.alpaca.connected}
                                        />
                                    </div>
                                    <div className="form-check">
                                        <input 
                                            className="form-check-input" 
                                            type="checkbox"
                                            checked={accounts.alpaca.paper}
                                            onChange={(e) => handleAccountChange('alpaca', 'paper', e.target.checked)}
                                            disabled={!accounts.alpaca.connected}
                                        />
                                        <label className="form-check-label">Paper Trading (Recommended)</label>
                                    </div>
                                </div>
                            )}
                            
                            {activeTab === 'binance' && (
                                <div>
                                    <div className="form-check mb-3">
                                        <input 
                                            className="form-check-input" 
                                            type="checkbox"
                                            checked={accounts.binance.connected}
                                            onChange={() => toggleConnection('binance')}
                                        />
                                        <label className="form-check-label">Enable Binance Trading</label>
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label">API Key</label>
                                        <input 
                                            type="text" 
                                            className="form-control"
                                            value={accounts.binance.apiKey}
                                            onChange={(e) => handleAccountChange('binance', 'apiKey', e.target.value)}
                                            disabled={!accounts.binance.connected}
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label">Secret Key</label>
                                        <input 
                                            type="password" 
                                            className="form-control"
                                            value={accounts.binance.secretKey}
                                            onChange={(e) => handleAccountChange('binance', 'secretKey', e.target.value)}
                                            disabled={!accounts.binance.connected}
                                        />
                                    </div>
                                    <div className="form-check">
                                        <input 
                                            className="form-check-input" 
                                            type="checkbox"
                                            checked={accounts.binance.testnet}
                                            onChange={(e) => handleAccountChange('binance', 'testnet', e.target.checked)}
                                            disabled={!accounts.binance.connected}
                                        />
                                        <label className="form-check-label">Testnet (Recommended)</label>
                                    </div>
                                </div>
                            )}
                            
                            {activeTab === 'coinbase' && (
                                <div>
                                    <div className="form-check mb-3">
                                        <input 
                                            className="form-check-input" 
                                            type="checkbox"
                                            checked={accounts.coinbase.connected}
                                            onChange={() => toggleConnection('coinbase')}
                                        />
                                        <label className="form-check-label">Enable Coinbase Pro Trading</label>
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label">API Key</label>
                                        <input 
                                            type="text" 
                                            className="form-control"
                                            value={accounts.coinbase.apiKey}
                                            onChange={(e) => handleAccountChange('coinbase', 'apiKey', e.target.value)}
                                            disabled={!accounts.coinbase.connected}
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label">Secret Key</label>
                                        <input 
                                            type="password" 
                                            className="form-control"
                                            value={accounts.coinbase.secretKey}
                                            onChange={(e) => handleAccountChange('coinbase', 'secretKey', e.target.value)}
                                            disabled={!accounts.coinbase.connected}
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label">Passphrase</label>
                                        <input 
                                            type="password" 
                                            className="form-control"
                                            value={accounts.coinbase.passphrase}
                                            onChange={(e) => handleAccountChange('coinbase', 'passphrase', e.target.value)}
                                            disabled={!accounts.coinbase.connected}
                                        />
                                    </div>
                                    <div className="form-check">
                                        <input 
                                            className="form-check-input" 
                                            type="checkbox"
                                            checked={accounts.coinbase.sandbox}
                                            onChange={(e) => handleAccountChange('coinbase', 'sandbox', e.target.checked)}
                                            disabled={!accounts.coinbase.connected}
                                        />
                                        <label className="form-check-label">Sandbox Mode (Recommended)</label>
                                    </div>
                                </div>
                            )}
                        </div>
                        
                        <div className="alert alert-warning mt-3">
                            <strong>Security Note:</strong> API credentials are stored locally in your browser and are not sent to the server until you start a bot. For maximum security, use paper trading/testnet modes.
                        </div>
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-secondary" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="button" className="btn btn-primary" onClick={() => onSave(accounts)}>
                            Save Settings
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Asset Selection Component
function AssetSelector({ selectedAssets, onAssetChange, type = 'stock' }) {
    const [customAsset, setCustomAsset] = useState('');
    const [showCustom, setShowCustom] = useState(false);
    
    const popularAssets = type === 'stock' 
        ? [...POPULAR_STOCKS, ...PRECIOUS_METALS] 
        : POPULAR_CRYPTO;

    const handleAssetToggle = (asset) => {
        const currentAssets = selectedAssets.split(',').map(s => s.trim()).filter(s => s);
        const isSelected = currentAssets.includes(asset);
        
        let newAssets;
        if (isSelected) {
            newAssets = currentAssets.filter(a => a !== asset);
        } else {
            newAssets = [...currentAssets, asset];
        }
        
        onAssetChange(newAssets.join(','));
    };

    const addCustomAsset = () => {
        if (!customAsset) return;
        
        const currentAssets = selectedAssets.split(',').map(s => s.trim()).filter(s => s);
        if (!currentAssets.includes(customAsset)) {
            onAssetChange([...currentAssets, customAsset].join(','));
        }
        setCustomAsset('');
    };

    const currentAssets = selectedAssets.split(',').map(s => s.trim()).filter(s => s);

    return (
        <div>
            <div className="d-flex justify-content-between align-items-center mb-2">
                <label className="form-label">{type === 'stock' ? 'Stocks & Metals' : 'Cryptocurrencies'}</label>
                <button 
                    type="button"
                    className="btn btn-link btn-sm"
                    onClick={() => setShowCustom(!showCustom)}
                >
                    + Add Custom
                </button>
            </div>
            
            {showCustom && (
                <div className="input-group mb-2">
                    <input 
                        type="text"
                        className="form-control form-control-sm"
                        placeholder={type === 'stock' ? 'e.g. AAPL' : 'e.g. BTC/USDT'}
                        value={customAsset}
                        onChange={(e) => setCustomAsset(e.target.value.toUpperCase())}
                    />
                    <button 
                        type="button"
                        className="btn btn-outline-secondary btn-sm"
                        onClick={addCustomAsset}
                    >
                        Add
                    </button>
                </div>
            )}
            
            <div className="border rounded p-2 mb-2" style={{maxHeight: '150px', overflowY: 'auto'}}>
                <div className="row g-1">
                    {popularAssets.map(asset => (
                        <div key={asset} className="col-auto">
                            <div className="form-check form-check-inline">
                                <input 
                                    className="form-check-input"
                                    type="checkbox"
                                    checked={currentAssets.includes(asset)}
                                    onChange={() => handleAssetToggle(asset)}
                                />
                                <label className="form-check-label small">
                                    {asset}
                                </label>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            
            <div className="form-text">
                Selected: {currentAssets.length} assets
                {currentAssets.length > 0 && (
                    <div className="small text-muted mt-1">
                        {currentAssets.slice(0, 10).join(', ')}
                        {currentAssets.length > 10 && ` and ${currentAssets.length - 10} more...`}
                    </div>
                )}
            </div>
        </div>
    );
}

// Create bot modal
function CreateBotModal({ onClose, onCreated }) {
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        initial_capital: 100000,
        max_portfolio_risk: 0.02,
        max_position_risk: 0.01,
        stock_universe: 'AAPL,MSFT,GOOGL,AMZN,TSLA',
        crypto_universe: 'BTC/USDT,ETH/USDT,ADA/USDT'
    });
    
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const payload = {
                ...formData,
                stock_universe: formData.stock_universe.split(',').map(s => s.trim()).filter(s => s),
                crypto_universe: formData.crypto_universe.split(',').map(s => s.trim()).filter(s => s)
            };

            const response = await fetch(`${API_BASE}/bots`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                onCreated();
                onClose();
            } else {
                const error = await response.json();
                alert(`Failed to create bot: ${error.detail}`);
            }
        } catch (err) {
            alert(`Failed to create bot: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal show d-block" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
            <div className="modal-dialog modal-lg">
                <div className="modal-content">
                    <form onSubmit={handleSubmit}>
                        <div className="modal-header">
                            <h5 className="modal-title">Create New Trading Bot</h5>
                            <button type="button" className="btn-close" onClick={onClose}></button>
                        </div>
                        <div className="modal-body">
                            <div className="mb-3">
                                <label className="form-label">Bot Name *</label>
                                <input 
                                    type="text" 
                                    className="form-control"
                                    value={formData.name}
                                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                                    required
                                />
                            </div>
                            <div className="mb-3">
                                <label className="form-label">Description</label>
                                <textarea 
                                    className="form-control"
                                    value={formData.description}
                                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                                    rows="2"
                                />
                            </div>
                            <div className="row">
                                <div className="col-md-6">
                                    <div className="mb-3">
                                        <label className="form-label">Initial Capital ($)</label>
                                        <input 
                                            type="number" 
                                            className="form-control"
                                            value={formData.initial_capital}
                                            onChange={(e) => setFormData({...formData, initial_capital: Number(e.target.value)})}
                                            min="1000"
                                            step="1000"
                                        />
                                    </div>
                                </div>
                                <div className="col-md-3">
                                    <div className="mb-3">
                                        <label className="form-label">Portfolio Risk</label>
                                        <input 
                                            type="number" 
                                            className="form-control"
                                            value={formData.max_portfolio_risk}
                                            onChange={(e) => setFormData({...formData, max_portfolio_risk: Number(e.target.value)})}
                                            min="0.001"
                                            max="0.1"
                                            step="0.001"
                                        />
                                    </div>
                                </div>
                                <div className="col-md-3">
                                    <div className="mb-3">
                                        <label className="form-label">Position Risk</label>
                                        <input 
                                            type="number" 
                                            className="form-control"
                                            value={formData.max_position_risk}
                                            onChange={(e) => setFormData({...formData, max_position_risk: Number(e.target.value)})}
                                            min="0.001"
                                            max="0.05"
                                            step="0.001"
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="mb-3">
                                <AssetSelector
                                    selectedAssets={formData.stock_universe}
                                    onAssetChange={(assets) => setFormData({...formData, stock_universe: assets})}
                                    type="stock"
                                />
                            </div>
                            <div className="mb-3">
                                <AssetSelector
                                    selectedAssets={formData.crypto_universe}
                                    onAssetChange={(assets) => setFormData({...formData, crypto_universe: assets})}
                                    type="crypto"
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button type="button" className="btn btn-secondary" onClick={onClose}>
                                Cancel
                            </button>
                            <button type="submit" className="btn btn-primary" disabled={loading}>
                                {loading ? 'Creating...' : 'Create Bot'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}

// Bot details modal
function BotDetailsModal({ bot, onClose }) {
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadDetails = async () => {
            try {
                const response = await fetch(`${API_BASE}/bots/${bot.id}/status`);
                const data = await response.json();
                setDetails(data);
            } catch (err) {
                console.error('Failed to load bot details:', err);
            } finally {
                setLoading(false);
            }
        };

        loadDetails();
    }, [bot.id]);

    return (
        <div className="modal show d-block" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
            <div className="modal-dialog modal-xl">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">Bot Details: {bot.name}</h5>
                        <button type="button" className="btn-close" onClick={onClose}></button>
                    </div>
                    <div className="modal-body">
                        {loading ? (
                            <div className="text-center">
                                <div className="spinner-border" role="status"></div>
                            </div>
                        ) : details ? (
                            <div className="row">
                                <div className="col-md-6">
                                    <h6>Performance Summary</h6>
                                    <table className="table table-sm">
                                        <tbody>
                                            <tr><td>Initial Capital:</td><td>${details.performance.initial_capital.toLocaleString()}</td></tr>
                                            <tr><td>Current Equity:</td><td>${details.performance.current_equity.toLocaleString()}</td></tr>
                                            <tr><td>Total Return:</td><td className={details.performance.total_return >= 0 ? 'text-success' : 'text-danger'}>{(details.performance.total_return * 100).toFixed(2)}%</td></tr>
                                            <tr><td>Total Trades:</td><td>{details.performance.total_trades}</td></tr>
                                            <tr><td>Win Rate:</td><td>{(details.performance.win_rate * 100).toFixed(1)}%</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                                <div className="col-md-6">
                                    <h6>Recent Trades</h6>
                                    {details.recent_trades.length > 0 ? (
                                        <div className="table-responsive">
                                            <table className="table table-sm">
                                                <thead>
                                                    <tr><th>Symbol</th><th>Side</th><th>PnL</th></tr>
                                                </thead>
                                                <tbody>
                                                    {details.recent_trades.slice(0, 5).map((trade, i) => (
                                                        <tr key={i}>
                                                            <td>{trade.symbol}</td>
                                                            <td><span className={`badge ${trade.side === 'buy' ? 'bg-success' : 'bg-danger'}`}>{trade.side}</span></td>
                                                            <td className={trade.pnl >= 0 ? 'text-success' : 'text-danger'}>
                                                                {trade.pnl ? `$${trade.pnl.toFixed(2)}` : '-'}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    ) : (
                                        <p className="text-muted">No recent trades</p>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="alert alert-warning">Failed to load bot details</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

// Render the main component
ReactDOM.render(<TradingBotDashboard />, document.getElementById('root'));