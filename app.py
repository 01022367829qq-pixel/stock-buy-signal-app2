# app.py
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import CCIIndicator, MACD, ADXIndicator
from ta.volatility import BollingerBands
from ta.volatility import AverageTrueRange

st.set_page_config(page_title="📈 매수 타점 분석기", layout="wide")

# 📌 기능: 기술 지표 점수 계산
def calculate_score(df):
    score = 0
    try:
        rsi = RSIIndicator(df['Close'], window=14).rsi().iloc[-1]
        stoch = StochasticOscillator(df['High'], df['Low'], df['Close'], window=14).stoch().iloc[-1]
        cci = CCIIndicator(df['High'], df['Low'], df['Close'], window=20).cci().iloc[-1]
        adx = ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx().iloc[-1]
        bb = BollingerBands(df['Close'], window=20)
        bb_percent = ((df['Close'].iloc[-1] - bb.bollinger_lband().iloc[-1]) / (bb.bollinger_hband().iloc[-1] - bb.bollinger_lband().iloc[-1])) * 100
        macd = MACD(df['Close']).macd_diff().iloc[-1]
        atr = AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range().iloc[-1]

        # 점수 계산 (가중치 및 조건은 조정 가능)
        if 30 < rsi < 50: score += 15
        if stoch < 20: score += 15
        if cci < -100: score += 15
        if adx > 25: score += 10
        if bb_percent < 30: score += 15
        if macd > 0: score += 10
        if atr / df['Close'].iloc[-1] > 0.03: score += 10

    except:
        pass

    return round(score, 1)

# 📌 기능: 매수 타점 자동 추정
def get_buy_signal(df):
    try:
        rsi = RSIIndicator(df['Close'], window=14).rsi()
        cci = CCIIndicator(df['High'], df['Low'], df['Close'], window=20).cci()
        macd_diff = MACD(df['Close']).macd_diff()
        adx = ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx()
        
        if (
            rsi.iloc[-1] < 40 and
            cci.iloc[-1] < -100 and
            macd_diff.iloc[-1] > 0 and
            adx.iloc[-1] > 20
        ):
            return True
        else:
            return False
    except:
        return False

# 📌 기능: Plotly 차트 시각화
def plot_candlestick(df, ticker):
    fig = go.Figure(data=[
        go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            name="가격"
        )
    ])
    fig.update_layout(title=f"{ticker} 캔들차트", xaxis_rangeslider_visible=False)
    return fig

# 📌 UI 구성
st.title("📊 주식 매수 타점 분석기")
st.markdown("Made by **16살 미국 주식 트레이더 & 웹개발자**")

ticker_input = st.text_input("🔍 분석할 종목 티커를 입력하세요 (예: AAPL, TSLA)", "KULR").upper()
period = st.selectbox("조회 기간", ["1mo", "3mo", "6mo", "1y"], index=1)
interval = st.selectbox("시간 간격", ["1d", "1h", "15m"], index=0)

if st.button("📈 분석 시작"):
    df = yf.download(ticker_input, period=period, interval=interval)
    if df.empty:
        st.error("❌ 종목 데이터를 불러올 수 없습니다.")
    else:
        score = calculate_score(df)
        buy_signal = get_buy_signal(df)
        asset_type = "암호화폐" if "-USD" in ticker_input else "ETF" if ticker_input.endswith("Q") else "주식"

        st.subheader(f"🔎 [{ticker_input}] 분석 결과")
        st.write(f"📊 기술적 분석 점수: **{score}점 / 100점**")
        st.write(f"💰 매수 신호 여부: {'✅ 발생함' if buy_signal else '❌ 아직 아님'}")
        st.write(f"📦 자산 종류: {asset_type}")
        
        st.plotly_chart(plot_candlestick(df, ticker_input), use_container_width=True)
