import json
import logging
import os
import sys
import io
from datetime import datetime
from config import DATA_PATH

# Windows 콘솔 이모지 인코딩 문제 해결
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logger = logging.getLogger(__name__)

PORTFOLIO_FILE = os.path.join(DATA_PATH, "portfolio.json")


class PortfolioManager:
    """포트폴리오 관리 클래스 - 자산 관리"""
    
    def __init__(self):
        self.portfolio = self.load_portfolio()
    
    def load_portfolio(self):
        """저장된 포트폴리오 로드"""
        if os.path.exists(PORTFOLIO_FILE):
            try:
                with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"포트폴리오 로드 실패: {str(e)}")
                return {}
        return {}
    
    def save_portfolio(self):
        """포트폴리오 저장"""
        try:
            os.makedirs(DATA_PATH, exist_ok=True)
            with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.portfolio, f, indent=2, ensure_ascii=False)
            logger.info("포트폴리오 저장 완료")
            return True
        except Exception as e:
            logger.error(f"포트폴리오 저장 실패: {str(e)}")
            return False
    
    def add_asset(self, symbol, name, quantity, purchase_price, purchase_date=None):
        """
        자산 추가
        
        Args:
            symbol: ETF 심볼 (예: QYLD)
            name: ETF 이름 (예: 글로벌엑스 나스닥100 커버드콜)
            quantity: 보유 개수
            purchase_price: 매입가
            purchase_date: 매입 날짜 (기본값: 현재 날짜)
        """
        if purchase_date is None:
            purchase_date = datetime.now().strftime("%Y-%m-%d")
        
        if symbol not in self.portfolio:
            self.portfolio[symbol] = {
                "name": name,
                "holdings": []
            }
        
        holding = {
            "quantity": quantity,
            "purchase_price": purchase_price,
            "purchase_date": purchase_date,
            "total_invested": quantity * purchase_price,
            "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.portfolio[symbol]["holdings"].append(holding)
        self.save_portfolio()
        
        logger.info(f"자산 추가: {name} {quantity}주 @ ${purchase_price}")
        return True
    
    def update_asset(self, symbol, holding_index, quantity=None, purchase_price=None):
        """
        자산 수정
        
        Args:
            symbol: ETF 심볼
            holding_index: 보유 자산 인덱스
            quantity: 새로운 개수
            purchase_price: 새로운 매입가
        """
        if symbol not in self.portfolio:
            logger.warning(f"자산 '{symbol}'을 찾을 수 없습니다.")
            return False
        
        holdings = self.portfolio[symbol]["holdings"]
        if holding_index >= len(holdings):
            logger.warning(f"보유 자산 인덱스 {holding_index}을 찾을 수 없습니다.")
            return False
        
        if quantity is not None:
            holdings[holding_index]["quantity"] = quantity
        if purchase_price is not None:
            holdings[holding_index]["purchase_price"] = purchase_price
        
        # total_invested 재계산
        holdings[holding_index]["total_invested"] = \
            holdings[holding_index]["quantity"] * holdings[holding_index]["purchase_price"]
        
        self.save_portfolio()
        logger.info(f"자산 수정 완료: {symbol}")
        return True
    
    def remove_asset(self, symbol, holding_index=None):
        """
        자산 제거
        
        Args:
            symbol: ETF 심볼
            holding_index: 보유 자산 인덱스 (None이면 전체 제거)
        """
        if symbol not in self.portfolio:
            logger.warning(f"자산 '{symbol}'을 찾을 수 없습니다.")
            return False
        
        if holding_index is None:
            del self.portfolio[symbol]
            logger.info(f"자산 전체 제거: {symbol}")
        else:
            holdings = self.portfolio[symbol]["holdings"]
            if holding_index < len(holdings):
                holdings.pop(holding_index)
                if not holdings:  # 보유 자산이 없으면 삭제
                    del self.portfolio[symbol]
                logger.info(f"자산 제거: {symbol} (인덱스 {holding_index})")
            else:
                logger.warning(f"보유 자산 인덱스 {holding_index}을 찾을 수 없습니다.")
                return False
        
        self.save_portfolio()
        return True
    
    def add_cash(self, amount, description="초기 현금"):
        """
        현금 추가
        
        Args:
            amount: 현금액
            description: 설명
        """
        if "CASH" not in self.portfolio:
            self.portfolio["CASH"] = {
                "name": "현금 (현재)",
                "holdings": []
            }
        
        holding = {
            "quantity": amount,
            "purchase_price": 1.0,
            "purchase_date": datetime.now().strftime("%Y-%m-%d"),
            "total_invested": amount,
            "description": description,
            "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.portfolio["CASH"]["holdings"].append(holding)
        self.save_portfolio()
        
        logger.info(f"현금 추가: ${amount:,.2f}")
        return True
    
    def get_cash(self):
        """
        현재 현금 잔고 반환
        
        Returns:
            float: 현금액
        """
        if "CASH" not in self.portfolio:
            return 0
        
        total_cash = 0
        for holding in self.portfolio["CASH"]["holdings"]:
            total_cash += holding["total_invested"]
        
        return total_cash
    
    def update_cash(self, holding_index, amount):
        """
        현금 수정
        
        Args:
            holding_index: 보유 현금 인덱스
            amount: 새로운 금액
        """
        if "CASH" not in self.portfolio:
            logger.warning("현금 정보가 없습니다.")
            return False
        
        holdings = self.portfolio["CASH"]["holdings"]
        if holding_index >= len(holdings):
            logger.warning(f"현금 인덱스 {holding_index}을 찾을 수 없습니다.")
            return False
        
        holdings[holding_index]["quantity"] = amount
        holdings[holding_index]["total_invested"] = amount
        
        self.save_portfolio()
        logger.info(f"현금 수정: ${amount:,.2f}")
        return True
    
    def remove_cash(self, holding_index=None):
        """
        현금 제거
        
        Args:
            holding_index: 보유 현금 인덱스 (None이면 전체 제거)
        """
        if "CASH" not in self.portfolio:
            logger.warning("현금 정보가 없습니다.")
            return False
        
        if holding_index is None:
            del self.portfolio["CASH"]
            logger.info("현금 전체 제거")
        else:
            holdings = self.portfolio["CASH"]["holdings"]
            if holding_index < len(holdings):
                holdings.pop(holding_index)
                if not holdings:
                    del self.portfolio["CASH"]
                logger.info(f"현금 제거 (인덱스 {holding_index})")
            else:
                logger.warning(f"현금 인덱스 {holding_index}을 찾을 수 없습니다.")
                return False
        
        self.save_portfolio()
        return True
    
    def get_portfolio_summary(self):
        """포트폴리오 요약 반환"""
        if not self.portfolio:
            return {"total_invested": 0, "total_cash": 0, "total_value": 0, "assets": []}
        
        total_invested = 0
        total_cash = 0
        assets = []
        
        for symbol, data in self.portfolio.items():
            # 현금 항목 처리
            if symbol == "CASH":
                for holding in data["holdings"]:
                    total_cash += holding["total_invested"]
                continue
            
            # 일반 자산 처리
            symbol_total = 0
            symbol_quantity = 0
            valid_holdings = []  # 0 개수가 아닌 항목만 저장
            
            for holding in data["holdings"]:
                if holding["quantity"] > 0:  # 0이 아닌 항목만
                    symbol_total += holding["total_invested"]
                    symbol_quantity += holding["quantity"]
                    valid_holdings.append(holding)
            
            # 유효한 보유량이 있을 때만 추가
            if symbol_quantity > 0:
                total_invested += symbol_total
                assets.append({
                    "symbol": symbol,
                    "name": data["name"],
                    "total_quantity": symbol_quantity,
                    "total_invested": symbol_total,
                    "holdings": valid_holdings
                })
        
        return {
            "total_invested": total_invested,
            "total_cash": total_cash,
            "total_value": total_invested + total_cash,
            "total_assets": len(assets),
            "assets": assets
        }
    
    def get_asset_info(self, symbol):
        """특정 자산 정보 반환"""
        if symbol not in self.portfolio:
            return None
        
        data = self.portfolio[symbol]
        total_quantity = sum(h["quantity"] for h in data["holdings"])
        total_invested = sum(h["total_invested"] for h in data["holdings"])
        
        return {
            "symbol": symbol,
            "name": data["name"],
            "total_quantity": total_quantity,
            "total_invested": total_invested,
            "average_price": total_invested / total_quantity if total_quantity > 0 else 0,
            "holdings": data["holdings"]
        }
    
    def print_portfolio(self):
        """포트폴리오 출력"""
        summary = self.get_portfolio_summary()
        
        print("\n" + "="*80)
        print("📊 포트폴리오 현황")
        print("="*80)
        
        # 현금 표시
        if summary["total_cash"] > 0:
            print(f"\n💵 현금 (현재): ${summary['total_cash']:,.2f}")
            if "CASH" in self.portfolio:
                for i, holding in enumerate(self.portfolio["CASH"]["holdings"]):
                    desc = holding.get("description", "현금")
                    print(f"   [{i}] ${holding['total_invested']:,.2f} ({desc})")
        
        if not summary["assets"]:
            print("\n보유 자산이 없습니다.")
            print(f"\n{'='*80}")
            print(f"총 자산액: ${summary['total_value']:,.2f}")
            print("="*80 + "\n")
            return
        
        for asset in summary["assets"]:
            print(f"\n🔹 {asset['symbol']} - {asset['name']}")
            print(f"   총 수량: {asset['total_quantity']}주")
            print(f"   총 투자액: ${asset['total_invested']:,.2f}")
            print(f"   평균 매입가: ${asset['total_invested']/asset['total_quantity']:,.2f}")
            
            print(f"   보유 내역:")
            for i, holding in enumerate(asset["holdings"]):
                print(f"      [{i}] {holding['quantity']}주 @ ${holding['purchase_price']} "
                      f"({holding['purchase_date']}) = ${holding['total_invested']:,.2f}")
        
        print(f"\n{'='*80}")
        print(f"ETF 투자액: ${summary['total_invested']:,.2f}")
        print(f"현금 잔고:  ${summary['total_cash']:,.2f}")
        print(f"총 자산액: ${summary['total_value']:,.2f}")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)
    
    pm = PortfolioManager()
    
    # 자산 추가 예시
    # pm.add_asset("QYLD", "글로벌엑스 나스닥100 커버드콜", 100, 45.50)
    # pm.add_asset("SCHD", "슈왑 미국 배당주", 50, 80.00)
    # pm.add_asset("SDTY", "일드맥스 S&P500 커버드콜", 30, 65.00)
    
    # 현금 추가 예시
    # pm.add_cash(10000, "초기 자금")
    
    pm.print_portfolio()
