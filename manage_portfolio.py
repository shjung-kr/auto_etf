"""
자산 관리 CLI 도구
포트폴리오에 자산을 추가, 수정, 제거할 수 있습니다.
"""

import logging
import sys
import io
from portfolio_manager import PortfolioManager

# Windows 콘솔 이모지 인코딩 문제 해결
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)


def print_menu():
    """메뉴 출력"""
    print("\n" + "="*60)
    print("💼 포트폴리오 관리")
    print("="*60)
    print("1. ETF 자산 추가")
    print("2. 보유 자산 조회")
    print("3. 자산 수정")
    print("4. 자산 제거")
    print("5. 💰 현금 관리")
    print("6. 포트폴리오 전체 보기")
    print("7. 종료")
    print("="*60)


def add_asset(pm):
    """자산 추가"""
    print("\n📝 새 자산 추가")
    print("-" * 40)
    
    symbol = input("ETF 심볼 입력 (예: QYLD): ").strip().upper()
    if not symbol:
        print("❌ 심볼을 입력해주세요.")
        return
    
    name = input("ETF 이름 입력 (예: 글로벌엑스 나스닥100 커버드콜): ").strip()
    if not name:
        print("❌ 이름을 입력해주세요.")
        return
    
    try:
        quantity = int(input("보유 개수 입력 (예: 100): "))
        purchase_price = float(input("매입가 입력 (예: 45.50): "))
        purchase_date = input("매입 날짜 입력 (YYYY-MM-DD) [선택사항, 엔터로 넘김]: ").strip()
        
        if purchase_date == "":
            purchase_date = None
        
        pm.add_asset(symbol, name, quantity, purchase_price, purchase_date)
        print(f"✅ {name} {quantity}주가 추가되었습니다!")
        
    except ValueError:
        print("❌ 개수와 가격은 숫자로 입력해주세요.")


def list_assets(pm):
    """자산 조회"""
    summary = pm.get_portfolio_summary()
    
    # 현금 표시
    cash = pm.get_cash()
    print(f"\n💰 현금: ${cash:,.2f}" if cash > 0 else "\n💰 현금: $0.00")
    
    if not summary["assets"]:
        print("\n📭 보유 ETF 자산이 없습니다.")
        print(f"\n총 자산액: ${summary['total_value']:,.2f}")
        return
    
    print("\n📋 보유 ETF 자산 목록")
    print("-" * 70)
    
    for asset in summary["assets"]:
        print(f"\n{asset['symbol']:6s} | {asset['name']:<40s}")
        print(f"  수량: {asset['total_quantity']:>6.0f}주 | 투자액: ${asset['total_invested']:>12,.2f}")
    
    print("\n" + "-" * 70)
    print(f"ETF 투자액: ${summary['total_invested']:,.2f}")
    print(f"현금 잔고:  ${summary['total_cash']:,.2f}")
    print(f"총 자산액: ${summary['total_value']:,.2f}")
    print("-" * 70)


def update_asset(pm):
    """자산 수정"""
    summary = pm.get_portfolio_summary()
    
    if not summary["assets"]:
        print("\n📭 보유 자산이 없습니다.")
        return
    
    print("\n✏️  자산 수정")
    print("-" * 40)
    
    # 자산 선택
    for i, asset in enumerate(summary["assets"]):
        print(f"{i}. {asset['symbol']} - {asset['name']}")
    
    try:
        asset_idx = int(input("수정할 자산 번호를 입력하세요: "))
        asset = summary["assets"][asset_idx]
        symbol = asset["symbol"]
        
        # 보유 내역 선택
        holdings = asset["holdings"]
        if len(holdings) == 1:
            holding_idx = 0
        else:
            print(f"\n{symbol}의 보유 내역:")
            for i, h in enumerate(holdings):
                print(f"{i}. {h['quantity']}주 @ ${h['purchase_price']} ({h['purchase_date']})")
            holding_idx = int(input("수정할 내역 번호를 입력하세요: "))
        
        # 수정 항목 선택
        print("\n1. 개수 수정")
        print("2. 매입가 수정")
        print("3. 둘 다 수정")
        
        choice = input("수정할 항목을 선택하세요: ").strip()
        
        quantity = None
        purchase_price = None
        
        if choice in ["1", "3"]:
            quantity = int(input("새로운 개수: "))
        
        if choice in ["2", "3"]:
            purchase_price = float(input("새로운 매입가: "))
        
        if pm.update_asset(symbol, holding_idx, quantity, purchase_price):
            print("✅ 자산이 수정되었습니다!")
        else:
            print("❌ 자산 수정에 실패했습니다.")
    
    except (ValueError, IndexError):
        print("❌ 올바른 번호를 입력해주세요.")


