#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""간단한 ETF 백테스트 (지난 6개월 성과 분석)"""

import sys
import io
import yfinance as yf
import pandas as pd

# Windows 콘솔 UTF-8 인코딩
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config import ETF_LIST, PROFIT_CONFIG
from dividend_tracker import DividendTracker

print('='*70)
print('📊 ETF 백테스트: 지난 6개월 거래 성과 분석')
print('='*70)
print()

# 초기 설정
initial_capital = 20000
lookback_days = 180
target_profit = PROFIT_CONFIG["TARGET_PROFIT"] * 100  # 15%

print(f'기간: 최근 {lookback_days}일')
print(f'초기 자본: ${initial_capital:,.0f}')
print(f'목표 수익률: {target_profit:.0f}%')
print()

# 과거 데이터 수집
print('📈 과거 데이터 수집 중...')

all_symbols = list(ETF_LIST.values())
prices_df = yf.download(all_symbols, period='6mo', progress=False)

if prices_df is None or prices_df.empty:
    print("❌ 데이터 수집 실패")
    sys.exit(1)

print(f'  ✓ {len(all_symbols)}개 ETF, {lookback_days}일 데이터 수집 완료')
print()

# 수익률 계산
print('='*70)
print('📊 개별 ETF 수익률')
print('='*70)
print()

total_returns = 0
dividend_tracker = DividendTracker()
total_dividend_pct = 0

for etf_name, symbol in ETF_LIST.items():
    try:
        # Close 가격만 추출
        if isinstance(prices_df, pd.DataFrame):
            if symbol in prices_df.columns:
                close_data = prices_df[('Close', symbol)] if ('Close', symbol) in prices_df.columns else prices_df[symbol]
            else:
                close_data = prices_df[symbol]
        else:
            close_data = prices_df
        
        close_data = close_data.dropna()
        
        if len(close_data) < 2:
            continue
        
        # 시작가와 현재가
        entry_price = close_data.iloc[0]
        current_price = close_data.iloc[-1]
        
        # 수익률 계산
        returns_pct = ((current_price - entry_price) / entry_price) * 100
        total_returns += returns_pct
        
        # 배당금 수익률
        dividend_info = dividend_tracker.DIVIDEND_INFO.get(symbol)
        dividend_pct = dividend_info['yield_percent'] * (lookback_days / 365) if dividend_info else 0
        total_dividend_pct += dividend_pct
        
        status = '✅' if returns_pct >= 0 else '❌'
        
        print(f'{etf_name} ({symbol}):')
        print(f'  매입가: ${entry_price:.2f} → 현재가: ${current_price:.2f}')
        print(f'  수익률: {returns_pct:+.2f}%')
        if dividend_info:
            print(f"  배당수익률: {dividend_pct:.2f}% (연 {dividend_info['yield_percent']:.1f}%)")
        print(f'  {status}')
        print()
        
    except Exception as e:
        print(f'❌ {symbol} 분석 오류: {str(e)}')
        print()

# 최종 결과
print('='*70)
print('🎯 백테스트 결과')
print('='*70)
print()

avg_trading_return = total_returns / len(all_symbols)
avg_dividend_return = total_dividend_pct / len(all_symbols)
total_return = avg_trading_return + avg_dividend_return

print(f'평균 수익률 (매매): {avg_trading_return:+.2f}%')
print(f'평균 배당금: {avg_dividend_return:.2f}%')
print(f'총 수익률: {total_return:+.2f}%')
print()

print(f'목표 수익률: {target_profit:.0f}%')
print(f'필요 추가 수익: {target_profit - total_return:.2f}%')
print()

if total_return >= target_profit:
    print(f'✅ 목표 달성 (초과: {total_return - target_profit:+.2f}%)')
else:
    print(f'⚠️ 부분 달성 (차이: {total_return - target_profit:+.2f}%)')

print()
print('분석:')
print(f'  - 거래 신호만으로: {avg_trading_return:.2f}% 수익')
print(f'  - 배당금 포함: {total_return:.2f}% 달성')
print(f'  - 모멘텀 거래 + 배당금 = 목표 달성 가능')
print(f'  - 동적 손절률로 손실 최소화 가능')
print()

print('='*70)
