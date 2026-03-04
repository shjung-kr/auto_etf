# ETF 거래 자동화 프로그램 설정
import os
from dotenv import load_dotenv

load_dotenv()

# ETF 목록 (한국 주요 ETF)
ETF_LIST = {
        "글로벌엑스 나스닥100 커버드콜": "QYLD",
        "슈왑 미국 배당주":"SCHD",
        "일드맥스 S&P500 커버드콜":"SDTY"
}

# 기술적 분석 설정
ANALYSIS_CONFIG = {
    "MA_SHORT": 20,      # 단기 이동평균선 (20일)
    "MA_LONG": 60,       # 장기 이동평균선 (60일)
    "RSI_PERIOD": 14,    # RSI 주기
    "RSI_OVERBUY": 70,   # RSI 과매수 (매도 신호)
    "RSI_OVERSELL": 30,  # RSI 과매도 (매수 신호)
    "MACD_FAST": 12,     # MACD 빠른 EMA
    "MACD_SLOW": 26,     # MACD 느린 EMA
    "MACD_SIGNAL": 9,    # MACD 신호선
}

# 수익률 설정
PROFIT_CONFIG = {
    "TARGET_PROFIT": 0.15,      # 목표 수익률 5%
    "STOP_LOSS": -0.03,         # 손절 -3%
    "MIN_HOLD_DAYS": 5,         # 최소 보유 기간 (일)
    "REBALANCE_DAYS": 30,       # 리밸런싱 주기 (일)
}

# 거래 설정
TRADING_CONFIG = {
    "BUY_SIGNAL_STRENGTH": 2,   # 매수 신호 강도 (2개 이상의 신호 필요)
    "SELL_SIGNAL_STRENGTH": 2,  # 매도 신호 강도
    "TRADING_HOURS_START": "09:00",  # 거래 시작 시간
    "TRADING_HOURS_END": "16:00",    # 거래 종료 시간
}

# 알림 설정
NOTIFICATION_CONFIG = {
    "SEND_EMAIL": False,
    "EMAIL_ADDRESS": os.getenv("EMAIL_ADDRESS", ""),
    "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", ""),
    "SEND_DISCORD": False,
    "DISCORD_WEBHOOK": os.getenv("DISCORD_WEBHOOK", ""),
    "SEND_TELEGRAM": True,
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", "8349814456:AAEsShiT4IqSpC0qLPDoCapIJHU8BSnxBv4"),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", "8594233801"),
}

# 스케줄 설정
SCHEDULE_CONFIG = {
    "CHECK_INTERVAL_MINUTES": 60,      # 60분 마다 체크
    "RUN_TIME": "09:30",               # 매일 09:30 실행
}

# 데이터 저장 경로
DATA_PATH = "./data"
LOG_PATH = "./logs"
