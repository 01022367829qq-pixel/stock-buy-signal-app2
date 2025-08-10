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
        data = yf.download(ticker, period="1mo", interval="1d")
        
        if data.empty:
            st.warning("데이터가 없습니다.")
        else:
            st.write("데이터 인덱스 타입:", type(data.index))
            st.write("데이터 인덱스 샘플:", data.index[:5])
            st.write("데이터 컬럼:", data.columns.tolist())
            st.write("결측치 개수:\n", data.isnull().sum())
            st.write("데이터 샘플:")
            st.dataframe(data.head())
            
            # 인덱스가 날짜 형식인지 확인
            if not isinstance(data.index, pd.DatetimeIndex):
                st.warning("데이터 인덱스가 날짜 형식이 아닙니다. 변환 시도합니다.")
                data.index = pd.to_datetime(data.index)
            
            # 필수 컬럼 확인
            required_cols = ['Open', 'High', 'Low', 'Close']
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                st.error(f"필수 컬럼이 없습니다: {missing_cols}")
            elif data[required_cols].isnull().any().any():
                st.error("데이터에 결측치가 포함되어 있습니다. 캔들 차트가 제대로 표시되지 않을 수 있습니다.")
            else:
                fig = go.Figure(data=[go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    increasing_line_color='green',
                    decreasing_line_color='red',
                    name=ticker
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
