import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, CCIIndicator, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange

# 1. 앱 기본 설정
st.set_page_config(page_title="📈 자산 분석 점수 시스템", layout="wide")

# 2. 타이틀 및 설명
st.title("📊 매수 타점 분석 및 변동성 시각화")
st.markdown("""
이 앱은 주식, ETF, 암호화폐에 대해 매수 타점 분석 및 변동성 점수를 제공합니다.  
주식은 매수 신호 점수를 제공하고, ETF 및 암호화폐는 변동성 점수만 표시됩니다.
""")

# 3. 사용자 입력
ticker = st.text_input("🔍 티커를 입력하세요 (예: AAPL, TSLA, BTC-USD, QQQ)", "AAPL")
asset_type = st.selectbox("자산 종류를 선택하세요", ["📈 주식", "💰 암호화폐", "📦 ETF"])

# 4. 데이터 다운로드
try:
    df = yf.download(ticker, period="6mo", interval="1d")
    if df.empty:
        st.error("❌ 유효하지 않은 티커입니다.")
        st.stop()
    df.dropna(inplace=True)
except Exception as e:
    st.error("❌ 데이터를 불러오지 못했습니다.")
    st.stop()

# 5. 지표 계산
df["RSI"] = RSIIndicator(df["Close"]).rsi()
df["STOCH"] = StochasticOscillator(df["High"], df["Low"], df["Close"]).stoch()
df["CCI"] = CCIIndicator(df["High"], df["Low"], df["Close"]).cci()
df["ADX"] = ADXIndicator(df["High"], df["Low"], df["Close"]).adx()
bb = BollingerBands(df["Close"])
df["BB_bbm"] = bb.bollinger_mavg()
df["BB_bbh"] = bb.bollinger_hband()
df["BB_bbl"] = bb.bollinger_lband()
df["ATR"] = AverageTrueRange(df["High"], df["Low"], df["Close"]).average_true_range()
df["MACD"] = MACD(df["Close"]).macd()

# 6. 점수 계산 함수 (NaN 안전 체크 추가)
def calculate_entry_score(row):
    score = 0
    try:
        if pd.notna(row["RSI"]) and row["RSI"] < 35: 
            score += 2
        if pd.notna(row["STOCH"]) and row["STOCH"] < 30: 
            score += 2
        if pd.notna(row["CCI"]) and row["CCI"] < -100: 
            score += 2
        if pd.notna(row["ADX"]) and row["ADX"] > 20: 
            score += 1
        if pd.notna(row["Close"]) and pd.notna(row["BB_bbl"]) and row["Close"] < row["BB_bbl"]: 
            score += 2
        if pd.notna(row["MACD"]) and row["MACD"] > 0: 
            score += 1
    except Exception:
        return 0
    return score

# 7. 분석 결과 적용
latest = df.iloc[-1]
entry_score = calculate_entry_score(latest)

# 8. 변동성 점수 계산 함수
def calculate_volatility_score(df):
    daily_range = (df["High"] - df["Low"]) / df["Close"]
    volatility = daily_range.rolling(window=14).mean()
    score = np.clip(volatility * 100, 0, 100)  # 0~100으로 정규화
    return score

vol_score_series = calculate_volatility_score(df)
vol_score = vol_score_series.iloc[-1] if not vol_score_series.isna().all() else 0

# 9. 결과 시각화
col1, col2 = st.columns(2)

with col1:
    if asset_type == "📈 주식":
        st.subheader("🟢 매수 신호 점수")
        st.metric(label="현재 점수 (0~10)", value=f"{entry_score} 점")
        st.progress(min(entry_score / 10, 1.0))
    else:
        st.subheader("📊 변동성 점수")
        st.metric(label="최근 변동성 점수 (0~100)", value=f"{vol_score:.2f} 점")
        st.progress(min(vol_score / 100, 1.0))

with col2:
    st.subheader("📈 종가 & 볼린저 밴드")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close", line=dict(color='white')))
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_bbh"], name="BB High", line=dict(color='red', dash="dot")))
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_bbl"], name="BB Low", line=dict(color='green', dash="dot")))
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

# 10. 전체 지표 테이블
with st.expander("📄 전체 기술 지표 보기"):
    st.dataframe(df.tail(20)[["Close", "RSI", "STOCH", "CCI", "ADX", "MACD", "BB_bbl", "BB_bbh", "ATR"]])

# 11. 피드백
st.markdown("---")
st.caption("📌 개발: Jiwan | Powered by Streamlit, yFinance, TA-Lib")
