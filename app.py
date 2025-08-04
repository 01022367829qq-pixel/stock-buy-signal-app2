import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# 점수 계산 함수
def check_buy_signal(df):
    if df.empty or len(df) < 20:
        return 0, "데이터 부족"

    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']

    # 지표 계산
    try:
        bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
        rsi = ta.momentum.RSIIndicator(close=close, window=14).rsi()
        adx = ta.trend.ADXIndicator(high=high, low=low, close=close, window=14).adx()
        cci = ta.trend.CCIIndicator(high=high, low=low, close=close, window=20).cci()
        atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
    except Exception as e:
        return 0, f"지표 계산 오류: {e}"

    latest = {
        'close': close.iloc[-1],
        'rsi': rsi.iloc[-1],
        'adx': adx.iloc[-1],
        'cci': cci.iloc[-1],
        'bb_low': bb.bollinger_lband().iloc[-1],
        'atr': atr.iloc[-1]
    }

    score = 0
    score += 10 if latest['rsi'] <= 30 else 0
    score += 10 if latest['rsi'] <= 20 else 0
    score += 10 if latest['cci'] <= -100 else 0
    score += 10 if latest['cci'] <= -150 else 0
    score += 10 if latest['adx'] <= 25 else 0
    score += 10 if latest['adx'] <= 20 else 0
    score += 20 if latest['close'] <= latest['bb_low'] * 1.01 else 0
    score += 20 if latest['close'] <= latest['bb_low'] * 1.005 else 0

    return min(score, 100), "분석 완료"

# UI 시작
st.title("📊 AI 주식 매수 점수 분석기")
ticker_input = st.text_input("종목 티커를 입력하세요 (예: NVDA)", "NVDA")

if st.button("분석 시작"):
    data = yf.download(ticker_input, period='60d', interval='1d', auto_adjust=True, progress=False)
    score, msg = check_buy_signal(data)

    if msg != "분석 완료":
        st.warning(f"{msg}")
    else:
        st.subheader(f"🎯 {ticker_input.upper()} 종목의 매수 점수는 {score}점입니다!")
        st.progress(score / 100)


