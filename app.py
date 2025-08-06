import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.markdown("""
<style>
/* 최상위 html, body, Streamlit 내부 여러 컨테이너 모두 배경, 글자색 강제 적용 */
html, body, [class^="css"], .main, section, div[data-testid="stAppViewContainer"] {
    background-color: #121212 !important;
    color: #e0e0e0 !important;
}

/* 앱 제목 */
.app-title {
    font-size: 40px;
    font-weight: bold;
    color: #90caf9;
    text-align: left;
    padding: 5px 0 5px 0;
    margin-left: 0;
    margin-top: -70px;
}

/* 카드 스타일 */
.card {
    background-color: #1e1e1e !important;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.7);
    text-align: center;
    transition: transform 0.2s;
    height: 100%;
    margin-bottom: 20px;
}
.card:hover {
    transform: scale(1.02);
    background-color: #333333 !important;
}

/* 카드 제목 */
.card-title {
    font-size: 20px;
    font-weight: bold;
    color: #81d4fa;
    margin-bottom: 10px;
}

/* 카드 설명 텍스트 */
.card-desc {
    font-size: 14px;
    color: #bbbbbb;
    margin-bottom: 15px;
}

/* 입력창 텍스트 중앙정렬 */
input {
    text-align: center;
    background-color: #2c2c2c !important;
    color: #e0e0e0 !important;
    border: 1px solid #444444 !important;
    border-radius: 5px;
}

/* 버튼 텍스트 색상 */
.stButton>button {
    background-color: #1976d2 !important;
    color: white !important;
    border-radius: 5px;
}

/* 기타 텍스트 색상 */
p, span, div, h1, h2, h3, h4, h5, h6 {
    color: #e0e0e0 !important;
}
</style>
""", unsafe_allow_html=True)


# 지표 계산 함수들
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
    minus_dm = low.diff()

    plus_dm_values = plus_dm.values
    minus_dm_values = minus_dm.values

    plus_dm_adj = np.where((plus_dm_values > minus_dm_values) & (plus_dm_values > 0), plus_dm_values, 0).flatten()
    minus_dm_adj = np.where((minus_dm_values > plus_dm_values) & (minus_dm_values > 0), minus_dm_values, 0).flatten()

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


