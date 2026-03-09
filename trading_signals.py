import logging
from datetime import datetime
from config import TRADING_CONFIG, PROFIT_CONFIG, ANALYSIS_CONFIG
from dividend_tracker import DividendTracker

logger = logging.getLogger(__name__)


class TradingSignalGenerator:
    """Trading signal generation and position management."""
    
    def __init__(self):
        self.signals = {}
        self.portfolio = {}
        self.trading_history = []
        self.dividend_tracker = DividendTracker()
        
        # ?먯젅瑜??ㅼ젙 (諛곕떦湲?誘몃컲??湲곕낯媛?
        self.base_stop_loss = PROFIT_CONFIG['STOP_LOSS']  # -0.03 (-3%)
        
        # 諛곕떦湲??뺣낫 李몄“
        self.DIVIDEND_INFO = self.dividend_tracker.DIVIDEND_INFO
    
    def generate_signal(self, analysis_result):
        """
        遺꾩꽍 寃곌낵瑜?湲곕컲?쇰줈 嫄곕옒 ?좏샇 ?앹꽦
        
        Args:
            analysis_result: ETF 遺꾩꽍 寃곌낵 (dict)
        
        Returns:
            dict: 嫄곕옒 ?좏샇 (BUY, SELL, HOLD)
        """
        symbol = analysis_result['symbol']
        
        buy_signals = 0
        sell_signals = 0
        total_checks = 0
        
        # ?대룞?됯퇏???좏샇
        ma_signal = analysis_result['moving_average'].get('signal')
        total_checks += 1
        if ma_signal == 'BUY':
            buy_signals += 1
        elif ma_signal == 'SELL':
            sell_signals += 1
        
        # RSI ?좏샇
        rsi_signal = analysis_result['rsi'].get('signal')
        total_checks += 1
        if rsi_signal == 'BUY':
            buy_signals += 1
        elif rsi_signal == 'SELL':
            sell_signals += 1
        
        # MACD ?좏샇
        macd_signal = analysis_result['macd'].get('signal')
        total_checks += 1
        if macd_signal == 'BUY':
            buy_signals += 1
        elif macd_signal == 'SELL':
            sell_signals += 1
        
        # ?섏씡瑜?湲곕컲 ?좏샇
        returns_1m = analysis_result['returns'].get('return_1m')
        total_checks += 1
        if returns_1m is not None:
            if returns_1m < PROFIT_CONFIG['STOP_LOSS'] * 100:
                sell_signals += 1  # ?먯젅
            elif returns_1m > PROFIT_CONFIG['TARGET_PROFIT'] * 100:
                sell_signals += 1  # ?듭젅

        # 以묎린 紐⑤찘? ?꾪꽣 (異붿꽭 ??뻾 留ㅼ닔/留ㅻ룄 ?꾪솕)
        momentum_3m = analysis_result['returns'].get('return_3m')
        momentum_buy_threshold = TRADING_CONFIG.get('MOMENTUM_3M_BUY_THRESHOLD', 2.0)
        momentum_sell_threshold = TRADING_CONFIG.get('MOMENTUM_3M_SELL_THRESHOLD', -5.0)
        total_checks += 1
        if momentum_3m is not None:
            if momentum_3m >= momentum_buy_threshold:
                buy_signals += 1
            elif momentum_3m <= momentum_sell_threshold:
                sell_signals += 1
        
        # 理쒖쥌 ?좏샇 寃곗젙
        buy_signal_strength_required = TRADING_CONFIG['BUY_SIGNAL_STRENGTH']
        sell_signal_strength_required = TRADING_CONFIG.get('SELL_SIGNAL_STRENGTH', buy_signal_strength_required)
        
        if buy_signals >= buy_signal_strength_required:
            final_signal = 'BUY'
        elif sell_signals >= sell_signal_strength_required:
            final_signal = 'SELL'
        else:
            final_signal = 'HOLD'
        
        signal_data = {
            'symbol': symbol,
            'signal': final_signal,
            'timestamp': analysis_result['timestamp'],
            'current_price': analysis_result['returns']['current_price'],
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'confidence': max(buy_signals, sell_signals) / max(total_checks, 1) * 100,  # ?좊ː??
            'analysis': analysis_result
        }
        
        self.signals[symbol] = signal_data
        logger.info(f"[{symbol}] ?좏샇: {final_signal} (?좊ː?? {signal_data['confidence']:.0f}%)")
        
        return signal_data
    
    def check_profit_target(self, symbol, entry_price, current_price):
        """
        ?섏씡 紐⑺몴 ?뺤씤
        
        Args:
            symbol: ETF 湲고샇
            entry_price: 留ㅼ엯 媛寃?
            current_price: ?꾩옱 媛寃?
        
        Returns:
            dict: 紐⑺몴 ?ъ꽦 ?щ? 諛??섏씡瑜?
        """
        returns = (current_price - entry_price) / entry_price * 100
        
        result = {
            'symbol': symbol,
            'entry_price': entry_price,
            'current_price': current_price,
            'returns': round(returns, 2),
            'reached_target': returns >= PROFIT_CONFIG['TARGET_PROFIT'] * 100,
            'reached_stop_loss': returns <= PROFIT_CONFIG['STOP_LOSS'] * 100,
        }
        
        return result
    
    def add_position(self, symbol, entry_price, quantity, notes=""):
        """
        ?ъ???異붽?
        
        Args:
            symbol: ETF 湲고샇
            entry_price: 留ㅼ엯 媛寃?
            quantity: ?섎웾
            notes: 鍮꾧퀬
        """
        position = {
            'symbol': symbol,
            'entry_price': entry_price,
            'quantity': quantity,
            'entry_date': datetime.now(),
            'notes': notes
        }
        
        if symbol not in self.portfolio:
            self.portfolio[symbol] = []
        
        self.portfolio[symbol].append(position)
        logger.info(f"?ъ???異붽?: {symbol} {quantity}二?@ {entry_price} (?⑷퀎: {quantity * entry_price})")
    
    def close_position(self, symbol, exit_price, quantity=None):
        """
        ?ъ???醫낅즺
        
        Args:
            symbol: ETF 湲고샇
            exit_price: 泥?궛 媛寃?
            quantity: ?섎웾 (None?대㈃ ?꾩껜)
        """
        if symbol not in self.portfolio or not self.portfolio[symbol]:
            logger.warning(f"{symbol}??????대┛ ?ъ??섏씠 ?놁뒿?덈떎.")
            return None
        
        positions = self.portfolio[symbol]
        closed_positions = []
        
        if quantity is None:
            quantity = sum(p['quantity'] for p in positions)
        
        remaining = quantity
        while remaining > 0 and positions:
            position = positions.pop(0)
            
            close_qty = min(remaining, position['quantity'])
            returns = (exit_price - position['entry_price']) / position['entry_price'] * 100
            
            trade_record = {
                'symbol': symbol,
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'quantity': close_qty,
                'entry_date': position['entry_date'],
                'exit_date': datetime.now(),
                'returns_pct': round(returns, 2),
                'profit': round(close_qty * (exit_price - position['entry_price']), 2)
            }
            
            self.trading_history.append(trade_record)
            closed_positions.append(trade_record)
            remaining -= close_qty
            
            logger.info(f"?ъ???醫낅즺: {symbol} {close_qty}二?@ {exit_price} (?섏씡: {trade_record['returns_pct']}%)")
        
        return closed_positions
    
    def get_position_status(self, symbol, current_price):
        """
        ?ъ????곹깭 議고쉶
        
        Args:
            symbol: ETF 湲고샇
            current_price: ?꾩옱 媛寃?
        
        Returns:
            dict: ?ъ????곹깭 諛??섏씡瑜?
        """
        if symbol not in self.portfolio or not self.portfolio[symbol]:
            return None
        
        positions = self.portfolio[symbol]
        total_quantity = sum(p['quantity'] for p in positions)
        avg_entry = sum(p['entry_price'] * p['quantity'] for p in positions) / total_quantity
        
        returns = (current_price - avg_entry) / avg_entry * 100
        
        status = {
            'symbol': symbol,
            'total_quantity': total_quantity,
            'avg_entry_price': round(avg_entry, 2),
            'current_price': current_price,
            'returns_pct': round(returns, 2),
            'total_value': round(current_price * total_quantity, 2),
            'unrealized_profit': round((current_price - avg_entry) * total_quantity, 2),
        }
        
        return status
    
    def get_all_signals(self):
        """紐⑤뱺 ?좏샇 諛섑솚"""
        return self.signals
    
    def get_portfolio(self):
        """?ы듃?대━??議고쉶"""
        return self.portfolio
    
    def get_trading_history(self):
        """嫄곕옒 ?대젰 諛섑솚"""
        return self.trading_history
    
    def calculate_portfolio_returns(self):
        """
        ?ы듃?대━??珥??섏씡瑜?怨꾩궛
        
        Returns:
            dict: ?ы듃?대━???깃낵 吏??
        """
        if not self.trading_history:
            return {'total_trades': 0, 'total_profit': 0, 'win_rate': 0}
        
        total_trades = len(self.trading_history)
        total_profit = sum(t['profit'] for t in self.trading_history)
        winning_trades = sum(1 for t in self.trading_history if t['profit'] > 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'total_profit': round(total_profit, 2),
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': round(win_rate, 2),
            'avg_profit_per_trade': round(total_profit / total_trades, 2) if total_trades > 0 else 0,
        }
    
    def calculate_trade_suggestion(self, signal_data, portfolio_summary, current_price):
        """
        매수/매도 수량 추천 계산

        Args:
            signal_data: 거래 신호 데이터
            portfolio_summary: 포트폴리오 요약 정보
            current_price: 현재 가격

        Returns:
            dict: 매수/매도 추천 정보
        """
        symbol = signal_data['symbol']
        signal = signal_data['signal']

        suggestion = {
            'symbol': symbol,
            'signal': signal,
            'current_price': current_price,
            'quantity': 0,
            'total_investment': 0,
            'description': ''
        }

        # 포트폴리오에서 해당 자산 보유 정보 찾기
        current_holding = None
        for asset in portfolio_summary['assets']:
            if asset['symbol'] == symbol:
                current_holding = asset
                break

        if signal == 'BUY':
            # ===== 매수 추천 =====
            available_cash = portfolio_summary['total_cash']

            # 현금의 30%를 기본 투자 한도로 사용
            reserve_ratio = TRADING_CONFIG.get("CASH_RESERVE_RATIO", 0.12)
            total_value = portfolio_summary.get("total_value", portfolio_summary.get("total_invested", 0) + available_cash)
            reserve_cash = max(0.0, total_value * reserve_ratio)
            investable_cash = max(0.0, available_cash - reserve_cash)

            # Invest at most 30% of investable cash per signal
            max_investment = investable_cash * 0.30

            if investable_cash > current_price:
                max_quantity = int(investable_cash / current_price)

                # 1) 신뢰도 계수
                confidence = signal_data['confidence']
                if confidence >= 75:
                    confidence_ratio = 1.0
                elif confidence >= 50:
                    confidence_ratio = 0.7
                else:
                    confidence_ratio = 0.5

                # 2) ETF별 모멘텀 계수 (3개월 수익률)
                momentum_3m = signal_data.get('analysis', {}).get('returns', {}).get('return_3m')
                momentum_ratio = 1.0
                if momentum_3m is not None:
                    # +10% 모멘텀 -> +20%, -10% -> -20% (0.6~1.4 제한)
                    momentum_ratio = max(0.6, min(1.4, 1.0 + (momentum_3m / 50.0)))

                # 3) 보유 비중 계수 (이미 많이 보유한 ETF는 추가 매수 축소)
                concentration_ratio = 1.0
                total_invested = portfolio_summary.get('total_invested', 0)
                if current_holding and total_invested > 0:
                    holding_weight = current_holding['total_invested'] / total_invested
                    concentration_ratio = max(0.5, 1.0 - max(0.0, holding_weight - 0.30))

                suggested_investment = max_investment * confidence_ratio * momentum_ratio * concentration_ratio
                quantity = int(suggested_investment / current_price)

                quantity = max(1, min(quantity, max_quantity))
                total_investment = quantity * current_price

                suggestion['quantity'] = quantity
                suggestion['total_investment'] = round(total_investment, 2)
                suggestion['description'] = (
                    f"현금 ${available_cash:,.0f} (예비현금 ${reserve_cash:,.0f} 유지)에서 {quantity}주 매수 추천 "
                    f"(투자액: ${total_investment:,.0f}, "
                    f"신뢰도계수 {confidence_ratio:.2f}, 모멘텀계수 {momentum_ratio:.2f}, 비중계수 {concentration_ratio:.2f})"
                )
            else:
                shortage = max(0.0, current_price - investable_cash)
                suggestion['description'] = (
                    f"현금 부족(필요: ${current_price:,.0f}, "
                    f"주문가능현금: ${investable_cash:,.0f}, "
                    f"부족금액: ${shortage:,.0f}, "
                    f"총현금: ${available_cash:,.0f}, "
                    f"예비현금: ${reserve_cash:,.0f})"
                )

        elif signal == 'SELL':
            # ===== 매도 추천 =====
            if current_holding and current_holding['total_quantity'] > 0:
                total_quantity = current_holding['total_quantity']
                avg_price = current_holding['total_invested'] / total_quantity
                current_returns = ((current_price - avg_price) / avg_price) * 100

                target_profit = PROFIT_CONFIG['TARGET_PROFIT'] * 100

                if 'dynamic_stop_loss' in signal_data and signal_data['dynamic_stop_loss'] is not None:
                    stop_loss = signal_data['dynamic_stop_loss'] * 100
                    is_dynamic = True
                else:
                    stop_loss = PROFIT_CONFIG['STOP_LOSS'] * 100
                    is_dynamic = False

                # 고정 비율 대신 수익률 크기에 따라 매도 비율 동적 조정
                if current_returns >= target_profit:
                    exceed = current_returns - target_profit
                    sell_ratio = min(1.0, 0.5 + max(0.0, exceed) / 30.0)
                    quantity = max(1, int(total_quantity * sell_ratio))
                    suggestion['description'] = (
                        f"익절 신호 - {quantity}주 매도 추천 "
                        f"(수익률: {current_returns:.1f}%, 매도비율: {sell_ratio*100:.0f}%)"
                    )
                elif current_returns <= stop_loss:
                    quantity = total_quantity
                    sl_str = f"{stop_loss:.2f}%" + (" (배당금 반영)" if is_dynamic else "")
                    suggestion['description'] = (
                        f"손절 신호 - {quantity}주 전량 매도 추천 "
                        f"(수익률: {current_returns:.1f}%, 손절률: {sl_str})"
                    )
                else:
                    if current_returns > 0:
                        sell_ratio = min(0.6, 0.2 + current_returns / 25.0)
                        quantity = max(1, int(total_quantity * sell_ratio))
                        suggestion['description'] = (
                            f"수익 실현 - {quantity}주 매도 추천 "
                            f"(수익률: {current_returns:.1f}%, 매도비율: {sell_ratio*100:.0f}%)"
                        )
                    else:
                        quantity = 0
                        sl_str = f"{stop_loss:.2f}%" + (" (배당금 반영)" if is_dynamic else "")
                        suggestion['description'] = (
                            f"손실 신호이나 손절 미만 - 매도 보류 "
                            f"(수익률: {current_returns:.1f}%, 손절률: {sl_str})"
                        )

                quantity = max(0, min(quantity, total_quantity))
                total_proceeds = quantity * current_price

                suggestion['quantity'] = quantity
                suggestion['total_investment'] = round(total_proceeds, 2)
                suggestion['current_returns'] = round(current_returns, 2)
            else:
                suggestion['description'] = "보유 자산 없음 - 매도 불가"

        else:  # HOLD
            if current_holding and current_holding['total_quantity'] > 0:
                total_quantity = current_holding['total_quantity']
                avg_price = current_holding['total_invested'] / total_quantity
                current_returns = ((current_price - avg_price) / avg_price) * 100
                suggestion['description'] = f"보유 신호 - ({total_quantity}주 보유, 수익률: {current_returns:.1f}%)"
                suggestion['current_returns'] = round(current_returns, 2)
            else:
                suggestion['description'] = "신호 없음"

        return suggestion

    def calculate_dynamic_stop_loss(self, symbol, current_holding):
        """
        諛곕떦湲덉쓣 怨좊젮???숈쟻 ?먯젅瑜?怨꾩궛
        
        ?믪? 諛곕떦?섏씡瑜좎쓣 媛吏?ETF???먯떎?????ㅻ옒 踰꾪떥 ???덉쓬
        
        Args:
            symbol: ETF ?щ낵
            current_holding: ?꾩옱 蹂댁쑀 ?뺣낫 (dict)
        
        Returns:
            float: ?숈쟻 ?먯젅瑜?(?? -0.05 = -5%)
        """
        if not current_holding or current_holding['total_quantity'] == 0:
            return self.base_stop_loss
        
        # 諛곕떦湲??뺣낫 媛?몄삤湲?
        dividend_info = self.DIVIDEND_INFO.get(symbol)
        
        if dividend_info:
            yield_percent = dividend_info.get('yield_percent', 0) / 100  # ??諛곕떦?섏씡瑜?
            
            # 諛곕떦湲?怨좊젮 湲곌컙 ?ㅼ젙 (3-6媛쒖썡 踰꾪떥 ???덈룄濡?
            # 諛곕떦?섏씡瑜좎뿉 ?곕씪 議곗젙
            if yield_percent >= 0.12:  # 12% ?댁긽 (QYLD, SDTY)
                hold_months = 4  # 4媛쒖썡 踰꾪떥 ???덈룄濡?
            elif yield_percent >= 0.03:  # 3-12% (SCHD)
                hold_months = 5  # 5媛쒖썡 踰꾪떥 ???덈룄濡?
            else:
                hold_months = 6  # 6媛쒖썡 湲곕낯媛?
            
            # ?대떦 湲곌컙 ?숈븞??諛곕떦湲덉쑝濡??먯젅瑜??곸뇙
            dividend_offset = yield_percent * (hold_months / 12)
            
            # ?덉쟾留덉쭊 80% ?곸슜 (諛곕떦湲덉쓽 80%留??먯젅瑜좎뿉 諛섏쁺)
            safety_margin = 0.80
            dynamic_stop_loss = self.base_stop_loss - (dividend_offset * safety_margin)
            
            logger.debug(
                f"[{symbol}] ?숈쟻 ?먯젅瑜?怨꾩궛:\n"
                f"  - ??諛곕떦?섏씡瑜? {yield_percent*100:.2f}%\n"
                f"  - 踰꾪떥 湲곌컙: {hold_months}媛쒖썡\n"
                f"  - 諛곕떦湲??ㅽ봽?? {dividend_offset*100:.2f}%\n"
                f"  - 湲곕낯 ?먯젅瑜? {self.base_stop_loss*100:.2f}%\n"
                f"  - ?숈쟻 ?먯젅瑜? {dynamic_stop_loss*100:.2f}%"
            )
            
            return round(dynamic_stop_loss, 4)
        
        return self.base_stop_loss
    
    def get_dynamic_stop_loss_for_portfolio(self, portfolio_summary, analysis_results):
        """
        ?ы듃?대━??媛??먯궛蹂??숈쟻 ?먯젅瑜?議고쉶
        
        Args:
            portfolio_summary: ?ы듃?대━???붿빟
            analysis_results: 遺꾩꽍 寃곌낵
        
        Returns:
            dict: ?щ낵蹂??숈쟻 ?먯젅瑜?
        """
        stop_losses = {}
        
        for asset in portfolio_summary['assets']:
            symbol = asset['symbol']
            stop_losses[symbol] = self.calculate_dynamic_stop_loss(symbol, asset)
        
        return stop_losses



