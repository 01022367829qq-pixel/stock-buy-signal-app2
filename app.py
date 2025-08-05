import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="\ud83d\udcc8 \ub9e4\uc218 \ud0c0\uc810 \ubd84\uc11d\uae30", layout="wide")

# --- 중간 생략 ---
# score_turtle_enhanced, score_swing_trading 등 기존 함수 유지

# 포지션 트레이딩 점수 함수 (장기 추세 기반)
def score_position_trading(df):
    if df is None or df.empty or len(df) < 200:
        return 0, "데이터가 충분하지 않습니다.", None, None, None

    df = df.copy()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['SMA_200'] = df['Close'].rolling(200).mean()
    df['RSI'] = calculate_rsi(df['Close'], 14)
    df['ADX'] = calculate_adx(df, 14)

    df.dropna(inplace=True)
    if len(df) < 1:
        return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)", None, None, None

    close = float(df['Close'].iloc[-1])
    sma_50 = float(df['SMA_50'].iloc[-1])
    sma_200 = float(df['SMA_200'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    adx = float(df['ADX'].iloc[-1])

    for val in [sma_50, sma_200, rsi, adx]:
        if val is None or np.isnan(val):
            return 0, "기술 지표 계산 중 오류 발생", None, None, None

    score = 0
    msgs = []

    if sma_50 > sma_200:
        score += 30
        msgs.append("골든 크로스")
    else:
        score -= 20
        msgs.append("데드 크로스")

    if close > sma_50:
        score += 20
        msgs.append("50일선 위에 위치")

    if rsi < 30:
        score += 10
        msgs.append("RSI 과매도")
    elif rsi > 70:
        score -= 10
        msgs.append("RSI 과매수")

    if adx > 25:
        score += 20
        msgs.append("강한 추세")

    score = max(0, min(100, score))
    if not msgs:
        msgs = ["신호 없음"]

    entry_price = close
    target_price = close * 1.2
    stop_loss = close * 0.85

    return score, "; ".join(msgs), entry_price, target_price, stop_loss

# --- UI: 기존 구조 유지하며 포지션 트레이딩 추가 ---

# ... col1, col2 유지 ...

with col3:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>3\u20e3 \ud3ec\uc9c0\uc158 \ud2b8\ub808\uc774\ub529</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>SMA + RSI + ADX 기반 장기 투자 전략</div>", unsafe_allow_html=True)
        ticker_position = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_position")
        if st.button("\ud83d\udd0d \ubd84\uc11d", key="btn_position"):
            if not ticker_position.strip():
                st.warning("티커를 입력하세요.")
            else:
                df_pos = yf.download(ticker_position, period="12mo", interval="1d")
                if df_pos.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    score, msg, entry, target, stop = score_position_trading(df_pos)
                    st.success(f"점수: {score} / 100")
                    st.info(msg)

                    if entry and target and stop:
                        st.markdown(f"""
                        <div style='margin-top:15px; padding:10px; border:1px solid #ccc; border-radius:10px;'>
                        <strong>\ud83d\udca1 \uc790\ub3d9 \uacc4\uc0b0 \uc9c4\uc785/\ucc38\uc0ac\uac00:</strong><br>
                        - 진입가: {entry:.2f}<br>
                        - 목표가: {target:.2f}<br>
                        - 손절가: {stop:.2f}
                        </div>
                        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ... col4, col5 유지 ...

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:13px; color:gray;'>Made by Son Jiwan | Powered by Streamlit</p>", unsafe_allow_html=True)
