#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""오늘 기준 ETF 분석 실행 스크립트"""

from datetime import datetime
from config import ETF_LIST
from etf_analyzer import ETFAnalyzer
from trading_signals import TradingSignalGenerator


def main():
    analyzer = ETFAnalyzer()
    signal_generator = TradingSignalGenerator()

    print('=' * 70)
    print(f"📅 오늘 기준 분석 실행: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('=' * 70)

    success_count = 0

    for etf_name, symbol in ETF_LIST.items():
        print(f"\n[{etf_name}] {symbol}")
        analysis = analyzer.analyze_etf(symbol)

        if not analysis:
            print("  ❌ 분석 실패 (외부 데이터 수집 실패 또는 데이터 없음)")
            continue

        signal = signal_generator.generate_signal(analysis)
        returns = analysis['returns']

        print(f"  현재가: {returns['current_price']:.2f}")
        print(
            f"  수익률: 1일 {returns.get('return_1d')}% | "
            f"1주 {returns.get('return_1w')}% | "
            f"1개월 {returns.get('return_1m')}% | "
            f"3개월 {returns.get('return_3m')}%"
        )
        print(
            f"  신호: {signal['signal']} "
            f"(신뢰도 {signal['confidence']:.1f}%, "
            f"BUY {signal['buy_signals']} / SELL {signal['sell_signals']})"
        )
        success_count += 1

    print("\n" + '=' * 70)
    print(f"완료: {success_count}/{len(ETF_LIST)} 종목 분석 성공")
    print('=' * 70)


if __name__ == '__main__':
    main()
