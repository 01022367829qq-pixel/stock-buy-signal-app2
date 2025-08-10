import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.title("내 투자 전략 웹사이트")  # 상단 중앙 제목

# 왼쪽 영역에 전략 선택과 티커 입력
strategy = st.selectbox("전략 선택", ["스윙 트레이딩", "데이 트레이딩", "포지션 트레이딩"])
ticker = st.text_input("종목 티커 입력", "AAPL")

# 차트 출력 영역
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
        
        # 가로 너비 100%, 세로는 가로 너비에 비율 맞추기
        fig.update_layout(
            autosize=True,
            width=800,  # 기본 크기 설정
            height=450,
            margin=dict(l=20, r=20, t=30, b=20),
            title=f"{ticker} 차트"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("잘못된 티커이거나 데이터가 없습니다.")
