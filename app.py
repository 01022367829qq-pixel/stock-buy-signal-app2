import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import ta
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📊 스마트 자산 분석 시스템 (by 16살 트레이더)")

# 자산 종류 선택
asset_type = st.selectbox("자산 종류를 선택하세요", ["📈 주식", "💰 암호화폐", "📉 ETF"])
ticker_input = st.text_input("티커를 입력하세요 (예: AAPL, TSLA, BTC-USD 등)", value="AAPL")

if ticker_input:
    try:
        df = yf.download(ticker_input, period='6mo', interval='1d')
        if len(df) < 30:
            st.error("데이터가 충분하지 않습니다.")
            st.stop()

        df.dropna(inplace=True)

        # 기술 지표 계산
        df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        df['CCI'] = ta.trend.CCIIndicator(df['High'], df['Low'], df['Close']).cci()
        df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close']).adx()
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close']).average_true_range()
        df['MACD'] = ta.trend.MACD(df['Close']).macd_diff()
        bb = ta.volatility.BollingerBands(df['Close'])
        df['BB_below'] = df['Close'] < bb.bollinger_lband()

        latest = df.iloc[-1]

        # 점수 계산
        score = 0
        explanations = []

        if latest['RSI'] < 30:
            score += 20
            explanations.append("✅ RSI 과매도 (<30)")
        if latest['CCI'] < -100:
            score += 20
            explanations.append("✅ CCI 과매도 (< -100)")
        if latest['ADX'] > 20:
            score += 15
            explanations.append("✅ ADX 추세 형성 중 (>20)")
        if latest['MACD'] > 0:
            score += 20
            explanations.append("✅ MACD 상승 전환")
        if latest['BB_below']:
            score += 15
            explanations.append("✅ 볼린저 밴드 하단 이탈")
        if df['Volume'].iloc[-1] > df['Volume'].rolling(10).mean().iloc[-1]:
            score += 10
            explanations.append("✅ 평균 이상 거래량")

        st.subheader(f"📊 종합 점수: {score} / 100")

        with st.expander("📌 점수 상세 해설"):
            for e in explanations:
                st.markdown(f"- {e}")

        # 매수 타점 계산
        entry_price = round(latest['Close'], 2)
        stop_loss = round(entry_price - latest['ATR'] * 1.5, 2)
        target_price = round(entry_price + latest['ATR'] * 2.5, 2)

        st.subheader("📈 매수 타점 추천")
        st.markdown(f"- 진입가 (Entry): **${entry_price}**")
        st.markdown(f"- 손절가 (Stop Loss): **${stop_loss}**")
        st.markdown(f"- 목표가 (Target): **${target_price}**")

        # 차트 시각화
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                     low=df['Low'], close=df['Close'], name='캔들'))

        fig.add_hline(y=entry_price, line_dash="dash", line_color="green", annotation_text="진입가")
        fig.add_hline(y=stop_loss, line_dash="dot", line_color="red", annotation_text="손절가")
        fig.add_hline(y=target_price, line_dash="dot", line_color="blue", annotation_text="목표가")

        fig.update_layout(title=f"{ticker_input.upper()} 차트 & 타점", height=500)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"에러 발생: {e}")
