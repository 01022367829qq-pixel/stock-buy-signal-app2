# app.py
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

# --------------------- 기술 지표 계산 함수 ---------------------
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return pd.Series(rsi, index=data.index)

def calculate_macd(data):
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_bollinger_bands(data, window=20):
    sma = data['Close'].rolling(window=window).mean()
    std = data['Close'].rolling(window=window).std()
    upper_band = sma + (2 * std)
    lower_band = sma - (2 * std)
    return upper_band, lower_band

def calculate_atr(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

def calculate_adx(data, period=14):
    df = data.copy()
    df['TR'] = np.maximum(df['High'] - df['Low'],
                          np.maximum(abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())))
    df['+DM'] = np.where((df['High'] - df['High'].shift()) > (df['Low'].shift() - df['Low']),
                         np.maximum(df['High'] - df['High'].shift(), 0), 0)
    df['-DM'] = np.where((df['Low'].shift() - df['Low']) > (df['High'] - df['High'].shift()),
                         np.maximum(df['Low'].shift() - df['Low'], 0), 0)

    tr_smooth = df['TR'].rolling(window=period).mean()
    plus_dm_smooth = df['+DM'].rolling(window=period).mean()
    minus_dm_smooth = df['-DM'].rolling(window=period).mean()

    plus_di = 100 * (plus_dm_smooth / tr_smooth)
    minus_di = 100 * (minus_dm_smooth / tr_smooth)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=period).mean()
    return adx

# --------------------- 전략 점수 계산 함수 ---------------------
def score_swing_trading(df):
    try:
        df['RSI'] = calculate_rsi(df)
        df['MACD'], df['Signal'] = calculate_macd(df)
        df['Upper'], df['Lower'] = calculate_bollinger_bands(df)
        df['ADX'] = calculate_adx(df)
        
        latest = df.iloc[-1]
        score = 0
        reasons = []

        if latest['RSI'] < 30:
            score += 20
            reasons.append('RSI 과매도')
        if latest['MACD'] > latest['Signal']:
            score += 20
            reasons.append('MACD 골든크로스')
        if latest['Close'] < latest['Lower']:
            score += 20
            reasons.append('볼린저 밴드 하단 이탈')
        if latest['ADX'] > 25:
            score += 20
            reasons.append(f'ADX({latest["ADX"]:.1f}) 강한 추세')

        entry = latest['Close']
        atr = calculate_atr(df).iloc[-1]
        target = entry + atr * 1.5
        stop = entry - atr

        return score, ", ".join(reasons), entry, target, stop

    except Exception as e:
        return 0, f"분석 실패: {e}", None, None, None

def score_position_trading(df):
    try:
        df['SMA_150'] = df['Close'].rolling(window=150).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['Volume_MA_50'] = df['Volume'].rolling(window=50).mean()

        latest = df.iloc[-1]
        score = 0
        reasons = []

        if latest['Close'] > latest['SMA_150'] > latest['SMA_200']:
            score += 30
            reasons.append('장기 상승 추세 유지')
        if df['SMA_150'].iloc[-1] > df['SMA_150'].iloc[-20]:
            score += 20
            reasons.append('150일선 상승 중')
        if latest['Volume'] > latest['Volume_MA_50']:
            score += 10
            reasons.append('거래량 증가')

        entry = latest['Close']
        atr = calculate_atr(df).iloc[-1]
        target = entry + atr * 2
        stop = entry - atr * 1.2

        return score, ", ".join(reasons), entry, target, stop

    except Exception as e:
        return 0, f"분석 실패: {e}", None, None, None

# --------------------- Streamlit UI ---------------------
st.set_page_config(page_title="📈 매매 신호 분석기")
st.title("📊 주식 자동 매매 전략 점수 분석기")

symbol = st.text_input("티커를 입력하세요 (예: AAPL, TSLA, KRX:005930):", value="AAPL")
option = st.selectbox("전략 선택", ["스윙 트레이딩", "포지션 트레이딩"])

if st.button("분석 시작"):
    df = yf.download(symbol, period="1y")
    if df.empty:
        st.error("데이터를 불러오지 못했습니다. 올바른 티커인지 확인해주세요.")
    else:
        if option == "스윙 트레이딩":
            score, reasons, entry, target, stop = score_swing_trading(df)
        elif option == "포지션 트레이딩":
            score, reasons, entry, target, stop = score_position_trading(df)

        st.subheader(f"✅ 점수: {score} / 100")
        st.write(f"📌 분석 근거: {reasons}")

        if entry and target and stop:
            st.markdown("""
            💡 **자동 계산 진입/청산가:**
            - 진입가: {:.2f}  
            - 목표가: {:.2f}  
            - 손절가: {:.2f}  
            """.format(entry, target, stop))

