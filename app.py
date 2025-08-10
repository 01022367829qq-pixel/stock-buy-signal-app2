import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.signal import find_peaks

# --- 보조 함수들 ---

def compute_rsi(series, period=14):
    series = pd.to_numeric(series, errors='coerce').dropna()
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_bollinger_bands(series, period=20, num_std=2):
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = sma + num_std * std
    lower = sma - num_std * std
    return upper, lower

def detect_wave_points(close, distance=5, prominence=1):
    # 고점 (peaks)
    peaks, _ = find_peaks(close, distance=distance, prominence=prominence)
    # 저점 (valleys)
    valleys, _ = find_peaks(-close, distance=distance, prominence=prominence)
    return peaks, valleys

def is_elliot_wave_possible(df):
    close = df['Close']
    if len(close) < 30:
        return False
    peaks, valleys = detect_wave_points(close, distance=5, prominence=(close.max()-close.min())*0.05)
    # 기본적으로 최소 5개 고점과 4개 저점이 있어야 상승 5파동 패턴 가능성 있다고 판단
    if len(peaks) >= 5 and len(valleys) >= 4:
        return True
    else:
        return False

def is_buy_signal_elliot_rsi_bb(df):
    if len(df) < 30:
        return False

    elliot_cond = is_elliot_wave_possible(df)

    rsi = compute_rsi(df['Close'])
    if rsi.isna().all():
        return False
    rsi_cond = rsi.iat[-1] <= 40 if not pd.isna(rsi.iat[-1]) else False

    upper, lower = compute_bollinger_bands(df['Close'])
    if pd.isna(lower.iat[-1]):
        return False
    bb_cond = df['Close'].iat[-1] <= lower.iat[-1] * 1.02  # 하단 밴드 2% 근처

    return elliot_cond and rsi_cond and bb_cond

def score_for_signal(method, df):
    score = 0
    msg = ""
    if method == "Elliot+RSI+BB" and is_buy_signal_elliot_rsi_bb(df):
        score = 50
        msg = "엘리엇 파동 가능성 + RSI 과매도 + 볼린저밴드 하단 근접 매수 신호"
    elif method == "RSI":
        rsi = compute_rsi(df['Close'])
        if not rsi.isna().all() and rsi.iat[-1] <= 40:
            score = 30
            msg = "RSI 과매도 구간 감지"
    return score, msg

# --- 티커 그룹 리스트 URL ---

SP500_TICKERS_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"

@st.cache_data(ttl=3600)
def get_sp500_tickers():
    df = pd.read_csv(SP500_TICKERS_URL)
    return df['Symbol'].tolist()

@st.cache_data(ttl=3600)
def get_nasdaq100_tickers():
    return [
        "AAPL","MSFT","AMZN","TSLA","NVDA","GOOGL","META","PEP","CSCO","ADBE",
        "PYPL","INTC","CMCSA","NFLX","TXN","QCOM","CHTR","AMD","SBUX","ISRG",
        "FISV","MDLZ","AMAT","GILD","BKNG","LRCX","ADI","MU","MRVL","KLAC",
        "MELI","MAR","ATVI","CDNS","CSX","XEL","NXPI","WDAY","ALGN","CTAS",
        "KDP","EBAY","REGN","BIIB","CERN","EXC","IDXX","WBA","SIRI","ANSS",
        "EA","VRSK","ROST","CTSH","CDW","ODFL","ULTA","PCAR","SGEN","BIDU",
        "NTES","DLTR","ORLY","FAST","LULU","ILMN","ASML","MCHP","SNPS","VRSN",
        "SPLK","XCOM","CHKP","DOCU","TTWO","ATRS","BMRN","VEEV","WDC","ZM",
        "ANET","SWKS","PAYX","INCY","FIS","MTCH","ZS","XLNX","MRNA","CRWD",
        "NET","TEAM","OKTA","SNOW","DDOG","MDB","PLTR"
    ]

@st.cache_data(ttl=3600)
def get_dj30_tickers():
    return [
        "AAPL", "MSFT", "JNJ", "JPM", "V", "DIS", "HD", "INTC", "KO",
        "MRK", "NKE", "PG", "TRV", "UNH", "VZ", "WMT", "GS", "CRM", "MCD",
        "IBM", "AXP", "CSCO", "BA", "CAT", "CVX", "DOW", "XOM", "WBA", "RTX"
    ]

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

st.title("엘리엇 파동 + RSI + 볼린저 밴드 매수 신호 분석기")

selected_group = st.selectbox("그룹 선택", options=["Nasdaq 100", "S&P 500", "Dow Jones 30", "Sector ETFs"])

method = st.radio(
    "분석 기법 선택 (하나만 선택)",
    options=["Elliot+RSI+BB", "RSI"],
    index=0
)

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
