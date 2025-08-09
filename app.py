import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# RSI 계산 함수
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 간단 매수 신호 판단 (RSI < 30일 때 매수 신호)
def is_buy_signal(df):
    rsi = compute_rsi(df['Close'])
    if rsi.empty or pd.isna(rsi.iloc[-1]):
        return False
    return rsi.iloc[-1] < 30

# 임시 진입/목표/손절가 계산 함수 (최근 종가 기준)
def calc_prices(df):
    entry = df['Close'].iloc[-1]
    target = entry * 1.05   # 목표가: 5% 상승 예상
    stop = entry * 0.95     # 손절가: 5% 하락 제한
    return entry, target, stop

st.title("섹터별 매수 신호 종목 분석 테스트")

# 섹터 선택박스
sector = st.selectbox("섹터 선택", ["Technology", "Financials", "Consumer Discretionary"])

# 섹터별 샘플 티커 리스트 (테스트용)
sector_tickers = {
    "Technology": ["AAPL", "MSFT", "NVDA"],
    "Financials": ["JPM", "BAC", "C"],
    "Consumer Discretionary": ["AMZN", "TSLA", "NKE"],
}

tickers = sector_tickers.get(sector, [])

st.write(f"선택된 섹터: {sector}")
st.write(f"종목 수: {len(tickers)}")

if st.button("🔍 매수 신호 종목 분석 시작"):
    buy_signals = []
    for ticker in tickers:
        df = yf.download(ticker, period="3mo", interval="1d")
        if df.empty:
            st.warning(f"{ticker} 데이터 로딩 실패")
            continue

        if is_buy_signal(df):
            entry, target, stop = calc_prices(df)
            buy_signals.append((ticker, entry, target, stop, df))

    if not buy_signals:
        st.info("매수 신호가 감지된 종목이 없습니다.")
    else:
        for ticker, entry, target, stop, df in buy_signals:
            st.subheader(f"{ticker} — 매수 신호 감지!")
            st.markdown(f"""
            - 진입가: {entry:.2f}  
            - 목표가: {target:.2f}  
            - 손절가: {stop:.2f}  
            """)
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color='green',
                decreasing_line_color='red'
            )])
            fig.update_layout(title=f"{ticker} 일간 캔들차트", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig)
