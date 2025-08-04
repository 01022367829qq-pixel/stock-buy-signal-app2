import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# ----------------------
# 📌 종목 데이터 가져오기
# ----------------------
def get_data(ticker):
    df = yf.download(ticker, period='60d', interval='1d', progress=False, auto_adjust=True)
    return df

def ensure_series_1d(series):
    if hasattr(series, 'values') and series.values.ndim > 1:
        return pd.Series(series.values.flatten(), index=series.index)
    return series

# ----------------------
# 📌 매수 타점 분석 함수
# ----------------------
def check_buy_signal(
    df,
    weight_rsi_30=1,
    weight_rsi_20=2,
    weight_cci_100=1,
    weight_cci_150=2,
    weight_adx_25=1,
    weight_adx_20=2,
    weight_bb_low_101=1,
    weight_bb_low_1005=1
):
    if df.empty or len(df) < 20:
        return None

    close = ensure_series_1d(df['Close'])
    high = ensure_series_1d(df['High'])
    low = ensure_series_1d(df['Low'])
    volume = ensure_series_1d(df['Volume'])

    try:
        bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
        rsi = ta.momentum.RSIIndicator(close=close, window=14).rsi()
        adx = ta.trend.ADXIndicator(high=high, low=low, close=close, window=14).adx()
        cci = ta.trend.CCIIndicator(high=high, low=low, close=close, window=20).cci()
        atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
    except Exception as e:
        return None

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
    if latest_rsi <= 30: score += weight_rsi_30
    if latest_rsi <= 20: score += weight_rsi_20
    if latest_cci <= -100: score += weight_cci_100
    if latest_cci <= -150: score += weight_cci_150
    if latest_adx <= 25: score += weight_adx_25
    if latest_adx <= 20: score += weight_adx_20
    if latest_close <= latest_bb_low * 1.01: score += weight_bb_low_101
    if latest_close <= latest_bb_low * 1.005: score += weight_bb_low_1005

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
            'Score': score,
            'VolumeStatus': vol_status
        }
    else:
        return None

# ----------------------
# 📌 Streamlit UI
# ----------------------
st.set_page_config(page_title="📈 주식 매수 타점 추천기", layout="wide")
st.title("📈 AI 기반 주식 매수 타점 추천")

user_input = st.text_input("✅ 분석할 티커를 입력하세요 (쉼표로 구분)", value="AAPL, TSLA, MSFT")
tickers = [ticker.strip().upper() for ticker in user_input.split(",") if ticker.strip()]

if st.button("🔍 분석 시작") and tickers:
    results = []
    with st.spinner("분석 중입니다..."):
        for ticker in tickers:
            try:
                df = get_data(ticker)
                signal = check_buy_signal(df)
                if signal:
                    results.append({'Ticker': ticker, **signal})
            except Exception as e:
                st.error(f"{ticker} 분석 중 오류 발생")

    if results:
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values(by='Score', ascending=False).reset_index(drop=True)
        st.success("분석 완료!")
        st.dataframe(df_results)
    else:
        st.warning("🔎 조건을 만족한 종목이 없습니다.")
else:
    st.info("👆 종목을 입력하고 '분석 시작' 버튼을 눌러주세요.")

