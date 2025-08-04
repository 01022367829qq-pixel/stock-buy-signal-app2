import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# 📌 종목 데이터 가져오기
def get_data(ticker):
    df = yf.download(ticker, period='60d', interval='1d', progress=False, auto_adjust=True)
    return df

# 📌 매수 신호 점수 계산 함수
def check_buy_score(
    df,
    weight_rsi_30=1,
    weight_rsi_20=1,
    weight_cci_100=1,
    weight_cci_150=1,
    weight_adx_25=1,
    weight_adx_20=1,
    weight_bb_low_101=1,
    weight_bb_low_1005=1
):
    if df.empty or len(df) < 20:
        return None

    # 1D Series로 변환
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    volume = df['Volume'].squeeze()

    try:
        bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
        rsi = ta.momentum.RSIIndicator(close=close, window=14).rsi()
        adx = ta.trend.ADXIndicator(high=high, low=low, close=close, window=14).adx()
        cci = ta.trend.CCIIndicator(high=high, low=low, close=close, window=20).cci()
        atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
    except Exception as e:
        return f"지표 계산 오류: {e}"

    latest_close = close.iloc[-1]
    latest_rsi = rsi.iloc[-1]
    latest_bb_low = bb.bollinger_lband().iloc[-1]
    latest_adx = adx.iloc[-1]
    latest_cci = cci.iloc[-1]
    latest_atr = atr.iloc[-1]

    recent_vol = volume.iloc[-1]
    avg_vol_5d = volume.iloc[-6:-1].mean() if len(volume) >= 6 else volume.mean()
    vol_status = "거래량 증가 O" if recent_vol > avg_vol_5d else "거래량 증가 X"

    score = 0
    if latest_rsi <= 30:
        score += weight_rsi_30
    if latest_rsi <= 20:
        score += weight_rsi_20
    if latest_cci <= -100:
        score += weight_cci_100
    if latest_cci <= -150:
        score += weight_cci_150
    if latest_adx <= 25:
        score += weight_adx_25
    if latest_adx <= 20:
        score += weight_adx_20
    if latest_close <= latest_bb_low * 1.01:
        score += weight_bb_low_101
    if latest_close <= latest_bb_low * 1.005:
        score += weight_bb_low_1005

    entry_price = latest_close
    stop_loss = entry_price - (1.5 * latest_atr)
    target_price = entry_price + (3 * latest_atr)

    return {
        'EntryPrice': round(entry_price, 2),
        'StopL
