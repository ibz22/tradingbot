// React Dashboard for Trading Bot Management
const { useState, useEffect, useCallback } = React;

// API Base URL - adjust for your server
const API_BASE = window.location.origin + '/api';

// WebSocket connection for real-time updates
let ws = null;

// Main Dashboard Component
function TradingBotDashboard() {
    const [bots, setBots] = useState([]);
    const [summary, setSummary] = useState({});
    const [selectedBot, setSelectedBot] = useState(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [recentActivity, setRecentActivity] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

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

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, [loadData]);

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
                                <label className="form-label">Stock Universe (comma-separated)</label>
                                <input 
                                    type="text" 
                                    className="form-control"
                                    value={formData.stock_universe}
                                    onChange={(e) => setFormData({...formData, stock_universe: e.target.value})}
                                    placeholder="AAPL,MSFT,GOOGL"
                                />
                            </div>
                            <div className="mb-3">
                                <label className="form-label">Crypto Universe (comma-separated)</label>
                                <input 
                                    type="text" 
                                    className="form-control"
                                    value={formData.crypto_universe}
                                    onChange={(e) => setFormData({...formData, crypto_universe: e.target.value})}
                                    placeholder="BTC/USDT,ETH/USDT,ADA/USDT"
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