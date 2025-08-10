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

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']

        for col in required_cols:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        data = data.dropna(subset=required_cols)

        data = data.astype({
            'Open': float,
            'High': float,
            'Low': float,
            'Close': float,
            'Volume': int
        })

        if data.empty:
            st.warning(f"{ticker} 데이터가 없습니다.")
        else:
            fig, axlist = mpf.plot(
                data,
                type='candle',
                style='charles',
                title=f"{ticker} 캔들 차트",
                ylabel='가격',
                figsize=(14, 7),
                returnfig=True,
                volume=False,
            )

            # legend 강제 제거
            for ax in axlist:
                if ax.legend_:
                    ax.legend_.remove()

            st.pyplot(fig)

    except Exception as e:
        st.error(f"데이터 불러오는 중 오류: {e}")
