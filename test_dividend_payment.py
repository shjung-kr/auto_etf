#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""배당금 지급 및 현금 증가 테스트"""

import json
import sys
import io

# Windows 콘솔 UTF-8 인코딩
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from portfolio_manager import PortfolioManager
from dividend_tracker import DividendTracker

# 1. 초기 포트폴리오 상태 확인
print("\n" + "="*70)
print("배당금 지급 및 현금 증가 테스트")
print("="*70)

portfolio = PortfolioManager()
summary = portfolio.get_portfolio_summary()

print("\n📊 초기 상태:")
print(f"  현금: ${summary['total_cash']:,.2f}")
print(f"  보유 자산:")
for asset in summary["assets"]:
    print(f"    - {asset['symbol']}: {asset['total_quantity']:.0f}주 (${asset['total_invested']:,.2f})")

# 2. 배당금 계산
print("\n" + "-"*70)
print("💵 배당금 계산 결과")
print("-"*70)

dividend_tracker = DividendTracker()
total_monthly = 0
total_annual = 0

for asset in summary["assets"]:
    symbol = asset['symbol']
    quantity = asset['total_quantity']
    # 현재가를 자산 정보에서 추정 (투자액/수량)
    current_price = asset['total_invested'] / quantity if quantity > 0 else 0
    
    dividend_info = dividend_tracker.calculate_dividend(symbol, quantity, current_price)
    if dividend_info:
        monthly = dividend_info['monthly_dividend']
        annual = dividend_info['annual_dividend']
        total_monthly += monthly
        total_annual += annual
        print(f"  {symbol}: 월 ${monthly:>10,.2f} / 연 ${annual:>10,.2f}")

print(f"\n  🎯 예상 배당금: 월 ${total_monthly:>10,.2f} / 연 ${total_annual:>10,.2f}")

# 3. 배당금 지급 시뮬레이션
print("\n" + "-"*70)
print("🔄 배당금 지급 시뮬레이션")
print("-"*70)

initial_cash = summary['total_cash']
portfolio.add_cash(total_monthly)
updated_summary = portfolio.get_portfolio_summary()

print(f"\n  기존 현금: ${initial_cash:,.2f}")
print(f"  배당금 추가: ${total_monthly:,.2f}")
print(f"  새로운 현금: ${updated_summary['total_cash']:,.2f}")
print(f"  증가액: ${updated_summary['total_cash'] - initial_cash:,.2f}")

# 4. 포트폴리오 파일 확인
print("\n" + "-"*70)
print("💾 포트폴리오 파일 상태")
print("-"*70)

with open('data/portfolio.json', 'r', encoding='utf-8') as f:
    portfolio_data = json.load(f)
    
cash_holdings = portfolio_data.get('CASH', {}).get('holdings', [])
total_cash_in_file = sum(h['total_invested'] for h in cash_holdings)
print(f"  파일에 저장된 현금: ${total_cash_in_file:,.2f}")

# 5. 배당금 기록 확인
print("\n" + "-"*70)
print("📋 배당금 지급 기록")
print("-"*70)

import os
if os.path.exists('data/dividends.json'):
    with open('data/dividends.json', 'r', encoding='utf-8') as f:
        dividends_data = json.load(f)

    if dividends_data:
        for symbol, data in dividends_data.items():
            payments = data.get('payments', [])
            print(f"\n  {symbol}:")
            for payment in payments:
                print(f"    - ${payment['amount']:>8,.2f} on {payment['payment_date']}")
    else:
        print("  아직 지급 기록이 없습니다.")
else:
    print("  배당금 기록 파일이 아직 생성되지 않았습니다.")
    print("  (main.py 실행 후 배당금이 지급되면 생성됩니다)")

print("\n" + "="*70)
print("✅ 테스트 완료!")
print("="*70 + "\n")
