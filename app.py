import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==============================
# 보조 함수
# ==============================

def compute_rsi(series, period=14):
    # 안전하게 숫자형으로 변환
    s = pd.to_numeric(series, errors='coerce')
    delta = s.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_bollinger_bands(series, period=20, num_std=2):
    s = pd.to_numeric(series, errors='coerce')
    sma = s.rolling(window=period).mean()
    std = s.rolling(window=period).std()
    upper = sma + num_std * std
    lower = sma - num_std * std
    return upper, lower

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
    if rsi.dropna().empty:
        return False
    try:
        rsi_last = float(rsi.dropna().iloc[-1])
        return rsi_last <= 40
    except Exception:
        return False

# ==============================
# 수정된: 엘리엇 + RSI + 볼린저밴드 결합 신호 (안전한 인덱싱)
# ==============================
def is_buy_signal_elliot_rsi_bb(df):
    # 기본 길이 체크
    if df is None or df.empty or len(df) < 21:
        return False

    try:
        # 1) 엘리엇(단순) 조건
        elliot_cond = is_buy_signal_elliot(df)

        # 2) RSI 조건 (유효값 있는지 확인 후 비교)
        rsi = compute_rsi(df['Close'])
        rsi_valid = rsi.dropna()
        if rsi_valid.empty:
            return False
        rsi_last = float(rsi_valid.iloc[-1])
        rsi_cond = (rsi_last <= 40)

        # 3) Bollinger Bands 조건 (유효값 확인 후 비교)
        upper, lower = compute_bollinger_bands(df['Close'])
        lower_valid = lower.dropna()
        if lower_valid.empty:
            return False
        lower_last = float(lower_valid.iloc[-1])
        close_last = float(pd.to_numeric(df['Close'].iloc[-1], errors='coerce'))
        # 하단선 근처(예: 하단선 이하 또는 2% 이내)
        bb_cond = (close_last <= lower_last * 1.02)

        return elliot_cond and rsi_cond and bb_cond

    except Exception:
        # 내부 예외는 False로 처리 (필요하면 로그 출력 추가)
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
    elif method == "Elliot+RSI+BB" and is_buy_signal_elliot_rsi_bb(df):
        score = 50
        msg = "엘리엇+RSI+볼린저밴드 매수 신호 감지"
    return score, msg

# ==============================
# 티커 데이터
# ==============================

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

# ==============================
# Streamlit UI
# ==============================

st.title("그룹별 매수 신호 종목 분석기")

selected_group = st.selectbox(
    "그룹 선택",
    options=["Nasdaq 100", "S&P 500", "Dow Jones 30", "Sector ETFs"]
)

method = st.radio(
    "분석 기법 선택",
    options=["Elliot Wave", "Moving Average", "RSI", "Elliot+RSI+BB"],
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
