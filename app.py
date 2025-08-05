import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="📈 매수 타점 분석기", layout="wide")

# 스타일 설정
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

# --- 기술지표 계산 함수들 ---

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

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
    return tr.rolling(period).mean()

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_macd(df, fast=12, slow=26, signal=9):
    ema_fast = calculate_ema(df['Close'], fast)
    ema_slow = calculate_ema(df['Close'], slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def calculate_adx(df, period=14):
    df = df.copy()
    df['TR'] = np.maximum.reduce([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ])
    df['+DM'] = np.where((df['High'] - df['High'].shift()) > (df['Low'].shift() - df['Low']), 
                         np.maximum(df['High'] - df['High'].shift(), 0), 0)
    df['-DM'] = np.where((df['Low'].shift() - df['Low']) > (df['High'] - df['High'].shift()),
                         np.maximum(df['Low'].shift() - df['Low'], 0), 0)
    
    TR14 = df['TR'].rolling(window=period).sum()
    plus_DM14 = df['+DM'].rolling(window=period).sum()
    minus_DM14 = df['-DM'].rolling(window=period).sum()
    
    plus_DI14 = 100 * (plus_DM14 / TR14)
    minus_DI14 = 100 * (minus_DM14 / TR14)
    
    DX = 100 * (abs(plus_DI14 - minus_DI14) / (plus_DI14 + minus_DI14))
    ADX = DX.rolling(window=period).mean()
    return ADX

# --- 데이 트레이딩 점수 함수 (기존) ---
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

# --- 스윙 트레이딩 점수 함수 (Tony Cruz + RSI, ADX, BB 결합) ---
def score_swing_trading(df):
    if df is None or df.empty or len(df) < 50:
        return 0, "데이터가 충분하지 않습니다.", None, None, None
    
    df = df.copy()
    df['EMA8'] = calculate_ema(df['Close'], 8)
    df['EMA21'] = calculate_ema(df['Close'], 21)
    df['MACD'], df['MACD_signal'], _ = calculate_macd(df)
    df['RSI'] = calculate_rsi(df['Close'], 14)
    df['ADX'] = calculate_adx(df, 14)
    df['BB_upper'], df['BB_lower'], df['BB_width'] = calculate_bollinger(df['Close'], 20, 2)
    df['Vol_mean'] = df['Volume'].rolling(20).mean()

    df.dropna(inplace=True)
    if len(df) < 1:
        return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)", None, None, None

    close = float(df['Close'].iloc[-1])
    ema8 = float(df['EMA8'].iloc[-1])
    ema21 = float(df['EMA21'].iloc[-1])
    macd = float(df['MACD'].iloc[-1])
    macd_signal = float(df['MACD_signal'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    adx = float(df['ADX'].iloc[-1])
    bb_upper = float(df['BB_upper'].iloc[-1])
    bb_lower = float(df['BB_lower'].iloc[-1])
    bbw = float(df['BB_width'].iloc[-1])
    vol = float(df['Volume'].iloc[-1])
    vol_mean = float(df['Vol_mean'].iloc[-1])

    for val in [ema8, ema21, macd, macd_signal, rsi, adx, bb_upper, bb_lower, bbw, vol_mean]:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)", None, None, None

    score = 0
    msgs = []

    # EMA8 > EMA21 : 상승추세 확인
    if ema8 > ema21:
        score += 30
        msgs.append("EMA8 > EMA21 (상승 추세)")

    # MACD 선이 시그널선 위에 있으면 상승 모멘텀
    if macd > macd_signal:
        score += 25
        msgs.append("MACD > 시그널선 (모멘텀 상승)")

    # RSI 30~70 사이면 안정적
    if 30 <= rsi <= 70:
        score += 10
        msgs.append(f"RSI({rsi:.1f}) 안정적 범위")

    # ADX 20 이상이면 추세 강함
    if adx >= 20:
        score += 20
        msgs.append(f"ADX({adx:.1f}) 강한 추세")

    # 거래량 20일 평균 대비 20% 이상 증가
    if vol > vol_mean * 1.2:
        score += 15
        msgs.append("거래량 증가")

    # 볼린저 밴드 하단 근처에서 반등 시 (종가가 하단 밴드보다 약간 위)
    if bb_lower * 0.98 <= close <= bb_lower * 1.02:
        score += 10
        msgs.append("볼린저 밴드 하단 근처")

    score = max(0, min(100, score))
    if not msgs:
        msgs = ["신호 없음"]

    # 진입가: 현재 종가
    entry_price = close
    # 손절가와 목표가는 ADX 강도에 따라 다르게 설정 (추세가 강할수록 손절은 좁게, 목표는 넓게)
    if adx >= 30:
        stop_loss = close * 0.97  # -3%
        target_price = close * 1.10  # +10%
    elif adx >= 20:
        stop_loss = close * 0.95  # -5%
        target_price = close * 1.07  # +7%
    else:
        stop_loss = close * 0.93  # -7%
        target_price = close * 1.05  # +5%

    return score, "; ".join(msgs), entry_price, target_price, stop_loss


# --- UI 렌더링 ---
st.markdown("<h1 style='text-align:center; color:#4CAF50;'>📈 매수 타점 분석기</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>당신의 투자 전략에 맞는 종목을 분석해보세요.</p>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3 = st.columns(3)

# 데이 트레이딩
with col1:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>1️⃣ 데이 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>터틀+RSI+BB+거래량+ATR 결합</div>", unsafe_allow_html=True)
        ticker_dt = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_dt")
        if st.button("🔍 분석", key="btn_dt"):
            if not ticker_dt.strip():
                st.warning("티커를 입력하세요.")
            else:
                df_dt = yf.download(ticker_dt, period="3mo", interval="1d")
                if df_dt.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    score, msg, entry, target, stop = score_turtle_enhanced(df_dt)
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

# 스윙 트레이딩
with col2:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>2️⃣ 스윙 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>Tony Cruz 전략 + RSI, ADX, BB 결합</div>", unsafe_allow_html=True)
        ticker_sw = st.text_input("", placeholder="티커 입력 (예: MSFT)", key="ticker_sw")
        if st.button("🔍 분석", key="btn_sw"):
            if not ticker_sw.strip():
                st.warning("티커를 입력하세요.")
            else:
                df_sw = yf.download(ticker_sw, period="6mo", interval="1d")
                if df_sw.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                else:
                    score, msg, entry, target, stop = score_swing_trading(df_sw)
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

# 포지션 트레이딩 (준비 중)
with col3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>3️⃣ 포지션 트레이딩</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-desc'>분석 준비 중...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

col4, col5, _ = st.columns([1,1,1])

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
