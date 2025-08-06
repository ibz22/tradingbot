#!/usr/bin/env python3
"""
Deployment Script for Halal Trading Bot GUI
Handles setup and deployment to Digital Ocean server
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
import yaml
import logging

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('deploy.log')
        ]
    )

def check_requirements():
    """Check if all required dependencies are installed"""
    required_commands = ['python', 'pip', 'systemctl']
    missing = []
    
    for cmd in required_commands:
        if not shutil.which(cmd):
            missing.append(cmd)
    
    if missing:
        logging.error(f"Missing required commands: {', '.join(missing)}")
        return False
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    logging.info("📦 Installing dependencies...")
    
    try:
        # Install GUI requirements
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'gui/requirements.txt'
        ], check=True)
        
        # Install main bot requirements
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True)
        
        logging.info("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Failed to install dependencies: {e}")
        return False

def create_systemd_service(service_name="halal-trading-gui", 
                         user="ubuntu", 
                         working_dir="/opt/tradingbot"):
    """Create systemd service for the GUI server"""
    logging.info("🔧 Creating systemd service...")
    
    service_content = f"""[Unit]
Description=Halal Trading Bot GUI Server
After=network.target

[Service]
Type=simple
User={user}
Group={user}
WorkingDirectory={working_dir}
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH={working_dir}
ExecStart={sys.executable} {working_dir}/gui/api_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    service_file = f"/etc/systemd/system/{service_name}.service"
    
    try:
        # Write service file (requires sudo)
        with open(f"{service_name}.service", 'w') as f:
            f.write(service_content)
        
        # Move to systemd directory
        subprocess.run([
            'sudo', 'mv', f"{service_name}.service", service_file
        ], check=True)
        
        # Reload systemd
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', service_name], check=True)
        
        logging.info(f"✅ Systemd service '{service_name}' created and enabled")
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Failed to create systemd service: {e}")
        return False

def setup_nginx(domain=None, port=3002):
    """Setup nginx reverse proxy"""
    logging.info("🌐 Setting up nginx reverse proxy...")
    
    if not domain:
        domain = "your-domain.com"
        logging.warning(f"No domain specified, using placeholder: {domain}")
    
    nginx_config = f"""server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}

    # WebSocket support
    location /ws {{
        proxy_pass http://127.0.0.1:{port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    
    try:
        config_file = f"tradingbot-{domain.replace('.', '-')}"
        
        # Write nginx config
        with open(f"{config_file}", 'w') as f:
            f.write(nginx_config)
        
        # Move to nginx sites-available
        subprocess.run([
            'sudo', 'mv', config_file, f"/etc/nginx/sites-available/{config_file}"
        ], check=True)
        
        # Enable site
        subprocess.run([
            'sudo', 'ln', '-sf', 
            f"/etc/nginx/sites-available/{config_file}",
            f"/etc/nginx/sites-enabled/{config_file}"
        ], check=True)
        
        # Test nginx config
        subprocess.run(['sudo', 'nginx', '-t'], check=True)
        
        # Reload nginx
        subprocess.run(['sudo', 'systemctl', 'reload', 'nginx'], check=True)
        
        logging.info(f"✅ Nginx configured for domain: {domain}")
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Failed to setup nginx: {e}")
        return False

def setup_ssl(domain, email):
    """Setup SSL certificate using Let's Encrypt"""
    logging.info("🔐 Setting up SSL certificate...")
    
    try:
        # Install certbot if not present
        if not shutil.which('certbot'):
            subprocess.run([
                'sudo', 'apt', 'install', '-y', 'certbot', 'python3-certbot-nginx'
            ], check=True)
        
        # Get SSL certificate
        subprocess.run([
            'sudo', 'certbot', '--nginx', '-d', domain, 
            '--email', email, '--agree-tos', '--non-interactive'
        ], check=True)
        
        logging.info(f"✅ SSL certificate installed for {domain}")
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Failed to setup SSL: {e}")
        return False

def setup_firewall(port=3002):
    """Setup UFW firewall rules"""
    logging.info("🔥 Configuring firewall...")
    
    try:
        # Allow SSH, HTTP, HTTPS, and custom port
        ports = ['22', '80', '443', str(port)]
        
        for port_num in ports:
            subprocess.run(['sudo', 'ufw', 'allow', port_num], check=True)
        
        # Enable firewall
        subprocess.run(['sudo', 'ufw', '--force', 'enable'], check=True)
        
        logging.info("✅ Firewall configured")
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Failed to setup firewall: {e}")
        return False

