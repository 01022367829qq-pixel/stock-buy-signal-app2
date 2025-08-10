import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

def compute_rsi(series, period=14):
    series = pd.to_numeric(series, errors='coerce').dropna()
    if series.empty:
        return pd.Series(dtype=float)
    
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

st.title("AAPL Close 데이터 및 RSI 계산 테스트")

df = yf.download("AAPL", period="1y", interval="1d", progress=False)
st.write("Close 데이터 샘플:")
st.write(df['Close'].tail(10))

rsi = compute_rsi(df['Close'])
st.write("RSI 데이터 샘플:")
st.write(rsi.tail(10))

if not rsi.empty:
    st.write("최종 RSI 값:", rsi.iat[-1])
else:
    st.write("RSI 계산 결과가 없습니다.")
