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

# 보조지표 계산 함수들
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

def calculate_adx(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']

    plus_dm = high.diff()
    minus_dm = low.diff() * -1

    plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm), 0.0)
    minus_dm = minus_dm.where((minus_dm > 0) & (minus_dm > plus_dm), 0.0)

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()

    return pd.Series(adx, index=df.index)

# 데이 트레이딩 점수 함수
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

# 스윙 트레이딩 점수 함수 (Tony Cruz 전략 + RSI, ADX, BB, 거래량)
def score_swing_trading(df):
    if df is None or df.empty or len(df) < 60:
        return 0, "데이터가 충분하지 않습니다.", None, None, None

    df = df.copy()
    df['ADX'] = calculate_adx(df, 14)
    df['RSI'] = calculate_rsi(df['Close'], 14)
    df['BB_upper'], df['BB_lower'], df['BB_width'] = calculate_bollinger(df['Close'], 20, 2)
    df['Vol_mean'] = df['Volume'].rolling(20).mean()

    df.dropna(inplace=True)
    if len(df) < 1:
        return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)", None, None, None

    close = float(df['Close'].iloc[-1])
    adx = float(df['ADX'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    bbw = float(df['BB_width'].iloc[-1])
    vol = float(df['Volume'].iloc[-1])
    vol_mean = float(df['Vol_mean'].iloc[-1])

    for val in [adx, rsi, bbw, vol_mean]:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)", None, None, None

    score = 0
    msgs = []

    if 30 <= rsi <= 60:
        score += 30
        msgs.append(f"RSI({rsi:.1f}) 안정적 범위")
    if adx >= 20:
        score += 30
        msgs.append(f"ADX({adx:.1f}) 강한 추세")
    if close > df['BB_lower'].iloc[-1] and close < df['BB_upper'].iloc[-1]:
        score += 20
        msgs.append("가격 볼린저 밴드 내 위치")
    if vol > vol_mean:
        score += 20
        msgs.append("거래량 평균 이상")

    score = max(0, min(100, score))
    if not msgs:
        msgs = ["신호 없음"]

    entry_price = close
    atr_val = calculate_atr(df, 14).iloc[-1] if not df.empty else 0
    if adx >= 25:
        target_price = close + atr_val * 1.5
        stop_loss = close - atr_val * 1.0
    else:
        target_price = close + atr_val * 1.0
        stop_loss = close - atr_val * 0.5

    return score, "; ".join(msgs), entry_price, target_price, stop_loss

# UI 렌더링
st.markdown("<h1 style='text-align:center; color:#4CAF50;'>📈 매수 타점 분석기</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>당신의 투자 전략에 맞는 종목을 분석해보세요.</p>", unsafe_allow_html=True)

ticker_input = st.text_input("종목 티커를 입력하세요 (예: AAPL, KULR)", value="AAPL").upper()
timeframe = st.selectbox("트레이딩 유형 선택", ["데이 트레이딩", "스윙 트레이딩"])

if ticker_input:
    df = yf.download(ticker_input, period="3mo", interval="1d")
    if df.empty:
        st.error("해당 종목 데이터가 없습니다. 티커를 다시 확인해주세요.")
    else:
        if timeframe == "데이 트레이딩":
            score, msg, entry, target, stop = score_turtle_enhanced(df)
        else:
            score, msg, entry, target, stop = score_swing_trading(df)

        st.markdown(f"### 분석 결과: {ticker_input} ({timeframe})")
        st.markdown(f"**점수: {score} / 100**")
        st.markdown(f"**상태 메시지:** {msg}")
        if entry and target and stop:
            st.markdown(f"💡 자동 계산 진입/청산가:")
            st.markdown(f"- 진입가: {entry:.2f}")
            st.markdown(f"- 목표가: {target:.2f}")
            st.markdown(f"- 손절가: {stop:.2f}")
