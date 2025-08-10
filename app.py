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

# --- Elliott Wave 관련 함수들 ---

def detect_wave_points(close, distance=5, prominence=None):
    """ 고점과 저점 자동 탐지 """
    if prominence is None:
        prominence = (close.max() - close.min()) * 0.05
    peaks, _ = find_peaks(close, distance=distance, prominence=prominence)
    valleys, _ = find_peaks(-close, distance=distance, prominence=prominence)
    return peaks, valleys

def fibonacci_ratio_check(lengths):
    """ 기본 Fibonacci 비율 확인 (0.38 ~ 0.62, 1.0, 1.618 등) """
    ratios = []
    for i in range(1, len(lengths)):
        if lengths[i-1] == 0:
            return False
        ratios.append(lengths[i] / lengths[i-1])
    # 간단히 0.38 ~ 1.62 사이인지 체크
    for r in ratios:
        if not (0.3 <= r <= 1.7):
            return False
    return True

def find_elliott_wave_pattern(close):
    """ 5파 + 3파 패턴 후보 탐색 (기본적 시도) """
    peaks, valleys = detect_wave_points(close)
    points = np.sort(np.concatenate((peaks, valleys)))
    # 최소 8개 포인트 필요 (5파 + 3파)
    if len(points) < 8:
        return None
    
    # 단순히 첫 8개 포인트를 5파로 가정하고 길이 체크
    wave_points = close.index[points[:8]]
    wave_values = close.iloc[points[:8]].values
    
    lengths = np.abs(np.diff(wave_values))
    if fibonacci_ratio_check(lengths):
        return points[:8]
    return None

def is_buy_signal_elliot(close):
    """ 단순 상승 추세 판단 """
    # Elliott Wave 5파 패턴이 발견되면 True
    pattern_points = find_elliott_wave_pattern(close)
    if pattern_points is not None:
        # 마지막 파동 상승 여부 체크
        if close.iat[pattern_points[-2]] < close.iat[pattern_points[-1]]:
            return True
    return False

def plot_elliott_wave(fig, close, wave_points):
    """ 차트에 파동 라벨 및 선 표시 """
    if wave_points is None:
        return fig
    x_vals = close.index[wave_points]
    y_vals = close.iloc[wave_points]

    # 번호 라벨 붙이기
    for i, (x, y) in enumerate(zip(x_vals, y_vals)):
        fig.add_annotation(x=x, y=y, text=str(i+1), showarrow=True, arrowhead=1, font=dict(color="blue"))

    # 파동 선 연결 (5파)
    for i in range(len(wave_points)-1):
        fig.add_shape(type="line",
                      x0=x_vals[i], y0=y_vals[i],
                      x1=x_vals[i+1], y1=y_vals[i+1],
                      line=dict(color="blue", width=2))
    return fig

# 기존 기법 함수

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

def is_buy_signal_elliot_rsi_bb(df):
    if len(df) < 21:
        return False
    close = df['Close']
    elliot_cond = is_buy_signal_elliot(close)
    
    rsi = compute_rsi(close)
    if rsi.empty or rsi.isna().iat[-1]:
        return False
    rsi_cond = rsi.iat[-1] <= 40

    upper, lower = compute_bollinger_bands(close)
    if lower.isna().iat[-1]:
        return False
    bb_cond = close.iat[-1] <= lower.iat[-1]

    return elliot_cond and rsi_cond and bb_cond

def score_for_signal(method, df):
    score = 0
    msg = ""
    if method == "Elliot Wave" and is_buy_signal_elliot(df['Close']):
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

# --- 티커 그룹 리스트 및 UI 부분은 기존과 동일하게 사용 ---

# ... (중략: 티커 리스트 함수 및 Streamlit UI 부분 기존 코드 유지)

# UI 분석 후 캔들 차트에 파동 표시하기 (Elliot 포함)

def main():
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
                # Elliott Wave 파동 시각화 (Elliot 포함 기법 선택 시)
                if method in ["Elliot Wave", "Elliot+RSI+BB"]:
                    close = df['Close']
                    wave_points = find_elliott_wave_pattern(close)
                    fig = plot_elliott_wave(fig, close, wave_points)

                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
