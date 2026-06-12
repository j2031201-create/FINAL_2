"""
슬기로운 영끌생활 · 부동산 투자 전략 게임 (캡스톤 최종판)
Professional Navy & Red · 감정평가 영구해금 · 3매물 스카우팅 · 시장예측 · 실질수익 리포트
"""
import streamlit as st
import random, time

st.set_page_config(page_title="슬기로운 영끌생활", page_icon="🏠",
                   layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────────────
# 데이터
# ─────────────────────────────────────────────────────
REGIONS = {
    "서울": {"desc":"높은 수요·강한 상승 모멘텀","level":"초급","vol":0.07,"trend":0.05,"icon":"🏙️"},
    "대전": {"desc":"신도시 개발·구도심 리스크","level":"중급","vol":0.12,"trend":0.01,"icon":"🌆"},
    "제주": {"desc":"수요 한정·유동성 낮음","level":"고급","vol":0.18,"trend":-0.01,"icon":"🏝️"},
}
BRANDS = ["e편한세상","래미안","힐스테이트","자이","아이파크","롯데캐슬","푸르지오","더샵"]

APPRAISAL = {
    "수익환원법": {"icon":"💰","def":"부동산이 장래 산출할 것으로 기대되는 순수익(임대료)을 환원율로 나누어 가치를 구하는 방식","calc":"income"},
    "거래사례비교법":{"icon":"📊","def":"대상과 유사한 인근의 실제 거래 사례를 수집해 입지·층·향 등을 보정하여 가치를 구하는 방식","calc":"compare"},
    "원가법":     {"icon":"🏗️","def":"대상을 다시 짓는다고 가정해 토지가격에 건축비를 더하고 감가상각을 빼서 가치를 구하는 방식","calc":"cost"},
}

NEWS_POOL = [
    {"head":"📈 한국은행 기준금리 0.25%p 인하","i1":"호가 +6%","i2":"대출이율 -0.5%","mood":"good","delta":0.06,"rate":-0.5,"hp":0},
    {"head":"📉 기준금리 0.5%p 인상","i1":"호가 -8%","i2":"대출이율 +1.0% · HP -5","mood":"bad","delta":-0.08,"rate":1.0,"hp":5},
    {"head":"🚇 수도권 GTX 신규 노선 확정","i1":"호가 +9%","i2":"역세권 수요 급증","mood":"good","delta":0.09,"rate":0,"hp":0},
    {"head":"🚨 토지거래허가구역 확대","i1":"호가 -7%","i2":"갭투자 제한","mood":"bad","delta":-0.07,"rate":0,"hp":0},
    {"head":"🏗️ 재건축 안전진단 완화","i1":"호가 +5%","i2":"노후단지 프리미엄","mood":"good","delta":0.05,"rate":0,"hp":0},
    {"head":"💸 DSR 3단계 시행","i1":"호가 -5%","i2":"대출한도 축소 · HP -10","mood":"bad","delta":-0.05,"rate":0,"hp":10},
    {"head":"🌊 전세 시장 안정세","i1":"호가 +3%","i2":"임대수익 안정","mood":"good","delta":0.03,"rate":0,"hp":0},
    {"head":"📰 미분양 8만 가구 돌파","i1":"호가 -6%","i2":"공급과잉 경고","mood":"bad","delta":-0.06,"rate":0,"hp":0},
    {"head":"🏦 특례보금자리론 재출시","i1":"호가 +4%","i2":"대출이율 -0.3%","mood":"good","delta":0.04,"rate":-0.3,"hp":0},
    {"head":"📊 소비자물가 3% 돌파","i1":"호가 +5%","i2":"인플레 헤지 수요","mood":"good","delta":0.05,"rate":0,"hp":0},
]
INFLATION = 0.025  # 연 인플레이션 2.5%

# ─────────────────────────────────────────────────────
# 세션
# ─────────────────────────────────────────────────────
def init():
    D={"phase":"intro","region":None,"capital":100000,"debt":0,"loan_rate":5.0,
       "hp":100,"turn":1,"monthly_income":200,"market":[],"owned":[],
       "news":None,"next_news":None,"unlocked":[],"selected":None,"quiz":None,
       "appraised":None,"appraisal_steps":[],"log":[],"total_interest":0,
       "game_over":False}
    for k,v in D.items():
        if k not in st.session_state: st.session_state[k]=v
init()
S=st.session_state

def won(v):
    v=int(round(v)); neg=v<0; v=abs(v); eok=v//10000; man=v%10000
    s=(f"{eok}억 " if eok else "")+(f"{man:,}만" if man else "")
    return ("-" if neg else "")+(s.strip() or "0")

def new_listing(rk):
    base=random.randint(50000,150000)
    fair=int(base*random.uniform(0.82,1.22))
    rent=int(base*random.uniform(0.035,0.055))
    area=random.randint(60,140)
    return {"id":random.randint(10000,99999),"name":random.choice(BRANDS),
            "type":random.choice(["아파트","오피스텔","상가","빌라"]),
            "base":base,"fair":fair,"current":base,"rent":rent,"area":area,
            "purchase_price":0}

def scout(rk):
    """매 턴 3개 매물만 추출"""
    S["market"]=[new_listing(rk) for _ in range(3)]

def apply_delta(d):
    for L in S["market"]:
        n=random.uniform(-0.02,0.02)
        L["current"]=max(10000,int(L["current"]*(1+d+n)))
        L["fair"]=max(10000,int(L["fair"]*(1+d*0.5+n)))
    for L in S["owned"]:
        n=random.uniform(-0.02,0.02)
        L["current"]=max(10000,int(L["current"]*(1+d+n)))

def make_quiz(method):
    opts=list(APPRAISAL.keys()); random.shuffle(opts)
    return {"answer":method,"definition":APPRAISAL[method]["def"],"options":opts,"tries":0}

def turn_finance():
    mi=int(S["debt"]*(S["loan_rate"]/100)/12)
    S["total_interest"]+=mi*12  # 연간 이자 누적 (1턴=1년)
    rent=sum(L["rent"] for L in S["owned"])
    net=S["monthly_income"]+rent-mi
    S["capital"]+=net*12  # 연 단위 반영
    if net<0:
        S["hp"]=max(0,S["hp"]-max(3,min(20,abs(net)//500)))

def new_turn():
    # 이번 턴 뉴스 = 지난 턴에 예고된 것 (없으면 랜덤)
    S["news"]=S["next_news"] or random.choice(NEWS_POOL)
    S["next_news"]=random.choice(NEWS_POOL)  # 다음 턴 예고
    apply_delta(S["news"]["delta"])
    if S["news"]["rate"]: S["loan_rate"]=max(1.0,S["loan_rate"]+S["news"]["rate"])
    if S["news"]["hp"]: S["hp"]=max(0,S["hp"]-S["news"]["hp"])
    scout(S["region"])
    turn_finance()
    S["selected"]=None; S["quiz"]=None; S["appraised"]=None; S["appraisal_steps"]=[]
    if S["hp"]<=0: S["game_over"]=True; S["phase"]="end"

def do_appraise(method,L):
    cap=round(random.uniform(0.04,0.065),3)
    if method=="수익환원법":
        v=int(L["rent"]/cap)
        steps=[f"1. 연 임대료: {L['rent']:,}만원",f"2. 환원율 {cap*100:.1f}% 적용",
               f"🎯 적정가치 = {L['rent']:,} ÷ {cap*100:.1f}% = {v:,}만원"]
    elif method=="거래사례비교법":
        adj=round(random.uniform(0.90,1.15),2); v=int(L["current"]*adj)
        steps=[f"1. 유사 거래 기준가: {L['current']:,}만원",f"2. 보정계수 {adj:.2f} 적용",
               f"🎯 적정가치 = {v:,}만원"]
    else:
        land=int(L["current"]*0.55); build=int(L["current"]*0.5); dep=int(build*random.uniform(0.1,0.35))
        v=land+build-dep
        steps=[f"1. 토지 {land:,}만원",f"2. 건축비 {build:,} − 감가 {dep:,}만원",f"🎯 적정가치 = {v:,}만원"]
    return v,steps

def buy(lid):
    L=next(x for x in S["market"] if x["id"]==lid); cost=L["current"]
    if cost>S["capital"]:
        need=cost-S["capital"]; S["debt"]+=need; S["capital"]=0
        S["log"].append(f"턴{S['turn']}: {L['name']} 영끌매수 (대출 {won(need)})")
    else:
        S["capital"]-=cost; S["log"].append(f"턴{S['turn']}: {L['name']} 매수")
    L["purchase_price"]=cost; S["owned"].append(L)
    S["market"]=[x for x in S["market"] if x["id"]!=lid]

def sell(i):
    L=S["owned"][i]; S["capital"]+=L["current"]
    p=L["current"]-L["purchase_price"]
    S["log"].append(f"턴{S['turn']}: {L['name']} 매도 (손익 {'+' if p>=0 else ''}{won(p)})")
    S["owned"].pop(i)

def advance():
    if S["turn"]>=10: S["phase"]="end"
    else: S["turn"]+=1; new_turn()
    st.rerun()

# ─────────────────────────────────────────────────────
# CSS · Professional Navy & Red
# ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Urbanist:wght@400;600;700;900&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
html,body,.stApp{font-family:'Urbanist','Noto Sans KR',sans-serif !important;
    background:#001f3f !important;color:#eaf0f8 !important;}
#MainMenu,footer{display:none !important;}
.main .block-container{padding:1rem 1.5rem 2rem !important;max-width:1500px !important;}
.g-title{font-size:22px;font-weight:900;color:#fff;display:flex;align-items:center;gap:8px;margin-bottom:2px;}
.g-sub{font-size:13px;color:#8fa8c8;margin-bottom:12px;}

/* 패널 */
.panel{background:#003366;border:1px solid #0a4377;border-radius:14px;padding:14px 16px;margin-bottom:12px;}
.panel-red{background:#003366;border:1px solid #FF0000;border-radius:14px;padding:14px 16px;margin-bottom:12px;}
.ptitle{font-size:13px;font-weight:700;color:#FF4136;margin-bottom:10px;letter-spacing:.02em;display:flex;align-items:center;gap:6px;}

/* 스탯 */
.stat-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px;}
.stat-card{background:#003366;border:1px solid #0a4377;border-radius:12px;padding:9px 10px;text-align:center;}
.stat-card .sl{font-size:11px;color:#7e98ba;margin-bottom:3px;}
.stat-card .sv{font-size:15px;font-weight:800;color:#fff;}
.sv.danger{color:#FF4136;} .sv.warn{color:#FFB700;}

/* 뉴스 */
.news{border-radius:12px;padding:12px 14px;margin-bottom:10px;}
.news-good{background:rgba(46,204,113,.12);border:1px solid #2ecc71;}
.news-bad{background:rgba(255,65,54,.12);border:1px solid #FF4136;}
.news-head{font-size:14px;font-weight:700;color:#fff;margin-bottom:6px;}
.news-info{font-size:12px;color:#c8d6e8;padding:2px 0;}

/* 매물 카드 — 우측과 동일 폰트 크기(13px) */
.li-card{background:#003366;border:1px solid #0a4377;border-radius:12px;padding:11px 13px;margin-bottom:7px;}
.li-card.sel{border-color:#FF0000;background:#04294f;}
.li-name{font-size:13px;font-weight:700;color:#fff;}
.li-price{font-size:13px;color:#a8bdd8;margin-top:2px;}

/* 퀴즈 */
.quiz-box{background:#04294f;border:1px solid #FF0000;border-radius:12px;padding:14px;margin:10px 0;}
.quiz-def{font-size:13px;color:#dce6f2;line-height:1.7;background:#001f3f;border-radius:10px;padding:11px;margin-bottom:8px;border:1px dashed #2a557f;}

/* 감정평가 결과 */
.ap-box{background:#04294f;border:1px solid #2ecc71;border-radius:12px;padding:14px;margin:10px 0;}
.ap-step{font-size:12px;color:#c8d6e8;padding:4px 0;border-bottom:1px solid #0a4377;}
.ap-step:last-child{border-bottom:none;font-size:14px;font-weight:800;color:#2ecc71;padding-top:8px;}

/* 인벤토리 */
.inv-item{border-radius:10px;padding:9px 11px;margin-bottom:6px;font-size:13px;font-weight:600;}
.inv-profit{background:rgba(46,204,113,.1);border:1px solid #2ecc71;}
.inv-loss{background:rgba(255,65,54,.1);border:1px solid #FF4136;}

/* 우측 디스플레이 — 13px 통일 */
.display{background:#04294f;border:1px solid #0a4377;border-radius:14px;padding:16px;}
.disp-item{font-size:13px;color:#c8d6e8;padding:6px 0;border-bottom:1px solid #0a4377;}
.disp-item:last-child{border-bottom:none;}
.disp-label{color:#7e98ba;font-size:12px;}
.forecast{background:rgba(255,183,0,.1);border:1px solid #FFB700;border-radius:12px;padding:13px;margin-top:10px;}
.forecast-head{font-size:13px;font-weight:700;color:#FFB700;margin-bottom:6px;}
.forecast-body{font-size:13px;color:#e8d8a8;line-height:1.6;}

.log-item{font-size:12px;color:#7e98ba;padding:3px 0;border-bottom:1px solid #0a3060;}

/* 버튼 */
.stButton>button{font-family:'Urbanist','Noto Sans KR',sans-serif !important;font-weight:700 !important;
    border-radius:10px !important;background:#003366 !important;border:1px solid #1a5490 !important;
    color:#fff !important;transition:.12s !important;}
.stButton>button:hover{background:#FF0000 !important;border-color:#FF0000 !important;transform:translateY(-1px);}
[data-testid="stMetric"]{background:#003366;border:1px solid #0a4377;border-radius:12px;padding:10px 14px;}
[data-testid="stMetricValue"]{color:#fff !important;} [data-testid="stMetricLabel"]{color:#8fa8c8 !important;}

/* 인트로 */
.intro-hero{text-align:center;padding:30px 0 10px;}
.intro-logo{font-size:40px;font-weight:900;color:#fff;letter-spacing:-0.02em;}
.intro-logo .red{color:#FF4136;}
.intro-tag{font-size:14px;color:#8fa8c8;margin-top:8px;}
.manual{background:#003366;border:1px solid #0a4377;border-radius:14px;padding:20px 24px;margin:18px 0;}
.manual h4{color:#FF4136;font-size:15px;margin:0 0 12px;}
.manual-item{font-size:13px;color:#dce6f2;padding:6px 0;line-height:1.6;display:flex;gap:10px;}
.manual-item .num{color:#FF4136;font-weight:800;flex:0 0 22px;}
.region-card{background:#003366;border:2px solid #0a4377;border-radius:16px;padding:20px;text-align:center;height:100%;}
.rc-icon{font-size:38px;} .rc-name{font-size:19px;font-weight:900;color:#fff;margin-top:6px;}
.rc-level{display:inline-block;font-size:11px;font-weight:700;padding:2px 12px;border-radius:100px;margin:6px 0;}
.rc-desc{font-size:12px;color:#8fa8c8;line-height:1.6;}

/* 결산 리포트 */
.report-hero{text-align:center;padding:24px;border-radius:18px;margin-bottom:20px;}
.report-big{font-size:52px;font-weight:900;line-height:1;letter-spacing:-0.02em;}
.report-label{font-size:14px;margin-top:10px;font-weight:600;}
.profit{background:linear-gradient(135deg,rgba(46,204,113,.15),rgba(46,204,113,.05));border:2px solid #2ecc71;}
.profit .report-big{color:#2ecc71;} .profit .report-label{color:#82e0aa;}
.loss{background:linear-gradient(135deg,rgba(255,65,54,.15),rgba(255,65,54,.05));border:2px solid #FF4136;}
.loss .report-big{color:#FF4136;} .loss .report-label{color:#ff8b82;}
.calc-table{width:100%;border-collapse:collapse;margin:14px 0;}
.calc-table td{padding:10px 14px;border-bottom:1px solid #0a4377;font-size:14px;color:#dce6f2;}
.calc-table td.r{text-align:right;font-weight:700;color:#fff;}
.calc-table tr.total td{border-top:2px solid #FF0000;border-bottom:none;font-size:16px;font-weight:900;color:#fff;padding-top:14px;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# 화면 A: 인트로 (랜딩 + 설명서)
# ─────────────────────────────────────────────────────
if S["phase"]=="intro":
    st.markdown("""
    <div class="intro-hero">
      <div class="intro-logo">🏠 슬기로운 <span class="red">영끌</span>생활</div>
      <div class="intro-tag">부동산 투자 전략 시뮬레이션 · 감정평가를 배우고 저평가 매물을 찾아라</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="manual">
      <h4>📖 게임 설명서</h4>
      <div class="manual-item"><span class="num">1</span><span><b>목표</b> — 초기자본 10억으로 10턴(10년) 동안 순자산을 최대한 불리세요.</span></div>
      <div class="manual-item"><span class="num">2</span><span><b>매물 스카우팅</b> — 매 턴 무작위 3개 매물이 공개됩니다. 호가와 적정가치를 비교하세요.</span></div>
      <div class="manual-item"><span class="num">3</span><span><b>감정평가 퀴즈</b> — 평가 방식의 정의를 읽고 이름을 맞히면 그 도구가 <b>영구 해금</b>됩니다.</span></div>
      <div class="manual-item"><span class="num">4</span><span><b>영끌(대출)</b> — 자본이 부족해도 매수 가능. 단, 이자가 소득을 넘으면 멘탈(HP)이 깎여 0이면 파산!</span></div>
      <div class="manual-item"><span class="num">5</span><span><b>시장 예측</b> — 우측 디스플레이의 '다음 턴 예고'를 보고 전략적으로 매수/매도하세요.</span></div>
      <div class="manual-item"><span class="num">6</span><span><b>실질 수익</b> — 종료 후 대출이자와 인플레이션을 뺀 '진짜 수익'으로 평가됩니다.</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### 🗺️ 지역을 선택하고 START")
    cols=st.columns(3)
    lc={"서울":"#3498db","대전":"#FFB700","제주":"#FF4136"}
    for col,(k,r) in zip(cols,REGIONS.items()):
        with col:
            c=lc[k]
            st.markdown(f"""<div class="region-card"><div class="rc-icon">{r['icon']}</div>
              <div class="rc-name">{k}</div><div class="rc-level" style="background:{c}22;color:{c};">{r['level']}</div>
              <div class="rc-desc">{r['desc']}</div></div>""", unsafe_allow_html=True)
            if st.button(f"▶ {k} START", key=f"go_{k}", use_container_width=True):
                S["region"]=k; S["phase"]="play"
                ph=st.empty()
                for msg in ["🗺️ 지도 로딩 중...","🏢 매물 스카우팅 중...","📊 시장 분석 중..."]:
                    ph.markdown(f'<div style="text-align:center;padding:40px;font-size:18px;font-weight:700;color:#FF4136;">{msg}</div>', unsafe_allow_html=True)
                    time.sleep(0.5)
                ph.empty()
                S["next_news"]=random.choice(NEWS_POOL)
                new_turn(); st.rerun()

# ─────────────────────────────────────────────────────
# 화면 B: 플레이
# ─────────────────────────────────────────────────────
elif S["phase"]=="play":
    rk=S["region"]; R=REGIONS[rk]
    st.markdown(f'<div class="g-title">{R["icon"]} 슬기로운 영끌생활 — {rk} <span style="color:#FF4136;font-size:14px;">{R["level"]}</span></div>', unsafe_allow_html=True)

    left,right=st.columns([1.15,0.85],gap="large")

    with left:
        mi=int(S["debt"]*(S["loan_rate"]/100)/12); rent=sum(L["rent"] for L in S["owned"])
        hpc="danger" if S["hp"]<=30 else ("warn" if S["hp"]<=60 else "")
        st.markdown(f"""<div class="stat-row">
          <div class="stat-card"><div class="sl">자본금</div><div class="sv">{won(S['capital'])}</div></div>
          <div class="stat-card"><div class="sl">대출</div><div class="sv {'danger' if S['debt']>0 else ''}">{won(S['debt'])}</div></div>
          <div class="stat-card"><div class="sl">멘탈</div><div class="sv {hpc}">{S['hp']}</div></div>
          <div class="stat-card"><div class="sl">턴</div><div class="sv">{S['turn']}/10</div></div>
        </div>
        <div class="stat-row">
          <div class="stat-card"><div class="sl">월소득</div><div class="sv">{won(S['monthly_income'])}</div></div>
          <div class="stat-card"><div class="sl">월세</div><div class="sv">{won(rent)}</div></div>
          <div class="stat-card"><div class="sl">월이자</div><div class="sv {'danger' if mi>0 else ''}">{won(mi)}</div></div>
          <div class="stat-card"><div class="sl">대출이율</div><div class="sv">{S['loan_rate']:.1f}%</div></div>
        </div>""", unsafe_allow_html=True)

        if S["news"]:
            nc="news-good" if S["news"]["mood"]=="good" else "news-bad"
            st.markdown(f"""<div class="news {nc}"><div class="news-head">{S['news']['head']}</div>
              <div class="news-info">📌 {S['news']['i1']}</div>
              <div class="news-info">📌 {S['news']['i2']}</div></div>""", unsafe_allow_html=True)

        st.markdown('<div class="ptitle">🏢 이번 턴 매물 (3건 스카우팅)</div>', unsafe_allow_html=True)
        for L in S["market"]:
            sel=S["selected"]==L["id"]
            st.markdown(f"""<div class="li-card {'sel' if sel else ''}">
              <div class="li-name">{L['name']} · {L['type']} ({L['area']}㎡)</div>
              <div class="li-price">호가 {won(L['current'])} · {int(L['current']/L['area']):,}만원/㎡ · 월세 {L['rent']:,}만</div>
            </div>""", unsafe_allow_html=True)
            if st.button("이 매물 선택", key=f"sel_{L['id']}"):
                S["selected"]=L["id"]; S["quiz"]=None; S["appraised"]=None; S["appraisal_steps"]=[]; st.rerun()

        # ── 감정평가 도구창 ──
        if S["selected"] and any(x["id"]==S["selected"] for x in S["market"]):
            L=next(x for x in S["market"] if x["id"]==S["selected"])
            st.markdown('<div class="ptitle" style="margin-top:14px;">🎯 감정평가 도구</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:13px;color:#a8bdd8;margin-bottom:8px;">선택: <b style="color:#fff;">{L["name"]}</b> · 호가 {won(L["current"])}</div>', unsafe_allow_html=True)

            if S["appraised"] is None:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.caption(f"해금된 도구: {', '.join(S['unlocked']) if S['unlocked'] else '없음 (퀴즈로 해금)'}")
                ac=st.columns(3)
                for i,(m,info) in enumerate(APPRAISAL.items()):
                    with ac[i]:
                        unlocked=m in S["unlocked"]
                        label=f"{info['icon']} {m}" + (" ✓" if unlocked else " 🔒")
                        if st.button(label, key=f"tool_{m}"):
                            if unlocked:
                                ph=st.empty()
                                for d in [".","..","..."]:
                                    ph.markdown(f'<div style="text-align:center;padding:12px;font-weight:800;color:#FF4136;">🎲 감정평가 중{d}</div>', unsafe_allow_html=True)
                                    time.sleep(0.4)
                                v,steps=do_appraise(m,L); S["appraised"]=v; S["appraisal_steps"]=steps
                                ph.empty(); st.rerun()
                            else:
                                S["quiz"]=make_quiz(m); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                if S["quiz"]:
                    q=S["quiz"]
                    st.markdown(f'<div class="quiz-box"><div style="font-weight:800;color:#fff;margin-bottom:6px;">📖 이 설명은 어떤 감정평가 방식?</div><div class="quiz-def">{q["definition"]}</div></div>', unsafe_allow_html=True)
                    oc=st.columns(3)
                    for i,opt in enumerate(q["options"]):
                        with oc[i]:
                            if st.button(opt, key=f"ans_{opt}_{q['tries']}"):
                                if opt==q["answer"]:
                                    if q["answer"] not in S["unlocked"]:
                                        S["unlocked"].append(q["answer"])
                                    S["quiz"]=None; st.rerun()
                                else:
                                    S["hp"]=max(0,S["hp"]-5); S["quiz"]["tries"]+=1
                                    if S["hp"]<=0: S["game_over"]=True; S["phase"]="end"
                                    st.rerun()
                    if q["tries"]>0:
                        st.warning(f"❌ 오답! HP -5 (현재 {S['hp']}) · 다시 시도")
            else:
                st.markdown('<div class="ap-box">'+"".join(f'<div class="ap-step">{s}</div>' for s in S["appraisal_steps"])+'</div>', unsafe_allow_html=True)
                diff=S["appraised"]-L["current"]
                if diff>2000: st.success(f"💎 저평가! 적정가 대비 {won(abs(diff))} 저렴")
                elif diff<-2000: st.warning(f"⚠️ 고평가! 적정가 대비 {won(abs(diff))} 비쌈")
                else: st.info("📊 적정 가격대")
                bc=st.columns(2)
                with bc[0]:
                    msg=f"💰 매수 ({won(L['current'])})"
                    if L["current"]>S["capital"]: msg=f"🏦 영끌매수 (+대출 {won(L['current']-S['capital'])})"
                    if st.button(msg,key="buy",use_container_width=True):
                        buy(S["selected"]); S["selected"]=None; S["appraised"]=None; st.rerun()
                with bc[1]:
                    if st.button("⏭️ 패스",key="pass",use_container_width=True):
                        S["selected"]=None; S["appraised"]=None; st.rerun()

        # ── 인벤토리 (시각 분리) ──
        st.markdown('<div class="ptitle" style="margin-top:14px;">🏦 보유 매물 (인벤토리)</div>', unsafe_allow_html=True)
        if S["owned"]:
            for i,L in enumerate(S["owned"]):
                p=L["current"]-L["purchase_price"]
                st.markdown(f'<div class="inv-item {"inv-profit" if p>=0 else "inv-loss"}">{"🟢" if p>=0 else "🔴"} {L["name"]} · 현재 {won(L["current"])} · 손익 {"+" if p>=0 else ""}{won(p)}</div>', unsafe_allow_html=True)
                if st.button("매도",key=f"sl_{i}"): sell(i); st.rerun()
        else:
            st.caption("아직 보유한 매물이 없습니다.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⏭️ 다음 턴으로 진행", use_container_width=True):
            advance()

    # ── 우측 디스플레이 ──
    with right:
        st.markdown('<div class="ptitle">📊 시장 디스플레이</div>', unsafe_allow_html=True)
        total_asset=S["capital"]+sum(L["current"] for L in S["owned"])
        st.markdown(f"""<div class="display">
          <div class="disp-item"><span class="disp-label">총 자산</span><br>{won(total_asset)}</div>
          <div class="disp-item"><span class="disp-label">순자산 (자산-부채)</span><br>{won(total_asset-S['debt'])}</div>
          <div class="disp-item"><span class="disp-label">누적 대출이자</span><br>{won(S['total_interest'])}</div>
          <div class="disp-item"><span class="disp-label">보유 매물</span><br>{len(S['owned'])}건</div>
          <div class="disp-item"><span class="disp-label">해금 감정평가</span><br>{', '.join(S['unlocked']) if S['unlocked'] else '없음'}</div>
        </div>""", unsafe_allow_html=True)

        # 시장 예측 (다음 턴 예고)
        if S["next_news"]:
            nn=S["next_news"]
            arrow="📈 상승 신호" if nn["mood"]=="good" else "📉 하락 신호"
            st.markdown(f"""<div class="forecast">
              <div class="forecast-head">🔮 다음 턴 시장 예측</div>
              <div class="forecast-body">{arrow}<br>예상 이슈: {nn['head'].split(' ',1)[1] if ' ' in nn['head'] else nn['head']}<br>
              <span style="color:#FFB700;">{nn['i1']} · {nn['i2']}</span></div>
            </div>""", unsafe_allow_html=True)
            st.caption("💡 예측을 보고 이번 턴 매수/매도를 결정하세요")

        if S["log"]:
            st.markdown('<div class="ptitle" style="margin-top:12px;">📜 거래 기록</div>', unsafe_allow_html=True)
            for e in reversed(S["log"][-6:]):
                st.markdown(f'<div class="log-item">{e}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# 화면 C: 최종 결산 리포트
# ─────────────────────────────────────────────────────
elif S["phase"]=="end":
    # 전환 연출
    if not S.get("_report_shown"):
        ph=st.empty()
        for msg in ["📊 최종 자산 집계 중...","🧮 실질 수익 계산 중...","📑 리포트 생성 중..."]:
            ph.markdown(f'<div style="text-align:center;padding:60px;font-size:20px;font-weight:800;color:#FF4136;">{msg}</div>', unsafe_allow_html=True)
            time.sleep(0.6)
        ph.empty(); S["_report_shown"]=True

    assets=S["capital"]+sum(L["current"] for L in S["owned"])
    net_worth=assets-S["debt"]
    start=100000
    # 실질수익 = 순자산 - 초기자본 - 누적이자 - 인플레보정
    inflation_adj=int(start*((1+INFLATION)**10-1))  # 10년 인플레 누적
    nominal=net_worth-start
    real=nominal-S["total_interest"]-inflation_adj

    st.markdown('<div class="g-title">🏁 최종 수익 리포트</div>', unsafe_allow_html=True)
    if S.get("game_over"):
        st.error("💔 멘탈 0 → 파산 엔딩! 이자 부담을 감당하지 못했습니다.")

    cls="profit" if real>=0 else "loss"
    sign="+" if real>=0 else ""
    st.markdown(f"""<div class="report-hero {cls}">
      <div class="report-big">{sign}{won(real)}</div>
      <div class="report-label">실질 수익 (대출이자·인플레이션 반영)</div>
    </div>""", unsafe_allow_html=True)

    c=st.columns(4)
    c[0].metric("총 자산", won(assets))
    c[1].metric("순자산", won(net_worth))
    c[2].metric("명목 수익", f"{'+' if nominal>=0 else ''}{won(nominal)}")
    c[3].metric("보유 매물", f"{len(S['owned'])}건")

    # 상세 계산표
    st.markdown('<div class="ptitle" style="margin-top:18px;">🧮 실질 수익 상세 계산</div>', unsafe_allow_html=True)
    st.markdown(f"""<table class="calc-table">
      <tr><td>최종 순자산 (자산 − 부채)</td><td class="r">{won(net_worth)}</td></tr>
      <tr><td>(−) 초기 자본금</td><td class="r">− {won(start)}</td></tr>
      <tr><td>= 명목 수익</td><td class="r">{'+' if nominal>=0 else ''}{won(nominal)}</td></tr>
      <tr><td>(−) 누적 대출 이자</td><td class="r">− {won(S['total_interest'])}</td></tr>
      <tr><td>(−) 인플레이션 보정 (연 {INFLATION*100:.1f}%·10년)</td><td class="r">− {won(inflation_adj)}</td></tr>
      <tr class="total"><td>= 실질 수익</td><td class="r">{sign}{won(real)}</td></tr>
    </table>""", unsafe_allow_html=True)

    # 등급
    rate=real/start*100
    if S.get("game_over"): grade,msg="💔 파산","대출 관리에 실패했습니다. 다음엔 영끌을 조심하세요!"
    elif rate>=40: grade,msg="🏆 부동산 마스터","감정평가와 시장예측을 완벽히 활용했습니다!"
    elif rate>=10: grade,msg="💼 유능한 투자자","인플레이션을 이기는 실질 수익을 냈습니다!"
    elif rate>=0: grade,msg="👍 본전 사수","원금은 지켰지만 인플레를 겨우 따라갔어요."
    else: grade,msg="📚 수업료를 낸 새내기","손실도 경험! 감정평가의 중요성을 배웠습니다."
    st.markdown(f"""<div class="panel-red" style="text-align:center;margin-top:8px;">
      <div style="font-size:22px;font-weight:900;color:#fff;">{grade}</div>
      <div style="font-size:13px;color:#a8bdd8;margin-top:6px;">{msg}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="ptitle">📜 전체 거래 기록</div>', unsafe_allow_html=True)
    for e in S["log"]:
        st.markdown(f'<div class="log-item">{e}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 다시 시작", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
