import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.signal import find_peaks

# --- 보조 함수들 ---

def compute_rsi(series, period=14):
    if not isinstance(series, pd.Series):
        try:
            series = pd.Series(series)
        except Exception:
            return pd.Series(dtype=float)
    series = pd.to_numeric(series, errors='coerce').dropna()
    if series.empty:
        return pd.Series(dtype=float)
    
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

def detect_wave_points(close, distance=5, prominence=None):
    close_arr = np.asarray(close)
    if np.isnan(close_arr).any():
        close_arr = close_arr[~np.isnan(close_arr)]
    peaks, _ = find_peaks(close_arr, distance=distance, prominence=prominence)
    valleys, _ = find_peaks(-close_arr, distance=distance, prominence=prominence)
    return peaks, valleys

def is_elliot_wave_pattern(close):
    prominence = (np.nanmax(close) - np.nanmin(close)) * 0.05
    peaks, valleys = detect_wave_points(close, distance=5, prominence=prominence)
    
    if len(peaks) < 3 or len(valleys) < 2:
        return False, None
    
    points = np.sort(np.concatenate((peaks, valleys)))
    if len(points) < 5:
        return False, None
    
    wave_points = points[:5]
    wave_lengths = np.diff(close.iloc[wave_points].values)
    fib_ratios = [0.382, 0.5, 0.618, 1.0, 1.618, 2.618]
    valid_fib = any(abs(abs(wave_lengths[1]) / abs(wave_lengths[0]) - fr) < 0.1 for fr in fib_ratios)
    
    if not valid_fib:
        return False, None
    
    return True, wave_points

def is_buy_signal_elliot(df):
    try:
        close = extract_close(df)
    except Exception:
        return False
    
    if len(close) < 10:
        return False
    try:
        result, points = is_elliot_wave_pattern(close)
        return result
    except Exception:
        return False

def is_buy_signal_ma(df):
    try:
        close = extract_close(df)
    except Exception:
        return False
    
    if len(close) < 51:
        return False
    short_ma = close.rolling(window=20).mean()
    long_ma = close.rolling(window=50).mean()
    try:
        if bool(short_ma.isna().iat[-2]) or bool(short_ma.isna().iat[-1]):
            return False
        if bool(long_ma.isna().iat[-2]) or bool(long_ma.isna().iat[-1]):
            return False
        return (short_ma.iat[-2] < long_ma.iat[-2]) and (short_ma.iat[-1] > long_ma.iat[-1])
    except Exception:
        return False

def is_buy_signal_rsi(df):
    try:
        close = extract_close(df)
    except Exception:
        return False
    
    rsi = compute_rsi(close)
    if len(rsi) == 0:
        return False
    try:
        if rsi.isna().iat[-1]:
            return False
        return rsi.iat[-1] <= 60  # RSI 조건 완화
    except Exception:
        return False

def is_buy_signal_elliot_rsi_bb(df):
    try:
        close = extract_close(df)
    except Exception:
        return False
    
    if len(close) < 21:
        return False
    elliot_cond = is_buy_signal_elliot(df)
    
    rsi = compute_rsi(close)
    if rsi.empty or rsi.isna().iat[-1]:
        return False
    rsi_cond = rsi.iat[-1] <= 60

    upper, lower = compute_bollinger_bands(close)
    if lower.isna().iat[-1]:
        return False
    bb_cond = close.iat[-1] <= lower.iat[-1]

    return elliot_cond and rsi_cond and bb_cond

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

def extract_close(df):
    # 멀티인덱스 처리
    if isinstance(df.columns, pd.MultiIndex):
        if 'Close' in df.columns.get_level_values(1):
            close_df = df.xs('Close', axis=1, level=1)
            if close_df.shape[1] == 1:
                return close_df.iloc[:, 0]
            else:
                # 여러 티커 데이터면 첫 번째 컬럼 선택 (필요하면 조정)
                return close_df.iloc[:, 0]
        else:
            raise KeyError("'Close' 컬럼이 멀티인덱스에 없습니다.")
    else:
        if 'Close' in df.columns:
            return df['Close']
        else:
            raise KeyError("'Close' 컬럼이 없습니다.")

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

st.title("그룹별 매수 신호 종목 분석기")

selected_group = st.selectbox("그룹 선택", options=["Nasdaq 100", "S&P 500", "Dow Jones 30", "Sector ETFs"])

method = st.radio(
    "분석 기법 선택 (하나만 선택)",
    options=["Moving Average", "RSI", "Elliot+RSI+BB"],
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
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty or len(df) < 60:
            continue

        try:
            score, msg = score_for_signal(method, df)
        except Exception as e:
            st.error(f"{ticker} 분석 중 오류 발생: {e}")
            continue

        if score > 0:
            try:
                close = extract_close(df)
                entry = close.iat[-1]
            except Exception:
                entry = None
            target = entry * 1.05 if entry else None
            stop = entry * 0.95 if entry else None
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
            if stock['entry']:
                st.markdown(f"""
                    - 진입가: {stock['entry']:.2f}  
                    - 목표가: {stock['target']:.2f}  
                    - 손절가: {stock['stop']:.2f}
                """)
            else:
                st.write("진입가 정보가 없습니다.")
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
            if method == "Elliot+RSI+BB" or method == "Elliot Wave":
                try:
                    close = extract_close(df)
                    _, points = is_elliot_wave_pattern(close)
                    if points is not None:
                        for idx, pt in enumerate(points):
                            if pt < len(df):
                                fig.add_annotation(
                                    x=df.index[pt],
                                    y=close.iat[pt],
                                    text=f"W{idx+1}",
                                    showarrow=True,
                                    arrowhead=2,
                                    ax=0,
                                    ay=-20,
                                    font=dict(color="blue")
                                )
                except Exception:
                    pass

            fig.update_layout(
                title=f"{stock['ticker']} 일간 캔들 차트",
                xaxis_title="날짜",
                yaxis_title="가격",
                xaxis_rangeslider_visible=False,
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
