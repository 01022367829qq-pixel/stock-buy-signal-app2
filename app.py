import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.set_page_config(page_title="AI 주식 매수 타점 추천 앱", layout="wide")

st.title("AI 기반 금융상품 매수 타점 추천")

category = st.radio("카테고리를 선택하세요", ['지수', '주식', '원자재', '통화', 'ETF', '채권', '펀드', '암호 화폐'])

# ----- 암호화폐 시세 간단 표시 -----
if category == '암호 화폐':
    st.subheader("암호화폐 시세")
    cryptos = {
        '비트코인': 'BTC-USD',
        '이더리움': 'ETH-USD',
        '리플': 'XRP-USD'
    }
    data = []
    for name, ticker in cryptos.items():
        ticker_data = yf.Ticker(ticker).history(period='1d')
        if not ticker_data.empty:
            price = ticker_data['Close'][-1]
            change = (ticker_data['Close'][-1] - ticker_data['Open'][-1]) / ticker_data['Open'][-1] * 100
            data.append({'종목': name, '현재가': round(price, 2), '변동률(%)': round(change, 2)})
    df_crypto = pd.DataFrame(data)
    st.table(df_crypto)

# ----- 주식 매수 타점 분석 기능 -----
elif category == '주식':
    st.subheader("주식 매수 타점 분석")

    # 티커 입력 받기
    user_ticker = st.text_input("분석할 종목 티커를 입력하세요 (예: AAPL, MSFT)")

    # 지표 가중치 설정 (예시)
    st.sidebar.header("기술 지표 가중치 조절")
    weight_rsi_30 = st.sidebar.slider("RSI <= 30", 0, 5, 1)
    weight_rsi_20 = st.sidebar.slider("RSI <= 20", 0, 5, 2)
    weight_cci_100 = st.sidebar.slider("CCI <= -100", 0, 5, 1)
    weight_cci_150 = st.sidebar.slider("CCI <= -150", 0, 5, 2)
    weight_adx_25 = st.sidebar.slider("ADX <= 25", 0, 5, 1)
    weight_adx_20 = st.sidebar.slider("ADX <= 20", 0, 5, 2)
    weight_bb_low_101 = st.sidebar.slider("Close <= BB Lower *1.01", 0, 5, 1)
    weight_bb_low_1005 = st.sidebar.slider("Close <= BB Lower *1.005", 0, 5, 1)

    def ensure_series_1d(series):
        if hasattr(series, 'values') and series.values.ndim > 1:
            return pd.Series(series.values.flatten(), index=series.index)
        return series

    def check_buy_signal(
        df,
        weight_rsi_30=1,
        weight_rsi_20=1,
        weight_cci_100=1,
        weight_cci_150=1,
        weight_adx_25=1,
        weight_adx_20=1,
        weight_bb_low_101=1,
        weight_bb_low_1005=1
    ):
        if df.empty or len(df) < 20:
            return None

        close = ensure_series_1d(df['Close'])
        high = ensure_series_1d(df['High'])
        low = ensure_series_1d(df['Low'])
        volume = ensure_series_1d(df['Volume'])

        try:
            bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
            rsi = ta.momentum.RSIIndicator(close=close, window=14).rsi()
            adx = ta.trend.ADXIndicator(high=high, low=low, close=close, window=14).adx()
            cci = ta.trend.CCIIndicator(high=high, low=low, close=close, window=20).cci()
            atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
        except Exception as e:
            st.error(f"지표 계산 오류: {e}")
            return None

        latest_close = close.iloc[-1]
        latest_rsi = rsi.iloc[-1]
        latest_bb_low = bb.bollinger_lband().iloc[-1]
        latest_adx = adx.iloc[-1]
        latest_cci = cci.iloc[-1]
        latest_atr = atr.iloc[-1]

        recent_vol = volume.iloc[-1]
        avg_vol_5d = volume.iloc[-6:-1].mean() if len(volume) >= 6 else volume.mean()
        vol_status = "거래량 증가 O" if recent_vol > avg_vol_5d else "거래량 증가 X"

        score = 0
        if latest_rsi <= 30:
            score += weight_rsi_30
        if latest_rsi <= 20:
            score += weight_rsi_20
        if latest_cci <= -100:
            score += weight_cci_100
        if latest_cci <= -150:
            score += weight_cci_150
        if latest_adx <= 25:
            score += weight_adx_25
        if latest_adx <= 20:
            score += weight_adx_20
        if latest_close <= latest_bb_low * 1.01:
            score += weight_bb_low_101
        if latest_close <= latest_bb_low * 1.005:
            score += weight_bb_low_1005

        # 점수 0~100 스케일링
        max_score = (weight_rsi_30 + weight_rsi_20 + weight_cci_100 + weight_cci_150 +
                     weight_adx_25 + weight_adx_20 + weight_bb_low_101 + weight_bb_low_1005)
        percent_score = int((score / max_score) * 100) if max_score > 0 else 0

        # 추천 문구 자동 생성
        if percent_score >= 70:
            recommendation = "강력 매수 추천"
        elif percent_score >= 40:
            recommendation = "관망 권장"
        else:
            recommendation = "매수 신중 권장"

        entry_price = latest_close
        stop_loss = entry_price - (1.5 * latest_atr)
        target_price = entry_price + (3 * latest_atr)

        return {
            'EntryPrice': round(entry_price, 2),
            'StopLoss': round(stop_loss, 2),
            'TargetPrice': round(target_price, 2),
            'RSI': round(latest_rsi, 2),
            'BollingerLow': round(latest_bb_low, 2),
            'ADX': round(latest_adx, 2),
            'CCI': round(latest_cci, 2),
            'ATR': round(latest_atr, 4),
            'Score': percent_score,
            'Recommendation': recommendation,
            'VolumeStatus': vol_status
        }

    if user_ticker:
        st.write(f"{user_ticker.upper()} 분석 중...")
        try:
            df = yf.download(user_ticker, period='60d', interval='1d', progress=False, auto_adjust=True)
            if df.empty:
                st.warning("데이터가 없습니다. 티커를 다시 확인해주세요.")
            else:
                signal = check_buy_signal(
                    df,
                    weight_rsi_30=weight_rsi_30,
                    weight_rsi_20=weight_rsi_20,
                    weight_cci_100=weight_cci_100,
                    weight_cci_150=weight_cci_150,
                    weight_adx_25=weight_adx_25,
                    weight_adx_20=weight_adx_20,
                    weight_bb_low_101=weight_bb_low_101,
                    weight_bb_low_1005=weight_bb_low_1005
                )
                if signal:
                    st.metric("매수 점수 (0~100)", signal['Score'])
                    st.write(f"추천: **{signal['Recommendation']}**")
                    st.write(f"손절가: {signal['StopLoss']}")
                    st.write(f"목표가: {signal['TargetPrice']}")
                    st.write(f"거래량 상태: {signal['VolumeStatus']}")
                    st.write("기술적 지표:")
                    st.write(f"RSI: {signal['RSI']}, ADX: {signal['ADX']}, CCI: {signal['CCI']}, ATR: {signal['ATR']}")
                else:
                    st.info("매수 신호가 부족하여 점수를 산출할 수 없습니다.")
        except Exception as e:
            st.error(f"데이터 불러오기 오류: {e}")

# ----- 기타 카테고리 안내 -----
else:
    st.info(f"{category} 카테고리는 현재 준비 중입니다.")



