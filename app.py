import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

def compute_rsi(series, period=14):
    if not isinstance(series, pd.Series):
        try:
            series = pd.Series(series)
        except Exception:
            return pd.Series(dtype=float)
    try:
        series = pd.to_numeric(series, errors='coerce')
    except Exception:
        return pd.Series(dtype=float)
    series = series.dropna()
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

def is_buy_signal_rsi(df):
    rsi = compute_rsi(df['Close'])
    if len(rsi) == 0:
        return False, None
    try:
        if rsi.isna().iat[-1]:
            return False, None
        cond = rsi.iat[-1] <= 60
        return cond, rsi.iat[-1]
    except Exception:
        return False, None

st.title("RSI 60 이하 매수 신호 테스트")

ticker = st.text_input("티커 입력 (예: AAPL)", "AAPL")

if st.button("분석 시작"):
    df = yf.download(ticker, period="1y", interval="1d", progress=False)
    if df.empty or 'Close' not in df.columns:
        st.error("데이터를 불러오지 못했습니다.")
    else:
        st.write(f"{ticker} Close 데이터 샘플:")
        st.write(df['Close'].tail(10))
        st.write(f"Close 컬럼 NaN 개수: {df['Close'].isna().sum()}")

        signal, last_rsi = is_buy_signal_rsi(df)
        if signal:
            st.success(f"매수 신호 감지! RSI: {last_rsi:.2f} (60 이하)")
        else:
            if last_rsi is not None:
                st.info(f"매수 신호 없음. 최근 RSI: {last_rsi:.2f}")
            else:
                st.info("RSI 계산 불가 또는 데이터 부족")
