import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# 섹터 선택
sector = st.selectbox("섹터 선택", ["Technology", "Financials", "Consumer Discretionary"])

# (예시) 섹터별 티커 리스트 - 실제로는 더 많이, 또는 API로 교체 가능
sector_tickers = {
    "Technology": ["AAPL", "MSFT", "NVDA"],
    "Financials": ["JPM", "BAC", "C"],
    "Consumer Discretionary": ["AMZN", "TSLA", "NKE"],
}

tickers = sector_tickers.get(sector, [])

# 간단 매수 신호 함수 (임시)
def is_buy_signal(df):
    # RSI 30 이하 등 간단 조건 (예시)
    rsi = compute_rsi(df['Close'])
    return rsi[-1] < 30

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

for ticker in tickers:
    df = yf.download(ticker, period="3mo", interval="1d")
    if df.empty:
        continue
    if is_buy_signal(df):
        st.subheader(f"{ticker} 매수 신호 감지!")
        st.write("진입가: ... 목표가: ... 손절가: ...")  # 여기 원하는 계산식 넣기
        
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
