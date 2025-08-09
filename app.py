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

# --- 티커 그룹 리스트 수집 (캐시 적용) ---

@st.cache_data(ttl=3600)
def get_sp500_tickers():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    df = pd.read_csv(url)
    return df['Symbol'].tolist()

@st.cache_data(ttl=3600)
def get_nasdaq100_tickers():
    url = "https://datahub.io/core/nasdaq-listings/r/nasdaq-listed-symbols.csv"
    df = pd.read_csv(url)
    # NASDAQ 100 공식 리스트가 아니므로, 예시로 NASDAQ 상장 기업 중 시총 상위 필터 가능 (여기선 그냥 상장된 NASDAQ 기업)
    # 정확한 나스닥100 리스트는 별도 공개 소스 참고 필요 (직접 수동 관리 추천)
    # 여기선 일단 전체 NASDAQ 상장 티커 반환 (테스트 목적)
    return df['Symbol'].tolist()

@st.cache_data(ttl=3600)
def get_dowjones30_tickers():
    # Dow Jones 30 공식 리스트가 너무 작으므로 직접 하드코딩 권장
    return [
        "AAPL", "MSFT", "JPM", "V", "JNJ", "WMT", "PG", "UNH",
        "HD", "DIS", "INTC", "MRK", "CVX", "VZ", "CSCO", "KO",
        "TRV", "IBM", "MCD", "NKE", "AXP", "BA", "CAT", "MMM",
        "GS", "DOW", "CSX", "RTX", "AMGN", "CRM"
    ]

@st.cache_data(ttl=3600)
def get_russell2000_tickers():
    # 러셀2000 전체 리스트 공개 URL이 별도로 없고 너무 많아, 보통 수동관리 혹은 API사용 권장
    # 여기서는 대표 샘플 티커 일부만 반환 (실제 리스트는 별도 수집 필요)
    return [
        "TROV", "IDEX", "TENB", "XELA", "OMEX", "MRTN", "GOGO", "INSG"
    ]

def get_sector_etfs():
    # 미국 대표 섹터 ETF 모음 (12개 대표 ETF)
    return [
        "XLB", "XLE", "XLF", "XLI", "XLK", "XLP",
        "XLRE", "XLU", "XLV", "XLY", "VOX", "VGT"
    ]

def get_tickers_for_group(group_name):
    if group_name == "S&P 500":
        return get_sp500_tickers()
    elif group_name == "Nasdaq 100":
        return get_nasdaq100_tickers()
    elif group_name == "Dow Jones 30":
        return get_dowjones30_tickers()
    elif group_name == "Russell 2000":
        return get_russell2000_tickers()
    elif group_name == "Sector ETFs":
        return get_sector_etfs()
    else:
        return []

# --- Streamlit UI ---

st.title("그룹별 매수 신호 종목 분석기")

selected_group = st.selectbox("그룹 선택", options=[
    "Nasdaq 100",
    "S&P 500",
    "Dow Jones 30",
    "Sector ETFs",
    "Russell 2000"
])

method = st.radio("분석 기법 선택 (하나만 선택)", options=["Elliot Wave", "Moving Average", "RSI"], index=1)

if st.button("분석 시작"):

    tickers = get_tickers_for_group(selected_group)
    buy_stocks = []

    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(tickers)

    for i, ticker in enumerate(tickers):
        status_text.text(f"{ticker} 데이터 다운로드 및 분석 중 ({i+1}/{total})...")
        try:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        except Exception as e:
            status_text.text(f"{ticker} 다운로드 실패: {e}")
            continue

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
