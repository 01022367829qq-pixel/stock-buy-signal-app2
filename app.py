import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# --- 기법별 신호 함수 및 보조 함수 ---

def is_buy_signal_elliot(df):
    # 엘리엇 파동 구현은 어려워 임시로 False 리턴
    return False

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def is_buy_signal_rsi(df):
    rsi = compute_rsi(df['Close'])
    if len(rsi) == 0 or pd.isna(rsi.iloc[-1]):
        return False
    return rsi.iloc[-1] <= 40  # RSI 40 이하 과매도 구간 예시

def is_buy_signal_ma(df):
    short_ma = df['Close'].rolling(window=20).mean()
    long_ma = df['Close'].rolling(window=50).mean()
    if len(short_ma) < 2 or len(long_ma) < 2:
        return False
    # 골든크로스 여부 판단
    return (short_ma.iloc[-2] < long_ma.iloc[-2]) and (short_ma.iloc[-1] > long_ma.iloc[-1])

# 간단 점수 계산 함수 예시 (실제 점수 체계는 자유롭게 조절)
def score_for_signal(signal_methods, df):
    score = 0
    if "Elliot Wave" in signal_methods and is_buy_signal_elliot(df):
        score += 40
    if "Moving Average" in signal_methods and is_buy_signal_ma(df):
        score += 30
    if "RSI" in signal_methods and is_buy_signal_rsi(df):
        score += 30
    return score

# 진입, 목표, 손절가 계산 (간단 비율 적용 예시)
def calculate_prices(df):
    entry = df['Close'].iloc[-1]
    target = entry * 1.05  # 5% 목표 수익
    stop = entry * 0.95    # 5% 손절
    return entry, target, stop

# --- 섹터별 종목 리스트 예시 (실제로는 종목코드 직접 업데이트 필요) ---
sector_dict = {
    "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL"],
    "Healthcare": ["JNJ", "PFE", "MRK", "ABT"],
    "Financials": ["JPM", "BAC", "WFC", "C"],
    "Consumer Discretionary": ["AMZN", "TSLA", "NKE", "SBUX"],
    "Industrials": ["HON", "UPS", "CAT", "BA"],
    "Energy": ["XOM", "CVX", "COP", "SLB"]
}

st.title("섹터 & 기법 선택 주식 매수 타점 분석기")

# --- UI: 섹터 선택 ---
selected_sector = st.selectbox("섹터를 선택하세요", list(sector_dict.keys()))

# --- UI: 기법 선택 (복수 선택 가능) ---
methods = st.multiselect("분석에 사용할 기법을 선택하세요", ["Elliot Wave", "Moving Average", "RSI"], default=["Moving Average", "RSI"])

if st.button("분석 시작"):
    if not selected_sector:
        st.warning("섹터를 선택하세요.")
    elif not methods:
        st.warning("적어도 하나 이상의 기법을 선택하세요.")
    else:
        tickers = sector_dict[selected_sector]
        st.write(f"선택한 섹터: {selected_sector} / 분석 기법: {', '.join(methods)}")
        buy_signals = []

        for ticker in tickers:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty or len(df) < 50:
                continue
            score = score_for_signal(methods, df)
            if score >= 30:  # 점수 기준 임의 조정 가능
                entry, target, stop = calculate_prices(df)
                buy_signals.append((ticker, score, entry, target, stop, df))

        if not buy_signals:
            st.info("매수 신호가 감지된 종목이 없습니다.")
        else:
            for ticker, score, entry, target, stop, df in buy_signals:
                st.markdown(f"### {ticker}  |  점수: {score}/100")
                st.markdown(f"- 진입가: {entry:.2f}")
                st.markdown(f"- 목표가: {target:.2f}")
                st.markdown(f"- 손절가: {stop:.2f}")

                fig = go.Figure(data=[go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    increasing_line_color='green',
                    decreasing_line_color='red',
                    name=ticker
                )])
                fig.update_layout(
                    title=f"{ticker} 캔들차트",
                    xaxis_title="날짜",
                    yaxis_title="가격",
                    xaxis_rangeslider_visible=False,
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)
