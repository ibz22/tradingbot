"""
Results Export System
Handles exporting trading bot results to CSV and Google Sheets
"""

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

from sqlalchemy.orm import Session
from models import BotInstance, Trade, PerformanceLog, get_db

class ResultsExporter:
    """Handles exporting bot performance data to various formats"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.exports_dir = self.base_dir / "exports"
        self.exports_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Google Sheets configuration
        self.sheets_client = None
        self._initialize_google_sheets()

    def _initialize_google_sheets(self):
        """Initialize Google Sheets client if credentials are available"""
        if not GOOGLE_SHEETS_AVAILABLE:
            self.logger.warning("Google Sheets libraries not installed. Only CSV export available.")
            return
        
        try:
            # Look for credentials file
            creds_file = self.base_dir / "google_sheets_credentials.json"
            if creds_file.exists():
                scope = ['https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive']
                
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    str(creds_file), scope
                )
                self.sheets_client = gspread.authorize(creds)
                self.logger.info("✅ Google Sheets integration initialized")
            else:
                self.logger.info("Google Sheets credentials not found. Only CSV export available.")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets: {e}")

    def export_bot_results(self, bot_id: int, format: str = "csv", 
                          output_path: Optional[str] = None) -> str:
        """Export comprehensive bot results"""
        with Session(bind=next(get_db()).bind) as db:
            bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
            if not bot:
                raise ValueError(f"Bot {bot_id} not found")
            
            # Gather all data
            trades = db.query(Trade).filter(Trade.bot_id == bot_id).all()
            performance = db.query(PerformanceLog).filter(PerformanceLog.bot_id == bot_id).all()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == "csv":
                return self._export_to_csv(bot, trades, performance, output_path, timestamp)
            elif format.lower() == "google_sheets":
                return self._export_to_google_sheets(bot, trades, performance)
            else:
                raise ValueError(f"Unsupported export format: {format}")

    def _export_to_csv(self, bot: BotInstance, trades: List[Trade], 
                      performance: List[PerformanceLog], 
                      output_path: Optional[str], timestamp: str) -> str:
        """Export bot data to CSV files"""
        
        bot_name = bot.name.replace(" ", "_").replace("-", "_")
        
        if output_path:
            export_dir = Path(output_path)
        else:
            export_dir = self.exports_dir / f"{bot_name}_{timestamp}"
        
        export_dir.mkdir(exist_ok=True)
        
        # 1. Bot Summary
        summary_file = export_dir / f"{bot_name}_summary.csv"
        with open(summary_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Bot Summary"])
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Name", bot.name])
            writer.writerow(["Description", bot.description or ""])
            writer.writerow(["Created", bot.created_at])
            writer.writerow(["Status", bot.status])
            writer.writerow(["Initial Capital", bot.initial_capital])
            writer.writerow(["Current Equity", bot.current_equity])
            writer.writerow(["Total Return (%)", f"{bot.total_return:.2%}"])
            writer.writerow(["Total Trades", bot.total_trades])
            writer.writerow(["Win Rate (%)", f"{bot.win_rate:.1%}"])
            writer.writerow(["Sharpe Ratio", f"{bot.sharpe_ratio:.2f}"])
            writer.writerow(["Max Drawdown (%)", f"{bot.max_drawdown:.2%}"])
        
        # 2. Trades Detail
        trades_file = export_dir / f"{bot_name}_trades.csv"
        if trades:
            trades_df = pd.DataFrame([
                {
                    "Trade ID": trade.id,
                    "Symbol": trade.symbol,
                    "Side": trade.side,
                    "Quantity": trade.quantity,
                    "Entry Price": trade.entry_price,
                    "Exit Price": trade.exit_price,
                    "Entry Time": trade.entry_time,
                    "Exit Time": trade.exit_time,
                    "Strategy": trade.strategy_name,
                    "PnL": trade.pnl,
                    "PnL %": f"{trade.pnl_pct:.2%}" if trade.pnl_pct else "",
                    "Fees": trade.fees,
                    "Slippage": trade.slippage,
                    "Status": trade.status,
                    "Is Halal": trade.is_halal,
                    "Confidence": trade.confidence,
                    "Notes": trade.notes or ""
                } for trade in trades
            ])
            trades_df.to_csv(trades_file, index=False)
        else:
            # Create empty file with headers
            with open(trades_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Trade ID", "Symbol", "Side", "Quantity", "Entry Price", 
                               "Exit Price", "Entry Time", "Exit Time", "Strategy", 
                               "PnL", "PnL %", "Fees", "Slippage", "Status", 
                               "Is Halal", "Confidence", "Notes"])
        
        # 3. Performance History
        performance_file = export_dir / f"{bot_name}_performance.csv"
        if performance:
            perf_df = pd.DataFrame([
                {
                    "Timestamp": perf.timestamp,
                    "Equity": perf.equity,
                    "Cash": perf.cash,
                    "Positions Value": perf.positions_value,
                    "Total Return %": f"{perf.total_return:.2%}",
                    "Daily Return %": f"{perf.daily_return:.2%}",
                    "Portfolio Risk": perf.portfolio_risk,
                    "VaR 95%": perf.var_95,
                    "Max Drawdown %": f"{perf.max_drawdown:.2%}",
                    "Total Trades": perf.total_trades,
                    "Winning Trades": perf.winning_trades,
                    "Losing Trades": perf.losing_trades,
                    "Win Rate %": f"{perf.win_rate:.1%}",
                    "Sharpe Ratio": perf.sharpe_ratio,
                    "Sortino Ratio": perf.sortino_ratio,
                    "Open Positions": perf.open_positions,
                    "Total Fees": perf.total_fees
                } for perf in performance
            ])
            perf_df.to_csv(performance_file, index=False)
        else:
            # Create empty file with headers
            with open(performance_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Equity", "Cash", "Positions Value", 
                               "Total Return %", "Daily Return %", "Portfolio Risk",
                               "VaR 95%", "Max Drawdown %", "Total Trades", 
                               "Winning Trades", "Losing Trades", "Win Rate %",
                               "Sharpe Ratio", "Sortino Ratio", "Open Positions", "Total Fees"])
        
        # 4. Trade Analysis
        analysis_file = export_dir / f"{bot_name}_analysis.csv"
        self._create_trade_analysis_csv(trades, analysis_file)
        
        self.logger.info(f"📊 Exported bot {bot.name} results to {export_dir}")
        return str(export_dir)

    def _create_trade_analysis_csv(self, trades: List[Trade], file_path: Path):
        """Create detailed trade analysis CSV"""
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Calculate statistics
            closed_trades = [t for t in trades if t.status == "closed" and t.pnl is not None]
            winning_trades = [t for t in closed_trades if t.pnl > 0]
            losing_trades = [t for t in closed_trades if t.pnl < 0]
            
            total_pnl = sum(t.pnl for t in closed_trades) if closed_trades else 0
            avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            # Write analysis
            writer.writerow(["Trade Analysis Summary"])
            writer.writerow([""])
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Trades", len(trades)])
            writer.writerow(["Closed Trades", len(closed_trades)])
            writer.writerow(["Open Trades", len(trades) - len(closed_trades)])
            writer.writerow(["Winning Trades", len(winning_trades)])
            writer.writerow(["Losing Trades", len(losing_trades)])
            writer.writerow(["Win Rate", f"{len(winning_trades)/len(closed_trades):.1%}" if closed_trades else "0%"])
            writer.writerow(["Total PnL", f"${total_pnl:.2f}"])
            writer.writerow(["Average Win", f"${avg_win:.2f}"])
            writer.writerow(["Average Loss", f"${avg_loss:.2f}"])
            writer.writerow(["Profit Factor", f"{abs(avg_win/avg_loss):.2f}" if avg_loss != 0 else "∞"])
            
            # Symbol analysis
            writer.writerow([""])
            writer.writerow(["Symbol Performance"])
            writer.writerow(["Symbol", "Trades", "Total PnL", "Win Rate"])
            
            symbol_stats = {}
            for trade in closed_trades:
                if trade.symbol not in symbol_stats:
                    symbol_stats[trade.symbol] = {"trades": 0, "pnl": 0, "wins": 0}
                symbol_stats[trade.symbol]["trades"] += 1
                symbol_stats[trade.symbol]["pnl"] += trade.pnl
                if trade.pnl > 0:
                    symbol_stats[trade.symbol]["wins"] += 1
            
            for symbol, stats in symbol_stats.items():
                win_rate = stats["wins"] / stats["trades"] if stats["trades"] > 0 else 0
                writer.writerow([symbol, stats["trades"], f"${stats['pnl']:.2f}", f"{win_rate:.1%}"])

    def _export_to_google_sheets(self, bot: BotInstance, trades: List[Trade], 
                               performance: List[PerformanceLog]) -> str:
        """Export bot data to Google Sheets"""
        if not self.sheets_client:
            raise ValueError("Google Sheets not configured")
        
        try:
            # Create or open spreadsheet
            sheet_name = f"TradingBot_{bot.name}_{datetime.now().strftime('%Y%m%d')}"
            
            try:
                spreadsheet = self.sheets_client.open(sheet_name)
            except gspread.SpreadsheetNotFound:
                spreadsheet = self.sheets_client.create(sheet_name)
                # Share with your email (optional, configure as needed)
                # spreadsheet.share('your-email@gmail.com', perm_type='user', role='writer')
            
            # Clear existing worksheets except the first one
            worksheets = spreadsheet.worksheets()
            for ws in worksheets[1:]:
                spreadsheet.del_worksheet(ws)
            
            # Rename first worksheet
            main_ws = worksheets[0]
            main_ws.update_title("Summary")
            
            # 1. Summary Sheet
            summary_data = [
                ["Bot Performance Summary"],
                [""],
                ["Metric", "Value"],
                ["Name", bot.name],
                ["Description", bot.description or ""],
                ["Created", str(bot.created_at)],
                ["Status", bot.status],
                ["Initial Capital", f"${bot.initial_capital:,.2f}"],
                ["Current Equity", f"${bot.current_equity:,.2f}"],
                ["Total Return", f"{bot.total_return:.2%}"],
                ["Total Trades", bot.total_trades],
                ["Win Rate", f"{bot.win_rate:.1%}"],
                ["Sharpe Ratio", f"{bot.sharpe_ratio:.2f}"],
                ["Max Drawdown", f"{bot.max_drawdown:.2%}"]
            ]
            main_ws.update("A1", summary_data)
            
            # 2. Trades Sheet
            trades_ws = spreadsheet.add_worksheet(title="Trades", rows=len(trades)+2, cols=15)
            if trades:
                trades_data = [
                    ["Trade ID", "Symbol", "Side", "Quantity", "Entry Price", "Exit Price",
                     "Entry Time", "Exit Time", "Strategy", "PnL", "PnL %", "Fees",
                     "Status", "Is Halal", "Confidence"]
                ]
                
                for trade in trades:
                    trades_data.append([
                        trade.id, trade.symbol, trade.side, trade.quantity,
                        trade.entry_price, trade.exit_price or "",
                        str(trade.entry_time), str(trade.exit_time) if trade.exit_time else "",
                        trade.strategy_name or "", trade.pnl or "",
                        f"{trade.pnl_pct:.2%}" if trade.pnl_pct else "",
                        trade.fees, trade.status, trade.is_halal, trade.confidence
                    ])
                
                trades_ws.update("A1", trades_data)
            
            # 3. Performance Sheet
            if performance:
                perf_ws = spreadsheet.add_worksheet(title="Performance", rows=len(performance)+2, cols=12)
                perf_data = [
                    ["Timestamp", "Equity", "Cash", "Positions Value", "Total Return %",
                     "Daily Return %", "Max Drawdown %", "Total Trades", "Win Rate %",
                     "Sharpe Ratio", "Open Positions", "Total Fees"]
                ]
                
                for perf in performance:
                    perf_data.append([
                        str(perf.timestamp), perf.equity, perf.cash, perf.positions_value,
                        f"{perf.total_return:.2%}", f"{perf.daily_return:.2%}",
                        f"{perf.max_drawdown:.2%}", perf.total_trades, f"{perf.win_rate:.1%}",
                        perf.sharpe_ratio or "", perf.open_positions, perf.total_fees
                    ])
                
                perf_ws.update("A1", perf_data)
            
            spreadsheet_url = spreadsheet.url
            self.logger.info(f"📈 Exported bot {bot.name} to Google Sheets: {spreadsheet_url}")
            return spreadsheet_url
            
        except Exception as e:
            self.logger.error(f"Failed to export to Google Sheets: {e}")
            raise

    def export_all_bots_summary(self, format: str = "csv") -> str:
        """Export summary of all bots"""
        with Session(bind=next(get_db()).bind) as db:
            bots = db.query(BotInstance).all()
            
            if format.lower() == "csv":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                summary_file = self.exports_dir / f"all_bots_summary_{timestamp}.csv"
                
                with open(summary_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["All Bots Performance Summary"])
                    writer.writerow(["Generated", datetime.now()])
                    writer.writerow([""])
                    writer.writerow(["Bot Name", "Status", "Initial Capital", "Current Equity", 
                                   "Total Return %", "Total Trades", "Win Rate %", 
                                   "Sharpe Ratio", "Max Drawdown %", "Last Update"])
                    
                    for bot in bots:
                        writer.writerow([
                            bot.name, bot.status, f"${bot.initial_capital:,.2f}",
                            f"${bot.current_equity:,.2f}", f"{bot.total_return:.2%}",
                            bot.total_trades, f"{bot.win_rate:.1%}",
                            f"{bot.sharpe_ratio:.2f}", f"{bot.max_drawdown:.2%}",
                            bot.last_heartbeat or bot.updated_at
                        ])
                
                self.logger.info(f"📊 Exported all bots summary to {summary_file}")
                return str(summary_file)
            
            else:
                raise ValueError(f"Unsupported format for summary: {format}")

    def get_export_history(self) -> List[Dict[str, Any]]:
        """Get list of previous exports"""
        exports = []
        
        for file_path in self.exports_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.csv', '.xlsx']:
                exports.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "created": datetime.fromtimestamp(file_path.stat().st_ctime),
                    "type": "CSV" if file_path.suffix == '.csv' else "Excel"
                })
        
        return sorted(exports, key=lambda x: x["created"], reverse=True)