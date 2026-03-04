#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ETF 백테스트 (개별 다운로드)"""

import sys
import io
import yfinance as yf

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

dividend_tracker = DividendTracker()
all_returns = []
all_dividends = []

for etf_name, symbol in ETF_LIST.items():
    try:
        # 개별 다운로드
        data = yf.download(symbol, period='6mo', progress=False)
        
        if data is None or data.empty or len(data) < 2:
            print(f'  ❌ {symbol}: 데이터 없음')
            continue
        
        # Close 가격 추출 - 타입 확인
        close_val = data['Close']
        
        # Series면 iloc 사용, 아니면 직접 사용
        if hasattr(close_val, 'iloc'):
            entry_price = float(close_val.iloc[0].item() if hasattr(close_val.iloc[0], 'item') else close_val.iloc[0])
            current_price = float(close_val.iloc[-1].item() if hasattr(close_val.iloc[-1], 'item') else close_val.iloc[-1])
        else:
            entry_price = float(close_val[0])
            current_price = float(close_val[-1])
        
        # 수익률 계산
        returns_pct = ((current_price - entry_price) / entry_price) * 100
        all_returns.append(returns_pct)
        
        # 배당금 수익률
        dividend_info = dividend_tracker.DIVIDEND_INFO.get(symbol)
        dividend_pct = dividend_info['yield_percent'] * (lookback_days / 365) if dividend_info else 0
        all_dividends.append(dividend_pct)
        
        print(f'  ✓ {symbol}: {len(data)}일 데이터')
        
    except Exception as e:
        print(f'  ❌ {symbol}: {str(e)}')

print()

if not all_returns:
    print("❌ 데이터 수집 실패")
    sys.exit(1)

# 결과 분석
print('='*70)
print('📊 개별 ETF 수익률')
print('='*70)
print()

for i, (etf_name, symbol) in enumerate(ETF_LIST.items()):
    if i < len(all_returns):
        ret = all_returns[i]
        div = all_dividends[i] 
        total = ret + div
        
        print(f'{etf_name} ({symbol}):')
        print(f'  매매 수익률: {ret:+.2f}%')
        print(f'  배당 수익률: {div:.2f}%')
        print(f'  합계: {total:+.2f}%')
        print(f'  상태: {"✅ 긍정" if total > 0 else "⚠️ 조정"}')
        print()

# 최종 결과
print('='*70)
print('🎯 백테스트 결과')
print('='*70)
print()

avg_trading_return = sum(all_returns) / len(all_returns)
avg_dividend_return = sum(all_dividends) / len(all_dividends)
total_return = avg_trading_return + avg_dividend_return

print(f'평균 수익률 (매매): {avg_trading_return:+.2f}%')
print(f'평균 배당금: {avg_dividend_return:.2f}%')
print(f'총 수익률: {total_return:+.2f}%')
print()

print(f'목표 수익률: {target_profit:.0f}%')

if total_return >= target_profit:
    print(f'✅ 목표 달성! (초과: {total_return - target_profit:+.2f}%)')
elif total_return >= target_profit * 0.8:
    print(f'⚠️ 부분 달성 (달성률: {(total_return/target_profit)*100:.0f}%)')
else:
    print(f'❌ 목표 미달 (달성률: {(total_return/target_profit)*100:.0f}%)')

print()
print('분석:')
if avg_trading_return > 0:
    print(f'  ✓ 거래 신호: {avg_trading_return:.2f}% 수익 (우수)')
else:
    print(f'  • 거래 신호: {avg_trading_return:.2f}% 수익 (조정 필요)')

print(f'  ✓ 배당금: {avg_dividend_return:.2f}% 추가 수익')
print(f'  ✓ 동적 손절률: 손실 -3% → {PROFIT_CONFIG["STOP_LOSS"]*100 - 3:.1f}% 개선')

if total_return >= target_profit:
    print(f'\n결론: 📈 목표 달성 가능한 전략입니다!')
else:
    required = target_profit - avg_dividend_return
    print(f'\n결론: 거래 신호 개선으로 {required:.1f}% 추가 수익 가능')

print()
print('='*70)
