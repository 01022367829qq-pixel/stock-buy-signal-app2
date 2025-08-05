import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 페이지 설정
st.set_page_config(page_title="📈 매수 타점 분석기", layout="wide")

# ---------------------- UI ----------------------
st.title("📊 매수 타점 분석기")
st.markdown("당신의 투자 전략에 맞는 종목을 진입가, 손절가, 목표가까지 빠르게 분석해보세요.")

# 전략 선택
strategy = st.selectbox("사용할 트레이딩 전략을 선택하세요.", [
    "데이 트레이딩 (Richard Dennis의 전략 + RSI,BB,거래량,ATR 지표 결합)",
    "스윙 트레이딩 (Tony Cruz의 전략 + RSI, ADX, BB, 거래량 지표 결합)",
    "포지션 트레이딩 (Richard Dennis의 전략 + EMA, RSI, ATR,거래량 지표 결합)"
])

ticker = st.text_input("종목 티커를 입력하세요 (예: AAPL, MSFT, TSLA 등):").upper()

# ---------------------- 지표 계산 함수 ----------------------
def get_data(ticker, interval='1d', period='6mo'):
    df = yf.download(ticker, interval=interval, period=period)
    df.dropna(inplace=True)
    return df

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_bb(data, window=20):
    ma = data['Close'].rolling(window).mean()
    std = data['Close'].rolling(window).std()
    upper = ma + (2 * std)
    lower = ma - (2 * std)
    return upper, lower

def calculate_ema(data, span=50):
    return data['Close'].ewm(span=span, adjust=False).mean()

def calculate_adx(data, period=14):
    high = data['High']
    low = data['Low']
    close = data['Close']
    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift())
    ], axis=1).max(axis=1)

    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0

    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = abs(100 * (minus_dm.rolling(period).mean() / atr))
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()

    return adx

# ---------------------- 전략 점수화 함수 ----------------------
def score_day_trading(df):
    rsi = calculate_rsi(df)
    upper, lower = calculate_bb(df)
    bb_signal = (df['Close'] < lower).iloc[-1]
    rsi_signal = (rsi.iloc[-1] < 30)
    volume_signal = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]
    score = sum([bb_signal, rsi_signal, volume_signal]) * 30
    score = min(score, 100)

    entry = df['Close'].iloc[-1]
    stop = entry * 0.97
    target = entry * 1.05

    return score, entry, target, stop

def score_swing_trading(df):
    rsi = calculate_rsi(df)
    bb_upper, bb_lower = calculate_bb(df)
    adx = calculate_adx(df)
    bb_contraction = (bb_upper - bb_lower).iloc[-1] < df['Close'].rolling(20).std().iloc[-1]
    adx_signal = adx.iloc[-1] > 25
    rsi_signal = (rsi.iloc[-1] > 50)
    volume_signal = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]
    score = sum([bb_contraction, adx_signal, rsi_signal, volume_signal]) * 25
    score = min(score, 100)

    entry = df['Close'].iloc[-1]
    stop = entry * 0.95
    target = entry * 1.10

    return score, entry, target, stop

def score_position_trading(df):
    ema = calculate_ema(df)
    rsi = calculate_rsi(df)
    atr = df['High'] - df['Low']
    ema_signal = df['Close'].iloc[-1] > ema.iloc[-1]
    rsi_signal = rsi.iloc[-1] > 50
    volume_signal = df['Volume'].iloc[-1] > df['Volume'].rolling(30).mean().iloc[-1]
    score = sum([ema_signal, rsi_signal, volume_signal]) * 33
    score = min(score, 100)

    entry = df['Close'].iloc[-1]
    stop = entry * 0.90
    target = entry * 1.20

    return score, entry, target, stop

# ---------------------- 실행 ----------------------
if st.button("분석 시작"):
    if not ticker:
        st.warning("티커를 입력해주세요.")
    else:
        with st.spinner("분석 중..."):
            if strategy.startswith("데이"):
                df = get_data(ticker, interval='30m', period='5d')
                score, entry, target, stop = score_day_trading(df)
                st.subheader("🔎 데이 트레이딩 결과")
            elif strategy.startswith("스윙"):
                df = get_data(ticker, interval='1d', period='3mo')
                score, entry, target, stop = score_swing_trading(df)
                st.subheader("🔎 스윙 트레이딩 결과")
            else:
                df = get_data(ticker, interval='1d', period='1y')
                score, entry, target, stop = score_position_trading(df)
                st.subheader("🔎 포지션 트레이딩 결과")

            st.write(f"**✅ 점수:** {score}/100")
            st.write(f"**📍 진입**
