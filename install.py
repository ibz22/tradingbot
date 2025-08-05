        logging.error(f"❌ Verification failed: {e}")
        return False

def run_basic_test():
    """Run a basic functionality test."""
    try:
        logging.info("🧪 Running basic functionality test...")
        
        # Test risk manager
        from halalbot.core.risk import RiskManager
        rm = RiskManager()
        
        # Test momentum strategy
        from halalbot.strategies.momentum import MomentumStrategy
        strategy = MomentumStrategy(lookback=20)
        
        # Test data gateway
        from halalbot.screening.data_gateway import FMPGateway
        gateway = FMPGateway('demo')
        
        logging.info("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        logging.error(f"❌ Basic test failed: {e}")
        return False

def print_next_steps():
    """Print instructions for next steps."""
    print("\n" + "="*60)
    print("🎉 INSTALLATION COMPLETE!")
    print("="*60)
    print()
    print("📋 NEXT STEPS:")
    print()
    print("1. 🔑 Configure API Keys:")
    print("   - Edit .env file with your API credentials")
    print("   - Get Alpaca API keys: https://alpaca.markets/")
    print("   - Get FMP API key: https://financialmodelingprep.com/")
    print()
    print("2. ⚙️ Review Configuration:")
    print("   - Edit config.yaml to customize trading parameters")
    print("   - Adjust risk management settings")
    print("   - Select your asset universe")
    print()
    print("3. 🧪 Test the System:")
    print("   python main.py --mode test")
    print("   python main.py --mode screen --symbol AAPL")
    print()
    print("4. 🚀 Start Trading:")
    print("   python main.py --mode live --dry-run    # Simulation")
    print("   python main.py --mode live               # Live trading")
    print()
    print("📚 Documentation:")
    print("   - README.md: Complete usage guide")
    print("   - examples/: Sample code and tutorials")
    print("   - halalbot/: Core package documentation")
    print()
    print("🕌 Remember: This system follows Islamic finance principles")
    print("   Always verify halal compliance with qualified scholars")
    print()
    print("="*60)

def main():
    """Main installation function."""
    setup_logging()
    
    print("🕌 Enhanced Halal Trading Bot v2.2 - Setup")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        logging.error("❌ Failed to install requirements. Please install manually:")
        logging.error("pip install -r requirements.txt")
        sys.exit(1)
    
    # Install package
    if not install_package():
        logging.error("❌ Failed to install package. Please install manually:")
        logging.error("pip install -e .")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        logging.warning("⚠️ Environment setup had issues")
    
    # Verify installation
    if not verify_installation():
        logging.error("❌ Installation verification failed")
        sys.exit(1)
    
    # Run basic test
    if not run_basic_test():
        logging.error("❌ Basic functionality test failed")
        sys.exit(1)
    
    # Print next steps
    print_next_steps()
    
    logging.info("✅ Setup completed successfully!")

if __name__ == "__main__":
    main()
