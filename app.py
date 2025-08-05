import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="📈 매수 타점 분석기", layout="wide")

# 스타일 설정 (생략, 기존 코드와 동일)
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

# --- 기존 RSI, BB, ATR, ADX 등 함수는 그대로 (생략) ---

# 여기서는 포지션 트레이딩 점수 함수만 새로 추가

def score_position_trading(df):
    if df is None or df.empty or len(df) < 200:
        return 0, "데이터가 충분하지 않습니다. 최소 200일 이상 필요합니다.", None, None, None

    df = df.copy()
    df['MA30'] = df['Close'].rolling(window=30).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()

    df.dropna(inplace=True)

    close = float(df['Close'].iloc[-1])
    ma30 = float(df['MA30'].iloc[-1])
    ma200 = float(df['MA200'].iloc[-1])
    vol = float(df['Volume'].iloc[-1])
    vol_ma20 = float(df['Vol_MA20'].iloc[-1])

    score = 0
    msgs = []

    # 1) 단기 이평 > 장기 이평 : 상승추세 신호
    if ma30 > ma200:
        score += 40
        msgs.append("30일 이평선이 200일 이평선 위에 있음 (상승 추세)")

    # 2) 최근 가격이 30일 이평선 위
    if close > ma30:
        score += 20
        msgs.append("현재가가 30일 이평선 위에 있음")

    # 3) 거래량 최근 평균 대비 증가
    if vol > vol_ma20 * 1.2:
        score += 20
        msgs.append("최근 거래량이 20일 평균 대비 20% 이상 증가")

    # 4) 추가 조건: 200일 이평선 방향 상승 여부 (마지막 10일 기울기)
    ma200_slope = (df['MA200'].iloc[-1] - df['MA200'].iloc[-10]) / 10
    if ma200_slope > 0:
        score += 20
        msgs.append("200일 이평선이 상승 추세임")

    score = min(100, score)

    # 진입/목표/손절가 계산 (단순 예시)
    entry_price = close
    target_price = close * 1.15  # 15% 목표 수익
    stop_loss = close * 0.90     # 10% 손실 시 손절

    if not msgs:
        msgs = ["특별한 신호 없음"]

    return score, "; ".join(msgs), entry_price, target_price, stop_loss


# --- UI 구성은 기존대로 두고, 포지션 트레이딩 칸만 수정 ---

# 기존 데이 트레이딩, 스윙 트레이딩 칸은 건드리지 않음

col1, col2, col3 = st.columns(3)

with col1:
    # 데이 트레이딩 기존 코드
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
                    # score_turtle_enhanced 함수 호출 (생략)
                    st.success("분석 완료 (생략)")
        st.markdown("</div>", unsafe_allow_html=True)

with col2:
    # 스윙 트레이딩 기존 코드
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>2️⃣ 스윙 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>Tony Cruz 전략 + RSI, ADX, BB, 거래량 결합</div>", unsafe_allow_html=True)
        ticker_swing = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_swing")
        if st.button("🔍 분석", key="btn_swing"):
            if not ticker_swing.strip():
                st.warning("티커를 입력하세요.")
            else:
                df_swing = yf.download(ticker_swing, period="6mo", interval="1d")
                if df_swing.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    # score_swing_trading 함수 호출 (생략)
                    st.success("분석 완료 (생략)")
        st.markdown("</div>", unsafe_allow_html=True)

with col3:
    # 여기를 포지션 트레이딩 작동 칸으로 바꿈
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>3️⃣ 포지션 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>30일, 200일 이동평균 + 거래량 기반 전략</div>", unsafe_allow_html=True)
        ticker_pos = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_pos")
        if st.button("🔍 분석", key="btn_pos"):
            if not ticker_pos.strip():
                st.warning("티커를 입력하세요.")
            else:
                df_pos = yf.download(ticker_pos, period="1y", interval="1d")
                if df_pos.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    score, msg, entry, target, stop = score_position_trading(df_pos)
                    st.success(f"점수: {score} / 100")
                    st.info(msg)
                    if entry and target and stop:
                        st.markdown(f"""
                        <div style='margin-top:15px; padding:10px; border:1px solid #ccc; border-radius:10px;'>
                        <strong>💡 자동 계산 진입/청산가:</strong><br>
                        - 진입가: {entry:.2f}<br>
                        - 목표가: {target:.2f}<br>
                        - 손절가: {stop:.2f}
                        </div>
                        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# 나머지 UI 칸들 (스캘핑, 뉴스 이벤트 등) 기존대로 둠
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
