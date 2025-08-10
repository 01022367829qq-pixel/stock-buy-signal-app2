import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 환경 설정
st.set_page_config(layout="wide")

# 제목
st.markdown(
    "<h1 style='text-align: center;'>내 투자 전략 웹사이트</h1>",
    unsafe_allow_html=True
)

# 전략 선택 + 티커 입력
col1, col2 = st.columns([1, 1])
with col1:
    strategy = st.selectbox("전략 선택", ["전략 A", "전략 B", "전략 C"])
with col2:
    ticker = st.text_input("티커 입력", value="AAPL")

# 차트 표시
if ticker:
    try:
        # 데이터 다운로드
        data = yf.download(ticker, period="1mo", interval="1d").dropna()

        # 인덱스 timezone 제거 (Plotly 버그 방지)
        data.index = data.index.tz_localize(None)

        if data.empty:
            st.warning(f"{ticker} 데이터가 없습니다.")
        else:
            # 캔들차트 생성
            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                increasing_line_color='green',
                decreasing_line_color='red'
            )])

            # 레이아웃 조정
            fig.update_layout(
                height=675,
                margin=dict(l=20, r=20, t=30, b=20),
                title=f"{ticker} 캔들 차트",
                xaxis_rangeslider_visible=False
            )

            # 안전 출력 (환경에 따라 st.write 사용)
            try:
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.write(fig)

    except Exception as e:
        st.error(f"데이터 불러오는 중 오류: {e}")
