import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import requests
from bs4 import BeautifulSoup
import ta

# 점수 계산 함수
def calculate_score(df):
    try:
        rsi = ta.momentum.RSIIndicator(df['Close']).rsi().iloc[-1]
        cci = ta.trend.CCIIndicator(df['High'], df['Low'], df['Close']).cci().iloc[-1]
        adx = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close']).adx().iloc[-1]
        bb = ta.volatility.BollingerBands(df['Close'])
        bb_percent = ((df['Close'].iloc[-1] - bb.bollinger_lband().iloc[-1]) /
                      (bb.bollinger_hband().iloc[-1] - bb.bollinger_lband().iloc[-1])) * 100

        score = 0
        if rsi < 30: score += 25
        if cci < -100: score += 20
        if adx > 20: score += 15
        if bb_percent < 20: score += 40

        return round(score, 1)
    except:
        return 0

# 뉴스 요약 (예시: 네이버 금융)
def get_korean_news(ticker):
    url = f"https://finance.naver.com/item/news_news.naver?code={ticker}&page=1"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = soup.select(".newsList ul li")

        news_summary = []
        for news in news_list[:5]:
            title = news.select_one("a").text.strip()
            date = news.select_one(".date").text.strip()
            news_summary.append(f"📌 {title} ({date})")
        return news_summary
    except:
        return ["❌ 뉴스 로딩 실패"]

# Streamlit UI
st.set_page_config(page_title="TradePicks", layout="wide")

st.title("📊 TradePicks - AI 주식 점수와 뉴스 요약")
st.caption("미국 & 한국 주식에 대한 AI 기술 분석 및 뉴스 요약 제공")

ticker = st.text_input("🔍 종목 티커 입력 (예: AAPL, TSLA, 005930)", value="AAPL").upper()

if ticker:
    try:
        df = yf.download(ticker, period="3mo", interval="1d")
        if df.empty:
            st.warning("❌ 데이터를 불러올 수 없습니다.")
        else:
            score = calculate_score(df)

            # 점수 시각화
            st.subheader(f"📈 기술적 분석 점수: `{score}/100`")
            st.progress(min(score / 100, 1.0))

            # 시세 차트
            st.line_chart(df['Close'])

            # 한국 뉴스
            if ticker.isdigit():
                st.subheader("📰 관련 뉴스 (Korea)")
                news = get_korean_news(ticker)
                for item in news:
                    st.write(item)
            else:
                st.subheader("📰 관련 뉴스 (미국)")
                st.caption("🔎 구글 뉴스 / Seeking Alpha 연동 예정 (현재는 미제공)")

    except Exception as e:
        st.error(f"에러 발생: {e}")
