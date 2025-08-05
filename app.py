import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="📈 매수 타점 분석기", layout="wide")

# 스타일 설정 (기존 유지)
st.markdown("""
<style>
.card {
    background-color: #f9f9f9;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
    text-align: center;
    transition: transform 0.2s;
    height: 100%;
    margin-bottom: 20px;
}
.card:hover {
    transform: scale(1.02);
    background-color: #e8f5e9;
}
.card-title {
    font-size: 20px;
    font-weight: bold;
    color: #2e7d32;
    margin-bottom: 10px;
}
.card-desc {
    font-size: 14px;
    color: #555;
    margin-bottom: 15px;
}
input {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# --- 보조지표 함수들 ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger(series, window=20, num_std=2):
    ma = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std
    width = upper - lower
    return upper, lower, width

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

def calculate_adx(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']

    plus_dm = high.diff()
    minus_dm = low.diff()

    plus_dm_adj = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0)
    minus_dm_adj = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0)

    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    plus_di = 100 * (pd.Series(plus_dm_adj, index=df.index).rolling(period).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm_adj, index=df.index).rolling(period).mean() / atr)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()

    adx = adx.fillna(method='bfill').fillna(method='ffill')

    return adx

def calculate_macd(df, fast=12, slow=26, signal=9):
    exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calculate_ema(series, period=50):
    return series.ewm(span=period, adjust=False).mean()

# --- 데이 트레이딩 점수 함수 ---
def score_turtle_enhanced(df):
    if df is None or df.empty or len(df) < 60:
        return 0, "데이터가 충분하지 않습니다.", None, None, None

    df = df.copy()
    df['20d_high'] = df['High'].rolling(20).max().shift(1)
    df['10d_low']  = df['Low'].rolling(10).min().shift(1)
    df['ATR']      = calculate_atr(df, 14)
    df['RSI']      = calculate_rsi(df['Close'], 14)
    df['BB_upper'], df['BB_lower'], df['BB_width'] = calculate_bollinger(df['Close'], 20, 2)
    df['BB_width_mean'] = df['BB_width'].rolling(20).mean()
    df['Vol_mean'] = df['Volume'].rolling(20).mean()

    df.dropna(inplace=True)
    if len(df) < 1:
        return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)", None, None, None

    close = float(df['Close'].iloc[-1])
    high20 = float(df['20d_high'].iloc[-1])
    low10 = float(df['10d_low'].iloc[-1])
    atr_val = float(df['ATR'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    bbw = float(df['BB_width'].iloc[-1])
    bbw_mean = float(df['BB_width_mean'].iloc[-1])
    vol = float(df['Volume'].iloc[-1])
    vol_mean = float(df['Vol_mean'].iloc[-1])

    for val in [high20, low10, atr_val, rsi, bbw, bbw_mean, vol_mean]:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)", None, None, None

    score = 0
    msgs = []

    if close > high20:
        score += 30
        msgs.append("20일 최고가 돌파")
    if rsi < 50:
        score += 10
        msgs.append(f"RSI({rsi:.1f}) 과매도/중립")
    prev_upper = df['BB_upper'].iloc[-2] if len(df) > 1 else None
    if bbw < bbw_mean * 0.8 and close > prev_upper:
        score += 15
        msgs.append("BB 수축 후 상단 돌파")
    if vol > vol_mean * 1.2:
        score += 15
        msgs.append("거래량 증가")
    atr_mean = df['ATR'].rolling(30).mean().iloc[-1]
    if atr_val > atr_mean:
        score += 20
        msgs.append("ATR 증가")
    if close < low10:
        score -= 20
        msgs.append("10일 최저가 이탈 위험")

    score = max(0, min(100, score))
    if not msgs:
        msgs = ["신호 없음"]

    entry_price = close
    target_price = close + (atr_val * 2)
    stop_loss = close - (atr_val * 1.5)

    return score, "; ".join(msgs), entry_price, target_price, stop_loss

# --- 스윙 트레이딩 점수 함수 ---
def score_swing_trading(df):
    if df is None or df.empty or len(df) < 50:
        return 0, "데이터가 충분하지 않습니다.", None, None, None

    df = df.copy()
    df['RSI'] = calculate_rsi(df['Close'], 14)
    df['ADX'] = calculate_adx(df, 14)
    df['BB_upper'], df['BB_lower'], df['BB_width'] = calculate_bollinger(df['Close'], 20, 2)
    df['Vol_mean'] = df['Volume'].rolling(20).mean()

    df.dropna(inplace=True)
    if len(df) < 1:
        return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)", None, None, None

    close = float(df['Close'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    adx = float(df['ADX'].iloc[-1])
    bbw = float(df['BB_width'].iloc[-1])
    vol = float(df['Volume'].iloc[-1])
    vol_mean = float(df['Vol_mean'].iloc[-1])

    for val in [rsi, adx, bbw, vol_mean]:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)", None, None, None

    score = 0
    msgs = []

    if rsi < 30:
        score += 10
        msgs.append(f"RSI({rsi:.1f}) 과매도")
    elif rsi > 70:
        score -= 10
        msgs.append(f"RSI({rsi:.1f}) 과매수")

    if adx > 25:
        score += 30
        msgs.append(f"ADX({adx:.1f}) 강한 추세")
    else:
        score += 10
        msgs.append(f"ADX({adx:.1f}) 약한 추세")

    if bbw < df['BB_width'].rolling(20).mean().iloc[-1]:
        score += 20
        msgs.append("볼린저 밴드 수축")

    if vol > vol_mean * 1.3:
        score += 20
        msgs.append("거래량 급증")

    score = max(0, min(100, score))
    if not msgs:
        msgs = ["신호 없음"]

    entry_price = close
    if adx > 30:
        target_price = close * 1.07
        stop_loss = close * 0.95
    else:
        target_price = close * 1.10
        stop_loss = close * 0.90

    return score, "; ".join(msgs), entry_price, target_price, stop_loss

# --- 포지션 트레이딩 점수 함수 (Stan Weinstein 전략) ---
def score_position_trading(df):
    if df is None or df.empty or len(df) < 100:
        return 0, "데이터가 충분하지 않습니다.", None, None, None

    df = df.copy()
    df['EMA_30'] = calculate_ema(df['Close'], 30)
    df['EMA_50'] = calculate_ema(df['Close'], 50)
    df['MACD'], df['Signal'], _ = calculate_macd(df)
    df['BB_upper'], df['BB_lower'], df['BB_width'] = calculate_bollinger(df['Close'], 20, 2)

    df.dropna(inplace=True)
    if len(df) < 1:
        return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)", None, None, None

    close = float(df['Close'].iloc[-1])
    ema30 = float(df['EMA_30'].iloc[-1])
    ema50 = float(df['EMA_50'].iloc[-1])
    macd = float(df['MACD'].iloc[-1])
    signal = float(df['Signal'].iloc[-1])
    bbw = float(df['BB_width'].iloc[-1])
    bbw_mean = df['BB_width'].rolling(20).mean().iloc[-1]

    score = 0
    msgs = []

    # 스탠 웨인스타인 기본 조건: EMA30 > EMA50 상승추세
    if ema30 > ema50:
        score += 40
        msgs.append("EMA30 > EMA50 상승 추세")
    else:
        msgs.append("EMA30 <= EMA50 하락 또는 횡보")

    # MACD 골든크로스 여부
    if macd > signal:
        score += 30
        msgs.append("MACD 골든크로스")
    else:
        msgs.append("MACD 데드크로스")

    # 볼린저 밴드 폭 축소 (수축기)
    if bbw < bbw_mean * 0.8:
        score += 20
        msgs.append("볼린저 밴드 수축")
    else:
        msgs.append("볼린저 밴드 확장 또는 변동성 증가")

    score = max(0, min(100, score))
    if not msgs:
        msgs = ["신호 없음"]

    entry_price = close
    target_price = close * 1.15
    stop_loss = close * 0.90

    return score, "; ".join(msgs), entry_price, target_price, stop_loss

# --- UI 렌더링 ---
st.markdown("<h1 style='text-align:center; color:#4CAF50;'>📈 매수 타점 분석기</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>당신의 투자 전략에 맞는 종목을 분석해보세요.</p>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>1️⃣ 데이 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>터틀+RSI+BB+거래량+ATR 결합</div>", unsafe_allow_html=True)
        ticker = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_dt")
        if st.button("🔍 분석", key="btn_dt"):
            if not ticker.strip():
                st.warning("티커를 입력하세요.")
            else:
                df = yf.download(ticker, period="3mo", interval="1d")
                if df.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    score, msg, entry, target, stop = score_turtle_enhanced(df)
                    st.success(f"점수: {score} / 100")
                    st.info(msg)
                    if entry and target and stop:
                        st.markdown(f"""
                        <div style='margin-top:15px; padding:10px; border:1px solid #ccc; border-radius:10px;'>
                        <strong>💡 자동 계산 진입/청산가:</strong><br>
                        - 진입가: {entry:.2f}<br>
                        - 목표가: {target:.2f}<br>
                        - 손절가: {stop:.2f}
                        </div>
                        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>2️⃣ 스윙 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>Tony Cruz 전략 + RSI, ADX, BB, 거래량 결합</div>", unsafe_allow_html=True)
        ticker_swing = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_swing")
        if st.button("🔍 분석", key="btn_swing"):
            if not ticker_swing.strip():
                st.warning("티커를 입력하세요.")
            else:
                df_swing = yf.download(ticker_swing, period="6mo", interval="1d")
                if df_swing.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    score, msg, entry, target, stop = score_swing_trading(df_swing)
                    st.success(f"점수: {score} / 100")
                    st.info(msg)
                    if entry and target and stop:
                        st.markdown(f"""
                        <div style='margin-top:15px; padding:10px; border:1px solid #ccc; border-radius:10px;'>
                        <strong>💡 자동 계산 진입/청산가:</strong><br>
                        - 진입가: {entry:.2f}<br>
                        - 목표가: {target:.2f}<br>
                        - 손절가: {stop:.2f}
                        </div>
                        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with col3:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>3️⃣ 포지션 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>Stan Weinstein 전략 + MACD, EMA, 볼린저 밴드</div>", unsafe_allow_html=True)
        ticker_position = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_position")
        if st.button("🔍 분석", key="btn_position"):
            if not ticker_position.strip():
                st.warning("티커를 입력하세요.")
            else:
                df_pos = yf.download(ticker_position, period="1y", interval="1d")
                if df_pos.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    score, msg, entry, target, stop = score_position_trading(df_pos)
                    st.success(f"점수: {score} / 100")
                    st.info(msg)
                    if entry and target and stop:
                        st.markdown(f"""
                        <div style='margin-top:15px; padding:10px; border:1px solid #ccc; border-radius:10px;'>
                        <strong>💡 자동 계산 진입/청산가:</strong><br>
                        - 진입가: {entry:.2f}<br>
                        - 목표가: {target:.2f}<br>
                        - 손절가: {stop:.2f}
                        </div>
                        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# 4,5번 미완성 상태 유지
col4, col5,_ = st.columns([1,1,1])
with col4:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>4️⃣ 스캘핑</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-desc'>분석 준비 중...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col5:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>5️⃣ 뉴스 이벤트 트레이딩</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-desc'>분석 준비 중...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:13px; color:gray;'>Made by Son Jiwan | Powered by Streamlit</p>", unsafe_allow_html=True)
