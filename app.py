import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.markdown(
    "<h1 style='text-align: center;'>내 투자 전략 웹사이트</h1>",
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 1])

with col1:
    strategy = st.selectbox("전략 선택", ["스윙 트레이딩", "데이 트레이딩", "포지션 트레이딩"])

with col2:
    ticker = st.text_input("종목 티커 입력", "AAPL")

if ticker:
    data = yf.download(ticker, period="1mo", interval="1d")
    if not data.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close']
        )])
        fig.update_layout(
            autosize=False,
            width=1800,
            height=500,
            margin=dict(l=20, r=20, t=30, b=20),
            title=f"{ticker} 차트"
        )
        st.plotly_chart(fig, use_container_width=False)
    else:
        st.warning("잘못된 티커이거나 데이터가 없습니다.")
