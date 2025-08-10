import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(layout="wide")

st.markdown(
    "<h1 style='text-align: center;'>내 투자 전략 웹사이트</h1>",
    unsafe_allow_html=True
)

ticker = "AAPL"
data = yf.download(ticker, period="1mo", interval="1d").dropna()

fig = go.Figure(data=[go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    increasing_line_color='green',
    decreasing_line_color='red'
)])
fig.update_layout(
    height=675,
    margin=dict(l=20, r=20, t=30, b=20),
    title=f"{ticker} 캔들 차트"
)
st.plotly_chart(fig, use_container_width=True)
