import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(layout="wide")

st.markdown(
    "<h1 style='text-align: center;'>내 투자 전략 웹사이트</h1>",
    unsafe_allow_html=True
)

col1, col2 = st.columns([2, 1])
with col1:
    strategy = st.selectbox("전략 선택", ["스윙 트레이딩", "데이 트레이딩", "포지션 트레이딩"])

with col2:
    ticker = st.text_input("종목 티커 입력", "").upper().strip()

if ticker:
    try:
        data = yf.download(ticker, period="1mo", interval="1d").dropna()
        data = data.tail(20)
        data = data[~data.index.duplicated(keep='last')]
        data = data.sort_index()

        if data.empty:
            st.warning("데이터가 없습니다.")
        else:
            st.write(f"캔들 차트에 쓸 데이터 개수: {len(data)}")
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
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
else:
    st.info("왼쪽 상단에 종목 티커를 입력해주세요.")
