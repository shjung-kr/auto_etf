import logging
from datetime import datetime
from config import (
    ANALYSIS_CONFIG,
    DEFAULT_PROFIT_RULE,
    ETF_PROFIT_RULES,
    PROFIT_CONFIG,
    TRADING_CONFIG,
)
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

    def get_profit_rule(self, symbol):
        """종목별 수익 실현 규칙 반환"""
        rule = DEFAULT_PROFIT_RULE.copy()
        symbol_rule = ETF_PROFIT_RULES.get(symbol, {})
        rule.update(symbol_rule)
        return rule

    def get_received_dividends_since(self, symbol, since_date):
        """현재 보유 기간 동안 실제 적립된 배당금을 합산"""
        if not since_date:
            return 0.0

        dividend_entry = self.dividend_tracker.dividends.get(symbol, {})
        payments = dividend_entry.get("payments", [])
        total_dividends = 0.0

        for payment in payments:
            payment_date = payment.get("payment_date")
            if not payment_date:
                continue

            try:
                paid_at = datetime.strptime(payment_date, "%Y-%m-%d")
            except ValueError:
                continue

            if paid_at >= since_date:
                total_dividends += float(payment.get("amount", 0.0))

        return round(total_dividends, 2)

    def calculate_position_metrics(self, symbol, current_holding, current_price):
        """현재 보유 포지션의 가격/배당 포함 수익률 계산"""
        if not current_holding or current_holding.get('total_quantity', 0) <= 0:
            return None

        total_quantity = current_holding['total_quantity']
        total_invested = current_holding['total_invested']
        avg_price = total_invested / total_quantity if total_quantity > 0 else 0

        if avg_price <= 0:
            return None

        holding_dates = []
        for holding in current_holding.get("holdings", []):
            purchase_date = holding.get("purchase_date")
            if not purchase_date:
                continue
            try:
                holding_dates.append(datetime.strptime(purchase_date, "%Y-%m-%d"))
            except ValueError:
                continue

        first_purchase_date = min(holding_dates) if holding_dates else None
        hold_days = (datetime.now() - first_purchase_date).days if first_purchase_date else 0

        current_value = total_quantity * current_price
        price_profit = current_value - total_invested
        price_return_pct = (price_profit / total_invested) * 100

        realized_dividends = self.get_received_dividends_since(symbol, first_purchase_date)
        dividend_return_pct = (realized_dividends / total_invested) * 100 if total_invested > 0 else 0
        total_return_pct = ((price_profit + realized_dividends) / total_invested) * 100 if total_invested > 0 else 0

        return {
            'symbol': symbol,
            'total_quantity': total_quantity,
            'avg_price': avg_price,
            'total_invested': total_invested,
            'current_value': current_value,
            'price_profit': round(price_profit, 2),
            'price_return_pct': round(price_return_pct, 2),
            'realized_dividends': round(realized_dividends, 2),
            'dividend_return_pct': round(dividend_return_pct, 2),
            'total_return_pct': round(total_return_pct, 2),
            'hold_days': hold_days,
        }

    def evaluate_exit_strategy(
        self,
        symbol,
        current_holding,
        current_price,
        signal,
        dynamic_stop_loss=None,
        completed_take_profit_levels=None,
    ):
        """종목별 목표수익률과 배당 반영 수익률로 청산 전략 평가"""
        metrics = self.calculate_position_metrics(symbol, current_holding, current_price)
        if not metrics:
            return None

        rule = self.get_profit_rule(symbol)
        effective_stop_loss = dynamic_stop_loss if dynamic_stop_loss is not None else rule['stop_loss']
        min_hold_days = rule.get('min_hold_days', PROFIT_CONFIG['MIN_HOLD_DAYS'])
        total_quantity = metrics['total_quantity']
        completed_levels = set(completed_take_profit_levels or [])

        if metrics['total_return_pct'] <= effective_stop_loss * 100:
            return {
                'action': 'FULL_SELL',
                'quantity': total_quantity,
                'reason': 'stop_loss',
                'rule': rule,
                'metrics': metrics,
                'description': (
                    f"손절 기준 도달 - {total_quantity}주 전량 매도 "
                    f"(총수익률 {metrics['total_return_pct']:.2f}%, 손절 {effective_stop_loss*100:.2f}%)"
                ),
            }

        if metrics['hold_days'] < min_hold_days:
            return {
                'action': 'HOLD',
                'quantity': 0,
                'reason': 'min_hold_days',
                'rule': rule,
                'metrics': metrics,
                'description': (
                    f"최소 보유기간 미충족 - 보유 유지 "
                    f"({metrics['hold_days']}일 / 최소 {min_hold_days}일)"
                ),
            }

        partial_rules = sorted(
            rule.get('partial_take_profits', []),
            key=lambda item: item.get('profit', 0),
            reverse=True,
        )
        for partial_rule in partial_rules:
            threshold_pct = partial_rule.get('profit', 0) * 100
            level_id = f"{partial_rule.get('profit', 0):.4f}:{partial_rule.get('sell_ratio', 0):.4f}"
            if level_id in completed_levels:
                continue
            if metrics['total_return_pct'] >= threshold_pct:
                quantity = max(1, int(total_quantity * partial_rule.get('sell_ratio', 0)))
                quantity = min(quantity, total_quantity)
                return {
                    'action': 'PARTIAL_SELL',
                    'quantity': quantity,
                    'level_id': level_id,
                    'reason': 'partial_take_profit',
                    'rule': rule,
                    'metrics': metrics,
                    'description': (
                        f"부분 익절 - {quantity}주 매도 "
                        f"(총수익률 {metrics['total_return_pct']:.2f}%, 목표 {threshold_pct:.2f}%)"
                    ),
                }

        if signal == 'SELL' and metrics['total_return_pct'] >= rule['target_profit'] * 100:
            return {
                'action': 'FULL_SELL',
                'quantity': total_quantity,
                'reason': 'target_profit_and_sell_signal',
                'rule': rule,
                'metrics': metrics,
                'description': (
                    f"목표수익률 달성 + 매도 신호 - {total_quantity}주 전량 매도 "
                    f"(총수익률 {metrics['total_return_pct']:.2f}%, 목표 {rule['target_profit']*100:.2f}%)"
                ),
            }

        return {
            'action': 'HOLD',
            'quantity': 0,
            'reason': 'no_exit',
            'rule': rule,
            'metrics': metrics,
            'description': (
                f"청산 조건 미충족 - 보유 유지 "
                f"(가격수익률 {metrics['price_return_pct']:.2f}%, "
                f"배당수익률 {metrics['dividend_return_pct']:.2f}%, "
                f"총수익률 {metrics['total_return_pct']:.2f}%)"
            ),
        }
    
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
    
    def calculate_trade_suggestion(self, signal_data, portfolio_summary, current_price, exit_strategy=None):
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
        effective_signal = signal

        if current_price is not None and exit_strategy and exit_strategy.get('action') in {'PARTIAL_SELL', 'FULL_SELL'}:
            effective_signal = 'SELL'

        suggestion = {
            'symbol': symbol,
            'signal': effective_signal,
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

        if effective_signal == 'BUY':
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

        elif effective_signal == 'SELL':
            # ===== 매도 추천 =====
            if current_holding and current_holding['total_quantity'] > 0:
                total_quantity = current_holding['total_quantity']
                position_metrics = self.calculate_position_metrics(symbol, current_holding, current_price)
                current_returns = position_metrics['price_return_pct'] if position_metrics else 0.0

                if 'dynamic_stop_loss' in signal_data and signal_data['dynamic_stop_loss'] is not None:
                    stop_loss = signal_data['dynamic_stop_loss'] * 100
                    is_dynamic = True
                else:
                    stop_loss = self.get_profit_rule(symbol)['stop_loss'] * 100
                    is_dynamic = False

                if exit_strategy and exit_strategy.get('action') in {'PARTIAL_SELL', 'FULL_SELL'}:
                    quantity = min(total_quantity, max(0, exit_strategy.get('quantity', 0)))
                    suggestion['description'] = exit_strategy.get('description', '')
                    metrics = exit_strategy.get('metrics', {})
                    suggestion['current_returns'] = round(metrics.get('price_return_pct', current_returns), 2)
                    suggestion['total_return_with_dividend'] = round(metrics.get('total_return_pct', current_returns), 2)
                    suggestion['realized_dividends'] = round(metrics.get('realized_dividends', 0.0), 2)
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
                position_metrics = self.calculate_position_metrics(symbol, current_holding, current_price)
                total_quantity = current_holding['total_quantity']
                if exit_strategy and exit_strategy.get('action') in {'PARTIAL_SELL', 'FULL_SELL'}:
                    suggestion['signal'] = 'SELL'
                    suggestion['quantity'] = min(total_quantity, max(0, exit_strategy.get('quantity', 0)))
                    suggestion['total_investment'] = round(suggestion['quantity'] * current_price, 2)
                    suggestion['description'] = exit_strategy.get('description', '')
                    metrics = exit_strategy.get('metrics', {})
                    suggestion['current_returns'] = round(metrics.get('price_return_pct', 0.0), 2)
                    suggestion['total_return_with_dividend'] = round(metrics.get('total_return_pct', 0.0), 2)
                    suggestion['realized_dividends'] = round(metrics.get('realized_dividends', 0.0), 2)
                else:
                    current_returns = position_metrics['price_return_pct'] if position_metrics else 0.0
                    total_returns = position_metrics['total_return_pct'] if position_metrics else current_returns
                    suggestion['description'] = (
                        f"보유 신호 - ({total_quantity}주 보유, 가격수익률: {current_returns:.1f}%, "
                        f"배당포함 총수익률: {total_returns:.1f}%)"
                    )
                    suggestion['current_returns'] = round(current_returns, 2)
                    suggestion['total_return_with_dividend'] = round(total_returns, 2)
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
