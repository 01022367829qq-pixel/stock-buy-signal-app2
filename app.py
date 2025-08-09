import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 보조 함수들 ---

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def is_buy_signal_elliot(df):
    close = df['Close']
    if len(close) < 5:
        return False
    try:
        return (close.iat[-3] < close.iat[-2]) and (close.iat[-2] < close.iat[-1])
    except Exception:
        return False

def is_buy_signal_ma(df):
    if len(df) < 51:
        return False
    short_ma = df['Close'].rolling(window=20).mean()
    long_ma = df['Close'].rolling(window=50).mean()
    try:
        if bool(short_ma.isna().iat[-2]) or bool(short_ma.isna().iat[-1]):
            return False
        if bool(long_ma.isna().iat[-2]) or bool(long_ma.isna().iat[-1]):
            return False
        return (short_ma.iat[-2] < long_ma.iat[-2]) and (short_ma.iat[-1] > long_ma.iat[-1])
    except Exception:
        return False

def is_buy_signal_rsi(df):
    rsi = compute_rsi(df['Close'])
    if len(rsi) == 0:
        return False
    try:
        if rsi.isna().iat[-1]:
            return False
        return rsi.iat[-1] <= 40
    except Exception:
        return False

def score_for_signal(method, df):
    score = 0
    msg = ""
    if method == "Elliot Wave" and is_buy_signal_elliot(df):
        score = 40
        msg = "엘리엇 웨이브 매수 신호 감지"
    elif method == "Moving Average" and is_buy_signal_ma(df):
        score = 30
        msg = "이동평균선 골든크로스 감지"
    elif method == "RSI" and is_buy_signal_rsi(df):
        score = 30
        msg = "RSI 과매도 구간 감지"
    return score, msg

# --- 티커 그룹 리스트 URL ---

SP500_TICKERS_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
DJ30_TICKERS_URL = "https://raw.githubusercontent.com/datasets/dow-jones/master/data/dow-jones.csv"

@st.cache_data(ttl=3600)
def get_sp500_tickers():
    df = pd.read_csv(SP500_TICKERS_URL)
    return df['Symbol'].tolist()

@st.cache_data(ttl=3600)
def get_dj30_tickers():
    df = pd.read_csv(DJ30_TICKERS_URL)
    return df['Symbol'].unique().tolist()

@st.cache_data(ttl=3600)
def get_nasdaq100_tickers():
    # 나스닥 100은 URL에서 안 읽히는 경우가 많아서 하드코딩으로 예시
    return ["AAPL", "MSFT", "AMZN", "TSLA", "NVDA", "GOOGL", "META", "PEP", "CSCO", "ADBE"]

def get_sector_etf_tickers():
    return ["XLK", "XLF", "XLV", "XLY", "XLI", "XLU"]

def get_tickers_for_group(group_name):
    if group_name == "S&P 500":
        return get_sp500_tickers()
    elif group_name == "Nasdaq 100":
        return get_nasdaq100_tickers()
    elif group_name == "Dow Jones 30":
        return get_dj30_tickers()
    elif group_name == "Sector ETFs":
        return get_sector_etf_tickers()
    else:
        return []

# --- Streamlit UI ---

st.title("그룹별 매수 신호 종목 분석기")

selected_group = st.selectbox("그룹 선택", options=["Nasdaq 100", "S&P 500", "Dow Jones 30", "Sector ETFs"])

method = st.radio("분석 기법 선택 (하나만 선택)", options=["Elliot Wave", "Moving Average", "RSI"], index=1)

if st.button("분석 시작"):

    tickers = get_tickers_for_group(selected_group)
    buy_stocks = []

    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(tickers)

    for i, ticker in enumerate(tickers):
        status_text.text(f"{ticker} 데이터 다운로드 및 분석 중 ({i+1}/{total})...")
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 60:
            continue

        score, msg = score_for_signal(method, df)
        if score > 0:
            entry = df['Close'].iat[-1]
            target = entry * 1.05
            stop = entry * 0.95
            buy_stocks.append({
                "ticker": ticker,
                "score": score,
                "msg": msg,
                "entry": entry,
                "target": target,
                "stop": stop,
                "data": df
            })
        progress_bar.progress((i+1)/total)

    progress_bar.empty()
    status_text.empty()

    if not buy_stocks:
        st.info("매수 신호가 감지된 종목이 없습니다.")
    else:
        for stock in buy_stocks:
            st.subheader(f"{stock['ticker']} - 점수: {stock['score']}")
            st.write(stock['msg'])
            st.markdown(f"""
                - 진입가: {stock['entry']:.2f}  
                - 목표가: {stock['target']:.2f}  
                - 손절가: {stock['stop']:.2f}
            """)
            df = stock['data']
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color='green',
                decreasing_line_color='red',
                name=stock['ticker']
            )])
            fig.update_layout(
                title=f"{stock['ticker']} 일간 캔들 차트",
                xaxis_title="날짜",
                yaxis_title="가격",
                xaxis_rangeslider_visible=False,
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
