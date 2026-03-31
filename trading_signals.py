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
        
        # 손절률 기본값 설정 (배당금 미반영)
        self.base_stop_loss = PROFIT_CONFIG['STOP_LOSS']  # -0.03 (-3%)
        
        # 배당금 정보 참조
        self.DIVIDEND_INFO = self.dividend_tracker.DIVIDEND_INFO
    
    def generate_signal(self, analysis_result):
        """
        분석 결과를 기반으로 거래 신호를 생성한다.
        
        Args:
            analysis_result: ETF 분석 결과 (dict)
        
        Returns:
            dict: 거래 신호 (BUY, SELL, HOLD)
        """
        symbol = analysis_result['symbol']
        
        buy_signals = 0
        sell_signals = 0
        total_checks = 0
        
        # 이동평균선 신호
        ma_signal = analysis_result['moving_average'].get('signal')
        total_checks += 1
        if ma_signal == 'BUY':
            buy_signals += 1
        elif ma_signal == 'SELL':
            sell_signals += 1
        
        # RSI 신호
        rsi_signal = analysis_result['rsi'].get('signal')
        total_checks += 1
        if rsi_signal == 'BUY':
            buy_signals += 1
        elif rsi_signal == 'SELL':
            sell_signals += 1
        
        # MACD 신호
        macd_signal = analysis_result['macd'].get('signal')
        total_checks += 1
        if macd_signal == 'BUY':
            buy_signals += 1
        elif macd_signal == 'SELL':
            sell_signals += 1
        
        # 수익률 기반 신호
        returns_1m = analysis_result['returns'].get('return_1m')
        total_checks += 1
        if returns_1m is not None:
            if returns_1m < PROFIT_CONFIG['STOP_LOSS'] * 100:
                sell_signals += 1  # 손절
            elif returns_1m > PROFIT_CONFIG['TARGET_PROFIT'] * 100:
                sell_signals += 1  # 익절

        # 중기 모멘텀 필터 (추세 진행 시 매수/매도 강화)
        momentum_3m = analysis_result['returns'].get('return_3m')
        momentum_buy_threshold = TRADING_CONFIG.get('MOMENTUM_3M_BUY_THRESHOLD', 2.0)
        momentum_sell_threshold = TRADING_CONFIG.get('MOMENTUM_3M_SELL_THRESHOLD', -5.0)
        total_checks += 1
        if momentum_3m is not None:
            if momentum_3m >= momentum_buy_threshold:
                buy_signals += 1
            elif momentum_3m <= momentum_sell_threshold:
                sell_signals += 1
        
        # 최종 신호 결정
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
            'confidence': max(buy_signals, sell_signals) / max(total_checks, 1) * 100,  # 신뢰도
            'analysis': analysis_result
        }
        
        self.signals[symbol] = signal_data
        logger.info(f"[{symbol}] 신호: {final_signal} (신뢰도 {signal_data['confidence']:.0f}%)")
        
        return signal_data
    
    def check_profit_target(self, symbol, entry_price, current_price):
        """
        수익 목표 달성 여부를 확인한다.
        
        Args:
            symbol: ETF 티커
            entry_price: 매입 가격
            current_price: 현재 가격
        
        Returns:
            dict: 목표 달성 여부와 수익률
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
        포지션을 추가한다.
        
        Args:
            symbol: ETF 티커
            entry_price: 매입 가격
            quantity: 수량
            notes: 비고
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
        logger.info(f"포지션 추가: {symbol} {quantity}주 @ {entry_price} (합계: {quantity * entry_price})")
    
    def close_position(self, symbol, exit_price, quantity=None):
        """
        포지션을 청산한다.
        
        Args:
            symbol: ETF 티커
            exit_price: 청산 가격
            quantity: 수량 (`None`이면 전체)
        """
        if symbol not in self.portfolio or not self.portfolio[symbol]:
            logger.warning(f"{symbol}에 대한 열린 포지션이 없습니다.")
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
            
            logger.info(f"포지션 청산: {symbol} {close_qty}주 @ {exit_price} (수익률: {trade_record['returns_pct']}%)")
        
        return closed_positions
    
    def get_position_status(self, symbol, current_price):
        """
        포지션 상태를 조회한다.
        
        Args:
            symbol: ETF 티커
            current_price: 현재 가격
        
        Returns:
            dict: 포지션 상태 및 수익률
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
        """모든 신호를 반환한다."""
        return self.signals
    
    def get_portfolio(self):
        """포트폴리오를 조회한다."""
        return self.portfolio
    
    def get_trading_history(self):
        """거래 이력을 반환한다."""
        return self.trading_history
    
    def calculate_portfolio_returns(self):
        """
        포트폴리오 총 수익률 통계를 계산한다.
        
        Returns:
            dict: 포트폴리오 성과 지표
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
        배당금을 고려한 동적 손절률을 계산한다.
        
        배당수익률이 높은 ETF는 더 긴 보유를 허용할 수 있다.
        
        Args:
            symbol: ETF 티커
            current_holding: 현재 보유 정보 (dict)
        
        Returns:
            float: 동적 손절률 (예: -0.05 = -5%)
        """
        if not current_holding or current_holding['total_quantity'] == 0:
            return self.base_stop_loss
        
        # 배당금 정보 조회
        dividend_info = self.DIVIDEND_INFO.get(symbol)
        
        if dividend_info:
            yield_percent = dividend_info.get('yield_percent', 0) / 100  # 연 배당수익률
            
            # 배당금 고려 기간 설정 (3-6개월 범위)
            # 배당수익률에 따라 조정
            if yield_percent >= 0.12:  # 12% 이상 (QYLD, SDTY)
                hold_months = 4  # 4개월 보유 허용
            elif yield_percent >= 0.03:  # 3-12% (SCHD)
                hold_months = 5  # 5개월 보유 허용
            else:
                hold_months = 6  # 6개월 기본값
            
            # 해당 기간 동안의 배당금으로 손절률을 완화
            dividend_offset = yield_percent * (hold_months / 12)
            
            # 안전 마진 80% 적용 (배당금의 80%만 반영)
            safety_margin = 0.80
            dynamic_stop_loss = self.base_stop_loss - (dividend_offset * safety_margin)
            
            logger.debug(
                f"[{symbol}] 동적 손절률 계산:\n"
                f"  - 연 배당수익률: {yield_percent*100:.2f}%\n"
                f"  - 반영 기간: {hold_months}개월\n"
                f"  - 배당금 오프셋: {dividend_offset*100:.2f}%\n"
                f"  - 기본 손절률: {self.base_stop_loss*100:.2f}%\n"
                f"  - 동적 손절률: {dynamic_stop_loss*100:.2f}%"
            )
            
            return round(dynamic_stop_loss, 4)
        
        return self.base_stop_loss
    
    def get_dynamic_stop_loss_for_portfolio(self, portfolio_summary, analysis_results):
        """
        포트폴리오 각 자산별 동적 손절률을 조회한다.
        
        Args:
            portfolio_summary: 포트폴리오 요약
            analysis_results: 분석 결과
        
        Returns:
            dict: 종목별 동적 손절률
        """
        stop_losses = {}
        
        for asset in portfolio_summary['assets']:
            symbol = asset['symbol']
            stop_losses[symbol] = self.calculate_dynamic_stop_loss(symbol, asset)
        
        return stop_losses


