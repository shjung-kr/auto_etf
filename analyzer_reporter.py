#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 분석 및 리포트 생성 스크립트
거래 결과를 분석하고 성과 리포트를 생성합니다.
"""

import os
import csv
import json
from datetime import datetime
from pathlib import Path
from trading_signals import TradingSignalGenerator
import logging

logger = logging.getLogger(__name__)


class DataAnalyzerAndReporter:
    """데이터 분석 및 리포트 생성 클래스"""
    
    def __init__(self):
        self.signal_generator = TradingSignalGenerator()
        self.data_path = Path("data")
        self.report_path = Path("reports")
        self.data_path.mkdir(exist_ok=True)
        self.report_path.mkdir(exist_ok=True)
    
    def export_portfolio_to_csv(self, filename=None):
        """
        포트폴리오를 CSV 파일로 내보내기
        
        Args:
            filename: 파일명 (기본값: portfolio_YYYYMMDD_HHMMSS.csv)
        """
        if filename is None:
            filename = f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.data_path / filename
        
        portfolio = self.signal_generator.get_portfolio()
        
        if not portfolio:
            print("❌ 보유 포지션이 없습니다.")
            return None
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['종목', '수량', '매입가', '매입일자', '비고'])
                
                for symbol, positions in portfolio.items():
                    for position in positions:
                        writer.writerow([
                            symbol,
                            position['quantity'],
                            f"{position['entry_price']:.2f}",
                            position['entry_date'].strftime('%Y-%m-%d %H:%M:%S'),
                            position['notes']
                        ])
            
            print(f"✓ 포트폴리오 내보내기 완료: {filepath}")
            return filepath
        
        except Exception as e:
            print(f"❌ 내보내기 실패: {str(e)}")
            return None
    
    def export_trading_history_to_csv(self, filename=None):
        """
        거래 이력을 CSV 파일로 내보내기
        
        Args:
            filename: 파일명 (기본값: trading_history_YYYYMMDD_HHMMSS.csv)
        """
        if filename is None:
            filename = f"trading_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.data_path / filename
        
        history = self.signal_generator.get_trading_history()
        
        if not history:
            print("❌ 거래 이력이 없습니다.")
            return None
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['종목', '매입가', '청산가', '수량', '매입일', '청산일', '수익률', '이익'])
                
                for trade in history:
                    writer.writerow([
                        trade['symbol'],
                        f"{trade['entry_price']:.2f}",
                        f"{trade['exit_price']:.2f}",
                        trade['quantity'],
                        trade['entry_date'].strftime('%Y-%m-%d'),
                        trade['exit_date'].strftime('%Y-%m-%d'),
                        f"{trade['returns_pct']:.2f}%",
                        f"{trade['profit']:.2f}"
                    ])
            
            print(f"✓ 거래 이력 내보내기 완료: {filepath}")
            return filepath
        
        except Exception as e:
            print(f"❌ 내보내기 실패: {str(e)}")
            return None
    
    def generate_performance_report(self, filename=None):
        """
        성과 리포트 생성
        
        Args:
            filename: 파일명 (기본값: performance_report_YYYYMMDD_HHMMSS.txt)
        """
        if filename is None:
            filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filepath = self.report_path / filename
        
        history = self.signal_generator.get_trading_history()
        returns = self.signal_generator.calculate_portfolio_returns()
        
        try:
            with open(filepath, 'w', encoding='utf-8-sig') as f:
                f.write("=" * 70 + "\n")
                f.write("ETF 자동 거래 프로그램 - 성과 리포트\n")
                f.write("=" * 70 + "\n\n")
                
                f.write(f"리포트 생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 전체 성과
                f.write("📊 전체 성과\n")
                f.write("-" * 70 + "\n")
                f.write(f"총 거래 건수: {returns['total_trades']}회\n")
                f.write(f"총 이익: {returns['total_profit']:,.2f}원\n")
                f.write(f"승리 건수: {returns['winning_trades']}회\n")
                f.write(f"패배 건수: {returns['losing_trades']}회\n")
                f.write(f"승률: {returns['win_rate']:.2f}%\n")
                f.write(f"거래당 평균 이익: {returns['avg_profit_per_trade']:,.2f}원\n\n")
                
                # 거래별 상세 정보
                if history:
                    f.write("📈 거래 상세 정보 (최근 20개)\n")
                    f.write("-" * 70 + "\n")
                    
                    for i, trade in enumerate(reversed(history[-20:]), 1):
                        f.write(f"\n{i}. {trade['symbol']}\n")
                        f.write(f"   매입: {trade['entry_price']}원 ({trade['entry_date'].strftime('%Y-%m-%d')})\n")
                        f.write(f"   청산: {trade['exit_price']}원 ({trade['exit_date'].strftime('%Y-%m-%d')})\n")
                        f.write(f"   수량: {trade['quantity']}주\n")
                        f.write(f"   수익률: {trade['returns_pct']:.2f}%\n")
                        f.write(f"   이익: {trade['profit']:,.2f}원\n")
                
                f.write("\n" + "=" * 70 + "\n")
            
            print(f"✓ 성과 리포트 생성 완료: {filepath}")
            return filepath
        
        except Exception as e:
            print(f"❌ 리포트 생성 실패: {str(e)}")
            return None
    
    def generate_json_report(self, filename=None):
        """
        JSON 형식의 상세 리포트 생성
        
        Args:
            filename: 파일명 (기본값: report_YYYYMMDD_HHMMSS.json)
        """
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.data_path / filename
        
        history = [
            {
                **trade,
                'entry_date': trade['entry_date'].isoformat(),
                'exit_date': trade['exit_date'].isoformat(),
            }
            for trade in self.signal_generator.get_trading_history()
        ]
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.signal_generator.calculate_portfolio_returns(),
            'trades': history
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"✓ JSON 리포트 생성 완료: {filepath}")
            return filepath
        
        except Exception as e:
            print(f"❌ JSON 리포트 생성 실패: {str(e)}")
            return None
    
    def create_daily_summary(self):
        """일일 요약 생성"""
        timestamp = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n{'='*70}")
        print(f"📊 {timestamp} 일일 요약")
        print(f"{'='*70}\n")
        
        signals = self.signal_generator.get_all_signals()
        if signals:
            buy_count = sum(1 for s in signals.values() if s['signal'] == 'BUY')
            sell_count = sum(1 for s in signals.values() if s['signal'] == 'SELL')
            
            print(f"📈 신호 발생: {len(signals)}개")
            print(f"  - 매수: {buy_count}개")
            print(f"  - 매도: {sell_count}개\n")
        
        returns = self.signal_generator.calculate_portfolio_returns()
        if returns['total_trades'] > 0:
            print(f"💰 누적 성과:")
            print(f"  - 총 이익: {returns['total_profit']:,.2f}원")
            print(f"  - 승률: {returns['win_rate']:.2f}%")
            print(f"  - 거래: {returns['total_trades']}회\n")


def main():
    """메인 함수"""
    
    analyzer = DataAnalyzerAndReporter()
    
    print("\n" + "="*70)
    print("🔍 데이터 분석 및 리포트 생성")
    print("="*70 + "\n")
    
    print("1. 포트폴리오 CSV 내보내기")
    analyzer.export_portfolio_to_csv()
    
    print("\n2. 거래 이력 CSV 내보내기")
    analyzer.export_trading_history_to_csv()
    
    print("\n3. 성과 리포트 생성")
    analyzer.generate_performance_report()
    
    print("\n4. JSON 리포트 생성")
    analyzer.generate_json_report()
    
    print("\n5. 일일 요약")
    analyzer.create_daily_summary()
    
    print("\n" + "="*70)
    print("✅ 리포트 생성 완료")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
