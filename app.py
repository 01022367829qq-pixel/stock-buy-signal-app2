import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import plotly.io as pio
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.markdown(
    "<h1 style='text-align: center;'>내 투자 전략 웹사이트</h1>",
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 1])
with col1:
    strategy = st.selectbox("전략 선택", ["전략 A", "전략 B", "전략 C"])
with col2:
    ticker = st.text_input("티커 입력", value="AAPL")

if ticker:
    try:
        data = yf.download(ticker, period="1mo", interval="1d").dropna()
        data.index = data.index.tz_localize(None)

        if data.empty:
            st.warning(f"{ticker} 데이터가 없습니다.")
        else:
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
                title=f"{ticker} 캔들 차트",
                xaxis_rangeslider_visible=False
            )

            # Plotly를 HTML로 변환 후 출력
            html_str = pio.to_html(fig, include_plotlyjs="cdn")
            components.html(html_str, height=700)

    except Exception as e:
        st.error(f"데이터 불러오는 중 오류: {e}")
