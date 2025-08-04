import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta import momentum, volatility, trend

st.set_page_config(layout="wide")
st.title("📊 매수 타점 분석 & 변동성 분석")

# 사용자 입력
asset_type = st.sidebar.selectbox("자산 종류 선택", ["주식", "ETF", "암호화폐"])
ticker = st.sidebar.text_input("티커 입력 (예: AAPL, BTC-USD, QQQ)", value="AAPL")

# 데이터 가져오기
@st.cache_data
def load_data(ticker):
    data = yf.download(ticker, period="3mo")
    return data

try:
    df = load_data(ticker)

    if df.empty:
        st.error("❌ 유효하지 않은 티커입니다.")
    else:
        df.dropna(inplace=True)

        # Plot - 종가 차트
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="종가"))
        fig.update_layout(title=f"{ticker} 종가 추이", xaxis_title="날짜", yaxis_title="가격")
        st.plotly_chart(fig, use_container_width=True)

        if asset_type == "주식":
            # 기술 지표 계산
            df["RSI"] = momentum.RSIIndicator(df["Close"]).rsi()
            df["MACD"] = trend.MACD(df["Close"]).macd()
            df["CCI"] = trend.CCIIndicator(df["High"], df["Low"], df["Close"]).cci()
            df["ADX"] = trend.ADXIndicator(df["High"], df["Low"], df["Close"]).adx()
            df["ATR"] = volatility.AverageTrueRange(df["High"], df["Low"], df["Close"]).average_true_range()

            # 최신값
            latest = df.iloc[-1]
            rsi, macd, cci, adx, atr = latest["RSI"], latest["MACD"], latest["CCI"], latest["ADX"], latest["ATR"]

            # 점수 계산 (0~100점)
            score = 0
            if rsi < 30: score += 20
            elif rsi < 50: score += 10
            if macd > 0: score += 20
            if cci < -100: score += 20
            if adx > 25: score += 20
            if atr > df["ATR"].mean(): score += 20

            st.subheader("🧠 매수 타점 점수")
            st.metric(label="총점", value=f"{score}/100")

            with st.expander("📌 보조지표 상세"):
                st.write(f"📉 RSI: {rsi:.2f}")
                st.write(f"📈 MACD: {macd:.2f}")
                st.write(f"📊 CCI: {cci:.2f}")
                st.write(f"📊 ADX: {adx:.2f}")
                st.write(f"📏 ATR: {atr:.4f}")

        else:
            # ETF & 암호화폐: 일일 변동성만 출력
            df["Daily Change %"] = df["Close"].pct_change() * 100
            daily_volatility = df["Daily Change %"].rolling(window=5).std().iloc[-1]
            st.subheader("📈 5일 평균 일일 변동성")
            st.metric(label="Daily Volatility", value=f"{daily_volatility:.2f}%")

except Exception as e:
    st.error(f"⚠️ 에러 발생: {e}")

