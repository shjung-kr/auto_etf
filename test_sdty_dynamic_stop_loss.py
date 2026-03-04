#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""동적 손절률 적용 테스트"""

import sys
import io

# Windows 콘솔 UTF-8 인코딩
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from trading_signals import TradingSignalGenerator
from config import PROFIT_CONFIG

# 테스트 시나리오: SDTY -5.5% 손실
signal_data = {
    'symbol': 'SDTY',
    'signal': 'SELL',
    'current_price': 42.45,
    'dynamic_stop_loss': -0.0647  # -6.47% (배당금 반영)
}

portfolio_summary = {
    'total_cash': 1777.15,
    'assets': [
        {
            'symbol': 'SDTY',
            'total_quantity': 236,
            'total_invested': 10601.12,  # avg_price = 10601.12 / 236 = 44.92
            'name': '일드맥스 S&P500 커버드콜'
        }
    ]
}

gen = TradingSignalGenerator()

print('='*70)
print('동적 손절률 적용 테스트 - SDTY 매도 로직')
print('='*70)
print()

# 포트폴리오에서 SDTY 찾기
current_holding = None
for asset in portfolio_summary['assets']:
    if asset['symbol'] == 'SDTY':
        current_holding = asset
        break

if current_holding:
    total_quantity = current_holding['total_quantity']
    avg_price = current_holding['total_invested'] / total_quantity
    current_returns = ((signal_data['current_price'] - avg_price) / avg_price) * 100
    
    print(f"보유 자산: {current_holding['name']}")
    print(f"보유 수량: {total_quantity}주")
    print(f"매입가: ${avg_price:.2f}")
    print(f"현재가: ${signal_data['current_price']:.2f}")
    print(f"현재 수익률: {current_returns:.2f}%")
    print()
    
    # 동적 손절률 적용
    trade_suggestion = gen.calculate_trade_suggestion(
        signal_data,
        portfolio_summary,
        signal_data['current_price']
    )
    
    print(f"추천 액션: {trade_suggestion['description']}")
    print(f"매도 수량: {trade_suggestion['quantity']}주")
    print()
    
    print("설명:")
    print(f"  - 기본 손절률: {PROFIT_CONFIG['STOP_LOSS']*100:.2f}%")
    print(f"  - 동적 손절률: {signal_data['dynamic_stop_loss']*100:.2f}% (배당금 반영)")
    print(f"  - 현재 수익률: {current_returns:.2f}%")
    print()
    
    if current_returns <= signal_data['dynamic_stop_loss'] * 100:
        print(f"결과: 손절 조건 충족 → 전량 매도")
    elif current_returns > signal_data['dynamic_stop_loss'] * 100:
        print(f"결과: 동적 손절률 범위 내 → 매도 보류")
    print()

print('='*70)
