import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import ETF_LIST, SCHEDULE_CONFIG, DATA_PATH, LOG_PATH
from etf_analyzer import ETFAnalyzer
from trading_signals import TradingSignalGenerator
from notification_manager import NotificationManager
from portfolio_manager import PortfolioManager
from dividend_tracker import DividendTracker

# 로깅 설정
os.makedirs(LOG_PATH, exist_ok=True)
os.makedirs(DATA_PATH, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOG_PATH}/etf_trader_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Windows 콘솔 이모지 인코딩 문제 해결
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logger = logging.getLogger(__name__)


class ETFAutoTrader:
    """ETF 자동 거래 프로그램"""
    
    def __init__(self):
        self.analyzer = ETFAnalyzer()
        self.signal_generator = TradingSignalGenerator()
        self.notifier = NotificationManager()
        self.portfolio = PortfolioManager()
        self.dividend_tracker = DividendTracker()
        self.scheduler = BackgroundScheduler()
        logger.info("ETF Auto Trader 초기화 완료")
    
    def analyze_and_trade(self):
        """
        모든 ETF 분석 및 거래 신호 생성
        """
        logger.info("="*60)
        logger.info("ETF 분석 시작")
        logger.info("="*60)
        
        # 포트폴리오 요약 사전 로드
        portfolio_summary = self.portfolio.get_portfolio_summary()
        portfolio_assets_map = {asset['symbol']: asset for asset in portfolio_summary["assets"]}
        
        for etf_name, symbol in ETF_LIST.items():
            try:
                logger.info(f"\n분석 중: {etf_name} ({symbol})")
                
                # 1. ETF 데이터 분석
                analysis = self.analyzer.analyze_etf(symbol)
                
                if analysis is None:
                    logger.warning(f"{symbol} 분석 실패")
                    continue
                
                # 2. 거래 신호 생성
                signal = self.signal_generator.generate_signal(analysis)
                
                # 2.5. 동적 손절률 계산 (배당금 고려)
                etf_asset = portfolio_assets_map.get(symbol)
                dynamic_stop_loss = self.signal_generator.calculate_dynamic_stop_loss(symbol, etf_asset)
                signal['dynamic_stop_loss'] = dynamic_stop_loss  # signal에 동적 손절률 추가
                logger.info(f"   손절률: {dynamic_stop_loss*100:.2f}% (기본 -3% → 배당금 반영 {dynamic_stop_loss*100:.2f}%)")
                
                # 3. 현재가 및 매수/매도 수량 계산용
                current_price = signal['current_price']
                
                # 4. 매수/매도 추천 수량 계산
                trade_suggestion = self.signal_generator.calculate_trade_suggestion(
                    signal, 
                    portfolio_summary,
                    current_price
                )
                
                # 5. 신호별 액션
                if signal['signal'] == 'BUY':
                    logger.info(f"📈 매수 신호: {etf_name}")
                    if trade_suggestion['quantity'] > 0:
                        logger.info(f"   추천: {trade_suggestion['quantity']}주 매수 (${trade_suggestion['total_investment']:,.0f})")
                    self.notifier.send_all_notifications(signal, trade_suggestion)
                    
                elif signal['signal'] == 'SELL':
                    logger.info(f"📉 매도 신호: {etf_name}")
                    if trade_suggestion['quantity'] > 0:
                        logger.info(f"   추천: {trade_suggestion['quantity']}주 매도 (${trade_suggestion['total_investment']:,.0f})")
                    self.notifier.send_all_notifications(signal, trade_suggestion)
                
                else:
                    logger.info(f"⏸️  보유 신호: {etf_name}")
                    self.notifier.send_all_notifications(signal, trade_suggestion)
                
                # 6. 현재 포지션 체크
                if etf_name in self.signal_generator.portfolio:
                    returns = analysis['returns']
                    current_price = returns['current_price']
                    
                    position_status = self.signal_generator.get_position_status(symbol, current_price)
                    if position_status:
                        logger.info(f"포지션 수익률: {position_status['returns_pct']}%")
                
                # 7. 배당금 계산 및 알림
                etf_asset = portfolio_assets_map.get(symbol)
                
                if etf_asset and etf_asset['total_quantity'] > 0:
                    quantity = etf_asset['total_quantity']
                    current_price = analysis['returns']['current_price']
                    
                    # 배당금 계산
                    dividend_info = self.dividend_tracker.calculate_dividend(symbol, quantity, current_price)
                    
                    # 배당금 지급 확인 (매달 한 번)
                    if self.dividend_tracker.should_pay_dividend(symbol):
                        monthly_dividend = dividend_info['monthly_dividend']
                        dividend_message = self.dividend_tracker.create_dividend_message(symbol, dividend_info)
                        logger.info(f"\n💵 {etf_name} 배당금 알림:\n{dividend_message}")
                        self.notifier.send_dividend_notification(dividend_message)
                        
                        # 배당금 지급 기록
                        self.dividend_tracker.record_dividend_payment(symbol, monthly_dividend)
                        
                        # 현금 잔고에 배당금 추가
                        self.portfolio.add_cash(monthly_dividend)
                        logger.info(f"💰 {etf_name} 배당금 ${monthly_dividend:,.2f} 현금에 추가됨")
                
            except Exception as e:
                logger.error(f"{etf_name} 분석 중 오류: {str(e)}", exc_info=True)
        
        # 5. 요약 보고
        self.print_summary()
    
    def print_summary(self):
        """분석 요약 출력"""
        logger.info("\n" + "="*70)
        logger.info("분석 요약")
        logger.info("="*70)
        
        signals = self.signal_generator.get_all_signals()
        
        buy_count = sum(1 for s in signals.values() if s['signal'] == 'BUY')
        sell_count = sum(1 for s in signals.values() if s['signal'] == 'SELL')
        hold_count = len(signals) - buy_count - sell_count
        
        logger.info(f"📈 매수 신호: {buy_count}개")
        logger.info(f"📉 매도 신호: {sell_count}개")
        logger.info(f"⏸️  보유 신호: {hold_count}개")
        
        # 포트폴리오 성과
        portfolio_returns = self.signal_generator.calculate_portfolio_returns()
        if portfolio_returns['total_trades'] > 0:
            logger.info(f"\n포트폴리오 성과:")
            logger.info(f"  총 거래: {portfolio_returns['total_trades']}회")
            logger.info(f"  총 수익: {portfolio_returns['total_profit']}")
            logger.info(f"  승률: {portfolio_returns['win_rate']}%")
            logger.info(f"  평균 수익: {portfolio_returns['avg_profit_per_trade']}")
        
        # 포트폴리오 현황
        logger.info("\n" + "-"*70)
        logger.info("📊 포트폴리오 현황")
        logger.info("-"*70)
        
        summary = self.portfolio.get_portfolio_summary()
        
        if summary["total_cash"] > 0:
            logger.info(f"💰 현금: ${summary['total_cash']:,.2f}")
        
        if summary["assets"]:
            logger.info("")
            for asset in summary["assets"]:
                logger.info(f"  {asset['symbol']:6s}: {asset['total_quantity']:>4.0f}주 @ ${asset['total_invested']:>12,.2f}")
        
        logger.info(f"\n총 투자액: ${summary['total_invested']:,.2f}")
        logger.info(f"현금 잔고: ${summary['total_cash']:,.2f}")
        logger.info(f"총 자산액: ${summary['total_value']:,.2f}")
        
        # 월간 배당금 예상액 계산
        logger.info("\n" + "-"*70)
        logger.info("💵 배당금 예상액")
        logger.info("-"*70)
        
        total_monthly_dividend = 0
        total_annual_dividend = 0
        
        for asset in summary["assets"]:
            symbol = asset['symbol']
            quantity = asset['total_quantity']
            from_etf_list = [k for k, v in ETF_LIST.items() if v == symbol]
            
            if from_etf_list:
                etf_name = from_etf_list[0]
                # 현재 가격으로 배당금 계산
                try:
                    analysis = self.analyzer.analyze_etf(symbol)
                    if analysis:
                        current_price = analysis['returns']['current_price']
                        dividend_info = self.dividend_tracker.calculate_dividend(symbol, quantity, current_price)
                        monthly = dividend_info['monthly_dividend']
                        annual = dividend_info['annual_dividend']
                        
                        total_monthly_dividend += monthly
                        total_annual_dividend += annual
                        
                        logger.info(f"  {etf_name:6s}: 월 ${monthly:>10,.2f} / 연 ${annual:>10,.2f}")
                except Exception as e:
                    logger.debug(f"배당금 계산 오류 ({symbol}): {str(e)}")
        
        logger.info("-"*70)
        logger.info(f"  합계: 월 ${total_monthly_dividend:>10,.2f} / 연 ${total_annual_dividend:>10,.2f}")
        
        # 동적 손절률 정보 표시
        logger.info("\n" + "-"*70)
        logger.info("📊 동적 손절률 (배당금 반영)")
        logger.info("-"*70)
        
        for asset in summary["assets"]:
            symbol = asset['symbol']
            dynamic_stop_loss = self.signal_generator.calculate_dynamic_stop_loss(symbol, asset)
            
            # 기본 손절률과 비교
            from config import PROFIT_CONFIG
            base_stop_loss = PROFIT_CONFIG['STOP_LOSS']
            improvement = (dynamic_stop_loss - base_stop_loss) * 100
            
            logger.info(f"  {symbol:6s}: {dynamic_stop_loss*100:>6.2f}% (기본 {base_stop_loss*100:.1f}% → {improvement:+.2f}%)")
        
        logger.info("="*70 + "\n")
    
    def start_scheduler(self):
        """자동 스케줄 시작"""
        run_time = SCHEDULE_CONFIG['RUN_TIME']
        
        # 매일 지정된 시간에 실행
        self.scheduler.add_job(
            self.analyze_and_trade,
            CronTrigger(hour=int(run_time.split(':')[0]), minute=int(run_time.split(':')[1]), timezone=pytz.timezone('Asia/Seoul')),
            id='etf_analysis_job',
            name='ETF Analysis Job',
            replace_existing=True
        )
        
        # 스케줄러 시작
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info(f"✅ 스케줄러 시작 - 매일 {run_time}에 실행")
    
    def stop_scheduler(self):
        """스케줄러 중지"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("❌ 스케줄러 중지")
    
    def run_once(self):
        """한 번만 실행 (테스트용)"""
        self.analyze_and_trade()
    
    def interactive_mode(self):
        """대화형 모드"""
        while True:
            print("\n" + "="*60)
            print("ETF 자동 거래 프로그램")
            print("="*60)
            print("1. 한 번 분석 실행")
            print("2. 자동 스케줄 시작")
            print("3. 포트폴리오 상태")
            print("4. 거래 이력 조회")
            print("5. 종료")
            
            choice = input("\n선택: ").strip()
            
            if choice == '1':
                self.run_once()
            
            elif choice == '2':
                self.start_scheduler()
                print("스케줄러가 시작되었습니다. (Ctrl+C로 중지)")
                try:
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.stop_scheduler()
                    print("스케줄러가 중지되었습니다.")
            
            elif choice == '3':
                # 자산 포트폴리오 정보 표시
                print("\n" + "="*70)
                print("📊 자산 포트폴리오 현황")
                print("="*70)
                
                summary = self.portfolio.get_portfolio_summary()
                
                # 현금 표시
                if summary["total_cash"] > 0:
                    print(f"\n💰 현금 (현재): ${summary['total_cash']:,.2f}")
                else:
                    print(f"\n💰 현금 (현재): $0.00")
                
                # ETF 자산 표시
                if summary["assets"]:
                    print(f"\n📈 ETF 투자 자산:")
                    for asset in summary["assets"]:
                        print(f"\n  {asset['symbol']} - {asset['name']}")
                        print(f"    수량: {asset['total_quantity']}주")
                        print(f"    투자액: ${asset['total_invested']:,.2f}")
                        print(f"    평균 매입가: ${asset['total_invested']/asset['total_quantity']:,.2f}")
                else:
                    print("\n📈 ETF 투자 자산이 없습니다.")
                
                # 총 자산액
                print(f"\n" + "-"*70)
                print(f"총 투자액: ${summary['total_invested']:,.2f}")
                print(f"현금 잔고: ${summary['total_cash']:,.2f}")
                print(f"총 자산액: ${summary['total_value']:,.2f}")
                print("="*70)
            
            elif choice == '4':
                history = self.signal_generator.get_trading_history()
                if history:
                    print("\n📈 거래 이력:")
                    for trade in history[-10:]:  # 최근 10개
                        print(f"\n{trade['symbol']}:")
                        print(f"  진입: {trade['entry_price']} ({trade['entry_date'].strftime('%Y-%m-%d')})")
                        print(f"  청산: {trade['exit_price']} ({trade['exit_date'].strftime('%Y-%m-%d')})")
                        print(f"  수익: {trade['returns_pct']}% ({trade['profit']})")
                else:
                    print("거래 이력이 없습니다.")
            
            elif choice == '5':
                print("프로그램을 종료합니다.")
                break
            
            else:
                print("잘못된 선택입니다.")


def main():
    """메인 함수"""
    print("\n🚀 ETF 자동 거래 프로그램 시작\n")
    
    trader = ETFAutoTrader()
    
    # 대화형 모드 실행
    try:
        trader.interactive_mode()
    except EOFError:
        logger.info("Non-interactive environment detected. Running one analysis cycle.")
        trader.run_once()
    except KeyboardInterrupt:
        print("\n\n프로그램을 종료합니다.")
        trader.stop_scheduler()


if __name__ == "__main__":
    main()
