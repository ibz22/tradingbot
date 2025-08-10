#!/usr/bin/env python3
"""
Claude Code Context Briefing Script
Provides complete context for seamless development continuation
"""

import os
import json
from pathlib import Path
from datetime import datetime

def generate_claude_briefing():
    """Generate a comprehensive briefing for Claude Code"""
    
    briefing = f"""
🤖 CLAUDE CODE DEVELOPMENT BRIEFING
==================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 PROJECT: SOLANA TRADING BOT - PHASE 3 IMPLEMENTATION
=====================================================

📊 CURRENT STATUS:
- ✅ Phase 1: Core Solana Integration (COMPLETE)
- ✅ Phase 2: Trading Intelligence & Multi-Strategy System (COMPLETE)  
- 🚧 Phase 3: News & Social Sentiment Trading (READY TO START)

🏗️ EXISTING ARCHITECTURE (Fully Operational):
├── solana_trading/
│   ├── core/                 # ✅ Solana RPC client & transactions
│   ├── defi/                 # ✅ Jupiter & DEX integrations
│   ├── strategies/           # ✅ DCA, Momentum, Arbitrage strategies
│   ├── risk/                 # ✅ Professional risk management
│   ├── portfolio/            # ✅ Portfolio management & P&L
│   ├── automation/           # ✅ Trading engine & scheduling
│   ├── market_data/          # ✅ Price feeds & technical analysis
│   ├── paper_trading/        # ✅ Paper trading simulation
│   └── compliance/           # ✅ Halal trading validation

🎯 PHASE 3 MISSION: NEWS & SOCIAL SENTIMENT TRADING
=================================================

GOAL: Build an AI-powered system that:
1. Monitors crypto news and social media for Solana token mentions
2. Analyzes sentiment and hype momentum in real-time
3. Identifies new tokens with viral potential before mass adoption
4. Validates token legitimacy and liquidity automatically
5. Executes rapid trades to capitalize on news-driven price movements

KEY CAPABILITIES TO BUILD:
- 📰 Real-time news monitoring (NewsAPI, CryptoPanic, RSS feeds)
- 🐦 Social media intelligence (Twitter, Reddit, Telegram)
- 🔍 Token discovery and validation (contract analysis, rug detection)
- ⚡ Lightning-fast execution (news-to-trade in <60 seconds)
- 🧠 AI sentiment analysis (OpenAI/Claude integration)
- 📈 Hype momentum tracking and timing optimization

🚨 CRITICAL SUCCESS FACTORS:
- SPEED: Sub-minute news-to-execution pipeline
- ACCURACY: 80%+ sentiment correlation with price moves
- SAFETY: Robust rug pull detection and risk controls
- INTEGRATION: Seamless with existing Phase 2 systems

📋 IMPLEMENTATION PLAN (4 Sessions):

SESSION 1: News Monitoring Foundation ⏳ NEXT
└── Build news aggregation, sentiment analysis, token extraction

SESSION 2: Social Media Intelligence ⏳ PENDING  
└── Twitter, Reddit, Telegram monitoring and sentiment aggregation

SESSION 3: Token Discovery & Validation ⏳ PENDING
└── Automated token validation, liquidity analysis, rug detection

SESSION 4: Hype Strategy & Rapid Execution ⏳ PENDING
└── Complete strategy integration with rapid execution system

🔧 TECHNICAL REQUIREMENTS:

APIs to Integrate:
- NewsAPI (newsapi.org) for crypto news feeds
- Twitter API v2 for trending topics and mentions  
- Reddit API (PRAW) for r/solana and crypto subreddit monitoring
- Telegram Bot API for channel monitoring
- Solscan/SolanaFM APIs for token data and validation
- OpenAI API for advanced sentiment analysis

New Dependencies Needed:
- newsapi-python>=0.2.6
- praw>=7.7.1  
- python-telegram-bot>=20.7
- tweepy>=4.14.0
- textblob>=0.17.1
- vaderSentiment>=3.3.2

Directory Structure to Create:
solana_trading/
├── sentiment/           # News & social sentiment analysis
├── discovery/           # Token finding & validation
├── hype/               # Momentum analysis & timing
└── strategies/
    └── hype_strategy.py # News-driven trading strategy

🛡️ RISK MANAGEMENT INTEGRATION:
- Max 2% portfolio allocation for speculative hype trades
- Automatic stop-losses at 10-15% for hype positions
- Rug pull detection with emergency exit mechanisms
- Time-based position exits if hype doesn't materialize
- Integration with existing Phase 2 risk management system

📊 PERFORMANCE TARGETS:
- News processing: <30 seconds from publication to analysis
- Social sentiment: Real-time tracking with 1-minute updates
- Token validation: Complete analysis in <60 seconds
- Trade execution: News-to-order in <2 minutes total
- Accuracy: 80%+ correlation between sentiment and price moves

🎯 IMMEDIATE NEXT STEPS:
1. Run progress tracker: `python phase3_progress.py`
2. Start Session 1: News monitoring infrastructure
3. Focus on NewsAPI integration and sentiment analysis first
4. Build token extraction from news articles
5. Test with real crypto news feeds

📝 DEVELOPMENT NOTES:
- Maintain async/await patterns throughout (matches existing code)
- Use existing logging and error handling frameworks
- Paper trading mode enabled by default for safe testing
- All new strategies must integrate with existing risk management
- Maintain halal compliance (no interest-based or manipulative trading)

🔄 PROGRESS TRACKING:
- Use `python phase3_progress.py` to check status anytime
- Progress automatically saved to PHASE3_PROGRESS.json
- Each session has detailed task breakdown and success criteria
- Blockers and notes tracked for seamless handoffs

⚡ READY TO START:
The foundation is solid. Phase 2 provides all core infrastructure.
Claude Code can now build the news/social intelligence layer on top.

Focus on Session 1 first - news monitoring is the foundation for everything else.

🚀 LET'S BUILD THE FUTURE OF ALPHA GENERATION! 🚀
"""
    
    return briefing

