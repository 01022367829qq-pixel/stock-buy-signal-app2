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

        # 엄격한 NaN 제거 및 숫자 변환
        data = data.dropna(how='any')
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        data = data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])

        data = data.astype({
            'Open': float,
            'High': float,
            'Low': float,
            'Close': float,
            'Volume': int
        })

        data.index.name = "Date"

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
