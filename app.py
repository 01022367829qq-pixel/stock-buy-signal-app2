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

# 지표 계산 함수들

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_bollinger(series, window=20, num_std=2):
    ma = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std
    width = upper - lower
    return upper, lower, width


def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# 점수 함수: 터틀 전략 + 보조지표 결합

def score_turtle_enhanced(df):
    # 데이터 충분성 체크
    if df is None or df.empty or len(df) < 60:
        return 0, "데이터가 충분하지 않습니다."

    df = df.copy()
    df['20d_high'] = df['High'].rolling(20).max().shift(1)
    df['10d_low']  = df['Low'].rolling(10).min().shift(1)
    df['ATR']      = calculate_atr(df, 14)
    df['RSI']      = calculate_rsi(df['Close'], 14)
    df['BB_upper'], df['BB_lower'], df['BB_width'] = calculate_bollinger(df['Close'], 20, 2)
    df['BB_width_mean'] = df['BB_width'].rolling(20).mean()
    df['Vol_mean'] = df['Volume'].rolling(20).mean()

    # 결측치 제거 및 인덱스 초기화
    df = df.dropna().reset_index(drop=True)
    if len(df) == 0:
        return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)"

    # 단일 스칼라 값으로 변환 (float)
    close = float(df['Close'].iloc[-1])
    high20 = float(df['20d_high'].iloc[-1])
    low10 = float(df['10d_low'].iloc[-1])
    atr_val = float(df['ATR'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    bbw = float(df['BB_width'].iloc[-1])
    bbw_mean = float(df['BB_width_mean'].iloc[-1])
    vol = float(df['Volume'].iloc[-1])
    vol_mean = float(df['Vol_mean'].iloc[-1])

    score = 0
    msgs = []

    # 터틀 돌파
    if close > high20:
        score += 30
        msgs.append("20일 최고가 돌파")

    # RSI 필터
    if rsi < 50:
        score += 10
        msgs.append(f"RSI({rsi:.1f}) 과매도/중립")

    # 볼린저 밴드 스퀴즈 탈출
    prev_upper = df['BB_upper'].iloc[-2] if len(df) > 1 else None
    if bbw is not None and bbw_mean is not None and prev_upper is not None:
        if bbw < bbw_mean * 0.8 and close > prev_upper:
            score += 15
            msgs.append("BB 수축 후 상단 돌파")

    # 거래량 필터
    if vol > vol_mean * 1.2:
        score += 15
        msgs.append("거래량 증가")

    # ATR 모멘텀
    atr_mean = df['ATR'].rolling(30).mean().iloc[-1]
    if atr_val > atr_mean:
        score += 20
        msgs.append("ATR 증가")

    # 위험 구간 패널티
    if close < low10:
        score -= 20
        msgs.append("10일 최저가 이탈 위험")

    score = max(0, min(100, score))
    if not msgs:
        msgs = ["신호 없음"]
    return score, "; ".join(msgs)

# UI 렌더링
st.markdown("<h1 style='text-align:center; color:#4CAF50;'>📈 매수 타점 분석기</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>당신의 투자 전략에 맞는 종목을 분석해보세요.</p>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>1️⃣ 데이 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>터틀+RSI+BB+거래량+ATR 결합</div>", unsafe_allow_html=True)
        ticker = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_dt")
        if st.button("🔍 분석", key="btn_dt"):
            if not ticker.strip():
                st.warning("티커를 입력하세요.")
            else:
                df = yf.download(ticker, period="3mo", interval="1d")
                if df.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    score, msg = score_turtle_enhanced(df)
                    st.success(f"점수: {score} / 100")
                    st.info(msg)
        st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>2️⃣ 스윙 트레이딩</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-desc'>분석 준비 중...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>3️⃣ 포지션 트레이딩</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-desc'>분석 준비 중...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

col4, col5,_ = st.columns([1,1,1])
with col4:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>4️⃣ 스캘핑</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-desc'>분석 준비 중...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col5:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>5️⃣ 뉴스 이벤트 트레이딩</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-desc'>분석 준비 중...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:13px; color:gray;'>Made by Son Jiwan | Powered by Streamlit</p>", unsafe_allow_html=True)
