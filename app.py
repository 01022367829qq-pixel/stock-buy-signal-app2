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
    close = df['Close']
    if len(close) < 10:
        st.write(f"{df.name} 엘리엇: 데이터 길이 부족")
        return False
    try:
        result, points = is_elliot_wave_pattern(close)
        st.write(f"{df.name} 엘리엇: 결과={result}, 포인트={points}")
        return result
    except Exception as e:
        st.write(f"{df.name} 엘리엇 예외 발생: {e}")
        return False

def is_buy_signal_ma(df):
    if len(df) < 51:
        st.write(f"{df.name} 이동평균선: 데이터 길이 부족")
        return False
    short_ma = df['Close'].rolling(window=20).mean()
    long_ma = df['Close'].rolling(window=50).mean()
    try:
        if bool(short_ma.isna().iat[-2]) or bool(short_ma.isna().iat[-1]):
            st.write(f"{df.name} 이동평균선: 단기 이동평균선 NaN 존재")
            return False
        if bool(long_ma.isna().iat[-2]) or bool(long_ma.isna().iat[-1]):
            st.write(f"{df.name} 이동평균선: 장기 이동평균선 NaN 존재")
            return False
        golden_cross = (short_ma.iat[-2] < long_ma.iat[-2]) and (short_ma.iat[-1] > long_ma.iat[-1])
        st.write(f"{df.name} 이동평균선 골든크로스 여부: {golden_cross}")
        return golden_cross
    except Exception as e:
        st.write(f"{df.name} 이동평균선 예외 발생: {e}")
        return False

def is_buy_signal_rsi(df):
    rsi = compute_rsi(df['Close'])
    if len(rsi) == 0:
        st.write(f"{df.name} RSI: 계산된 RSI 데이터 없음")
        return False
    try:
        if rsi.isna().iat[-1]:
            st.write(f"{df.name} RSI: 마지막 RSI 값이 NaN")
            return False
        st.write(f"{df.name} RSI 마지막 값: {rsi.iat[-1]:.2f}")
        rsi_cond = rsi.iat[-1] <= 60
        st.write(f"{df.name} RSI 조건 만족 여부: {rsi_cond}")
        return rsi_cond
    except Exception as e:
        st.write(f"{df.name} RSI 예외 발생: {e}")
        return False

def is_buy_signal_elliot_rsi_bb(df):
    if len(df) < 21:
        st.write(f"{df.name} 엘리엇+RSI+BB: 데이터 길이 부족")
        return False
    elliot_cond = is_buy_signal_elliot(df)
    rsi = compute_rsi(df['Close'])
    if rsi.empty or rsi.isna().iat[-1]:
        st.write(f"{df.name} 엘리엇+RSI+BB: RSI 데이터 부족 또는 NaN")
        return False
    rsi_cond = rsi.iat[-1] <= 60

    upper, lower = compute_bollinger_bands(df['Close'])
    if lower.isna().iat[-1]:
        st.write(f"{df.name} 엘리엇+RSI+BB: 볼린저밴드 하단 NaN")
        return False
    bb_cond = df['Close'].iat[-1] <= lower.iat[-1]
    st.write(f"{df.name} 엘리엇+RSI+BB 조건: elliot={elliot_cond}, rsi={rsi_cond}, bb={bb_cond}")
    
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
    else:
        st.write(f"{df.name} {method} 조건 미충족")
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
        df.name = ticker  # 디버깅용 이름 할당
        if df.empty or len(df) < 60:
            st.write(f"{ticker} 데이터 부족 또는 비어 있음")
            continue
        
        # 데이터 상태 확인용 출력 (필요시 주석 처리 가능)
        st.write(f"{ticker} Close 데이터 샘플:")
        st.write(df['Close'].tail(10))
        st.write(f"Close 컬럼 NaN 개수: {df['Close'].isna().sum()}")

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
        else:
            st.write(f"{ticker} 신호 점수 0 - 매수 신호 아님")
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
            if method == "Elliot+RSI+BB" or method == "Elliot Wave":
                try:
                    _, points = is_elliot_wave_pattern(df['Close'])
                    if points is not None:
                        for idx, pt in enumerate(points):
                            if pt < len(df):
                                fig.add_annotation(
                                    x=df.index[pt],
                                    y=df['Close'].iat[pt],
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
