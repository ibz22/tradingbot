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