# 데이 트레이딩 점수 함수
def score_turtle_enhanced(df):
    required_cols = ['High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            return 0, f"데이터에 필수 컬럼 '{col}'이(가) 없습니다.", None, None, None
    if df[required_cols].isnull().any().any():
        return 0, "데이터에 결측치가 포함되어 있습니다.", None, None, None

    if df.empty or len(df) < 60:
        return 0, "데이터가 충분하지 않습니다.", None, None, None

    df = df.copy()
    df['20d_high'] = df['High'].rolling(20).max().shift(1)
    df['10d_low'] = df['Low'].rolling(10).min().shift(1)
    df['ATR'] = calculate_atr(df, 14)
    df['RSI'] = calculate_rsi(df['Close'], 14)
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


# 스윙 트레이딩 점수 함수
def score_swing_trading(df):
    required_cols = ['High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            return 0, f"데이터에 필수 컬럼 '{col}'이(가) 없습니다.", None, None, None
    if df[required_cols].isnull().any().any():
        return 0, "데이터에 결측치가 포함되어 있습니다.", None, None, None

    if df.empty or len(df) < 50:
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


# 포지션 트레이딩 점수 함수
def score_position_trading(df):
    required_cols = ['High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            return 0, f"데이터에 필수 컬럼 '{col}'이(가) 없습니다.", None, None, None
    if df[required_cols].isnull().any().any():
        return 0, "데이터에 결측치가 포함되어 있습니다.", None, None, None

    if df.empty or len(df) < 50:
        return 0, "데이터가 충분하지 않습니다.", None, None, None

    df = df.copy()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['RSI'] = calculate_rsi(df['Close'], 14)
    df['ATR'] = calculate_atr(df, 14)

    df.dropna(inplace=True)
    if len(df) < 1:
        return 0, "기술 지표 계산 중 오류 발생 (데이터 부족 가능성)", None, None, None

    close = float(df['Close'].iloc[-1])
    ema50 = float(df['EMA50'].iloc[-1])
    ema200 = float(df['EMA200'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    atr = float(df['ATR'].iloc[-1])

    score = 0
    msgs = []

    if ema50 > ema200:
        score += 40
        msgs.append("EMA50 > EMA200: 상승 추세")
    else:
        msgs.append("EMA50 <= EMA200: 하락 추세")

    if rsi < 40:
        score += 10
        msgs.append(f"RSI({rsi:.1f}) 과매도 영역")
    elif rsi > 70:
        score -= 10
        msgs.append(f"RSI({rsi:.1f}) 과매수 영역")

    if atr > df['ATR'].rolling(50).mean().iloc[-1]:
        score += 20
        msgs.append("ATR 증가: 변동성 확대")

    score = max(0, min(100, score))
    if not msgs:
        msgs = ["신호 없음"]

    entry_price = close
    target_price = close * 1.15
    stop_loss = close - (atr * 2)

    return score, "; ".join(msgs), entry_price, target_price, stop_loss


# UI 렌더링
st.markdown("<h1 style='text-align:center; color:#4CAF50;'>📈 매수 타점 분석기</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>당신의 투자 전략에 맞는 종목을 진입가, 손절가, 목표가까지 모두 빠르게 분석해보세요.</p>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("""
<div class='card-title'>
  1️⃣ 데이 트레이딩
  <span style="cursor: help;" title="Richard Dennis의 추세추종 전략 기반으로 RSI, 볼린저 밴드, 거래량, ATR을 활용한 단기 매매 전략입니다.">ⓘ</span>
</div>
""", unsafe_allow_html=True)


desc_text_dt = "Richard Dennis의 추세추종 전략 기반으로 RSI, 볼린저 밴드, 거래량, ATR을 활용한 단기 매매 전략입니다."
show_desc_dt = st.checkbox("설명 보기", key="chk_desc_dt")
if show_desc_dt:
    st.markdown(
        f"<div style='margin-top:5px; margin-bottom:5px; font-size:small;'>{desc_text_dt}</div>",
        unsafe_allow_html=True
    )

col_input, col_button = st.columns([3, 1])
with col_input:
    ticker = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_dt")
with col_button:
    if st.button("🔍 분석", key="btn_dt"):
        if not ticker.strip():
            st.warning("티커를 입력하세요.")
        else:
            df = yf.download(ticker, period="3mo", interval="1d")
            required_cols = ['High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if df.empty:
                st.error("데이터를 불러올 수 없습니다.")
            elif missing_cols:
                st.error(f"필수 컬럼이 없습니다: {missing_cols}")
            elif df[required_cols].isnull().any().any():
                st.error("데이터에 결측치가 있습니다.")
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
        st.markdown("""
<div class='card-title'>
  2️⃣ 스윙 트레이딩
  <span style="cursor: help;" title="Tony Cruz 전략과 RSI, ADX, 볼린저 밴드, 거래량을 결합한 중기 매매 전략입니다.">ⓘ</span>
</div>
""", unsafe_allow_html=True)

        st.markdown("<div class='card-desc'>Tony Cruz의 전략 + RSI, BB, ADX, 거래량 지표 결합</div>", unsafe_allow_html=True)
        ticker_swing = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_swing")
        if st.button("🔍 분석", key="btn_swing"):
            if not ticker_swing.strip():
                st.warning("티커를 입력하세요.")
            else:
                df_swing = yf.download(ticker_swing, period="6mo", interval="1d")
                required_cols = ['High', 'Low', 'Close', 'Volume']
                missing_cols = [col for col in required_cols if col not in df_swing.columns]

                if df_swing.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                elif missing_cols:
                    st.error(f"필수 컬럼이 없습니다: {missing_cols}")
                elif df_swing[required_cols].isnull().any().any():
                    st.error("데이터에 결측치가 있습니다.")
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
        st.markdown("""
<div class='card-title'>
  3️⃣ 포지션 트레이딩
  <span style="cursor: help;" title="EMA50/EMA200, RSI, ATR을 이용한 장기 투자용 전략입니다.">ⓘ</span>
</div>
""", unsafe_allow_html=True)

        st.markdown("<div class='card-desc'>EMA50/EMA200 골든크로스 + RSI, ATR 활용</div>", unsafe_allow_html=True)
        ticker_pos = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_pos")
        if st.button("🔍 분석", key="btn_pos"):
            if not ticker_pos.strip():
                st.warning("티커를 입력하세요.")
            else:
                df_pos = yf.download(ticker_pos, period="12mo", interval="1d")
                required_cols = ['High', 'Low', 'Close', 'Volume']
                missing_cols = [col for col in required_cols if col not in df_pos.columns]

                if df_pos.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                elif missing_cols:
                    st.error(f"필수 컬럼이 없습니다: {missing_cols}")
                elif df_pos[required_cols].isnull().any().any():
                    st.error("데이터에 결측치가 있습니다.")
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
# 상단 컬럼 선언부
# 첫 줄: 3개 컬럼
col1, col2, col3 = st.columns(3)

# 두 번째 줄: 2개 컬럼
col4, col5 = st.columns(2)


# 이후에 4번째 카드
with col4:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("""<div class='card-title'>
4️⃣ 스캘핑
<span style="cursor: pointer;" title="빠른 매매를 위한 초단기 전략입니다.">ⓘ</span>
</div>""", unsafe_allow_html=True)

        scalping_desc = "스캘핑은 빠른 매매를 목표로 하는 초단기 전략입니다. 현재 기능 개발 중입니다."

        show_scalping_desc = st.checkbox("설명 보기", key="chk_scalping_desc")
        if show_scalping_desc:
            st.markdown(f"<div class='card-desc'>{scalping_desc}</div>", unsafe_allow_html=True)

        ticker_scalp = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_scalp")
        if st.button("🔍 분석", key="btn_scalp"):
            if not ticker_scalp.strip():
                st.warning("티커를 입력하세요.")
            else:
                st.info("스캘핑 분석 기능은 현재 준비 중입니다.")

        st.markdown("</div>", unsafe_allow_html=True)


# 5번째 카드
with col5:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("""<div class='card-title'>
5️⃣ 이벤트 트레이딩
<span style="cursor: pointer;" title="주요 이벤트 기반 매매 전략입니다.">ⓘ</span>
</div>""", unsafe_allow_html=True)

        event_trading_desc = "이벤트 트레이딩은 주요 뉴스, 경제 이벤트 등을 기반으로 한 매매 전략입니다. 기능 개발 중입니다."

        show_event_desc = st.checkbox("설명 보기", key="chk_event_desc")
        if show_event_desc:
            st.markdown(f"<div class='card-desc'>{event_trading_desc}</div>", unsafe_allow_html=True)

        ticker_event = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker_event")
        if st.button("🔍 분석", key="btn_event"):
            if not ticker_event.strip():
                st.warning("티커를 입력하세요.")
            else:
                st.info("이벤트 트레이딩 분석 기능은 현재 준비 중입니다.")

        st.markdown("</div>", unsafe_allow_html=True)
