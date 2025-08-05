import streamlit as st

st.set_page_config(page_title="📈 매수 타점 분석기", layout="centered")

# 제목
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>📈 매수 타점 분석기</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>당신의 투자 스타일에 맞는 전략을 선택해보세요.</p>", unsafe_allow_html=True)

st.markdown("---")

# 전략 선택
st.markdown("### 📌 투자 전략을 선택하세요:")
strategy = st.radio(
    label="",
    options=[
        "1️⃣ 데이 트레이딩 (단기 고변동성 매매)",
        "2️⃣ 스윙 트레이딩 (며칠 ~ 몇 주 보유)",
        "3️⃣ 포지션 트레이딩 (중장기 추세 매매)",
        "4️⃣ 스캘핑 (초단타 고속 매매)",
        "5️⃣ 뉴스 이벤트 트레이딩 (이슈 기반)"
    ],
    index=0,
    key="strategy_choice"
)

st.markdown("---")

# 티커 입력
st.markdown("### 🔍 분석할 종목의 티커를 입력하세요:")
ticker = st.text_input("예: AAPL, TSLA, NVDA", key="ticker_input")

# 분석 버튼
st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.button("🚀 분석 시작", use_container_width=True)

# 하단 푸터
st.markdown("---")
st.markdown(
    "<p style='text-align: center; font-size: 13px; color: gray;'>Made by Son Jiwan | Powered by Streamlit</p>",
    unsafe_allow_html=True
)
