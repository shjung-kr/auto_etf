import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from config import NOTIFICATION_CONFIG

logger = logging.getLogger(__name__)


class NotificationManager:
    """알림 관리 클래스"""
    
    def __init__(self):
        self.notifications = []
    
    def create_message(self, signal_data, trade_suggestion=None):
        """
        신호 데이터를 기반으로 알림 메시지 생성 (요구 포맷)
        1. 종목 : 현재가
        2. 수익률 : %
        3. 배당: 있으면, 금액 적고(날짜), 없으면 배당없음
        4. 거래신호: 매수 XX개, 매도 XX개, 거래금액 :
        5. 한국 시간 기준 거래가능시간
        """
        from config import TRADING_CONFIG
        from dividend_tracker import DividendTracker
        symbol = signal_data['symbol']
        signal = signal_data['signal']
        current_price = signal_data['current_price']
        analysis = signal_data['analysis']
        returns_1m = analysis['returns'].get('return_1m', 'N/A')
        returns_1w = analysis['returns'].get('return_1w', 'N/A')
        # 1. 종목 : 현재가
        message = f"\n[종목] {symbol} : ${current_price:,.2f}"
        # 2. 수익률 : %
        message += f"\n[수익률] 1주: {returns_1w}% / 1개월: {returns_1m}%"
        # 3. 배당
        dividend_tracker = DividendTracker()
        # 포트폴리오 정보가 없으므로 1주 보유 가정
        dividend_info = dividend_tracker.calculate_dividend(symbol, 1, current_price)
        if dividend_info and dividend_info['monthly_dividend'] > 0:
            message += f"\n[배당] 월 ${dividend_info['monthly_dividend']:,.2f} (연 {dividend_info['yield_percent']}%)"
        else:
            message += "\n[배당] 배당없음"
        # 4. 거래신호
        buy_signals = signal_data.get('buy_signals', 0)
        sell_signals = signal_data.get('sell_signals', 0)
        trade_amount = 0
        if trade_suggestion:
            trade_amount = trade_suggestion.get('total_investment', 0)
        message += f"\n[거래신호] 매수 {buy_signals}개, 매도 {sell_signals}개, 거래금액: ${trade_amount:,.2f}"
        # 5. 한국 시간 기준 거래가능시간
        start = TRADING_CONFIG.get('TRADING_HOURS_START', '09:00')
        end = TRADING_CONFIG.get('TRADING_HOURS_END', '16:00')
        message += f"\n[한국 거래가능시간] {start} ~ {end} (KST)"
        message += f"\n⏰ 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message += "\n" + "="*50
        return message
    
    def send_console_notification(self, signal_data):
        """
        콘솔로 알림 전송
        
        Args:
            signal_data: 거래 신호 데이터
        """
        message = self.create_message(signal_data)
        print(message)
        logger.info(f"콘솔 알림 전송: {signal_data['symbol']}")
    
    def send_email_notification(self, signal_data):
        """
        이메일로 알림 전송
        
        Args:
            signal_data: 거래 신호 데이터
        """
        if not NOTIFICATION_CONFIG['SEND_EMAIL']:
            return False
        
        try:
            email = NOTIFICATION_CONFIG['EMAIL_ADDRESS']
            password = NOTIFICATION_CONFIG['EMAIL_PASSWORD']
            
            if not email or not password:
                logger.warning("이메일 설정이 없습니다.")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = email
            msg['Subject'] = f"[ETF 거래 신호] {signal_data['symbol']} - {signal_data['signal']}"
            
            body = self.create_message(signal_data)
            msg.attach(MIMEText(body, 'plain'))
            
            # Gmail SMTP 서버 사용 (앱 비밀번호 필요)
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email, password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"이메일 알림 전송: {email}")
            return True
        
        except Exception as e:
            logger.error(f"이메일 전송 실패: {str(e)}")
            return False
    
    def send_telegram_notification(self, signal_data, trade_suggestion=None):
        """
        텔레그램으로 알림 전송
        
        Args:
            signal_data: 거래 신호 데이터
            trade_suggestion: 매수/매도 추천 정보 (선택사항)
        """
        if not NOTIFICATION_CONFIG['SEND_TELEGRAM']:
            return False
        
        bot_token = NOTIFICATION_CONFIG['TELEGRAM_BOT_TOKEN']
        chat_id = NOTIFICATION_CONFIG['TELEGRAM_CHAT_ID']
        
        if not bot_token or not chat_id:
            logger.warning("텔레그램 설정이 없습니다.")
            return False
        
        try:
            message = self.create_message(signal_data, trade_suggestion)
            
            # 텔레그램 메시지 전송 API URL
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"텔레그램 알림 전송 완료: {signal_data['symbol']}")
                return True
            else:
                logger.error(f"텔레그램 전송 실패: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"텔레그램 알림 전송 실패: {str(e)}")
            return False
    
    def send_discord_notification(self, signal_data):
        """
        Discord로 알림 전송
        
        Args:
            signal_data: 거래 신호 데이터
        """
        if not NOTIFICATION_CONFIG['SEND_DISCORD']:
            return False
        
        webhook_url = NOTIFICATION_CONFIG['DISCORD_WEBHOOK']
        
        if not webhook_url:
            logger.warning("Discord Webhook이 설정되지 않았습니다.")
            return False
        
        try:
            symbol = signal_data['symbol']
            signal = signal_data['signal']
            confidence = signal_data['confidence']
            current_price = signal_data['current_price']
            
            # 신호에 따른 색상 지정
            color = 3066993 if signal == 'BUY' else 15158332 if signal == 'SELL' else 9807270
            
            embed = {
                "title": f"{symbol} - {signal}",
                "color": color,
                "fields": [
                    {"name": "신호", "value": signal, "inline": True},
                    {"name": "신뢰도", "value": f"{confidence:.0f}%", "inline": True},
                    {"name": "현재 가격", "value": f"{current_price}", "inline": False},
                    {
                        "name": "기술 지표",
                        "value": f"MA: {signal_data['analysis']['moving_average'].get('signal', 'N/A')}\nRSI: {signal_data['analysis']['rsi'].get('rsi', 'N/A')}",
                        "inline": False
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            payload = {"embeds": [embed]}
            
            response = requests.post(webhook_url, json=payload)
            
            if response.status_code == 204:
                logger.info(f"Discord 알림 전송 완료: {symbol}")
                return True
            else:
                logger.error(f"Discord 전송 실패: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Discord 알림 전송 실패: {str(e)}")
            return False
    
    def send_all_notifications(self, signal_data, trade_suggestion=None):
        """
        모든 설정된 채널로 알림 전송
        
        Args:
            signal_data: 거래 신호 데이터
            trade_suggestion: 매수/매도 추천 정보 (선택사항)
        """
        # 콘솔 알림 (항상 전송)
        print("\n" + "="*70)
        print(self.create_message(signal_data, trade_suggestion))
        print("="*70 + "\n")
        logger.info(f"콘솔 알림 전송: {signal_data['symbol']}")
        
        # 텔레그램 알림
        if NOTIFICATION_CONFIG['SEND_TELEGRAM']:
            self.send_telegram_notification(signal_data, trade_suggestion)
        
        # 이메일 알림
        if NOTIFICATION_CONFIG['SEND_EMAIL']:
            self.send_email_notification(signal_data)
        
        # Discord 알림
        if NOTIFICATION_CONFIG['SEND_DISCORD']:
            self.send_discord_notification(signal_data)
        
        self.notifications.append({
            'symbol': signal_data['symbol'],
            'signal': signal_data['signal'],
            'timestamp': datetime.now()
        })
    
    def send_dividend_notification(self, dividend_message):
        """
        배당금 지급 알림 전송 (텔레그램)
        
        Args:
            dividend_message: 배당금 알림 메시지
        """
        if not NOTIFICATION_CONFIG['SEND_TELEGRAM']:
            return False
        
        bot_token = NOTIFICATION_CONFIG['TELEGRAM_BOT_TOKEN']
        chat_id = NOTIFICATION_CONFIG['TELEGRAM_CHAT_ID']
        
        if not bot_token or not chat_id:
            logger.warning("텔레그램 설정이 없습니다.")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": dividend_message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("배당금 알림 전송 완료")
                return True
            else:
                logger.error(f"배당금 알림 전송 실패: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"배당금 알림 전송 실패: {str(e)}")
            return False
    
    def send_dividend_summary_notification(self, dividend_summary_message):
        """
        배당금 요약 알림 전송 (텔레그램)
        
        Args:
            dividend_summary_message: 배당금 요약 메시지
        """
        if not NOTIFICATION_CONFIG['SEND_TELEGRAM']:
            return False
        
        bot_token = NOTIFICATION_CONFIG['TELEGRAM_BOT_TOKEN']
        chat_id = NOTIFICATION_CONFIG['TELEGRAM_CHAT_ID']
        
        if not bot_token or not chat_id:
            logger.warning("텔레그램 설정이 없습니다.")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": dividend_summary_message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("배당금 요약 알림 전송 완료")
                return True
            else:
                logger.error(f"배당금 요약 알림 전송 실패: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"배당금 요약 알림 전송 실패: {str(e)}")
            return False
    
    def get_notification_history(self):
        """알림 이력 반환"""
        return self.notifications
