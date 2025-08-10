import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

st.title("캔들 차트 테스트")

ticker = st.text_input("티커 입력", "AAPL")

if ticker:
    data = yf.download(ticker, period="1mo", interval="1d")
    st.write("원본 데이터:")
    st.write(data.head())
    st.write(f"인덱스 타입: {type(data.index)}")
    st.write(f"컬럼: {list(data.columns)}")

    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)
        st.write("인덱스를 DatetimeIndex로 변환함")

    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        st.error(f"필수 컬럼 누락: {missing_cols}")
    else:
        # 숫자 아닌 값 강제 NaN 처리 후 제거
        for col in required_cols:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        data = data.dropna(subset=required_cols)

        # 타입 변환
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
            st.warning("데이터가 없습니다.")
        else:
            try:
                fig, ax = mpf.plot(
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
                st.error(f"mplfinance.plot 오류: {e}")
