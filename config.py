import os
from dotenv import load_dotenv

load_dotenv()

ETF_LIST = {
    "Global X Nasdaq 100 Covered Call": "QYLD",
    "Schwab US Dividend Equity": "SCHD",
    "YieldMax S&P 500 Covered Call": "SDTY",
}

ANALYSIS_CONFIG = {
    "MA_SHORT": 20,
    "MA_LONG": 60,
    "RSI_PERIOD": 14,
    "RSI_OVERBUY": 70,
    "RSI_OVERSELL": 30,
    "MACD_FAST": 12,
    "MACD_SLOW": 26,
    "MACD_SIGNAL": 9,
}

PROFIT_CONFIG = {
    "TARGET_PROFIT": 0.15,
    "STOP_LOSS": -0.03,
    "MIN_HOLD_DAYS": 5,
    "REBALANCE_DAYS": 30,
}

DEFAULT_PROFIT_RULE = {
    "target_profit": 0.07,
    "stop_loss": -0.04,
    "partial_take_profits": [],
    "include_dividend_in_return": True,
    "min_hold_days": 5,
}

ETF_PROFIT_RULES = {
    "QYLD": {
        "target_profit": 0.05,
        "stop_loss": -0.04,
        "partial_take_profits": [
            {"profit": 0.05, "sell_ratio": 0.30},
            {"profit": 0.08, "sell_ratio": 0.30},
        ],
        "include_dividend_in_return": True,
        "min_hold_days": 7,
    },
    "SCHD": {
        "target_profit": 0.08,
        "stop_loss": -0.05,
        "partial_take_profits": [
            {"profit": 0.08, "sell_ratio": 0.40},
            {"profit": 0.12, "sell_ratio": 0.30},
        ],
        "include_dividend_in_return": True,
        "min_hold_days": 14,
    },
    "SDTY": {
        "target_profit": 0.06,
        "stop_loss": -0.05,
        "partial_take_profits": [
            {"profit": 0.06, "sell_ratio": 0.30},
            {"profit": 0.10, "sell_ratio": 0.30},
        ],
        "include_dividend_in_return": True,
        "min_hold_days": 7,
    },
}

TRADING_CONFIG = {
    "BUY_SIGNAL_STRENGTH": 2,
    "SELL_SIGNAL_STRENGTH": 2,
    "CASH_RESERVE_RATIO": 0.12,
    "MOMENTUM_3M_BUY_THRESHOLD": 2.0,
    "MOMENTUM_3M_SELL_THRESHOLD": -5.0,
    "TRADING_HOURS_START": "09:00",
    "TRADING_HOURS_END": "16:00",
}

NOTIFICATION_CONFIG = {
    "SEND_EMAIL": False,
    "EMAIL_ADDRESS": os.getenv("EMAIL_ADDRESS", ""),
    "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", ""),
    "SEND_DISCORD": False,
    "DISCORD_WEBHOOK": os.getenv("DISCORD_WEBHOOK", ""),
    "SEND_TELEGRAM": True,
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
}

SCHEDULE_CONFIG = {
    "CHECK_INTERVAL_MINUTES": 60,
    "RUN_TIME": "14:33",
}

DATA_PATH = "./data"
LOG_PATH = "./logs"
