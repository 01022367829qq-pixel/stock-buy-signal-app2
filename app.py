import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

# 기술적 지표 계산 함수들
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_adx(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']

    plus_dm = np.where((high.diff() > low.diff()) & (high.diff() > 0), high.diff(), 0)
    minus_dm = np.where((low.diff() > high.diff()) & (low.diff() > 0), -low.diff(), 0)
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.DataFrame({'TR1': tr1, 'TR2': tr2, 'TR3': tr3}).max(axis=1)
    atr = tr.rolling(period).mean()

    plus_di = 100 * pd.Series(plus_dm).rolling(period).mean() / atr
    minus_di = 100 * pd.Series(minus_dm).rolling(period).mean() / atr
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()
    return adx

def calculate_macd(df):
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_bollinger_band_width(df, period=20):
    sma = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    return (upper - lower) / sma * 100

def calculate_volume_spike(df):
    avg_volume = df['Volume'].rolling(window=20).mean()
    return df['Volume'] > avg_volume * 1.5

# 전략 점수 계산 함수들
def score_day_trading(df):
    score = 0
    rsi = calculate_rsi(df, 14)
    latest_rsi = rsi.iloc[-1]
    msg = f"RSI({latest_rsi:.1f}) "
    if latest_rsi < 30:
        score += 10
        msg += "과매도"
    elif latest_rsi > 70:
        msg += "과매수"
    else:
        score += 5
        msg += "중립"

    entry = df['Close'].iloc[-1]
    target = entry * 1.16
    stop = entry * 0.88
    return score, msg, entry, target, stop

def score_swing_trading(df):
    score = 0
    try:
        rsi = calculate_rsi(df, 14)
        adx = calculate_adx(df, 14)
        bb_width = calculate_bollinger_band_width(df)
        df['RSI'] = rsi
        df['ADX'] = adx
        df['BB_Width'] = bb_width
        latest = df.iloc[-1]

        msg = ""
        if latest['ADX'] > 25:
            score += 15
            msg += f"ADX({latest['ADX']:.1f}) 강한 추세; "
        else:
            msg += f"ADX({latest['ADX']:.1f}) 약한 추세; "

        if latest['BB_Width'] < 15:
            score += 15
            msg += "볼린저 밴드 수축"
        else:
            msg += "볼린저 밴드 확장"

    except Exception as e:
        msg = "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)"

    entry = df['Close'].iloc[-1]
    target = entry * 1.07
    stop = entry * 0.95
    return score, msg, entry, target, stop

def score_position_trading(df):
    score = 0
    df['SMA_30'] = df['Close'].rolling(window=30).mean()
    df['SMA_30_slope'] = df['SMA_30'].diff()
    adx = calculate_adx(df, 14)
    rsi = calculate_rsi(df, 14)
    macd, signal = calculate_macd(df)
    volume_spike = calculate_volume_spike(df)

    df['ADX'] = adx
    df['RSI'] = rsi
    df['MACD'] = macd
    df['Signal'] = signal
    df['Volume_Spike'] = volume_spike

    latest = df.iloc[-1]
    msg = ""

    if latest['Close'] > latest['SMA_30'] and latest['SMA_30_slope'] > 0:
        score += 20
        msg += "30주선 위 + 상승중; "

    if latest['ADX'] > 25:
        score += 20
        msg += f"ADX({latest['ADX']:.1f}) 강한 추세; "

    if latest['MACD'] > latest['Signal']:
        score += 10
        msg += "MACD 상향 돌파; "

    if latest['Volume_Spike']:
        score += 10
        msg += "거래량 급증; "

    if latest['RSI'] > 50:
        score += 10
        msg += f"RSI({latest['RSI']:.1f}) 강세"

    entry = latest['Close']
    target = entry * 1.15
    stop = entry * 0.90

    return score, msg, entry, target, stop

# Streamlit UI
st.title("📊 주식 매수 신호 분석기")

symbol = st.text_input("종목 심볼 입력 (예: AAPL, KULR 등)", value="KULR")
option = st.selectbox("분석 전략 선택", ["데이 트레이딩", "스윙 트레이딩", "포지션 트레이딩"])

if st.button("분석 시작"):
    period = "1y" if option == "포지션 트레이딩" else "6mo"
    interval = "1wk" if option == "포지션 트레이딩" else "1d"

    try:
        df = yf.download(symbol, period=period, interval=interval)
        st.write(f"데이터 미리보기 ({symbol})")
        st.dataframe(df.tail())

        if option == "데이 트레이딩":
            score, msg, entry, target, stop = score_day_trading(df)
        elif option == "스윙 트레이딩":
            score, msg, entry, target, stop = score_swing_trading(df)
        elif option == "포지션 트레이딩":
            score, msg, entry, target, stop = score_position_trading(df)

        st.subheader(f"✅ 점수: {score} / 100")
        st.write(msg)

        st.markdown("""
        ### 💡 자동 계산 진입/청산가:
        - **진입가**: ${:.2f}  
        - **목표가**: ${:.2f}  
        - **손절가**: ${:.2f}  
        """.format(entry, target, stop))

    except Exception as e:
        st.error(f"데이터를 불러오거나 분석 중 오류 발생: {e}")
