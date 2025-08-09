import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

SECTORS = {
    'Technology': ['AAPL', 'MSFT', 'NVDA'],
    'Healthcare': ['JNJ', 'PFE', 'MRNA'],
    'Financial': ['JPM', 'BAC', 'C']
}

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# (위에 기법별 함수 정의)

st.title("섹터별 다중 투자기법 매수 신호 분석")

sector = st.selectbox("섹터 선택", list(SECTORS.keys()))
methods = st.multiselect("투자 기법 선택", ["Elliot Wave", "이동평균선", "RSI"])

if st.button("분석 시작"):
    tickers = SECTORS[sector]
    buy_candidates = []

    for ticker in tickers:
        df = yf.download(ticker, period="3mo", interval="1d")
        if df.empty:
            continue

        signals = []
        if "Elliot Wave" in methods and is_buy_signal_elliot(df):
            signals.append("Elliot Wave")
        if "이동평균선" in methods and is_buy_signal_ma(df):
            signals.append("이동평균선")
        if "RSI" in methods and is_buy_signal_rsi(df):
            signals.append("RSI")

        if signals:
            buy_candidates.append((ticker, signals, df))

    if not buy_candidates:
        st.warning("매수 신호 감지된 종목이 없습니다.")
    else:
        for ticker, signals, df in buy_candidates:
            st.subheader(f"{ticker} - 매수 신호: {', '.join(signals)}")

            # 간단한 진입가/손절가 예시 (종가 기준)
            entry = df['Close'].iloc[-1]
            stop = entry * 0.95
            target = entry * 1.1

            st.markdown(f"""
            - 진입가: {entry:.2f}  
            - 손절가: {stop:.2f}  
            - 목표가: {target:.2f}
            """)

            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color='green',
                decreasing_line_color='red',
                name=ticker
            )])
            fig.update_layout(xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
