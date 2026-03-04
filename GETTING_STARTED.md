# 🚀 ETF 자동 거래 프로그램 - 설치 및 실행 가이드

## 빠른 시작 (5분)

### 1단계: 파이썬 설치
- [Python 3.8+ 다운로드](https://www.python.org/downloads/)
- 설치 시 **"Add Python to PATH"** 체크 필수!

### 2단계: 프로그램 실행

#### Windows 사용자
```bash
start.bat
```

#### Mac/Linux 사용자
```bash
bash start.sh
```

또는 수동 설치:

```bash
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 필요한 라이브러리 설치
pip install -r requirements.txt

# 빠른 시작 실행
python quick_start.py
```

## 상세 설설 가이드

### 1. 환경 설정

#### .env 파일 설정 (선택사항)
1. `.env.example` 파일을 `.env`로 복사
2. 다음 정보 입력:

```env
# Gmail 알림 (선택사항)
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Discord 웹훅 (선택사항)
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
```

#### Gmail 앱 비밀번호 생성
1. Google 계정 접속: https://myaccount.google.com/
2. 좌측 "보안" 메뉴
3. 2단계 인증 활성화
4. "앱 비밀번호" 검색 후 생성
5. 생성된 16자리 비밀번호를 .env에 입력

#### Discord 웹훅 설정
1. Discord 서버 접속
2. 채널 → 설정 → 연동
3. 웹훅 → "새 웹훅" 생성
4. URL 복사

### 2. ETF 목록 커스터마이징

`config.py`에서 `ETF_LIST`를 수정:

```python
ETF_LIST = {
    "TIGER 200": "069500.KS",
    "KODEX 200": "069660.KS",
    "TIGER 나스닥100": "133690.KS",
    # 원하는 ETF 추가 가능
}
```

**주요 한국 ETF 티커:**
- TIGER 200: 069500.KS
- KODEX 200: 069660.KS
- TIGER 미국나스닥100: 133690.KS
- KODEX 레버리지: 122630.KS
- TIGER 인버스: 114800.KS
- KODEX S&P500: 102110.KS

### 3. 거래 전략 커스터마이징

#### 기술 지표 설정
```python
ANALYSIS_CONFIG = {
    "MA_SHORT": 20,      # 단기 이동평균선 (더 작으면 더 민감)
    "MA_LONG": 60,       # 장기 이동평균선
    "RSI_PERIOD": 14,    # RSI 기간
    "RSI_OVERBUY": 70,   # 과매수 (높을수록 신호 감소)
    "RSI_OVERSELL": 30,  # 과매도 (낮을수록 신호 증가)
}
```

#### 수익률 및 손절 설정
```python
PROFIT_CONFIG = {
    "TARGET_PROFIT": 0.05,      # 5% 이익 시 손절
    "STOP_LOSS": -0.03,         # -3% 손실 시 청산
    "MIN_HOLD_DAYS": 5,         # 최소 5일 보유
}
```

#### 신호 강도 조정
```python
TRADING_CONFIG = {
    "BUY_SIGNAL_STRENGTH": 2,   # 2개 이상의 신호 필요 (1-4)
    "SELL_SIGNAL_STRENGTH": 2,  # 매도도 동일하게 필요
}
```

## 프로그램 사용법

### 메인 프로그램 실행
```bash
python main.py
```

### 대화형 메뉴
```
1. 한 번 분석 실행      → 즉시 분석
2. 자동 스케줄 시작     → 매일 자동 실행
3. 포트폴리오 상태      → 열린 포지션 확인
4. 거래 이력 조회       → 과거 거래 보기
5. 종료                → 프로그램 종료
```

### 테스트 실행
프로그램을 처음 사용하기 전에 테스트:
```bash
python test.py
```

### 리포트 생성
거래 결과를 분석하고 리포트 생성:
```bash
python analyzer_reporter.py
```

생성되는 파일:
- `data/portfolio_*.csv` - 현재 포트폴리오
- `data/trading_history_*.csv` - 거래 이력
- `reports/performance_report_*.txt` - 성과 리포트
- `data/report_*.json` - 상세 데이터 (JSON)

## 신호 해석

### 매수 신호 (BUY)
- ✅ 이동평균: 단기 > 장기 (상향 추세)
- ✅ RSI: 30 이하 (과매도)
- ✅ MACD: MACD > 신호선 (상향)

→ 2개 이상의 신호 → **매수**

### 매도 신호 (SELL)
- ✅ 이동평균: 단기 < 장기 (하향 추세)
- ✅ RSI: 70 이상 (과매수)
- ✅ MACD: MACD < 신호선 (하향)
- ✅ 목표 수익률 도달: 5% 수익
- ✅ 손절 기준 도달: -3% 손실

→ 2개 이상의 신호 → **매도**

## 로그 및 데이터

### 로그 파일
```
logs/etf_trader_YYYYMMDD.log
```
- 분석 결과
- 신호 생성
- 오류 및 경고

### 데이터 파일
```
data/                    # 수집한 데이터
reports/                 # 생성된 리포트
```

## 트러블슈팅

### 문제: "Python not found"
- **해결**: Python을 설치하고 PATH에 추가했는지 확인
- 명령어: `python --version`

### 문제: "No module named 'yfinance'"
- **해결**: 의존 라이브러리 설치
- 명령어: `pip install -r requirements.txt`

### 문제: 데이터를 불러올 수 없음
- **해결**: 인터넷 연결 확인
- 명령어: `python test.py` 로 테스트

### 문제: 스케줄이 실행되지 않음
- **해결**: 프로그램을 백그라운드에서 계속 실행해야 함
- 메뉴에서 "2. 자동 스케줄 시작" 선택 후 창 유지

## 자동 실행 설정

### Windows 작업 스케줄러
1. "작업 스케줄러" 열기
2. "기본 작업 만들기"
3. 트리거: 매일 시간 설정
4. 작업: `python main.py`

### Mac/Linux (crontab)
```bash
# crontab 편집
crontab -e

# 매일 09:30 실행
30 09 * * * cd /path/to/auto_stock_v2 && python main.py
```

## 주요 파일 설명

| 파일 | 설명 |
|------|------|
| `main.py` | 메인 프로그램 |
| `etf_analyzer.py` | ETF 분석 모듈 |
| `trading_signals.py` | 거래 신호 생성 |
| `notification_manager.py` | 알림 관리 |
| `config.py` | 설정 파일 |
| `quick_start.py` | 초기 설정 스크립트 |
| `test.py` | 테스트 스크립트 |
| `analyzer_reporter.py` | 리포트 생성 스크립트 |
| `requirements.txt` | 필요 라이브러리 목록 |

## ⚠️ 중요 주의사항

1. **시뮬레이션**
   - 현재 프로그램은 분석 및 신호 생성만 수행
   - 실제 주문은 미포함
   - 실제 거래 연동 시 증권사 API 필수

2. **위험 관리**
   - 목표 수익률과 손절은 신중하게 설정
   - 과도한 거래 방지
   - 충분한 테스트 후 사용

3. **시장 조건**
   - 기술 지표는 100% 정확하지 않음
   - 시장 상황에 따라 신호 실패 가능
   - 항상 모니터링 필수

4. **백업 및 복구**
   - 거래 이력을 정기적으로 백업
   - 설정값을 안전하게 저장

## 성과 향상 팁

1. **파라미터 최적화**
   - 과거 데이터로 백테스트
   - 다양한 조합 시도
   - 일관된 결과 확인

2. **신호 필터링**
   - 신호 강도 조정 (1-4)
   - 특정 시간대만 거래 가능
   - 거래량 기반 필터

3. **리스크 관리**
   - 손절을 항상 설정
   - 목표 수익률 실현
   - 포지션 사이징

4. **모니터링**
   - 정기적으로 로그 확인
   - 성과 분석
   - 필요시 조정

## 피드백 및 개선

더 나은 기능이나 개선 사항이 있으면:
1. 로그 파일 확인
2. 테스트 실행
3. 설정값 조정
4. 재실행

---

행운을 빕니다! 🚀📈

**마지막 업데이트: 2026-03-04**
