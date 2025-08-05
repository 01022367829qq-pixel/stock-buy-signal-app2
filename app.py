import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="📈 매수 타점 분석기", layout="wide")

# 스타일 설정
st.markdown("""
    <style>
    .card {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.2s;
        height: 100%;
        margin-bottom: 20px;
    }
    .card:hover {
        transform: scale(1.02);
        background-color: #e8f5e9;
    }
    .card-title {
        font-size: 20px;
        font-weight: bold;
        color: #2e7d32;
        margin-bottom: 10px;
    }
    .card-desc {
        font-size: 14px;
        color: #555;
        margin-bottom: 15px;
    }
    input {
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ATR 계산 함수
def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

# 터틀 트레이딩 변형 점수 함수 (데이 트레이딩용)
def score_turtle_day_trading(df):
    # 데이터 충분성 체크
    if df is None or df.empty or len(df) < 30:
        return 0, "데이터가 충분하지 않습니다."

    # 지표 계산
    df = df.copy()
    df['20d_high'] = df['High'].rolling(window=20).max().shift(1)
    df['10d_low']  = df['Low'].rolling(window=10).min().shift(1)
    df['ATR']      = calculate_atr(df, 14)

    # 마지막 값 추출 (스칼라)
    close_last = df['Close'].iat[-1]
    high_20d   = df['20d_high'].iat[-1]
    low_10d    = df['10d_low'].iat[-1]
    atr_val    = df['ATR'].iat[-1]

    # NaN or None 체크
    if any([high_20d is None, low_10d is None, atr_val is None,
            (isinstance(high_20d, float) and np.isnan(high_20d)),
            (isinstance(low_10d, float)  and np.isnan(low_10d)),
            (isinstance(atr_val, float)  and np.isnan(atr_val))]):
        return 0, "필요한 기술 지표 데이터가 부족합니다."

    score = 0
    messages = []

    # 매수 신호
    if close_last > high_20d:
        score += 50
        messages.append("20일 최고가 돌파: 매수 신호 강함")

    # 위험 신호
    if close_last < low_10d:
        score -= 30
        messages.append("10일 최저가 이탈: 위험 신호")

    # 변동성 증가 확인
    atr_mean = df['ATR'].rolling(window=30).mean().iat[-1]
    if atr_val > atr_mean:
        score += 30
        messages.append("ATR 증가: 변동성 높음")

    # 점수 한계 설정
    score = max(0, min(100, score))

    if not messages:
        messages.append("신호 없음 - 관망 권장")

    return score, "; ".join(messages)

# 제목
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>📈 매수 타점 분석기</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>당신의 투자 전략에 맞는 종목을 분석해보세요.</p>", unsafe_allow_html=True)
st.markdown("---")

# 카드 묶음 1
col1, col2, col3 = st.columns(3)

# 데이 트레이딩 카드: 터틀 전략 변형 적용
with col1:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>1️⃣ 데이 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>20일 고점 돌파 + 위험 구간 이탈 + ATR 기반 점수 산정</div>", unsafe_allow_html=True)
        ticker1 = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker1")
        if st.button("🔍 분석", key="btn1"):
            if not ticker1.strip():
                st.warning("티커를 입력하세요.")
            else:
                df = yf.download(ticker1, period="3mo", interval="1d")
                if df.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    score, msg = score_turtle_day_trading(df)
                    st.success(f"점수: {score} / 100")
                    st.info(msg)
        st.markdown("</div>", unsafe_allow_html=True)

# 스윙, 포지션 등 나머지 카드(기본 UI만)
with col2:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>2️⃣ 스윙 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>며칠~몇 주 보유, 추세 추종 및 기술적 분석 기반.</div>", unsafe_allow_html=True)
        ticker2 = st.text_input("", placeholder="티커 입력 (예: TSLA)", key="ticker2")
        if st.button("🔍 분석", key="btn2"):
            st.success(f"{ticker2} (스윙 트레이딩) 분석 준비 중...")
        st.markdown("</div>", unsafe_allow_html=True)

with col3:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>3️⃣ 포지션 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>수 주~수년 보유, 업종 분석 및 장기 추세 중심.</div>", unsafe_allow_html=True)
        ticker3 = st.text_input("", placeholder="티커 입력 (예: MSFT)", key="ticker3")
        if st.button("🔍 분석", key="btn3"):
            st.success(f"{ticker3} (포지션 트레이딩) 분석 준비 중...")
        st.markdown("</div>", unsafe_allow_html=True)

# 카드 묶음 2
col4, col5, _ = st.columns([1, 1, 1])

with col4:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>4️⃣ 스캘핑</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>초단타 전략. 수초~수분 보유. 빠른 매매 대응 필요.</div>", unsafe_allow_html=True)
        ticker4 = st.text_input("", placeholder="티커 입력 (예: NVDA)", key="ticker4")
        if st.button("🔍 분석", key="btn4"):
            st.success(f"{ticker4} (스캘핑) 분석 준비 중...")
        st.markdown("</div>", unsafe_allow_html=True)

with col5:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>5️⃣ 뉴스 이벤트 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>실적, 인수, 뉴스 기반으로 단기 변동성 포착.</div>", unsafe_allow_html=True)
        ticker5 = st.text_input("", placeholder="티커 입력 (예: AMZN)", key="ticker5")
        if st.button("🔍 분석", key="btn5"):
            st.success(f"{ticker5} (뉴스 이벤트 트레이딩) 분석 준비 중...")
        st.markdown("</div>", unsafe_allow_html=True)

# 푸터
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; font-size: 13px; color: gray;'>Made by Son Jiwan | Powered by Streamlit</p>",
    unsafe_allow_html=True
)
