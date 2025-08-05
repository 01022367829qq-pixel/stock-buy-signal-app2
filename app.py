import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -------------------------- UI 설정 --------------------------
st.set_page_config(page_title="매수 타점 분석기", layout="wide")
st.title("📊 주식 매수 타점 분석기")
st.markdown("""
**3가지 전략 분석 가능**  
- 📅 데이 트레이딩  
- 📈 스윙 트레이딩  
- 🧭 포지션 트레이딩  
""")

# -------------------------- 티커 입력 --------------------------
ticker = st.text_input("티커 입력 (예: AAPL, TSLA, KULR)", value="AAPL")

# -------------------------- 데이터 불러오기 --------------------------
@st.cache_data
def load_data(ticker):
    try:
        df = yf.download(ticker, period='6mo', interval='1d')
        df.dropna(inplace=True)
        return df
    except:
        return pd.DataFrame()

df = load_data(ticker)

# -------------------------- 보조지표 함수 --------------------------
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df):
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_bollinger_bands(df, window=20):
    sma = df['Close'].rolling(window).mean()
    std = df['Close'].rolling(window).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    return upper, lower

def calculate_adx(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (abs(minus_dm).rolling(period).mean() / atr)
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(period).mean()
    return adx

# -------------------------- 전략 점수 계산 함수 --------------------------
def score_day_trading(df):
    if len(df) < 50:
        return 0, "데이터 부족", None, None, None

    rsi = calculate_rsi(df)
    macd, signal = calculate_macd(df)

    latest_rsi = rsi.iloc[-1]
    latest_macd = macd.iloc[-1]
    latest_signal = signal.iloc[-1]

    score = 0
    if latest_rsi < 30:
        score += 40
    elif latest_rsi < 50:
        score += 20

    if latest_macd > latest_signal:
        score += 40

    if df['Close'].iloc[-1] > df['Close'].iloc[-2]:
        score += 20

    msg = "RSI와 MACD 기반 점수 산정 완료"
    entry = df['Close'].iloc[-1]
    target = entry * 1.02
    stop = entry * 0.98

    return score, msg, entry, target, stop

def score_swing_trading(df):
    if len(df) < 50:
        return 0, "데이터 부족", None, None, None

    upper, lower = calculate_bollinger_bands(df)
    adx = calculate_adx(df)
    df['ADX'] = adx

    latest_price = df['Close'].iloc[-1]
    latest_adx = df['ADX'].iloc[-1]
    latest_upper = upper.iloc[-1]
    latest_lower = lower.iloc[-1]

    score = 0
    if latest_adx > 25:
        score += 50
    if latest_price < latest_upper and latest_price > latest_lower:
        score += 30
    if latest_price > df['Close'].iloc[-2]:
        score += 20

    msg = "볼린저 밴드와 ADX 기반 점수 산정 완료"
    entry = latest_price
    target = entry * 1.07
    stop = entry * 0.95

    return score, msg, entry, target, stop

def score_position_trading(df):
    if len(df) < 200:
        return 0, "데이터 부족", None, None, None

    ma30 = df['Close'].rolling(30).mean()
    ma200 = df['Close'].rolling(200).mean()

    latest_price = df['Close'].iloc[-1]
    latest_ma30 = ma30.iloc[-1]
    latest_ma200 = ma200.iloc[-1]

    score = 0
    if latest_ma30 > latest_ma200:
        score += 50
    if latest_price > latest_ma30:
        score += 30
    if df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]:
        score += 20

    msg = "장기 이동평균선 기반 점수 산정 완료"
    entry = latest_price
    target = entry * 1.15
    stop = entry * 0.90

    return score, msg, entry, target, stop

# -------------------------- 분석 결과 출력 --------------------------
if st.button("📊 분석 실행"):
    if df.empty:
        st.error("유효하지 않은 티커입니다.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("📅 데이 트레이딩")
            score, msg, entry, target, stop = score_day_trading(df)
            st.write(f"**점수:** {score} / 100")
            st.caption(msg)
            if entry:
                st.write(f"- 진입가: {entry:.2f}")
                st.write(f"- 목표가: {target:.2f}")
                st.write(f"- 손절가: {stop:.2f}")

        with col2:
            st.subheader("📈 스윙 트레이딩")
            score, msg, entry, target, stop = score_swing_trading(df)
            st.write(f"**점수:** {score} / 100")
            st.caption(msg)
            if entry:
                st.write(f"- 진입가: {entry:.2f}")
                st.write(f"- 목표가: {target:.2f}")
                st.write(f"- 손절가: {stop:.2f}")

        with col3:
            st.subheader("🧭 포지션 트레이딩")
            score, msg, entry, target, stop = score_position_trading(df)
            st.write(f"**점수:** {score} / 100")
            st.caption(msg)
            if entry:
                st.write(f"- 진입가: {entry:.2f}")
                st.write(f"- 목표가: {target:.2f}")
                st.write(f"- 손절가: {stop:.2f}")
