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

# 濡쒓퉭 ?ㅼ젙
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

# Windows 肄섏넄 ?대え吏 ?몄퐫??臾몄젣 ?닿껐
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logger = logging.getLogger(__name__)


class ETFAutoTrader:
    """ETF ?먮룞 嫄곕옒 ?꾨줈洹몃옩"""
    
    def __init__(self):
        self.analyzer = ETFAnalyzer()
        self.signal_generator = TradingSignalGenerator()
        self.notifier = NotificationManager()
        self.portfolio = PortfolioManager()
        self.dividend_tracker = DividendTracker()
        self.scheduler = BackgroundScheduler()
        logger.info("ETF Auto Trader 珥덇린???꾨즺")
    
    def analyze_and_trade(self):
        """
        Run analysis for all ETFs and execute simulated fills at current price.
        """
        logger.info("=" * 60)
        logger.info("ETF analysis start")
        logger.info("=" * 60)

        for etf_name, symbol in ETF_LIST.items():
            try:
                # Always use the latest portfolio snapshot per symbol.
                portfolio_summary = self.portfolio.get_portfolio_summary()
                portfolio_assets_map = {asset['symbol']: asset for asset in portfolio_summary["assets"]}

                logger.info(f"\nAnalyzing {etf_name} ({symbol})")
                analysis = self.analyzer.analyze_etf(symbol)

                if analysis is None:
                    logger.warning(f"{symbol} analysis failed")
                    continue

                signal = self.signal_generator.generate_signal(analysis)

                etf_asset = portfolio_assets_map.get(symbol)
                dynamic_stop_loss = self.signal_generator.calculate_dynamic_stop_loss(symbol, etf_asset)
                signal['dynamic_stop_loss'] = dynamic_stop_loss

                current_price = signal['current_price']
                trade_suggestion = self.signal_generator.calculate_trade_suggestion(
                    signal,
                    portfolio_summary,
                    current_price,
                )

                if signal['signal'] == 'BUY':
                    logger.info(f"BUY signal: {etf_name}")
                    if trade_suggestion['quantity'] > 0:
                        buy_qty = trade_suggestion['quantity']
                        total_cost = buy_qty * current_price
                        self.portfolio.add_asset(symbol, etf_name, buy_qty, current_price)
                        self.portfolio.add_cash(-total_cost, f"{symbol} buy {buy_qty} shares")
                        logger.info(f"Filled BUY: {symbol} {buy_qty} @ ${current_price:.2f} (cash -${total_cost:,.2f})")
                    self.notifier.send_all_notifications(signal, trade_suggestion)

                elif signal['signal'] == 'SELL':
                    logger.info(f"SELL signal: {etf_name}")
                    if trade_suggestion['quantity'] > 0:
                        sell_qty = trade_suggestion['quantity']
                        sold_qty = self.portfolio.sell_asset_quantity(symbol, sell_qty)
                        if sold_qty > 0:
                            total_proceeds = sold_qty * current_price
                            self.portfolio.add_cash(total_proceeds, f"{symbol} sell {sold_qty} shares")
                            logger.info(f"Filled SELL: {symbol} {sold_qty} @ ${current_price:.2f} (cash +${total_proceeds:,.2f})")
                    self.notifier.send_all_notifications(signal, trade_suggestion)

                else:
                    logger.info(f"HOLD signal: {etf_name}")
                    self.notifier.send_all_notifications(signal, trade_suggestion)

                # Refresh snapshot after possible fills, then process dividends.
                portfolio_summary = self.portfolio.get_portfolio_summary()
                portfolio_assets_map = {asset['symbol']: asset for asset in portfolio_summary["assets"]}
                etf_asset = portfolio_assets_map.get(symbol)

                if etf_asset and etf_asset['total_quantity'] > 0:
                    quantity = etf_asset['total_quantity']
                    current_price = analysis['returns']['current_price']
                    dividend_info = self.dividend_tracker.calculate_dividend(symbol, quantity, current_price)

                    if self.dividend_tracker.should_pay_dividend(symbol):
                        monthly_dividend = dividend_info['monthly_dividend']
                        dividend_message = self.dividend_tracker.create_dividend_message(symbol, dividend_info)
                        logger.info(f"\nDividend notice ({etf_name}):\n{dividend_message}")
                        self.notifier.send_dividend_notification(dividend_message)

                        self.dividend_tracker.record_dividend_payment(symbol, monthly_dividend)
                        self.portfolio.add_cash(monthly_dividend, f"{symbol} dividend")
                        logger.info(f"Dividend credited: {symbol} +${monthly_dividend:,.2f} cash")

            except Exception as e:
                logger.error(f"{etf_name} error: {str(e)}", exc_info=True)

        self.print_summary()

    def print_summary(self):
        """遺꾩꽍 ?붿빟 異쒕젰"""
        logger.info("\n" + "="*70)
        logger.info("遺꾩꽍 ?붿빟")
        logger.info("="*70)
        
        signals = self.signal_generator.get_all_signals()
        
        buy_count = sum(1 for s in signals.values() if s['signal'] == 'BUY')
        sell_count = sum(1 for s in signals.values() if s['signal'] == 'SELL')
        hold_count = len(signals) - buy_count - sell_count
        
        logger.info(f"BUY signals: {buy_count}")
        logger.info(f"SELL signals: {sell_count}")
        logger.info(f"HOLD signals: {hold_count}")
        
        # ?ы듃?대━???깃낵
        portfolio_returns = self.signal_generator.calculate_portfolio_returns()
        if portfolio_returns['total_trades'] > 0:
            logger.info(f"\n?ы듃?대━???깃낵:")
            logger.info(f"  Total trades: {portfolio_returns['total_trades']}" )
            logger.info(f"  珥??섏씡: {portfolio_returns['total_profit']}")
            logger.info(f"  ?밸쪧: {portfolio_returns['win_rate']}%")
            logger.info(f"  ?됯퇏 ?섏씡: {portfolio_returns['avg_profit_per_trade']}")
        
        # ?ы듃?대━???꾪솴
        logger.info("\n" + "-"*70)
        logger.info("?뱤 ?ы듃?대━???꾪솴")
        logger.info("-"*70)
        
        summary = self.portfolio.get_portfolio_summary()
        
        if summary["total_cash"] > 0:
            logger.info(f"?뮥 ?꾧툑: ${summary['total_cash']:,.2f}")
        
        if summary["assets"]:
            logger.info("")
            for asset in summary["assets"]:
                logger.info(f"  {asset['symbol']:6s}: {asset['total_quantity']:>4.0f}二?@ ${asset['total_invested']:>12,.2f}")
        
        logger.info(f"\n珥??ъ옄?? ${summary['total_invested']:,.2f}")
        logger.info(f"?꾧툑 ?붽퀬: ${summary['total_cash']:,.2f}")
        logger.info(f"珥??먯궛?? ${summary['total_value']:,.2f}")
        
        # ?붽컙 諛곕떦湲??덉긽??怨꾩궛
        logger.info("\n" + "-"*70)
        logger.info("Dividend estimate")
        logger.info("-"*70)
        
        total_monthly_dividend = 0
        total_annual_dividend = 0
        
        for asset in summary["assets"]:
            symbol = asset['symbol']
            quantity = asset['total_quantity']
            from_etf_list = [k for k, v in ETF_LIST.items() if v == symbol]
            
            if from_etf_list:
                etf_name = from_etf_list[0]
                # ?꾩옱 媛寃⑹쑝濡?諛곕떦湲?怨꾩궛
                try:
                    analysis = self.analyzer.analyze_etf(symbol)
                    if analysis:
                        current_price = analysis['returns']['current_price']
                        dividend_info = self.dividend_tracker.calculate_dividend(symbol, quantity, current_price)
                        monthly = dividend_info['monthly_dividend']
                        annual = dividend_info['annual_dividend']
                        
                        total_monthly_dividend += monthly
                        total_annual_dividend += annual
                        
                        logger.info(f"  {etf_name:6s}: ??${monthly:>10,.2f} / ??${annual:>10,.2f}")
                except Exception as e:
                    logger.debug(f"諛곕떦湲?怨꾩궛 ?ㅻ쪟 ({symbol}): {str(e)}")
        
        logger.info("-"*70)
        logger.info(f"  ?⑷퀎: ??${total_monthly_dividend:>10,.2f} / ??${total_annual_dividend:>10,.2f}")
        
        # ?숈쟻 ?먯젅瑜??뺣낫 ?쒖떆
        logger.info("\n" + "-"*70)
        logger.info("?뱤 ?숈쟻 ?먯젅瑜?(諛곕떦湲?諛섏쁺)")
        logger.info("-"*70)
        
        for asset in summary["assets"]:
            symbol = asset['symbol']
            dynamic_stop_loss = self.signal_generator.calculate_dynamic_stop_loss(symbol, asset)
            
            # 湲곕낯 ?먯젅瑜좉낵 鍮꾧탳
            from config import PROFIT_CONFIG
            base_stop_loss = PROFIT_CONFIG['STOP_LOSS']
            improvement = (dynamic_stop_loss - base_stop_loss) * 100
            
            logger.info(f"  {symbol:6s}: {dynamic_stop_loss*100:>6.2f}% (湲곕낯 {base_stop_loss*100:.1f}% ??{improvement:+.2f}%)")
        
        logger.info("="*70 + "\n")
    
    def start_scheduler(self):
        """?먮룞 ?ㅼ?以??쒖옉"""
        run_time = SCHEDULE_CONFIG['RUN_TIME']
        
        # 留ㅼ씪 吏?뺣맂 ?쒓컙???ㅽ뻾
        self.scheduler.add_job(
            self.analyze_and_trade,
            CronTrigger(hour=int(run_time.split(':')[0]), minute=int(run_time.split(':')[1]), timezone=pytz.timezone('Asia/Seoul')),
            id='etf_analysis_job',
            name='ETF Analysis Job',
            replace_existing=True
        )
        
        # ?ㅼ?以꾨윭 ?쒖옉
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info(f"???ㅼ?以꾨윭 ?쒖옉 - 留ㅼ씪 {run_time}???ㅽ뻾")
    
    def stop_scheduler(self):
        """?ㅼ?以꾨윭 以묒?"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("???ㅼ?以꾨윭 以묒?")
    
    def run_once(self):
        """??踰덈쭔 ?ㅽ뻾 (?뚯뒪?몄슜)"""
        self.analyze_and_trade()
    
    def interactive_mode(self):
        """??뷀삎 紐⑤뱶"""
        while True:
            print("\n" + "="*60)
            print("ETF ?먮룞 嫄곕옒 ?꾨줈洹몃옩")
            print("="*60)
            print("1. ??踰?遺꾩꽍 ?ㅽ뻾")
            print("2. ?먮룞 ?ㅼ?以??쒖옉")
            print("3. ?ы듃?대━???곹깭")
            print("4. 嫄곕옒 ?대젰 議고쉶")
            print("5. 醫낅즺")
            
            choice = input("\n?좏깮: ").strip()
            
            if choice == '1':
                self.run_once()
            
            elif choice == '2':
                self.start_scheduler()
                print("?ㅼ?以꾨윭媛 ?쒖옉?섏뿀?듬땲?? (Ctrl+C濡?以묒?)")
                try:
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.stop_scheduler()
                    print("?ㅼ?以꾨윭媛 以묒??섏뿀?듬땲??")
            
            elif choice == '3':
                # ?먯궛 ?ы듃?대━???뺣낫 ?쒖떆
                print("\n" + "="*70)
                print("?뱤 ?먯궛 ?ы듃?대━???꾪솴")
                print("="*70)
                
                summary = self.portfolio.get_portfolio_summary()
                
                # ?꾧툑 ?쒖떆
                if summary["total_cash"] > 0:
                    print(f"\n?뮥 ?꾧툑 (?꾩옱): ${summary['total_cash']:,.2f}")
                else:
                    print(f"\n?뮥 ?꾧툑 (?꾩옱): $0.00")
                
                # ETF ?먯궛 ?쒖떆
                if summary["assets"]:
                    print(f"\n?뱢 ETF ?ъ옄 ?먯궛:")
                    for asset in summary["assets"]:
                        print(f"\n  {asset['symbol']} - {asset['name']}")
                        print(f"    수량: {asset['total_quantity']}주")
                        print(f"    ?ъ옄?? ${asset['total_invested']:,.2f}")
                        print(f"    ?됯퇏 留ㅼ엯媛: ${asset['total_invested']/asset['total_quantity']:,.2f}")
                else:
                    print("\n?뱢 ETF ?ъ옄 ?먯궛???놁뒿?덈떎.")
                
                # 珥??먯궛??
                print(f"\n" + "-"*70)
                print(f"珥??ъ옄?? ${summary['total_invested']:,.2f}")
                print(f"?꾧툑 ?붽퀬: ${summary['total_cash']:,.2f}")
                print(f"珥??먯궛?? ${summary['total_value']:,.2f}")
                print("="*70)
            
            elif choice == '4':
                history = self.signal_generator.get_trading_history()
                if history:
                    print("\n?뱢 嫄곕옒 ?대젰:")
                    for trade in history[-10:]:  # 理쒓렐 10媛?
                        print(f"\n{trade['symbol']}:")
                        print(f"  吏꾩엯: {trade['entry_price']} ({trade['entry_date'].strftime('%Y-%m-%d')})")
                        print(f"  泥?궛: {trade['exit_price']} ({trade['exit_date'].strftime('%Y-%m-%d')})")
                        print(f"  ?섏씡: {trade['returns_pct']}% ({trade['profit']})")
                else:
                    print("嫄곕옒 ?대젰???놁뒿?덈떎.")
            
            elif choice == '5':
                print("?꾨줈洹몃옩??醫낅즺?⑸땲??")
                break
            
            else:
                print("?섎せ???좏깮?낅땲??")


def main():
    """硫붿씤 ?⑥닔"""
    print("\n?? ETF ?먮룞 嫄곕옒 ?꾨줈洹몃옩 ?쒖옉\n")
    
    trader = ETFAutoTrader()
    
    # ??뷀삎 紐⑤뱶 ?ㅽ뻾
    try:
        trader.interactive_mode()
    except EOFError:
        logger.info("Non-interactive environment detected. Running one analysis cycle.")
        trader.run_once()
    except KeyboardInterrupt:
        print("\n\n?꾨줈洹몃옩??醫낅즺?⑸땲??")
        trader.stop_scheduler()


if __name__ == "__main__":
    main()



