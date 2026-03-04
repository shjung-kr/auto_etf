import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
from config import ETF_LIST, ANALYSIS_CONFIG

logger = logging.getLogger(__name__)


class ETFAnalyzer:
    """ETF 데이터 분석 및 수익률 계산 클래스"""
    
    def __init__(self):
        self.etf_data = {}
        self.analysis_results = {}
        
    def fetch_etf_data(self, symbol, period="3mo", interval="1d"):
        """
        ETF 데이터 수집
        
        Args:
            symbol: ETF 티커 기호
            period: 조회 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, etc.)
            interval: 데이터 간격 (1m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo)
        
        Returns:
            DataFrame: OHLCV 데이터
        """
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            if data.empty:
                logger.warning(f"{symbol}에 대한 데이터를 찾을 수 없습니다.")
                return None
            
            self.etf_data[symbol] = data
            logger.info(f"{symbol} 데이터 수집 완료: {len(data)} 행")
            return data
        except Exception as e:
            logger.error(f"{symbol} 데이터 수집 실패: {str(e)}")
            return None
    
    def calculate_returns(self, symbol):
        """
        수익률 계산
        
        Args:
            symbol: ETF 티커 기호
        
        Returns:
            dict: 다양한 주기의 수익률 정보
        """
        if symbol not in self.etf_data:
            return None
        
        data = self.etf_data[symbol]
        current_price = data['Close'].iloc[-1].item() if hasattr(data['Close'].iloc[-1], 'item') else float(data['Close'].iloc[-1])
        
        returns = {
            'current_price': current_price,
            'timestamp': data.index[-1],
        }
        
        # 다양한 기간의 수익률 계산
        periods = {
            '1d': 1,
            '1w': 5,
            '1m': 20,
            '3m': 60,
        }
        
        for period_name, days in periods.items():
            if len(data) > days:
                past_price = data['Close'].iloc[-days-1].item() if hasattr(data['Close'].iloc[-days-1], 'item') else float(data['Close'].iloc[-days-1])
                ret = (current_price - past_price) / past_price * 100
                returns[f'return_{period_name}'] = round(ret, 2)
            else:
                returns[f'return_{period_name}'] = None
        
        return returns
    
    def calculate_moving_averages(self, symbol):
        """
        이동평균선 계산 (매수/매도 신호)
        
        Args:
            symbol: ETF 티커 기호
        
        Returns:
            dict: MA 정보 및 신호
        """
        if symbol not in self.etf_data:
            return None
        
        data = self.etf_data[symbol].copy()
        ma_short = ANALYSIS_CONFIG['MA_SHORT']
        ma_long = ANALYSIS_CONFIG['MA_LONG']
        
        data['MA_SHORT'] = data['Close'].rolling(window=ma_short).mean()
        data['MA_LONG'] = data['Close'].rolling(window=ma_long).mean()
        
        current_price = data['Close'].iloc[-1].item() if hasattr(data['Close'].iloc[-1], 'item') else float(data['Close'].iloc[-1])
        ma_short_val = data['MA_SHORT'].iloc[-1].item() if hasattr(data['MA_SHORT'].iloc[-1], 'item') else float(data['MA_SHORT'].iloc[-1])
        ma_long_val = data['MA_LONG'].iloc[-1].item() if hasattr(data['MA_LONG'].iloc[-1], 'item') else float(data['MA_LONG'].iloc[-1])
        
        signal = {
            'current_price': current_price,
            'ma_short': round(ma_short_val, 2) if not np.isnan(ma_short_val) else None,
            'ma_long': round(ma_long_val, 2) if not np.isnan(ma_long_val) else None,
            'signal': None
        }
        
        # 신호 생성
        if not np.isnan(ma_short_val) and not np.isnan(ma_long_val):
            if current_price > ma_short_val > ma_long_val:
                signal['signal'] = 'BUY'  # 상향 추세
            elif current_price < ma_short_val < ma_long_val:
                signal['signal'] = 'SELL'  # 하향 추세
            else:
                signal['signal'] = 'HOLD'  # 혼합
        
        return signal
    
    def calculate_rsi(self, symbol):
        """
        RSI (Relative Strength Index) 계산
        
        Args:
            symbol: ETF 티커 기호
        
        Returns:
            dict: RSI 값 및 신호
        """
        if symbol not in self.etf_data:
            return None
        
        data = self.etf_data[symbol].copy()
        period = ANALYSIS_CONFIG['RSI_PERIOD']
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1].item() if hasattr(rsi.iloc[-1], 'item') else float(rsi.iloc[-1])
        
        signal = {
            'rsi': round(current_rsi, 2) if not np.isnan(current_rsi) else None,
            'signal': None
        }
        
        # RSI 신호
        if not np.isnan(current_rsi):
            if current_rsi > ANALYSIS_CONFIG['RSI_OVERBUY']:
                signal['signal'] = 'SELL'  # 과매수
            elif current_rsi < ANALYSIS_CONFIG['RSI_OVERSELL']:
                signal['signal'] = 'BUY'   # 과매도
            else:
                signal['signal'] = 'HOLD'
        
        return signal
    
    def calculate_macd(self, symbol):
        """
        MACD (Moving Average Convergence Divergence) 계산
        
        Args:
            symbol: ETF 티커 기호
        
        Returns:
            dict: MACD 값 및 신호
        """
        if symbol not in self.etf_data:
            return None
        
        data = self.etf_data[symbol].copy()
        
        fast = ANALYSIS_CONFIG['MACD_FAST']
        slow = ANALYSIS_CONFIG['MACD_SLOW']
        signal_period = ANALYSIS_CONFIG['MACD_SIGNAL']
        
        ema_fast = data['Close'].ewm(span=fast).mean()
        ema_slow = data['Close'].ewm(span=slow).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal_period).mean()
        histogram = macd - signal_line
        
        current_macd = macd.iloc[-1].item() if hasattr(macd.iloc[-1], 'item') else float(macd.iloc[-1])
        current_signal = signal_line.iloc[-1].item() if hasattr(signal_line.iloc[-1], 'item') else float(signal_line.iloc[-1])
        current_histogram = histogram.iloc[-1].item() if hasattr(histogram.iloc[-1], 'item') else float(histogram.iloc[-1])
        
        result = {
            'macd': round(current_macd, 4) if not np.isnan(current_macd) else None,
            'signal_line': round(current_signal, 4) if not np.isnan(current_signal) else None,
            'histogram': round(current_histogram, 4) if not np.isnan(current_histogram) else None,
            'signal': None
        }
        
        # MACD 신호
        if not np.isnan(current_histogram):
            if current_macd > current_signal:
                result['signal'] = 'BUY'
            else:
                result['signal'] = 'SELL'
        
        return result
    
    def analyze_etf(self, symbol):
        """
        종합 분석 (모든 지표)
        
        Args:
            symbol: ETF 티커 기호
        
        Returns:
            dict: 종합 분석 결과
        """
        # 데이터 수집
        self.fetch_etf_data(symbol, period="3mo")
        
        if symbol not in self.etf_data:
            return None
        
        # 모든 지표 계산
        returns = self.calculate_returns(symbol)
        ma_signal = self.calculate_moving_averages(symbol)
        rsi_signal = self.calculate_rsi(symbol)
        macd_signal = self.calculate_macd(symbol)
        
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'returns': returns,
            'moving_average': ma_signal,
            'rsi': rsi_signal,
            'macd': macd_signal,
        }
        
        self.analysis_results[symbol] = analysis
        return analysis
    
    def get_all_analysis(self):
        """모든 분석 결과 반환"""
        return self.analysis_results
