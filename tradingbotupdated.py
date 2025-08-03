import logging
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import yaml


def setup_logging(log_level: str = "INFO", log_file: str = "trading_bot.log"):
    """Simple logging setup used in tests."""
    from logging.handlers import RotatingFileHandler

    Path("logs").mkdir(exist_ok=True)
    file_handler = RotatingFileHandler(
        f"logs/{log_file}", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=[file_handler, console_handler],
        force=True,
    )


@dataclass
class TradingConfig:
    """Configuration dataclass used for tests."""

    max_portfolio_risk: float = 0.02
    max_position_risk: float = 0.01
    max_position_pct: float = 0.1

    confidence_threshold: float = 0.4
    rebalance_frequency: str = "1h"
    min_data_points: int = 50

    alpaca_paper_trading: bool = True
    binance_testnet: bool = True
    max_retries: int = 3
    retry_delay: float = 5.0

    default_strategy_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "momentum_breakout": 0.4,
            "mean_reversion": 0.3,
            "ml_strategy": 0.3,
        }
    )

    stock_universe: List[str] = field(
        default_factory=lambda: [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "BRK.B",
            "JNJ",
            "V",
        ]
    )
    crypto_universe: List[str] = field(
        default_factory=lambda: [
            "BTC/USDT",
            "ETH/USDT",
            "SOL/USDT",
            "ADA/USDT",
            "DOT/USDT",
            "AVAX/USDT",
            "ALGO/USDT",
        ]
    )

    enable_notifications: bool = True
    notification_channels: List[str] = field(
        default_factory=lambda: ["telegram", "email"]
    )

    ml_retrain_hours: int = 24
    ml_min_samples: int = 100
    ml_feature_selection: bool = True
    ml_ensemble_models: bool = True

    max_concurrent_assets: int = 10
    data_cache_hours: int = 1
    enable_performance_monitoring: bool = True

    def __post_init__(self):
        self._validate_risk_parameters()
        self._validate_strategy_weights()
        self._validate_trading_parameters()
        self._validate_ml_parameters()

    def _validate_risk_parameters(self):
        if not (0 < self.max_portfolio_risk <= 1):
            raise ValueError(
                f"max_portfolio_risk must be between 0 and 1, got {self.max_portfolio_risk}"
            )
        if not (0 < self.max_position_risk <= 1):
            raise ValueError(
                f"max_position_risk must be between 0 and 1, got {self.max_position_risk}"
            )
        if not (0 < self.max_position_pct <= 1):
            raise ValueError(
                f"max_position_pct must be between 0 and 1, got {self.max_position_pct}"
            )
        if self.max_position_risk > self.max_portfolio_risk:
            raise ValueError("max_position_risk cannot exceed max_portfolio_risk")

    def _validate_strategy_weights(self):
        total_weight = sum(self.default_strategy_weights.values())
        if not (0.99 <= total_weight <= 1.01):
            raise ValueError(f"Strategy weights must sum to 1, got {total_weight}")
        for strategy, weight in self.default_strategy_weights.items():
            if not (0 <= weight <= 1):
                raise ValueError(
                    f"Strategy weight for {strategy} must be between 0 and 1, got {weight}"
                )

    def _validate_trading_parameters(self):
        if not (0 < self.confidence_threshold <= 1):
            raise ValueError(
                f"confidence_threshold must be between 0 and 1, got {self.confidence_threshold}"
            )
        if self.min_data_points < 20:
            raise ValueError(
                f"min_data_points must be at least 20, got {self.min_data_points}"
            )
        if self.max_retries < 1:
            raise ValueError(f"max_retries must be at least 1, got {self.max_retries}")
        if self.retry_delay < 0:
            raise ValueError(
                f"retry_delay must be non-negative, got {self.retry_delay}"
            )

    def _validate_ml_parameters(self):
        if self.ml_min_samples < 50:
            raise ValueError(
                f"ml_min_samples must be at least 50, got {self.ml_min_samples}"
            )
        if self.ml_retrain_hours < 1:
            raise ValueError(
                f"ml_retrain_hours must be at least 1, got {self.ml_retrain_hours}"
            )
        if self.max_concurrent_assets < 1:
            raise ValueError(
                f"max_concurrent_assets must be at least 1, got {self.max_concurrent_assets}"
            )

    @classmethod
    def from_yaml(cls, file_path: str = "config.yaml"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)
            instance = cls(**config_dict)
            logging.info(f"✅ Configuration loaded from {file_path}")
            return instance
        except FileNotFoundError:
            logging.warning(
                f"Config file {file_path} not found, creating default configuration"
            )
            instance = cls()
            instance.save_to_yaml(file_path)
            return instance
        except yaml.YAMLError as e:
            logging.error(f"YAML parsing error in {file_path}: {e}")
            return cls()
        except Exception as e:
            logging.error(f"Error loading config from {file_path}: {e}")
            return cls()

    def save_to_yaml(self, file_path: str = "config.yaml"):
        try:
            config_dict = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2, sort_keys=True)
            logging.info(f"✅ Configuration saved to {file_path}")
        except Exception as e:
            logging.error(f"Error saving config to {file_path}: {e}")
