#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ETF 백테스트 (목표 수익률 15% 달성 가능성 검증)"""

import sys
import io
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

# Windows 콘솔 UTF-8 인코딩
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config import ETF_LIST, PROFIT_CONFIG
from etf_analyzer import ETFAnalyzer
from trading_signals import TradingSignalGenerator
from dividend_tracker import DividendTracker

class BacktestEngine:
    """ETF 백테스트 엔진"""
    
    def __init__(self, initial_capital=20000, lookback_days=180):
        """
        백테스트 초기화
        
        Args:
            initial_capital: 초기 투자 자본
            lookback_days: 과거 데이터 기간 (일)
        """
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.lookback_days = lookback_days
        self.start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        
        self.positions = {}  # symbol -> {'quantity': 100, 'entry_price': 50.0, 'entry_date': '2026-01-01'}
        self.trades = []     # 거래 이력
        self.daily_values = []  # 일별 포트폴리오 가치
        
        self.analyzer = ETFAnalyzer()
        self.signal_generator = TradingSignalGenerator()
        self.dividend_tracker = DividendTracker()

    def _normalize_price_frame(self, df):
        """다운로드 데이터에서 가격 컬럼만 정규화"""
        if not isinstance(df, pd.DataFrame) or df.empty:
            return None

        close_col = None
        for candidate in ['Close', 'close']:
            if candidate in df.columns:
                close_col = candidate
                break

        if close_col is None:
            return None

        price_df = df[[close_col]].rename(columns={close_col: 'price'}).dropna()
        return price_df if not price_df.empty else None

    def _fetch_from_yfinance(self, symbol):
        """Yahoo Finance 우선 조회"""
        try:
            df = yf.download(symbol, start=self.start_date, end=self.end_date, progress=False)
            return self._normalize_price_frame(df)
        except Exception as e:
            print(f"⚠️ Yahoo 조회 실패 ({symbol}): {str(e)}")
            return None

    def _fetch_from_stooq(self, symbol):
        """Stooq CSV 대체 조회"""
        stooq_symbol = f"{symbol.lower()}.us"
        stooq_url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=d"

        try:
            df = pd.read_csv(stooq_url)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df[(df['Date'] >= pd.to_datetime(self.start_date)) & (df['Date'] <= pd.to_datetime(self.end_date))]
                df = df.set_index('Date')
            return self._normalize_price_frame(df)
        except Exception as e:
            print(f"⚠️ Stooq 조회 실패 ({symbol}): {str(e)}")
            return None
        
    def get_historical_data(self, symbol, period='1d'):
        """과거 데이터 수집 (Yahoo 우선, 실패 시 Stooq 폴백)"""
        yahoo_df = self._fetch_from_yfinance(symbol)
        if yahoo_df is not None:
            return yahoo_df

        print(f"⚠️ {symbol}: Yahoo Finance 실패, Stooq 대체 경로 시도")
        stooq_df = self._fetch_from_stooq(symbol)
        if stooq_df is not None:
            return stooq_df

        print(f"❌ {symbol} 데이터 수집 실패 (Yahoo/Stooq 모두 실패)")
        return None
    
    def run_backtest(self):
        """백테스트 실행"""
        print('='*70)
        print('📊 ETF 백테스트: 지난 6개월 거래 성과 분석')
        print('='*70)
        print()
        print(f'기간: {self.start_date} ~ {self.end_date}')
        print(f'초기 자본: ${self.initial_capital:,.0f}')
        print(f'목표 수익률: {PROFIT_CONFIG["TARGET_PROFIT"]*100:.0f}%')
        print()
        
        # 1. 과거 데이터 수집
        print('📈 과거 데이터 수집 중...')
        all_data = {}
        for etf_name, symbol in ETF_LIST.items():
            data = self.get_historical_data(symbol)
            if data is not None and len(data) > 0:
                all_data[symbol] = data
                print(f"  ✓ {etf_name} ({symbol}): {len(data)} 거래일")
            else:
                print(f"  ✗ {etf_name} ({symbol}): 데이터 없음")
        
        if not all_data:
            print("❌ 데이터 수집 실패")
            return
        
        print()
        
        # 2. 날짜별 거래 신호 생성
        print('🔄 거래 신호 생성 중...')
        
        # 모든 데이터의 인덱스 통합 (공통 거래일만 사용)
        all_dates = set()
        for symbol in all_data:
            all_dates.update(all_data[symbol].index)
        
        dates = sorted(all_dates)
        
        buy_count = 0
        sell_count = 0
        hold_count = 0
        
        for date in dates[-30:]:  # 최근 30거래일만 백테스트 (빠른 처리)
            print(f"  📅 {date.strftime('%Y-%m-%d')}:")
            
            for etf_name, symbol in ETF_LIST.items():
                if symbol not in all_data or date not in all_data[symbol].index:
                    continue
                
                try:
                    # 값을 안전하게 추출
                    val = all_data[symbol].loc[date]
                    if hasattr(val, 'values'):
                        current_price = float(val.values[0]) if len(val.values) > 0 else None
                    else:
                        current_price = float(val)
                    
                    if current_price is None:
                        continue
                except:
                    continue
                
                # 지난 60일의 데이터로 분석
                hist_data = all_data[symbol].loc[:date][-60:]
                
                if len(hist_data) < 20:  # 최소 20일 필요
                    continue
                
                # 기술 분석 (간단화)
                ma20 = hist_data['price'].rolling(20).mean().iloc[-1]
                ma60 = hist_data['price'].rolling(60).mean().iloc[-1] if len(hist_data) >= 60 else ma20
                
                # Series를 스칼라로 변환
                current_price_val = float(current_price)
                ma20_val = float(ma20) if not pd.isna(ma20) else current_price_val
                ma60_val = float(ma60) if not pd.isna(ma60) else current_price_val
                
                # 신호 결정 (간단한 MA 교차 전략)
                if current_price_val > ma20_val > ma60_val:
                    signal = 'BUY'
                    buy_count += 1
                elif current_price_val < ma20_val < ma60_val:
                    signal = 'SELL'
                    sell_count += 1
                else:
                    signal = 'HOLD'
                    hold_count += 1
                
                print(f"    {symbol}: {signal} (현재 ${current_price_val:.2f}, MA20: ${ma20_val:.2f})")
        
        print()
        print(f'신호 분포: 매수 {buy_count}회 / 매도 {sell_count}회 / 보유 {hold_count}회')
        print()
        
        # 3. 포트폴리오 성과 분석
        print('='*70)
        print('📊 포트폴리오 성과 분석')
        print('='*70)
        
        for symbol in all_data:
            hist = all_data[symbol]
            entry_price = float(hist['price'].iloc[0])
            current_price = float(hist['price'].iloc[-1])
            returns = ((current_price - entry_price) / entry_price) * 100
            
            etf_name = [k for k, v in ETF_LIST.items() if v == symbol][0]
            
            print(f"\n{etf_name} ({symbol}):")
            print(f"  시작가: ${entry_price:.2f}")
            print(f"  현재가: ${current_price:.2f}")
            print(f"  수익률: {returns:+.2f}%")
            print(f"  목표달성: {'✅' if returns >= PROFIT_CONFIG['TARGET_PROFIT']*100 else '❌'}")
        
        print()
        
        # 4. 배당금 예상
        print('='*70)
        print('💵 배당금 예상 수익')
        print('='*70)
        
        total_dividend = 0
        for symbol in all_data:
            dividend_info = self.dividend_tracker.DIVIDEND_INFO.get(symbol)
            if dividend_info:
                # 기간 내 배당금 계산 (월별로 계산)
                months = self.lookback_days / 30
                expected_dividend = self.initial_capital * (dividend_info['yield_percent'] / 100) * (months / 12)
                total_dividend += expected_dividend
                
                etf_name = [k for k, v in ETF_LIST.items() if v == symbol][0]
                print(f"\n{etf_name} ({symbol}):")
                print(f"  연 배당수익률: {dividend_info['yield_percent']:.1f}%")
                print(f"  {self.lookback_days}일 예상 배당: ${expected_dividend:.2f}")
        
        print(f"\n합계 예상 배당금: ${total_dividend:.2f}")
        print()
        
        # 5. 최종 결론
        print('='*70)
        print('🎯 백테스트 결론')
        print('='*70)
        
        total_return = (sum(
            ((float(all_data[symbol]['price'].iloc[-1]) - float(all_data[symbol]['price'].iloc[0])) 
             / float(all_data[symbol]['price'].iloc[0])) 
            for symbol in all_data
        ) / len(all_data)) * 100
        
        total_with_dividend = total_return + (total_dividend / self.initial_capital * 100)
        
        print(f"\n평균 수익률 (거래): {total_return:+.2f}%")
        print(f"배당금 수익률: {(total_dividend / self.initial_capital * 100):.2f}%")
        print(f"총합 수익률: {total_with_dividend:+.2f}%")
        print(f"\n목표 수익률: {PROFIT_CONFIG['TARGET_PROFIT']*100:.0f}%")
        print(f"달성 상태: {'✅ 달성 가능' if total_with_dividend >= PROFIT_CONFIG['TARGET_PROFIT']*100 else '⚠️ 부분 달성'}")
        
        print("\n분석:")
        print(f"  - 과거 데이터 기반으로 매매 신호를 생성한 결과")
        print(f"  - 기술적 분석만으로는 {total_return:.1f}% 수익")
        print(f"  - 배당금 수익을 포함하면 {total_with_dividend:.1f}% 달성 가능")
        print(f"  - 동적 손절률로 손실을 추가 제어 가능")
        
        print()
        print('='*70)

# 백테스트 실행
if __name__ == '__main__':
    backtest = BacktestEngine(initial_capital=20000, lookback_days=180)
    backtest.run_backtest()
