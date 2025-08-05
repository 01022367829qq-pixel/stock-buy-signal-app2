# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 기술 지표 계산 함수들 ---------------------------------------

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_bollinger_bands(data, window=20):
    sma = data['Close'].rolling(window).mean()
    std = data['Close'].rolling(window).std()
    upper_band = sma + (2 * std)
    lower_band = sma - (2 * std)
    return upper_band, lower_band

def calculate_macd(data):
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_adx(df, period=14):
    df = df.copy()
    high = df['High']
    low = df['Low']
    close = df['Close']

    plus_dm = high.diff()
    minus_dm = low.diff().abs()

    plus_dm_adj = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0).astype(float).flatten()
    minus_dm_adj = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0).astype(float).flatten()

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(window=period).mean()
    atr = atr.replace(0, np.nan)

    plus_di = 100 * (pd.Series(plus_dm_adj, index=df.index).rolling(period).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm_adj, index=df.index).rolling(period).mean() / atr)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=period).mean()

    return adx

# 전략 점수 함수들 ---------------------------------------

def score_day_trading(df):
    rsi = calculate_rsi(df)
    macd, signal = calculate_macd(df)
    score = 0
    reason = []

    if rsi.iloc[-1] < 30:
        score += 20
        reason.append("RSI 과매도")

    if macd.iloc[-1] > signal.iloc[-1]:
        score += 20
        reason.append("MACD 골든크로스")

    if df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]:
        score += 10
        reason.append("거래량 증가")

    entry = df['Close'].iloc[-1]
    target = round(entry * 1.015, 2)
    stop = round(entry * 0.985, 2)

    return score, ", ".join(reason), entry, target, stop


def score_swing_trading(df):
    upper, lower = calculate_bollinger_bands(df)
    adx = calculate_adx(df)
    score = 0
    reason = []

    if df['Close'].iloc[-1] < lower.iloc[-1]:
        score += 25
        reason.append("볼린저 밴드 하단 근접")

    if adx.iloc[-1] > 25:
        score += 25
        reason.append(f"강한 추세 (ADX: {adx.iloc[-1]:.1f})")

    entry = df['Close'].iloc[-1]
    target = round(entry * 1.07, 2)
    stop = round(entry * 0.95, 2)

    return score, ", ".join(reason), entry, target, stop


def score_position_trading(df):
    ma30 = df['Close'].rolling(window=30).mean()
    ma150 = df['Close'].rolling(window=150).mean()
    ma200 = df['Close'].rolling(window=200).mean()
    volume_ma = df['Volume'].rolling(window=50).mean()

    score = 0
    reason = []

    if df['Close'].iloc[-1] > ma150.iloc[-1] and df['Close'].iloc[-1] > ma200.iloc[-1]:
        score += 25
        reason.append("주가가 MA150 및 MA200 위에 위치")

    if ma150.iloc[-1] > ma200.iloc[-1]:
        score += 25
        reason.append("MA150 > MA200 (우상향)")

    if ma30.iloc[-1] > ma150.iloc[-1] and ma30.iloc[-1] > ma200.iloc[-1]:
        score += 25
        reason.append("MA30 > MA150/MA200 (단기 상승세)")

    if df['Volume'].iloc[-1] > volume_ma.iloc[-1]:
        score += 15
        reason.append("거래량 평균 초과")

    entry = df['Close'].iloc[-1]
    target = round(entry * 1.25, 2)
    stop = round(entry * 0.88, 2)

    return score, ", ".join(reason), entry, target, stop

# UI ------------------------------------------------------

st.title("📈 주식 매수 시그널 분석기")

ticker = st.text_input("티커를 입력하세요 (예: AAPL, TSLA, KULR 등)", value="KULR")
strategy = st.selectbox("트레이딩 전략 선택", ["Day Trading", "Swing Trading", "Position Trading"])

if st.button("분석 시작"):
    df = yf.download(ticker, period="1y", interval="1d")

    if df.empty:
        st.error("유효한 티커를 입력하세요.")
    else:
        st.subheader(f"{strategy} 분석 결과")

        if strategy == "Day Trading":
            score, reason, entry, target, stop = score_day_trading(df)
        elif strategy == "Swing Trading":
            score, reason, entry, target, stop = score_swing_trading(df)
        else:
            score, reason, entry, target, stop = score_position_trading(df)

        st.write(f"📊 **점수: {score} / 100**")
        st.write(f"📌 **분석 근거:** {reason}")
        st.markdown(f"""
        💡 **자동 계산 진입/청산가**  
        - 진입가: `{entry}`  
        - 목표가: `{target}`  
        - 손절가: `{stop}`
        """)

