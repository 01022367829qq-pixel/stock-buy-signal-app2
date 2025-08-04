import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.title("AI 주식 매수 타점 추천 앱")

tickers = [
    "KULR", "BNGO", "INM", "RGTI", "NNDM", "VERI", "SINT", "VUZI", "CLSK", "EBET",
    "CABA", "BBIG", "IDEX", "HILS", "DRMA", "HGEN", "GNFT", "CRKN", "PHUN", "BKKT"
]

def get_data(ticker):
    df = yf.download(ticker, period='60d', interval='1d', progress=False, auto_adjust=True)
    return df

def ensure_series_1d(series):
    if hasattr(series, 'values') and series.values.ndim > 1:
        return pd.Series(series.values.flatten(), index=series.index)
    return series

def check_buy_signal(df):
    if df.empty or len(df) < 20:
        return None

    close = ensure_series_1d(df['Close'])
    high = ensure_series_1d(df['High'])
    low = ensure_series_1d(df['Low'])
    volume = ensure_series_1d(df['Volume'])

    bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
    rsi = ta.momentum.RSIIndicator(close=close, window=14).rsi()
    adx = ta.trend.ADXIndicator(high=high, low=low, close=close, window=14).adx()
    cci = ta.trend.CCIIndicator(high=high, low=low, close=close, window=20).cci()
    atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()

    latest_close = close.iloc[-1]
    latest_rsi = rsi.iloc[-1]
    latest_bb_low = bb.bollinger_lband().iloc[-1]
    latest_adx = adx.iloc[-1]
    latest_cci = cci.iloc[-1]
    latest_atr = atr.iloc[-1]

    score = 0
    if latest_rsi <= 30:
        score += 1
    if latest_rsi <= 20:
        score += 2
    if latest_cci <= -100:
        score += 1
    if latest_cci <= -150:
        score += 2
    if latest_adx <= 25:
        score += 1
    if latest_adx <= 20:
        score += 2
    if latest_close <= latest_bb_low * 1.01:
        score += 1
    if latest_close <= latest_bb_low * 1.005:
        score += 1

    if score >= 3:
        entry_price = latest_close
        stop_loss = entry_price - (1.5 * latest_atr)
        target_price = entry_price + (3 * latest_atr)

        return {
            'EntryPrice': round(entry_price, 2),
            'StopLoss': round(stop_loss, 2),
            'TargetPrice': round(target_price, 2),
            'RSI': round(latest_rsi, 2),
            'BollingerLow': round(latest_bb_low, 2),
            'ADX': round(latest_adx, 2),
            'CCI': round(latest_cci, 2),
            'ATR': round(latest_atr, 4),
            'Score': score
        }
    else:
        return None

if st.button("매수 타점 분석 시작"):
    results = []
    for ticker in tickers:
        data = get_data(ticker)
        signal = check_buy_signal(data)
        if signal:
            results.append({'Ticker': ticker, **signal})

    if len(results) == 0:
        st.write("🚫 조건을 만족한 종목이 없습니다.")
    else:
        df_results = pd.DataFrame(results).sort_values(by='Score', ascending=False).reset_index(drop=True)
        st.dataframe(df_results)

