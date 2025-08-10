import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align: center;'>내 투자 전략 웹사이트</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    strategy = st.selectbox("전략 선택", ["전략 A", "전략 B", "전략 C"])
with col2:
    ticker = st.text_input("티커 입력", value="AAPL")

if ticker:
    try:
        data = yf.download(ticker, period="1mo", interval="1d")
        st.write("원본 데이터:")
        st.write(data.head())

        # 인덱스가 DatetimeIndex인지 체크, 아니면 변환
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

        # 필요한 컬럼 존재 확인
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in data.columns:
                st.error(f"필수 컬럼 {col}이 데이터에 없습니다.")
                st.stop()

        # 숫자가 아닌 값 강제 NaN으로 바꾸고 dropna
        for col in required_cols:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        data = data.dropna(subset=required_cols)

        # 타입 강제 변환
        data = data.astype({
            'Open': float,
            'High': float,
            'Low': float,
            'Close': float,
            'Volume': int
        })

        st.write("정제된 데이터:")
        st.write(data.head())

        if data.empty:
            st.warning(f"{ticker} 데이터가 없습니다.")
        else:
            fig, axlist = mpf.plot(
                data,
                type='candle',
                style='charles',
                title=f"{ticker} 캔들 차트",
                ylabel='가격',
                figsize=(16,8),
                returnfig=True
            )
            st.pyplot(fig)

    except Exception as e:
        st.error(f"데이터 불러오는 중 오류: {e}")
