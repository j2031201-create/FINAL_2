"""
슬기로운 영끌생활 · 지도 기반 부동산 학습 보드게임
캡스톤 세컨드 프로젝트 · 일반 대중용 에듀테크 게임
"""
import streamlit as st
import random
import time

st.set_page_config(page_title="슬기로운 영끌생활", page_icon="🏠",
                   layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────────────
# 더미 데이터
# ─────────────────────────────────────────────────────
REGIONS = {
    "kingul": {"name":"킹울","level":"초급","desc":"인구 유입 지속 · 변동성 낮음","vol":0.08,"trend":0.04,"icon":"🏙️"},
    "daejeon":{"name":"대전","level":"중급","desc":"인근 신도시 개발 · 구도심 인구 감소 위험","vol":0.16,"trend":0.0,"icon":"🌆"},
    "jeju":   {"name":"제쥬","level":"고급","desc":"수요 한정 · 유동성 낮음","vol":0.26,"trend":-0.02,"icon":"🏝️"},
}

BRANDS = ["내미안","쉴스테이트","파이(Pi)","누르지오","덜샵","모래캐슬"]

NEWS = [
    {"head":"🚨 토지거래허가구역 지정!","effect":"💡 갭투자 불가! 매수 시 현금 100% 필요, 2턴간 매도 금지","mood":"bad"},
    {"head":"📈 기준금리 0.5%p 인하","effect":"💡 대출이자 부담 완화! 이번 턴 매수가 5% 할인","mood":"good"},
    {"head":"🚇 GTX 신규 노선 발표","effect":"💡 역세권 수혜! 보유 매물 가치 10% 상승","mood":"good"},
    {"head":"📉 미분양 물량 급증 경고","effect":"💡 시장 위축! 이번 턴 매물 적정가가 8% 하락","mood":"bad"},
    {"head":"🏗️ 재건축 안전진단 규제 완화","effect":"💡 노후단지 호재! 적정가 12% 상승 가능성","mood":"good"},
    {"head":"💸 DSR 3단계 규제 시행","effect":"💡 대출 한도 축소! 멘탈(HP) -10, 신중한 판단 필요","mood":"bad"},
    {"head":"🏦 전세사기 특별법 통과","effect":"💡 시장 신뢰 회복! 거래량 증가, 매도 시 보너스","mood":"good"},
]

APPRAISAL = {
    "수익환원법":{"desc":"임대수익 ÷ 환원율로 가치 산출 (수익형 부동산)","icon":"💰"},
    "거래사례비교법":{"desc":"인근 유사 거래사례와 비교해 가치 산출 (아파트)","icon":"📊"},
    "원가법":{"desc":"토지값 + 건축비 - 감가상각으로 가치 산출 (단독·특수)","icon":"🏗️"},
}

# ─────────────────────────────────────────────────────
# 세션 상태 초기화
# ─────────────────────────────────────────────────────
def init_state():
    for k,v in {"phase":"intro","region":None,"capital":100000,"hp":100,
                "turn":1,"owned":0,"listing":None,"news":None,
                "appraised":None,"method":None,"log":[]}.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()  # capital 단위: 만원 (10억 = 100,000만원)

def new_turn():
    """새 턴: 뉴스 + 매물 생성"""
    region = REGIONS[st.session_state.region]
    st.session_state.news = random.choice(NEWS)
    base = random.randint(60000, 130000)  # 만원
    rent = int(base * random.uniform(0.04, 0.06))  # 연 임대료
    st.session_state.listing = {
        "name": random.choice(BRANDS),
        "type": random.choice(["아파트","오피스텔","상가","단독주택"]),
        "base": base, "rent": rent,
        "block": random.randint(0,15),
    }
    st.session_state.appraised = None
    st.session_state.method = None

def do_appraisal(method):
    L = st.session_state.listing
    cap_rate = round(random.uniform(0.045, 0.06), 3)
    if method == "수익환원법":
        value = int(L["rent"] / cap_rate)
        steps = [f"1. 연 임대료 산출: {L['rent']:,}만원",
                 f"2. 지역 환원율 {cap_rate*100:.1f}% 적용",
                 f"🎯 적정가치 = {L['rent']:,} ÷ {cap_rate*100:.1f}% = {value:,}만원"]
    elif method == "거래사례비교법":
        adj = random.uniform(0.92, 1.12)
        value = int(L["base"] * adj)
        steps = [f"1. 인근 유사 거래사례 기준가: {L['base']:,}만원",
                 f"2. 입지·층·향 보정계수 {adj:.2f} 적용",
                 f"🎯 적정가치 = {L['base']:,} × {adj:.2f} = {value:,}만원"]
    else:  # 원가법
        land = int(L["base"]*0.6); build = int(L["base"]*0.5); deprec = int(build*random.uniform(0.1,0.3))
        value = land + build - deprec
        steps = [f"1. 토지가격: {land:,}만원",
                 f"2. 건축비 {build:,}만원 − 감가상각 {deprec:,}만원",
                 f"🎯 적정가치 = {land:,} + {build:,} − {deprec:,} = {value:,}만원"]
    # 뉴스 효과 반영
    if st.session_state.news["mood"]=="good": value = int(value*1.08)
    else: value = int(value*0.94)
    return value, steps, cap_rate

def advance_turn():
    """턴 종료 → 다음 턴 또는 게임 종료"""
    news = st.session_state.news
    # 뉴스 패널티: DSR 규제면 HP 감소
    if "DSR" in news["head"]:
        st.session_state.hp = max(st.session_state.hp-10, 0)
    if st.session_state.turn >= 10:
        st.session_state.phase = "end"
    else:
        st.session_state.turn += 1
        new_turn()
    st.rerun()

# ─────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
html,body,.stApp{font-family:'Noto Sans KR',sans-serif !important;}
.stApp{background:linear-gradient(160deg,#1a1530 0%,#251a45 100%) !important;}
#MainMenu,footer{display:none !important;}
.game-title{font-size:30px;font-weight:900;color:#fff;text-align:center;letter-spacing:-0.02em;
    text-shadow:0 2px 20px rgba(124,77,255,.5);margin-bottom:4px;}
.game-sub{text-align:center;color:#b8a9e0;font-size:13px;margin-bottom:18px;}
.panel{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
    border-radius:16px;padding:18px 20px;margin-bottom:14px;backdrop-filter:blur(8px);}
.panel-title{font-size:14px;font-weight:700;color:#c9b8ff;margin-bottom:10px;display:flex;align-items:center;gap:6px;}
.news-card{border-radius:14px;padding:16px 18px;margin-bottom:14px;}
.news-good{background:linear-gradient(135deg,rgba(46,204,113,.18),rgba(46,204,113,.06));border:1px solid rgba(46,204,113,.4);}
.news-bad{background:linear-gradient(135deg,rgba(231,76,60,.18),rgba(231,76,60,.06));border:1px solid rgba(231,76,60,.4);}
.news-head{font-size:16px;font-weight:700;color:#fff;margin-bottom:6px;}
.news-effect{font-size:13px;color:#e0d6ff;line-height:1.6;}
.dice-box{text-align:center;padding:30px;font-size:20px;font-weight:700;color:#fff;
    background:rgba(124,77,255,.15);border-radius:16px;border:1px dashed rgba(124,77,255,.5);}
.value-result{background:linear-gradient(135deg,rgba(124,77,255,.25),rgba(124,77,255,.08));
    border:1px solid rgba(124,77,255,.5);border-radius:14px;padding:18px;margin:12px 0;}
.value-step{font-size:13px;color:#e0d6ff;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.08);}
.value-step:last-child{border-bottom:none;font-size:15px;font-weight:700;color:#fff;padding-top:10px;}

/* 아이소메트릭 보드 */
.iso-stage{perspective:1000px;height:480px;display:flex;align-items:center;justify-content:center;margin-top:20px;}
.iso-board{transform:rotateX(60deg) rotateZ(-45deg);transform-style:preserve-3d;
    width:300px;height:300px;display:grid;grid-template-columns:repeat(4,1fr);grid-template-rows:repeat(4,1fr);
    gap:4px;}
.iso-cell{background:linear-gradient(135deg,rgba(124,77,255,.22),rgba(124,77,255,.08));
    border:1px solid rgba(167,139,250,.35);border-radius:4px;
    box-shadow:0 8px 0 rgba(80,50,160,.4);}
.iso-marker{background:linear-gradient(135deg,#ffd54f,#ff9800) !important;
    border:1px solid #fff !important;box-shadow:0 22px 0 rgba(180,100,0,.5) !important;
    transform:translateZ(40px);animation:float 2s ease-in-out infinite;}
@keyframes float{0%,100%{transform:translateZ(40px);}50%{transform:translateZ(60px);}}
.iso-legend{text-align:center;color:#b8a9e0;font-size:12px;margin-top:24px;}
.marker-name{text-align:center;margin-top:30px;}
.marker-name .mn{font-size:22px;font-weight:900;color:#ffd54f;text-shadow:0 2px 12px rgba(255,152,0,.5);}
.marker-name .mt{font-size:13px;color:#c9b8ff;margin-top:4px;}

.region-card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);
    border-radius:16px;padding:22px;text-align:center;height:100%;}
.region-card .ri{font-size:42px;margin-bottom:8px;}
.region-card .rn{font-size:20px;font-weight:900;color:#fff;}
.region-card .rl{display:inline-block;font-size:11px;font-weight:700;padding:2px 10px;border-radius:100px;margin:6px 0;}
.region-card .rd{font-size:12px;color:#c9b8ff;line-height:1.6;min-height:48px;}
.stButton>button{background:linear-gradient(135deg,#7c4dff,#6236d4) !important;color:#fff !important;
    border:none !important;border-radius:10px !important;font-weight:700 !important;padding:10px 18px !important;
    font-family:'Noto Sans KR',sans-serif !important;transition:.15s !important;}
.stButton>button:hover{filter:brightness(1.15);transform:translateY(-1px);}
[data-testid="stMetric"]{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
    border-radius:12px;padding:10px 14px;}
[data-testid="stMetricLabel"]{color:#b8a9e0 !important;}
[data-testid="stMetricValue"]{color:#fff !important;font-size:1.3rem !important;}
</style>
""", unsafe_allow_html=True)

def won(manwon):
    """만원 → 보기 좋은 억/만원 표기"""
    eok = manwon // 10000
    rest = manwon % 10000
    if eok>0 and rest>0: return f"{eok}억 {rest:,}만"
    if eok>0: return f"{eok}억"
    return f"{rest:,}만"

# ─────────────────────────────────────────────────────
# 화면 1: 인트로 (지역 선택)
# ─────────────────────────────────────────────────────
if st.session_state.phase == "intro":
    st.markdown('<div class="game-title">🏠 슬기로운 영끌생활</div>', unsafe_allow_html=True)
    st.markdown('<div class="game-sub">지도 위에서 배우는 부동산 투자 · 감정평가와 규제를 게임으로</div>', unsafe_allow_html=True)
    st.markdown('<div class="game-sub">지역을 선택하세요 · 초기자본 10억 · 멘탈 100 · 10턴(10년)</div>', unsafe_allow_html=True)

    cols = st.columns(3)
    for col,(key,r) in zip(cols, REGIONS.items()):
        with col:
            lvl_color = {"초급":"#2ecc71","중급":"#f39c12","고급":"#e74c3c"}[r["level"]]
            st.markdown(f"""
            <div class="region-card">
              <div class="ri">{r['icon']}</div>
              <div class="rn">{r['name']}</div>
              <div class="rl" style="background:{lvl_color}33;color:{lvl_color};">{r['level']}</div>
              <div class="rd">{r['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"{r['name']} 선택", key=f"sel_{key}", use_container_width=True):
                st.session_state.region = key
                st.session_state.phase = "play"
                new_turn()
                st.rerun()

# ─────────────────────────────────────────────────────
# 화면 2: 게임 플레이
# ─────────────────────────────────────────────────────
elif st.session_state.phase == "play":
    region = REGIONS[st.session_state.region]
    L = st.session_state.listing
    news = st.session_state.news

    st.markdown(f'<div class="game-title">🏠 슬기로운 영끌생활 — {region["icon"]} {region["name"]} ({region["level"]})</div>', unsafe_allow_html=True)

    left, right = st.columns([1,1])

    # ===== 좌측: 상태 + 뉴스 + 액션 =====
    with left:
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("자본금", won(st.session_state.capital))
        m2.metric("멘탈(HP)", f"{st.session_state.hp}")
        m3.metric("턴", f"{st.session_state.turn}/10")
        m4.metric("보유매물", f"{st.session_state.owned}")

        st.markdown(f"""
        <div class="news-card news-{news['mood']}">
          <div class="news-head">{news['head']}</div>
          <div class="news-effect">{news['effect']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="panel">
          <div class="panel-title">🏢 이번 턴 매물</div>
          <div style="color:#fff;font-size:18px;font-weight:700;">{L['name']} <span style="font-size:13px;color:#c9b8ff;">· {L['type']}</span></div>
          <div style="color:#c9b8ff;font-size:13px;margin-top:6px;">호가: {won(L['base'])} · 연 임대료: {L['rent']:,}만원</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.appraised is None:
            st.markdown('<div class="panel-title">🎲 감정평가 방식 선택</div>', unsafe_allow_html=True)
            for method,info in APPRAISAL.items():
                if st.button(f"{info['icon']} {method}", key=f"ap_{method}", use_container_width=True):
                    ph = st.empty()
                    for i in range(3):
                        ph.markdown(f'<div class="dice-box">🎲 감정평가 주사위 굴리는 중{"."*(i+1)}</div>', unsafe_allow_html=True)
                        time.sleep(0.5)
                    value, steps, cap = do_appraisal(method)
                    st.session_state.appraised = value
                    st.session_state.method = method
                    st.session_state.appraisal_steps = steps
                    ph.empty()
                    st.rerun()
                st.caption(info['desc'])
        else:
            value = st.session_state.appraised
            st.markdown(f'<div class="value-result"><div style="font-size:13px;color:#c9b8ff;margin-bottom:8px;">📐 {st.session_state.method} 평가 결과</div>'
                        + "".join(f'<div class="value-step">{s}</div>' for s in st.session_state.appraisal_steps)
                        + '</div>', unsafe_allow_html=True)
            gap = value - L['base']
            if gap>0:
                st.success(f"💎 적정가치가 호가보다 {won(abs(gap))} 높음 — 저평가 매물!")
            else:
                st.warning(f"⚠️ 적정가치가 호가보다 {won(abs(gap))} 낮음 — 고평가 주의!")

            b1,b2 = st.columns(2)
            with b1:
                can_buy = st.session_state.capital >= L['base']
                if st.button("✅ 매수", use_container_width=True, disabled=not can_buy):
                    st.session_state.capital -= L['base']
                    st.session_state.owned += 1
                    profit = gap
                    st.session_state.capital += max(profit,0)//2  # 일부 즉시 반영(간이)
                    st.session_state.log.append(f"{st.session_state.turn}턴: {L['name']} 매수 ({'저평가' if gap>0 else '고평가'})")
                    advance_turn()
            with b2:
                if st.button("⏭️ 패스", use_container_width=True):
                    st.session_state.log.append(f"{st.session_state.turn}턴: {L['name']} 패스")
                    advance_turn()
            if not can_buy:
                st.caption("⚠️ 자본금 부족으로 매수 불가")

    # ===== 우측: 아이소메트릭 보드 =====
    with right:
        cells = ""
        for i in range(16):
            cls = "iso-cell iso-marker" if i==L["block"] else "iso-cell"
            cells += f'<div class="{cls}"></div>'
        st.markdown(f"""
        <div class="iso-stage"><div class="iso-board">{cells}</div></div>
        <div class="marker-name">
          <div class="mn">📍 {L['name']}</div>
          <div class="mt">{region['name']} · {L['type']} · 이번 턴 매물 위치</div>
        </div>
        <div class="iso-legend">🟡 노란 블록이 이번 턴 매물입니다</div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# 화면 3: 결과
# ─────────────────────────────────────────────────────
elif st.session_state.phase == "end":
    region = REGIONS[st.session_state.region]
    final = st.session_state.capital
    start = 100000
    rate = (final-start)/start*100
    st.markdown('<div class="game-title">🏁 게임 종료!</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric("최종 자산", won(final))
    c2.metric("수익률", f"{rate:+.1f}%")
    c3.metric("보유 매물", f"{st.session_state.owned}건")

    if rate>=30: grade,msg = "🏆 부동산 마스터","감정평가와 규제를 완벽히 활용했어요!"
    elif rate>=0: grade,msg = "👍 안정형 투자자","원금을 지키며 신중하게 플레이했어요."
    else: grade,msg = "📚 수업료를 낸 새내기","괜찮아요, 규제와 평가를 배운 게 수익이에요!"

    st.markdown(f"""
    <div class="panel" style="text-align:center;">
      <div style="font-size:24px;font-weight:900;color:#ffd54f;">{grade}</div>
      <div style="color:#c9b8ff;margin-top:8px;">{msg}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="panel-title">📜 플레이 기록</div>', unsafe_allow_html=True)
    for log in st.session_state.log:
        st.markdown(f'<div style="color:#c9b8ff;font-size:13px;padding:4px 0;">· {log}</div>', unsafe_allow_html=True)

    if st.button("🔄 다시 시작", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