def remove_asset(pm):
    """자산 제거"""
    summary = pm.get_portfolio_summary()
    
    if not summary["assets"]:
        print("\n📭 보유 자산이 없습니다.")
        return
    
    print("\n🗑️  자산 제거")
    print("-" * 40)
    
    # 자산 선택
    for i, asset in enumerate(summary["assets"]):
        print(f"{i}. {asset['symbol']} - {asset['name']}")
    
    try:
        asset_idx = int(input("제거할 자산 번호를 입력하세요: "))
        asset = summary["assets"][asset_idx]
        symbol = asset["symbol"]
        
        # 전체 또는 특정 보유 내역만 제거
        holdings = asset["holdings"]
        if len(holdings) == 1:
            holding_idx = None
            confirm = input(f"'{asset['name']}'을 제거하시겠습니까? (y/n): ")
        else:
            print(f"\n{symbol}의 보유 내역:")
            print(f"0. 전체 제거")
            for i, h in enumerate(holdings):
                print(f"{i+1}. {h['quantity']}주 @ ${h['purchase_price']} ({h['purchase_date']})")
            
            choice = int(input("선택: "))
            holding_idx = None if choice == 0 else choice - 1
            confirm = input(f"정말 제거하시겠습니까? (y/n): ")
        
        if confirm.lower() == "y":
            if pm.remove_asset(symbol, holding_idx):
                print("✅ 자산이 제거되었습니다!")
            else:
                print("❌ 자산 제거에 실패했습니다.")
        else:
            print("취소되었습니다.")
    
    except (ValueError, IndexError):
        print("❌ 올바른 번호를 입력해주세요.")


def manage_cash(pm):
    """현금 관리"""
    print("\n" + "="*60)
    print("💰 현금 관리")
    print("="*60)
    print("1. 현금 추가")
    print("2. 현금 current 확인")
    print("3. 현금 수정")
    print("4. 현금 제거")
    print("5. 돌아가기")
    print("="*60)
    
    choice = input("선택해주세요 (1-5): ").strip()
    
    if choice == "1":
        # 현금 추가
        print("\n💵 현금 추가")
        print("-" * 40)
        try:
            amount = float(input("추가할 현금액 입력 (예: 10000): "))
            description = input("설명 입력 (예: 초기 자금, 월급) [선택사항]: ").strip()
            if description == "":
                description = "현금"
            
            if pm.add_cash(amount, description):
                print(f"✅ ${amount:,.2f}이(가) 추가되었습니다!")
            else:
                print("❌ 현금 추가에 실패했습니다.")
        except ValueError:
            print("❌ 숫자로 입력해주세요.")
    
    elif choice == "2":
        # 현금 확인
        cash = pm.get_cash()
        print(f"\n💵 현재 보유 현금: ${cash:,.2f}")
        
        if "CASH" in pm.portfolio:
            print("\n현금 내역:")
            for i, holding in enumerate(pm.portfolio["CASH"]["holdings"]):
                desc = holding.get("description", "현금")
                print(f"  [{i}] ${holding['total_invested']:,.2f} ({desc}) - {holding['added_date']}")
    
    elif choice == "3":
        # 현금 수정
        cash = pm.get_cash()
        if cash == 0:
            print("\n현금이 없습니다.")
            return
        
        print(f"\n현재 보유 현금: ${cash:,.2f}")
        
        if "CASH" in pm.portfolio:
            holdings = pm.portfolio["CASH"]["holdings"]
            print("\n현금 내역:")
            for i, h in enumerate(holdings):
                desc = h.get("description", "현금")
                print(f"  [{i}] ${h['total_invested']:,.2f} ({desc})")
            
            try:
                holding_idx = int(input("\n수정할 내역 번호를 입력하세요: "))
                new_amount = float(input("새로운 금액 입력: "))
                
                if pm.update_cash(holding_idx, new_amount):
                    print(f"✅ 현금이 ${new_amount:,.2f}로 수정되었습니다!")
                else:
                    print("❌ 현금 수정에 실패했습니다.")
            except ValueError:
                print("❌ 올바른 번호를 입력해주세요.")
    
    elif choice == "4":
        # 현금 제거
        cash = pm.get_cash()
        if cash == 0:
            print("\n현금이 없습니다.")
            return
        
        print(f"\n현재 보유 현금: ${cash:,.2f}")
        
        if "CASH" in pm.portfolio:
            holdings = pm.portfolio["CASH"]["holdings"]
            print("\n현금 내역:")
            print("0. 전체 제거")
            for i, h in enumerate(holdings):
                desc = h.get("description", "현금")
                print(f"  [{i+1}] ${h['total_invested']:,.2f} ({desc})")
            
            try:
                choice = int(input("\n선택: "))
                holding_idx = None if choice == 0 else choice - 1
                
                confirm = input("정말 제거하시겠습니까? (y/n): ")
                if confirm.lower() == "y":
                    if pm.remove_cash(holding_idx):
                        print("✅ 현금이 제거되었습니다!")
                    else:
                        print("❌ 현금 제거에 실패했습니다.")
                else:
                    print("취소되었습니다.")
            except ValueError:
                print("❌ 올바른 번호를 입력해주세요.")


def main():
    """메인 함수"""
    pm = PortfolioManager()
    
    print("\n🎯 자산 관리 시스템에 오신 것을 환영합니다!")
    
    while True:
        print_menu()
        choice = input("선택해주세요 (1-7): ").strip()
        
        if choice == "1":
            add_asset(pm)
        elif choice == "2":
            list_assets(pm)
        elif choice == "3":
            update_asset(pm)
        elif choice == "4":
            remove_asset(pm)
        elif choice == "5":
            manage_cash(pm)
        elif choice == "6":
            pm.print_portfolio()
        elif choice == "7":
            print("\n👋 프로그램을 종료합니다.")
            break
        else:
            print("❌ 1~7 중 하나를 선택해주세요.")


if __name__ == "__main__":
    main()
