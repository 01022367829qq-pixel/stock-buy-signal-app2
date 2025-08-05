import streamlit as st

st.set_page_config(page_title="📈 매수 타점 분석기", layout="wide")

st.markdown("""
    <style>
    .card {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        text-align: center;
        transition: transform 0.2s;
        height: 100%;
    }
    .card:hover {
        transform: scale(1.02);
        background-color: #e8f5e9;
    }
    .card-title {
        font-size: 20px;
        font-weight: bold;
        color: #2e7d32;
    }
    .card-desc {
        font-size: 14px;
        color: #555;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #4CAF50;'>📈 매수 타점 분석기</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>당신의 투자 스타일에 맞는 전략을 선택하세요.</p>", unsafe_allow_html=True)

st.markdown("---")

# 카드 UI
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("1️⃣ 데이 트레이딩"):
        st.session_state.selected_strategy = "데이 트레이딩"
    st.markdown("""
    <div class="card">
        <div class="card-title">1️⃣ 데이 트레이딩</div>
        <div class="card-desc">당일 매수/매도, 고변동성 단타 매매. 수 분~수 시간 보유.</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if st.button("2️⃣ 스윙 트레이딩"):
        st.session_state.selected_strategy = "스윙 트레이딩"
    st.markdown("""
    <div class="card">
        <div class="card-title">2️⃣ 스윙 트레이딩</div>
        <div class="card-desc">며칠~몇 주 보유, 추세 추종 및 기술적 분석 기반.</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    if st.button("3️⃣ 포지션 트레이딩"):
        st.session_state.selected_strategy = "포지션 트레이딩"
    st.markdown("""
    <div class="card">
        <div class="card-title">3️⃣ 포지션 트레이딩</div>
        <div class="card-desc">수 주~수년 보유, 업종 분석 및 장기 추세 중심.</div>
    </div>
    """, unsafe_allow_html=True)

col4, col5, _ = st.columns([1, 1, 1])
with col4:
    if st.button("4️⃣ 스캘핑"):
        st.session_state.selected_strategy = "스캘핑"
    st.markdown("""
    <div class="card">
        <div class="card-title">4️⃣ 스캘핑</div>
        <div class="card-desc">초단타 전략. 수초~수분 보유. 빠른 매매 대응 필요.</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    if st.button("5️⃣ 뉴스 이벤트 트레이딩"):
        st.session_state.selected_strategy = "뉴스 이벤트 트레이딩"
    st.markdown("""
    <div class="card">
        <div class="card-title">5️⃣ 뉴스 이벤트 트레이딩</div>
        <div class="card-desc">실적, 인수, 뉴스 기반으로 단기 변동성 포착.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 선택된 전략 표시
if "selected_strategy" in st.session_state:
    st.success(f"✅ 선택된 전략: {st.session_state.selected_strategy}")
    ticker = st.text_input("🔍 분석할 티커를 입력하세요 (예: AAPL)")
    st.button("🚀 분석 시작")
else:
    st.info("전략을 선택하면 티커 입력창이 나타납니다.")

# 푸터
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; font-size: 13px; color: gray;'>Made by Son Jiwan | Powered by Streamlit</p>",
    unsafe_allow_html=True
)
