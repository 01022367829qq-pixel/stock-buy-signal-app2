import streamlit as st

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

# 제목
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>📈 매수 타점 분석기</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>당신의 투자 전략에 맞는 종목을 분석해보세요.</p>", unsafe_allow_html=True)
st.markdown("---")

# **중복 입력창 완전 삭제** — 화면 상단에 ticker = st.text_input("티커 입력") 같은 건 아예 없음

# 카드 묶음 1
col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>1️⃣ 데이 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>당일 매수/매도, 고변동성 단타 매매. 수 분~수 시간 보유.</div>", unsafe_allow_html=True)
        ticker1 = st.text_input("", placeholder="티커 입력 (예: AAPL)", key="ticker1")
        if st.button("🔍 분석", key="btn1"):
            if ticker1.strip() != "":
                st.success(f"{ticker1.upper()} (데이 트레이딩) 분석 준비 중...")
            else:
                st.warning("티커를 입력하세요.")
        st.markdown("</div>", unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>2️⃣ 스윙 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>며칠~몇 주 보유, 추세 추종 및 기술적 분석 기반.</div>", unsafe_allow_html=True)
        ticker2 = st.text_input("", placeholder="티커 입력 (예: TSLA)", key="ticker2")
        if st.button("🔍 분석", key="btn2"):
            if ticker2.strip() != "":
                st.success(f"{ticker2.upper()} (스윙 트레이딩) 분석 준비 중...")
            else:
                st.warning("티커를 입력하세요.")
        st.markdown("</div>", unsafe_allow_html=True)

with col3:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>3️⃣ 포지션 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>수 주~수년 보유, 업종 분석 및 장기 추세 중심.</div>", unsafe_allow_html=True)
        ticker3 = st.text_input("", placeholder="티커 입력 (예: MSFT)", key="ticker3")
        if st.button("🔍 분석", key="btn3"):
            if ticker3.strip() != "":
                st.success(f"{ticker3.upper()} (포지션 트레이딩) 분석 준비 중...")
            else:
                st.warning("티커를 입력하세요.")
        st.markdown("</div>", unsafe_allow_html=True)

# 카드 묶음 2
col4, col5, _ = st.columns([1, 1, 1])

with col4:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>4️⃣ 스캘핑</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>초단타 전략. 수초~수분 보유. 빠른 매매 대응 필요.</div>", unsafe_allow_html=True)
        ticker4 = st.text_input("", placeholder="티커 입력 (예: NVDA)", key="ticker4")
        if st.button("🔍 분석", key="btn4"):
            if ticker4.strip() != "":
                st.success(f"{ticker4.upper()} (스캘핑) 분석 준비 중...")
            else:
                st.warning("티커를 입력하세요.")
        st.markdown("</div>", unsafe_allow_html=True)

with col5:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>5️⃣ 뉴스 이벤트 트레이딩</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-desc'>실적, 인수, 뉴스 기반으로 단기 변동성 포착.</div>", unsafe_allow_html=True)
        ticker5 = st.text_input("", placeholder="티커 입력 (예: AMZN)", key="ticker5")
        if st.button("🔍 분석", key="btn5"):
            if ticker5.strip() != "":
                st.success(f"{ticker5.upper()} (뉴스 이벤트 트레이딩) 분석 준비 중...")
            else:
                st.warning("티커를 입력하세요.")
        st.markdown("</div>", unsafe_allow_html=True)

# 푸터
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; font-size: 13px; color: gray;'>Made by Son Jiwan | Powered by Streamlit</p>",
    unsafe_allow_html=True
)
