import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(layout="wide")  # 전체 페이지 레이아웃 넓게

st.markdown(
    "<h1 style='text-align: center;'>AI 매수타점 분석기</h1>",
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
            height=675,
            margin=dict(l=20, r=20, t=30, b=20),
            title=f"{ticker} 차트"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("잘못된 티커이거나 데이터가 없습니다.")
