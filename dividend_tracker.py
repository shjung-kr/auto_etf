import json
import logging
import os
from datetime import datetime, timedelta
from config import DATA_PATH

logger = logging.getLogger(__name__)

DIVIDEND_FILE = os.path.join(DATA_PATH, "dividends.json")


class DividendTracker:
    """ETF 배당금 추적 클래스"""
    
    # ETF별 배당금 정보 (수익률, 지급주기, 배당금액)
    DIVIDEND_INFO = {
        "QYLD": {
            "name": "글로벌엑스 나스닥100 커버드콜",
            "frequency": "MONTHLY",  # 월 배당
            "yield_percent": 14.0,  # 연 배당수익률
            "last_payment_date": None,
        },
        "SCHD": {
            "name": "슈왑 미국 배당주",
            "frequency": "MONTHLY",  # 월 배당
            "yield_percent": 3.5,  # 연 배당수익률
            "last_payment_date": None,
        },
        "SDTY": {
            "name": "일드맥스 S&P500 커버드콜",
            "frequency": "MONTHLY",  # 월 배당
            "yield_percent": 13.0,  # 연 배당수익률
            "last_payment_date": None,
        }
    }
    
    def __init__(self):
        self.dividends = self.load_dividends()
    
    def load_dividends(self):
        """저장된 배당금 정보 로드"""
        if os.path.exists(DIVIDEND_FILE):
            try:
                with open(DIVIDEND_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"배당금 정보 로드 실패: {str(e)}")
                return {}
        return {}
    
    def save_dividends(self):
        """배당금 정보 저장"""
        try:
            os.makedirs(DATA_PATH, exist_ok=True)
            with open(DIVIDEND_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.dividends, f, indent=2, ensure_ascii=False)
            logger.info("배당금 정보 저장 완료")
            return True
        except Exception as e:
            logger.error(f"배당금 정보 저장 실패: {str(e)}")
            return False
    
    def calculate_dividend(self, symbol, quantity, current_price):
        """
        예상 배당금 계산
        
        Args:
            symbol: ETF 심볼
            quantity: 보유 수량
            current_price: 현재가
        
        Returns:
            dict: 배당금 정보
        """
        if symbol not in self.DIVIDEND_INFO:
            return None
        
        info = self.DIVIDEND_INFO[symbol]
        total_investment = quantity * current_price
        
        # 연 배당금
        annual_dividend = total_investment * (info['yield_percent'] / 100)
        
        # 월 배당금
        monthly_dividend = annual_dividend / 12
        
        return {
            'symbol': symbol,
            'name': info['name'],
            'quantity': quantity,
            'current_price': current_price,
            'total_investment': total_investment,
            'yield_percent': info['yield_percent'],
            'annual_dividend': round(annual_dividend, 2),
            'monthly_dividend': round(monthly_dividend, 2),
            'frequency': info['frequency']
        }
    
    def record_dividend_payment(self, symbol, dividend_amount, payment_date=None):
        """
        배당금 지급 기록
        
        Args:
            symbol: ETF 심볼
            dividend_amount: 배당금액
            payment_date: 지급일 (기본값: 현재 날짜)
        """
        if payment_date is None:
            payment_date = datetime.now().strftime("%Y-%m-%d")
        
        if symbol not in self.dividends:
            self.dividends[symbol] = {
                "name": self.DIVIDEND_INFO.get(symbol, {}).get('name', symbol),
                "payments": []
            }
        
        payment = {
            "amount": dividend_amount,
            "payment_date": payment_date,
            "recorded_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.dividends[symbol]["payments"].append(payment)
        self.save_dividends()
        
        logger.info(f"{symbol} 배당금 기록: ${dividend_amount:,.2f}")
        return True
    
    def should_pay_dividend(self, symbol):
        """
        배당금 지급 여부 확인 (월간 배당 기준)
        
        Args:
            symbol: ETF 심볼
        
        Returns:
            bool: 배당금 지급 여부
        """
        if symbol not in self.DIVIDEND_INFO:
            return False
        
        # 배당금 지급 기록 확인
        if symbol not in self.dividends or not self.dividends[symbol]["payments"]:
            # 처음으로 배당금을 받을 수 있음
            return True
        
        # 마지막 배당금 지급일로부터 30일 이상 경과했는지 확인
        last_payment = self.dividends[symbol]["payments"][-1]
        last_payment_date = datetime.strptime(last_payment["payment_date"], "%Y-%m-%d")
        days_since_payment = (datetime.now() - last_payment_date).days
        
        # 월 배당의 경우 30일 이상 경과시 다시 배당 가능
        return days_since_payment >= 30
    
    def get_dividend_summary(self, portfolio_summary):
        """
        포트폴리오 배당금 요약
        
        Args:
            portfolio_summary: 포트폴리오 요약 정보
        
        Returns:
            dict: 배당금 요약
        """
        total_annual = 0
        total_monthly = 0
        dividend_details = []
        
        for asset in portfolio_summary["assets"]:
            symbol = asset["symbol"]
            quantity = asset["total_quantity"]
            current_price = asset["total_invested"] / quantity if quantity > 0 else 0
            
            dividend_info = self.calculate_dividend(symbol, quantity, current_price)
            
            if dividend_info:
                total_annual += dividend_info["annual_dividend"]
                total_monthly += dividend_info["monthly_dividend"]
                dividend_details.append(dividend_info)
        
        return {
            "total_annual_dividend": round(total_annual, 2),
            "total_monthly_dividend": round(total_monthly, 2),
            "details": dividend_details
        }
    
    def create_dividend_message(self, symbol, dividend_info):
        """
        배당금 알림 메시지 생성
        
        Args:
            symbol: ETF 심볼
            dividend_info: 배당금 정보
        
        Returns:
            str: 포맷된 메시지
        """
        message = f"""
💰 ETF 배당금 지급 알림
{'='*50}

📊 ETF: {dividend_info['name']} ({symbol})
💵 배당금액: ${dividend_info['monthly_dividend']:,.2f}
📈 배당수익률: {dividend_info['yield_percent']}%
📅 지급주기: {dividend_info['frequency']}

📊 상세 정보:
   - 보유 수량: {dividend_info['quantity']}주
   - 현재가: ${dividend_info['current_price']:,.2f}
   - 투자액: ${dividend_info['total_investment']:,.2f}
   - 연 배당금: ${dividend_info['annual_dividend']:,.2f}
   - 월 배당금: ${dividend_info['monthly_dividend']:,.2f}

💡 팁: 이 배당금을 재투자하면 복리 효과로 더 큰 수익을 얻을 수 있습니다!

⏰ 지급 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*50}
        """
        return message
    
    def create_dividend_summary_message(self, portfolio_summary):
        """
        포트폴리오 배당금 요약 메시지 생성
        
        Args:
            portfolio_summary: 포트폴리오 요약 정보
        
        Returns:
            str: 포맷된 메시지
        """
        dividend_summary = self.get_dividend_summary(portfolio_summary)
        
        message = f"""
💰 포트폴리오 배당금 요약
{'='*50}

📊 월 배당금 예상액: ${dividend_summary['total_monthly_dividend']:,.2f}
📈 연 배당금 예상액: ${dividend_summary['total_annual_dividend']:,.2f}

📋 ETF별 배당금:
"""
        
        for detail in dividend_summary['details']:
            message += f"""
{detail['name']} ({detail['symbol']})
   월 배당: ${detail['monthly_dividend']:,.2f}
   연 배당: ${detail['annual_dividend']:,.2f}
   수익률: {detail['yield_percent']}%
"""
        
        message += f"""
{'='*50}
⏰ 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return message


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    dt = DividendTracker()
    
    # 테스트
    dividend = dt.calculate_dividend("QYLD", 235, 45.50)
    print(dt.create_dividend_message("QYLD", dividend))
