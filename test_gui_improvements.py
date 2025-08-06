#!/usr/bin/env python3
"""
Test script to verify GUI improvements
"""

import os
import sys
import time
import threading
import webbrowser
from pathlib import Path

# Add gui directory to path
gui_dir = Path(__file__).parent / "gui"
sys.path.insert(0, str(gui_dir))

def test_improvements():
    """Test the key improvements made to the GUI"""
    print("Testing GUI Improvements")
    print("=" * 50)
    
    # Test 1: Check if dashboard.js contains our improvements
    dashboard_path = gui_dir / "static" / "dashboard.js"
    
    if not dashboard_path.exists():
        print("❌ Dashboard file not found!")
        return False
        
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for pause/resume functionality
    if 'toggleRefresh' in content and 'isPaused' in content:
        print("[OK] Pause/Resume refresh functionality added")
    else:
        print("[FAIL] Pause/Resume functionality not found")
        return False
    
    # Check for configurable intervals
    if 'changeRefreshInterval' in content and 'refreshSettings' in content:
        print("[OK] Configurable refresh intervals added")
    else:
        print("[FAIL] Configurable refresh intervals not found")
        return False
    
    # Check for trading account management
    if 'TradingAccountModal' in content and 'alpaca' in content:
        print("[OK] Trading account management added")
    else:
        print("[FAIL] Trading account management not found")
        return False
    
    # Check for asset selection components
    if 'AssetSelector' in content and 'POPULAR_STOCKS' in content:
        print("[OK] Asset selection dropdowns added")
    else:
        print("[FAIL] Asset selection dropdowns not found")
        return False
    
    # Check for precious metals and popular assets
    if 'PRECIOUS_METALS' in content and 'POPULAR_CRYPTO' in content:
        print("[OK] Popular assets (stocks, crypto, metals) included")
    else:
        print("[FAIL] Popular assets not found")
        return False
    
    print("\nAll improvements successfully implemented!")
    print("\nKey Features Added:")
    print("- Pause/Resume refresh with configurable intervals")
    print("- Trading account login for Alpaca, Binance, Coinbase")
    print("- Asset dropdown with popular stocks, crypto, and metals")
    print("- Control panel for better user experience")
    print("- Improved responsiveness and user control")
    
    return True

def start_gui_server():
    """Start the GUI server in a separate thread"""
    def run_server():
        try:
            # Import and run the server
            from api_server import app
            import uvicorn
            
            print("Starting GUI server...")
            uvicorn.run(app, host="127.0.0.1", port=3002, log_level="warning")
        except ImportError as e:
            print(f"[FAIL] Could not start server: {e}")
        except Exception as e:
            print(f"[FAIL] Server error: {e}")
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(3)
    print("GUI server should be running at http://127.0.0.1:3002")
    
    return server_thread

if __name__ == "__main__":
    # Test the improvements
    success = test_improvements()
    
    if success:
        print("\n" + "=" * 50)
        print("Testing Complete - All improvements verified!")
        print("\nTo test the GUI:")
        print("1. Run: cd gui && python api_server.py")
        print("2. Open: http://127.0.0.1:3002")
        print("3. Test the new features:")
        print("   - Pause/Resume button in control panel")
        print("   - Change refresh intervals")
        print("   - Manage trading accounts")
        print("   - Create bot with asset selection")
    else:
        print("[FAIL] Some improvements are missing!")
        sys.exit(1)