def check_project_status():
    """Verify project is ready for Phase 3"""
    required_files = [
        "solana_trading/core/client.py",
        "solana_trading/defi/jupiter.py",
        "solana_trading/strategies/base_strategy.py", 
        "solana_trading/risk/risk_manager.py",
        "solana_phase2_main.py"
    ]
    
    status = {
        "ready": True,
        "missing_files": [],
        "existing_modules": []
    }
    
    for file_path in required_files:
        if os.path.exists(file_path):
            status["existing_modules"].append(file_path)
        else:
            status["missing_files"].append(file_path)
            status["ready"] = False
    
    return status

def save_briefing_files():
    """Save all briefing files to the project directory"""
    
    # Save the main briefing
    briefing_content = generate_claude_briefing()
    with open("CLAUDE_BRIEFING.md", "w") as f:
        f.write(briefing_content)
    
    # Save a quick start command file
    quick_start = """#!/bin/bash
# Claude Code Quick Start for Phase 3
# Run this to get oriented and start development

echo "🤖 CLAUDE CODE - PHASE 3 QUICK START"
echo "====================================="

echo ""
echo "📊 Checking project status..."
python phase3_progress.py

echo ""
echo "📋 Current briefing:"
echo "Run: cat CLAUDE_BRIEFING.md"

echo ""
echo "🚀 To start Phase 3 Session 1:"
echo "1. Review the briefing above"
echo "2. Start with: python phase3_progress.py start 1"
echo "3. Begin implementing news monitoring infrastructure"

echo ""
echo "📂 Key files to create in Session 1:"
echo "   - solana_trading/sentiment/news_monitor.py"
echo "   - solana_trading/sentiment/sentiment_analyzer.py" 
echo "   - solana_trading/discovery/token_extractor.py"

echo ""
echo "Ready to build the future of alpha generation! 🚀"
"""
    
    with open("phase3_quickstart.sh", "w") as f:
        f.write(quick_start)
    
    # Save Phase 3 requirements
    requirements_phase3 = """# Phase 3 Additional Requirements
# Add these to your existing requirements.txt

# News & Social Media APIs
newsapi-python>=0.2.6
praw>=7.7.1
python-telegram-bot>=20.7
tweepy>=4.14.0

# Sentiment Analysis
textblob>=0.17.1
vaderSentiment>=3.3.2
openai>=1.3.0

# Web Scraping & Data Processing  
beautifulsoup4>=4.12.2
requests>=2.31.0
feedparser>=6.0.10

# Additional Utilities
python-dateutil>=2.8.2
pytz>=2023.3
"""
    
    with open("requirements_phase3.txt", "w") as f:
        f.write(requirements_phase3)

def main():
    """Main function to set up complete Phase 3 development context"""
    
    print("🚀 Setting up Phase 3 development context...")
    
    # Check project readiness
    status = check_project_status()
    
    if not status["ready"]:
        print("⚠️  WARNING: Missing required Phase 2 files:")
        for file in status["missing_files"]:
            print(f"   ❌ {file}")
        print("\nPlease ensure Phase 2 is complete before starting Phase 3")
        return
    
    # Create all briefing and template files
    save_briefing_files()
    
    print("✅ Phase 3 development context created!")
    print("\n📁 Files created:")
    print("   📄 CLAUDE_BRIEFING.md - Complete context for Claude Code")
    print("   📄 phase3_progress.py - Progress tracking system")
    print("   📄 phase3_quickstart.sh - Quick start script")
    print("   📄 requirements_phase3.txt - Additional dependencies")
    
    print("\n🎯 READY FOR CLAUDE CODE!")
    print("Run this command to start:")
    print("   claude")
    print("\nThen use the briefing and progress tracker for seamless development.")
    
    # Show current status
    print("\n" + "="*50)
    print("📊 CURRENT PROJECT STATUS:")
    print("="*50)
    
    print(f"✅ Phase 2 Dependencies: {len(status['existing_modules'])}/{len(status['existing_modules'])}")
    print("🎯 Ready for Phase 3 implementation")
    print("📋 Next: Start Session 1 - News Monitoring Foundation")
    
    print("\n🚀 Let's build the future of alpha generation! 🚀")

if __name__ == "__main__":
    main()