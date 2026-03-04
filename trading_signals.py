import logging
from datetime import datetime
from config import TRADING_CONFIG, PROFIT_CONFIG, ANALYSIS_CONFIG
from dividend_tracker import DividendTracker

logger = logging.getLogger(__name__)


class TradingSignalGenerator:
    """거래 신호 생성 및 관리 클래스"""
    
    def __init__(self):
        self.signals = {}
        self.portfolio = {}
        self.trading_history = []
        self.dividend_tracker = DividendTracker()
        
        # 손절률 설정 (배당금 미반영 기본값)
        self.base_stop_loss = PROFIT_CONFIG['STOP_LOSS']  # -0.03 (-3%)
        
        # 배당금 정보 참조
        self.DIVIDEND_INFO = self.dividend_tracker.DIVIDEND_INFO
    
    def generate_signal(self, analysis_result):
        """
        분석 결과를 기반으로 거래 신호 생성
        
        Args:
            analysis_result: ETF 분석 결과 (dict)
        
        Returns:
            dict: 거래 신호 (BUY, SELL, HOLD)
        """
        symbol = analysis_result['symbol']
        
        buy_signals = 0
        sell_signals = 0
        
        # 이동평균선 신호
        ma_signal = analysis_result['moving_average'].get('signal')
        if ma_signal == 'BUY':
            buy_signals += 1
        elif ma_signal == 'SELL':
            sell_signals += 1
        
        # RSI 신호
        rsi_signal = analysis_result['rsi'].get('signal')
        if rsi_signal == 'BUY':
            buy_signals += 1
        elif rsi_signal == 'SELL':
            sell_signals += 1
        
        # MACD 신호
        macd_signal = analysis_result['macd'].get('signal')
        if macd_signal == 'BUY':
            buy_signals += 1
        elif macd_signal == 'SELL':
            sell_signals += 1
        
        # 수익률 기반 신호
        returns_1m = analysis_result['returns'].get('return_1m')
        if returns_1m is not None:
            if returns_1m < PROFIT_CONFIG['STOP_LOSS'] * 100:
                sell_signals += 1  # 손절
            elif returns_1m > PROFIT_CONFIG['TARGET_PROFIT'] * 100:
                sell_signals += 1  # 익절
        
        # 최종 신호 결정
        signal_strength_required = TRADING_CONFIG['BUY_SIGNAL_STRENGTH']
        
        if buy_signals >= signal_strength_required:
            final_signal = 'BUY'
        elif sell_signals >= signal_strength_required:
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
            'confidence': max(buy_signals, sell_signals) / 4 * 100,  # 신뢰도
            'analysis': analysis_result
        }
        
        self.signals[symbol] = signal_data
        logger.info(f"[{symbol}] 신호: {final_signal} (신뢰도: {signal_data['confidence']:.0f}%)")
        
        return signal_data
    
    def check_profit_target(self, symbol, entry_price, current_price):
        """
        수익 목표 확인
        
        Args:
            symbol: ETF 기호
            entry_price: 매입 가격
            current_price: 현재 가격
        
        Returns:
            dict: 목표 달성 여부 및 수익률
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
        포지션 추가
        
        Args:
            symbol: ETF 기호
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
        포지션 종료
        
        Args:
            symbol: ETF 기호
            exit_price: 청산 가격
            quantity: 수량 (None이면 전체)
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
            
            logger.info(f"포지션 종료: {symbol} {close_qty}주 @ {exit_price} (수익: {trade_record['returns_pct']}%)")
        
        return closed_positions
    
    def get_position_status(self, symbol, current_price):
        """
        포지션 상태 조회
        
        Args:
            symbol: ETF 기호
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
        """모든 신호 반환"""
        return self.signals
    
    def get_portfolio(self):
        """포트폴리오 조회"""
        return self.portfolio
    
    def get_trading_history(self):
        """거래 이력 반환"""
        return self.trading_history
    
    def calculate_portfolio_returns(self):
        """
        포트폴리오 총 수익률 계산
        
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
        
        # 포트폴리오에서 해당 자산의 정보 찾기
        current_holding = None
        for asset in portfolio_summary['assets']:
            if asset['symbol'] == symbol:
                current_holding = asset
                break
        
        if signal == 'BUY':
            # ===== 매수 추천 =====
            available_cash = portfolio_summary['total_cash']
            
            # 현금의 30%를 각 매수에 사용 (자금 관리)
            max_investment = available_cash * 0.30
            
            if available_cash > current_price:
                # 매수 가능한 최대 수량
                max_quantity = int(available_cash / current_price)
                
                # 신뢰도 기반 수량 결정
                confidence = signal_data['confidence']
                
                if confidence >= 75:
                    quantity = int(max_investment / current_price)
                elif confidence >= 50:
                    quantity = int(max_investment / current_price * 0.7)
                else:
                    quantity = int(max_investment / current_price * 0.5)
                
                # 최소 1주부터 최대 max_quantity까지
                quantity = max(1, min(quantity, max_quantity))
                total_investment = quantity * current_price
                
                suggestion['quantity'] = quantity
                suggestion['total_investment'] = round(total_investment, 2)
                suggestion['description'] = f"현금 ${available_cash:,.0f}에서 {quantity}주 매수 추천 (투자액: ${total_investment:,.0f})"
            else:
                suggestion['description'] = f"현금 부족 (필요: ${current_price:,.0f}, 보유: ${available_cash:,.0f})"
        
        elif signal == 'SELL':
            # ===== 매도 추천 =====
            if current_holding and current_holding['total_quantity'] > 0:
                total_quantity = current_holding['total_quantity']
                avg_price = current_holding['total_invested'] / total_quantity
                current_returns = ((current_price - avg_price) / avg_price) * 100
                
                # 목표 수익률 및 손절률 (동적 손절률 사용)
                target_profit = PROFIT_CONFIG['TARGET_PROFIT'] * 100
                
                # 동적 손절률이 있으면 사용, 없으면 기본값 사용
                if 'dynamic_stop_loss' in signal_data and signal_data['dynamic_stop_loss'] is not None:
                    stop_loss = signal_data['dynamic_stop_loss'] * 100
                    is_dynamic = True
                else:
                    stop_loss = PROFIT_CONFIG['STOP_LOSS'] * 100
                    is_dynamic = False
                
                # 수익률 상황에 따른 매도량 결정
                if current_returns >= target_profit:
                    # 익절: 전체의 50% 매도
                    quantity = int(total_quantity * 0.5)
                    suggestion['description'] = f"익절 신호 - {quantity}주 매도 추천 (수익률: {current_returns:.1f}%)"
                elif current_returns <= stop_loss:
                    # 손절: 전체 매도
                    quantity = total_quantity
                    sl_str = f"{stop_loss:.2f}%" + (" (배당금 반영)" if is_dynamic else "")
                    suggestion['description'] = f"손절 신호 - {quantity}주 전량 매도 추천 (수익률: {current_returns:.1f}%, 손절률: {sl_str})"
                else:
                    # 부분 매도: 수익률에 따라 조정
                    if current_returns > 0:
                        quantity = int(total_quantity * 0.3)
                        suggestion['description'] = f"수익 실현 - {quantity}주 매도 추천 (수익률: {current_returns:.1f}%)"
                    else:
                        quantity = 0
                        sl_str = f"{stop_loss:.2f}%" + (" (배당금 반영)" if is_dynamic else "")
                        suggestion['description'] = f"하락 신호이나 손절 수준 미만 - 매도 보류 (수익률: {current_returns:.1f}%, 손절률: {sl_str})"
                
                quantity = max(0, min(quantity, total_quantity))
                total_proceeds = quantity * current_price
                
                suggestion['quantity'] = quantity
                suggestion['total_investment'] = round(total_proceeds, 2)
                suggestion['current_returns'] = round(current_returns, 2)
            else:
                suggestion['description'] = f"보유 자산 없음 - 매도 불가"
        
        else:  # HOLD
            if current_holding and current_holding['total_quantity'] > 0:
                total_quantity = current_holding['total_quantity']
                avg_price = current_holding['total_invested'] / total_quantity
                current_returns = ((current_price - avg_price) / avg_price) * 100
                suggestion['description'] = f"보유 신호 - ({total_quantity}주 보유, 수익률: {current_returns:.1f}%)"
                suggestion['current_returns'] = round(current_returns, 2)
            else:
                suggestion['description'] = f"신호 없음"
        
        return suggestion    
    def calculate_dynamic_stop_loss(self, symbol, current_holding):
        """
        배당금을 고려한 동적 손절률 계산
        
        높은 배당수익률을 가진 ETF는 손실을 더 오래 버틸 수 있음
        
        Args:
            symbol: ETF 심볼
            current_holding: 현재 보유 정보 (dict)
        
        Returns:
            float: 동적 손절률 (예: -0.05 = -5%)
        """
        if not current_holding or current_holding['total_quantity'] == 0:
            return self.base_stop_loss
        
        # 배당금 정보 가져오기
        dividend_info = self.DIVIDEND_INFO.get(symbol)
        
        if dividend_info:
            yield_percent = dividend_info.get('yield_percent', 0) / 100  # 연 배당수익률
            
            # 배당금 고려 기간 설정 (3-6개월 버틸 수 있도록)
            # 배당수익률에 따라 조정
            if yield_percent >= 0.12:  # 12% 이상 (QYLD, SDTY)
                hold_months = 4  # 4개월 버틸 수 있도록
            elif yield_percent >= 0.03:  # 3-12% (SCHD)
                hold_months = 5  # 5개월 버틸 수 있도록
            else:
                hold_months = 6  # 6개월 기본값
            
            # 해당 기간 동안의 배당금으로 손절률 상쇄
            dividend_offset = yield_percent * (hold_months / 12)
            
            # 안전마진 80% 적용 (배당금의 80%만 손절률에 반영)
            safety_margin = 0.80
            dynamic_stop_loss = self.base_stop_loss - (dividend_offset * safety_margin)
            
            logger.debug(
                f"[{symbol}] 동적 손절률 계산:\n"
                f"  - 연 배당수익률: {yield_percent*100:.2f}%\n"
                f"  - 버틸 기간: {hold_months}개월\n"
                f"  - 배당금 오프셋: {dividend_offset*100:.2f}%\n"
                f"  - 기본 손절률: {self.base_stop_loss*100:.2f}%\n"
                f"  - 동적 손절률: {dynamic_stop_loss*100:.2f}%"
            )
            
            return round(dynamic_stop_loss, 4)
        
        return self.base_stop_loss
    
    def get_dynamic_stop_loss_for_portfolio(self, portfolio_summary, analysis_results):
        """
        포트폴리오 각 자산별 동적 손절률 조회
        
        Args:
            portfolio_summary: 포트폴리오 요약
            analysis_results: 분석 결과
        
        Returns:
            dict: 심볼별 동적 손절률
        """
        stop_losses = {}
        
        for asset in portfolio_summary['assets']:
            symbol = asset['symbol']
            stop_losses[symbol] = self.calculate_dynamic_stop_loss(symbol, asset)
        
        return stop_losses