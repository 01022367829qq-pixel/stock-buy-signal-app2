import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import numpy as np
import ta
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

def fetch_data(ticker):
    start_date = datetime.today() - timedelta(days=240)  # 약 8개월
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
    return data

def calculate_indicators(df):
    # ta 라이브러리 기반 지표 계산
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_upper'] = bb.bollinger_hband()
    df['BB_middle'] = bb.bollinger_mavg()
    df['BB_lower'] = bb.bollinger_lband()
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    return df

def generate_signal_with_targets(df):
    rsi = df['RSI'].iloc[-1]
    price = df['Close'].iloc[-1]
    atr = df['ATR'].iloc[-1]
    adx = df['ADX'].iloc[-1]
    bb_lower = df['BB_lower'].iloc[-1]

    rsi_signal = rsi <= 40
    bb_signal = price <= bb_lower
    adx_signal = adx > 20

    buy_signal = rsi_signal and bb_signal and adx_signal

    if buy_signal:
        k1 = 2.5 if adx > 30 else 2.0
        k2 = 0.8
        target_price = price + k1 * atr
        stop_loss = price - k2 * atr
        comment = (
            f"매수 신호: RSI {rsi:.1f} ≤ 40, "
            f"주가가 볼린저 밴드 하단 근접, ADX {adx:.1f} (강한 추세), "
            f"목표가 및 손절가 자동 산출 완료."
        )
    else:
        target_price = None
        stop_loss = None
        comment = "매수 조건 미충족."

    return buy_signal, target_price, stop_loss, comment

def plot_candle_with_targets(df, ticker, target_price=None, stop_loss=None):
    addplots = []
    if target_price is not None:
        target_line = pd.Series(target_price, index=df.index)
        addplots.append(mpf.make_addplot(target_line, color='green', linestyle='--', width=1.5))
    if stop_loss is not None:
        stop_line = pd.Series(stop_loss, index=df.index)
        addplots.append(mpf.make_addplot(stop_line, color='red', linestyle='--', width=1.5))

    fig, axlist = mpf.plot(
        df,
        type='candle',
        style='charles',
        title=f"{ticker} 최근 8개월 캔들 차트",
        ylabel='가격',
        figsize=(16, 9),
        returnfig=True,
        volume=False,
        addplot=addplots
    )

    ax = axlist[0]
    xmin, xmax = ax.get_xlim()
    xrange = xmax - xmin
    ax.set_xlim(xmin, xmax + xrange * 0.10)  # 오른쪽 여백 10%

    # legend 제거
    for ax in axlist:
        if ax.legend_:
            ax.legend_.remove()

    return fig

if ticker:
    try:
        data = fetch_data(ticker)

        if data.empty:
            st.warning(f"{ticker} 데이터가 없습니다.")
        else:
            data = calculate_indicators(data)
            buy_signal, target_price, stop_loss, comment = generate_signal_with_targets(data)

            st.markdown(f"### 전략 결과")
            st.write(comment)

            fig = plot_candle_with_targets(data, ticker, target_price, stop_loss)
            st.pyplot(fig)

    except Exception as e:
        st.error(f"데이터 불러오는 중 오류: {e}")
