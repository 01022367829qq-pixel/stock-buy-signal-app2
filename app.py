import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# 가운데 정렬 제목 (스타일 직접 지정)
st.markdown(
    "<h1 style='text-align: center;'>내 투자 전략 웹사이트</h1>",
    unsafe_allow_html=True
)

# 전략 선택과 티커 입력을 한 줄에 배치하되, 너비를 조절
col1, col2 = st.columns([1, 1])  # 비율 1:1로 균등 분할

with col1:
    strategy = st.selectbox("전략 선택", ["스윙 트레이딩", "데이 트레이딩", "포지션 트레이딩"])

with col2:
    ticker = st.text_input("종목 티커 입력", "AAPL")

# 차트 출력
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
            autosize=True,
            height=450,
            margin=dict(l=20, r=20, t=30, b=20),
            title=f"{ticker} 차트"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("잘못된 티커이거나 데이터가 없습니다.")
