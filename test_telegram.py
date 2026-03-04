"""
텔레그램 알림 테스트 스크립트
"""
import requests
from config import NOTIFICATION_CONFIG
from datetime import datetime

def test_telegram():
    """텔레그램 메시지 전송 테스트"""
    
    bot_token = NOTIFICATION_CONFIG['TELEGRAM_BOT_TOKEN']
    chat_id = NOTIFICATION_CONFIG['TELEGRAM_CHAT_ID']
    
    if not bot_token or not chat_id:
        print("❌ 텔레그램 토큰이 설정되지 않았습니다.")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        test_message = f"""
✅ 텔레그램 연결 테스트 성공!

🤖 봇 토큰: {bot_token[:20]}...
💬 채팅 ID: {chat_id}
⏰ 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

이제 ETF 거래 신호를 받을 준비가 되었습니다!
        """
        
        payload = {
            "chat_id": chat_id,
            "text": test_message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ 텔레그램 연결 성공! 메시지가 전송되었습니다.")
            return True
        else:
            print(f"❌ 텔레그램 전송 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("텔레그램 연결 테스트")
    print("=" * 50)
    test_telegram()