def create_env_file():
    """Create environment file template"""
    logging.info("📝 Creating environment file...")
    
    env_content = """# Halal Trading Bot GUI Environment Variables

# API Keys (Replace with your actual keys)
ALPACA_API_KEY=your_alpaca_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_here
BINANCE_API_KEY=your_binance_key_here
BINANCE_SECRET_KEY=your_binance_secret_here
FMP_API_KEY=your_fmp_key_here

# Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
NOTIFICATION_EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Database
DATABASE_URL=sqlite:///./trading_bots.db

# Security
SECRET_KEY=your_secret_key_here

# Server Configuration
PORT=3002
HOST=0.0.0.0
DEBUG=False
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        logging.info("✅ Created .env file template")
        logging.warning("⚠️  Please edit .env file with your actual API keys!")
    else:
        logging.info("📄 .env file already exists")

def setup_directories():
    """Create necessary directories"""
    logging.info("📁 Creating directories...")
    
    directories = [
        'logs/bots',
        'configs',
        'exports',
        'gui/static',
        'data'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    logging.info("✅ Directories created")

def initialize_database():
    """Initialize the database"""
    logging.info("🗄️  Initializing database...")
    
    try:
        # Import and create tables
        sys.path.append('gui')
        from models import create_tables
        create_tables()
        
        logging.info("✅ Database initialized")
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to initialize database: {e}")
        return False

def create_startup_script():
    """Create startup script for manual execution"""
    logging.info("📋 Creating startup script...")
    
    startup_content = """#!/bin/bash
# Startup script for Halal Trading Bot GUI

set -e

echo "🚀 Starting Halal Trading Bot GUI..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install -r gui/requirements.txt
pip install -r requirements.txt

# Initialize database
echo "🗄️  Initializing database..."
python -c "from gui.models import create_tables; create_tables()"

# Start the GUI server
echo "🌐 Starting GUI server on port 3002..."
python gui/api_server.py
"""
    
    with open('start_gui.sh', 'w') as f:
        f.write(startup_content)
    
    # Make executable
    os.chmod('start_gui.sh', 0o755)
    
    logging.info("✅ Created start_gui.sh script")

def deploy_local():
    """Deploy for local development"""
    logging.info("🏠 Setting up for local development...")
    
    success = True
    
    # Check requirements
    if not check_requirements():
        return False
    
    # Setup directories
    setup_directories()
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Create env file
    create_env_file()
    
    # Initialize database
    if not initialize_database():
        success = False
    
    # Create startup script
    create_startup_script()
    
    if success:
        logging.info("✅ Local deployment completed!")
        logging.info("To start the GUI server, run: ./start_gui.sh")
        logging.info("Or directly: python gui/api_server.py")
        logging.info("Access dashboard at: http://localhost:3002")
    
    return success

def deploy_server(domain, email, port=3002):
    """Deploy to production server"""
    logging.info("🚀 Setting up for production server...")
    
    success = True
    
    # Check if running as root/sudo
    if os.geteuid() != 0:
        logging.error("❌ Server deployment requires root privileges. Use sudo.")
        return False
    
    # Basic setup
    if not deploy_local():
        return False
    
    # Create systemd service
    if not create_systemd_service(working_dir=os.getcwd()):
        success = False
    
    # Setup nginx
    if not setup_nginx(domain, port):
        success = False
    
    # Setup firewall
    if not setup_firewall(port):
        success = False
    
    # Setup SSL (if domain and email provided)
    if domain != "localhost" and email:
        if not setup_ssl(domain, email):
            logging.warning("⚠️  SSL setup failed, continuing without HTTPS")
    
    if success:
        logging.info("✅ Server deployment completed!")
        logging.info(f"GUI will be available at: http{'s' if email else ''}://{domain}")
        logging.info("To start the service: sudo systemctl start halal-trading-gui")
        logging.info("To check status: sudo systemctl status halal-trading-gui")
        logging.info("To view logs: sudo journalctl -u halal-trading-gui -f")
    
    return success

def main():
    """Main deployment function"""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Deploy Halal Trading Bot GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy.py --local                              # Local development
  python deploy.py --server --domain example.com       # Server without SSL
  python deploy.py --server --domain example.com --email admin@example.com  # Server with SSL
        """
    )
    
    parser.add_argument('--local', action='store_true', 
                       help='Deploy for local development')
    parser.add_argument('--server', action='store_true', 
                       help='Deploy for production server')
    parser.add_argument('--domain', default='localhost',
                       help='Domain name for server deployment')
    parser.add_argument('--email', 
                       help='Email for SSL certificate registration')
    parser.add_argument('--port', type=int, default=3002,
                       help='Port for the GUI server (default: 3002)')
    
    args = parser.parse_args()
    
    if not args.local and not args.server:
        parser.print_help()
        return
    
    logging.info("🕌 Halal Trading Bot GUI Deployment")
    logging.info("=" * 50)
    
    try:
        if args.local:
            success = deploy_local()
        elif args.server:
            success = deploy_server(args.domain, args.email, args.port)
        
        if success:
            logging.info("\n🎉 Deployment completed successfully!")
            if not args.local:
                logging.info("⚠️  Remember to:")
                logging.info("   1. Edit .env file with your API keys")
                logging.info("   2. Configure your DNS to point to this server")
                logging.info("   3. Start the service: sudo systemctl start halal-trading-gui")
        else:
            logging.error("\n❌ Deployment failed! Check the logs above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("\n⚡ Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()