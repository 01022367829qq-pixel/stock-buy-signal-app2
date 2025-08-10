import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# 제목 가운데 정렬
st.markdown("<h1 style='text-align: center;'>내 투자 전략 웹사이트</h1>", unsafe_allow_html=True)

# 전략별 설명
with st.expander("전략별 설명 보기"):
    st.markdown("""
    ### 전략 A
    - 단기 추세 추종 전략
    - RSI, MACD 지표를 활용

    ### 전략 B
    - 중기 스윙 트레이딩
    - 이동평균선 돌파 기반

    ### 전략 C
    - 장기 포지션 트레이딩
    - 펀더멘털 및 기술적 지표 결합
    """)

# 투자 시 유의 사항
with st.expander("투자 시 유의 사항"):
    st.markdown("""
    - 모든 투자는 원금 손실 가능성이 있습니다.
    - 본 웹사이트의 전략은 참고용일 뿐, 투자 책임은 사용자 본인에게 있습니다.
    - 시장 변동성 및 외부 요인에 따라 성과가 달라질 수 있습니다.
    - 충분한 검토 후 투자 결정을 하시기 바랍니다.
    """)

# 전략 선택과 티커 입력 (왼쪽 정렬, 좁은 너비)
col1, col2 = st.columns([1, 1])
with col1:
    strategy = st.selectbox("전략 선택", ["전략 A", "전략 B", "전략 C"])
with col2:
    ticker = st.text_input("티커 입력", value="AAPL")

if ticker:
    try:
        # 8개월 전 날짜 계산
        start_date = datetime.today() - timedelta(days=240)
        start_str = start_date.strftime('%Y-%m-%d')

        data = yf.download(ticker, start=start_str, interval="1d")

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
                title=f"{ticker} 최근 8개월 캔들 차트",
                ylabel='가격',
                figsize=(16, 9),
                returnfig=True,
                volume=False,
            )

            # 오른쪽 여백 10% 추가
            ax = axlist[0]
            xmin, xmax = ax.get_xlim()
            xrange = xmax - xmin
            ax.set_xlim(xmin, xmax + xrange * 0.10)  # 10% 여백

            # legend 제거
            for ax in axlist:
                if ax.legend_:
                    ax.legend_.remove()

            st.pyplot(fig)

    except Exception as e:
        st.error(f"데이터 불러오는 중 오류: {e}")
