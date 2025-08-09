import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 보조 함수들 ---

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def is_buy_signal_elliot(df):
    close = df['Close']
    if len(close) < 5:
        return False
    try:
        return (close.iat[-3] < close.iat[-2]) and (close.iat[-2] < close.iat[-1])
    except Exception:
        return False

def is_buy_signal_ma(df):
    if len(df) < 51:
        return False
    short_ma = df['Close'].rolling(window=20).mean()
    long_ma = df['Close'].rolling(window=50).mean()
    # NaN 체크
    try:
        if bool(short_ma.isna().iloc[-2]) or bool(short_ma.isna().iloc[-1]):
            return False
        if bool(long_ma.isna().iloc[-2]) or bool(long_ma.isna().iloc[-1]):
            return False
        return (short_ma.iat[-2] < long_ma.iat[-2]) and (short_ma.iat[-1] > long_ma.iat[-1])
    except Exception:
        return False

def is_buy_signal_rsi(df):
    rsi = compute_rsi(df['Close'])
    if len(rsi) == 0:
        return False
    try:
        is_nan = rsi.isna().iloc[-1]
        if is_nan:
            return False
        return rsi.iat[-1] <= 40
    except Exception:
        return False

def score_for_signal(methods, df):
    score = 0
    msgs = []
    if "Elliot Wave" in methods and is_buy_signal_elliot(df):
        score += 40
        msgs.append("엘리엇 웨이브 매수 신호 감지")
    if "Moving Average" in methods and is_buy_signal_ma(df):
        score += 30
        msgs.append("이동평균선 골든크로스 감지")
    if "RSI" in methods and is_buy_signal_rsi(df):
        score += 30
        msgs.append("RSI 과매도 구간 감지")
    return score, ", ".join(msgs)

# --- 섹터별 티커 예시 (간단하게 일부만) ---
SECTORS = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "INTC", "CSCO"],
    "Healthcare": ["JNJ", "PFE", "MRK", "ABBV", "TMO"],
    "Finance": ["JPM", "BAC", "WFC", "C", "GS"],
    "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE"],
    "Industrials": ["BA", "CAT", "DE", "GE", "MMM"],
    "Utilities": ["NEE", "DUK", "SO", "AEP", "EXC"]
}

st.title("섹터별 매수 신호 종목 분석기")

# 1. 섹터 선택
selected_sector = st.selectbox("섹터 선택", options=list(SECTORS.keys()))

# 2. 기법 선택
methods = st.multiselect(
    "분석 기법 선택",
    options=["Elliot Wave", "Moving Average", "RSI"],
    default=["Moving Average", "RSI"]
)

if st.button("분석 시작"):

    tickers = SECTORS[selected_sector]
    buy_stocks = []

    for ticker in tickers:
        df = yf.download(ticker, period="6mo", interval="1d")
        if df.empty or len(df) < 60:
            continue
        
        score, msg = score_for_signal(methods, df)
        if score > 0:
            entry = df['Close'].iat[-1]
            target = entry * 1.05
            stop = entry * 0.95
            buy_stocks.append({
                "ticker": ticker,
                "score": score,
                "msg": msg,
                "entry": entry,
                "target": target,
                "stop": stop,
                "data": df
            })

    if not buy_stocks:
        st.info("매수 신호가 감지된 종목이 없습니다.")
    else:
        for stock in buy_stocks:
            st.subheader(f"{stock['ticker']} - 점수: {stock['score']}")
            st.write(stock['msg'])
            st.markdown(f"""
                - 진입가: {stock['entry']:.2f}  
                - 목표가: {stock['target']:.2f}  
                - 손절가: {stock['stop']:.2f}
            """)
            df = stock['data']
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color='green',
                decreasing_line_color='red',
                name=stock['ticker']
            )])
            fig.update_layout(
                title=f"{stock['ticker']} 일간 캔들 차트",
                xaxis_title="날짜",
                yaxis_title="가격",
                xaxis_rangeslider_visible=False,
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
