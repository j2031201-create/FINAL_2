"""
슬기로운 영끌생활 · 부동산 투자 전략 게임 (캡스톤 최종판 v2)
시장원리 반영 · 영구해금 · 시장예측 · 실질수익 리포트 · sticky 스탯 · 설명서 팝업
"""
import streamlit as st
import random, time

st.set_page_config(page_title="슬기로운 영끌생활", page_icon="🏠",
                   layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────────────
# 데이터 · 시장 원리 반영
# ─────────────────────────────────────────────────────
# 지역별 난이도: 초기자본·변동성·증감폭·성장트렌드 차등
REGIONS = {
    "서울": {"desc":"높은 수요·공급절벽·강한 상승 모멘텀","level":"난이도 하","icon":"🏙️",
             "capital":120000,"vol":0.06,"apt_trend":0.04,"yield_trend":0.0},
    "대전": {"desc":"신도시 개발 호재·구도심 양극화","level":"난이도 중","icon":"🌆",
             "capital":100000,"vol":0.11,"apt_trend":0.01,"yield_trend":-0.005},
    "제주": {"desc":"수요 한정·유동성 낮음·관광 의존","level":"난이도 상","icon":"🏝️",
             "capital":80000,"vol":0.17,"apt_trend":-0.01,"yield_trend":-0.01},
}

# 위트있는 브랜드 패러디 (실제와 유사)
BRANDS = {
    "아파트":   ["래미안 더퍼스트","힐스테이트 센트럴","자이 프레스티지","아이파크 스카이","푸르지오 시그니처"],
    "오피스텔": ["롯데캐슬 스튜디오","SK뷰 오피스","두산위브 텔","쌍용예가 리빙텔"],
    "상가":     ["타임스퀘어몰","스트리트 상가","센트럴 플라자","로데오 스퀘어"],
    "빌라":     ["하이빌 그린","수목원빌","햇살가득빌","청계힐"],
}

# 매물 유형별 시장 특성 (현실 반영)
TYPE_SPEC = {
    "아파트":   {"yield":(0.020,0.030),"appr":(0.03,0.12),"tag":"시세차익형","note":"입지·공급절벽으로 가격 상승 · 월세 수익률은 낮음"},
    "오피스텔": {"yield":(0.050,0.070),"appr":(-0.02,0.02),"tag":"월세수익형","note":"월세 수익률 높음 · 시세 상승 거의 없음"},
    "상가":     {"yield":(0.060,0.090),"appr":(-0.03,0.02),"tag":"월세수익형","note":"월세 최고 · 단, 공실 위험 존재"},
    "빌라":     {"yield":(0.040,0.060),"appr":(-0.03,0.01),"tag":"월세수익형","note":"월세 중간 · 시세 하락 위험 주의"},
}

APPRAISAL = {
    "수익환원법": {"icon":"💰","def":"부동산이 장래 산출할 것으로 기대되는 순수익(임대료)을 환원율로 나누어 가치를 구하는 방식","best_for":["오피스텔","상가","빌라"]},
    "거래사례비교법":{"icon":"📊","def":"대상과 유사한 인근의 실제 거래 사례를 수집해 입지·층·향 등을 보정하여 가치를 구하는 방식","best_for":["아파트"]},
    "원가법":     {"icon":"🏗️","def":"대상을 다시 짓는다고 가정해 토지가격에 건축비를 더하고 감가상각을 빼서 재조달원가로 가치를 구하는 방식","best_for":[]},
}

NEWS_POOL = [
    {"head":"📈 한국은행 기준금리 0.25%p 인하","i1":"전체 호가 +6%","i2":"대출이율 -0.5%","mood":"good","delta":0.06,"rate":-0.5,"hp":0,"apt_boost":0.02},
    {"head":"📉 기준금리 0.5%p 인상","i1":"전체 호가 -8%","i2":"대출이율 +1.0% · HP -5","mood":"bad","delta":-0.08,"rate":1.0,"hp":5,"apt_boost":-0.02},
    {"head":"🚇 수도권 GTX 신규 노선 확정","i1":"아파트 +12%","i2":"역세권 시세차익 기대","mood":"good","delta":0.04,"rate":0,"hp":0,"apt_boost":0.08},
    {"head":"🚨 토지거래허가구역 확대","i1":"전체 호가 -7%","i2":"갭투자 제한·거래 위축","mood":"bad","delta":-0.07,"rate":0,"hp":0,"apt_boost":0},
    {"head":"🏗️ 재건축 안전진단 완화","i1":"아파트 +9%","i2":"노후단지 시세 프리미엄","mood":"good","delta":0.03,"rate":0,"hp":0,"apt_boost":0.06},
    {"head":"💸 DSR 3단계 시행","i1":"전체 호가 -5%","i2":"대출한도 축소 · HP -10","mood":"bad","delta":-0.05,"rate":0,"hp":10,"apt_boost":0},
    {"head":"🏪 상권 활성화 정책 발표","i1":"상가 월세 +15%","i2":"임대수익형 수혜","mood":"good","delta":0.02,"rate":0,"hp":0,"apt_boost":0,"rent_boost":0.15},
    {"head":"📰 미분양 8만 가구 돌파","i1":"전체 호가 -6%","i2":"공급과잉·아파트 직격","mood":"bad","delta":-0.06,"rate":0,"hp":0,"apt_boost":-0.04},
    {"head":"🏦 특례보금자리론 재출시","i1":"전체 호가 +4%","i2":"대출이율 -0.3%","mood":"good","delta":0.04,"rate":-0.3,"hp":0,"apt_boost":0.02},
    {"head":"🌊 전세사기 여파·빌라 기피","i1":"빌라 -10%","i2":"비아파트 수요 위축","mood":"bad","delta":-0.02,"rate":0,"hp":0,"apt_boost":0,"villa_hit":-0.10},
]
INFLATION = 0.025

# ─────────────────────────────────────────────────────
# 세션
# ─────────────────────────────────────────────────────
def init():
    D={"phase":"intro","region":None,"capital":100000,"debt":0,"loan_rate":5.0,
       "hp":100,"turn":1,"income_year":3000,"market":[],"owned":[],
       "news":None,"next_news":None,"unlocked":[],"selected":None,"quiz":None,
       "appraised":None,"appraisal_steps":[],"appraisal_method":None,"log":[],
       "total_interest":0,"game_over":False,"show_manual":False,"_report_shown":False}
    for k,v in D.items():
        if k not in st.session_state: st.session_state[k]=v
init()
S=st.session_state

def won(v):
    v=int(round(v)); neg=v<0; v=abs(v); eok=v//10000; man=v%10000
    s=(f"{eok}억 " if eok else "")+(f"{man:,}만" if man else "")
    return ("-" if neg else "")+(s.strip() or "0")

import os, base64
def img_b64(path):
    """이미지가 있으면 base64 data URI 반환, 없으면 None"""
    if os.path.exists(path):
        with open(path,"rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return None

def new_listing(rk):
    t=random.choice(list(TYPE_SPEC.keys()))
    spec=TYPE_SPEC[t]
    area=random.randint(60,140)
    base=random.randint(50000,150000)
    # 월세: 유형별 수익률 반영, 50~400만원 범위로 클램프
    y=random.uniform(*spec["yield"])
    monthly=int(base*y/12)
    monthly=max(50,min(400,monthly))
    deposit=monthly*12  # 보증금 = 월세 1년치
    fair=int(base*random.uniform(0.85,1.18))
    return {"id":random.randint(10000,99999),"name":random.choice(BRANDS[t]),"type":t,
            "tag":spec["tag"],"base":base,"fair":fair,"current":base,
            "monthly":monthly,"deposit":deposit,"area":area,"purchase_price":0}

def scout(rk):
    S["market"]=[new_listing(rk) for _ in range(3)]

def apply_market(news, rk):
    R=REGIONS[rk]
    for L in S["market"]+S["owned"]:
        spec=TYPE_SPEC[L["type"]]
        # 유형별 시세 변동
        if L["type"]=="아파트":
            ch=random.uniform(*spec["appr"])+R["apt_trend"]+news.get("apt_boost",0)
        else:
            ch=random.uniform(*spec["appr"])+R["yield_trend"]
        # 뉴스 전체 델타
        ch+=news["delta"]
        # 특수 뉴스
        if L["type"]=="빌라" and news.get("villa_hit"): ch+=news["villa_hit"]
        L["current"]=max(10000,int(L["current"]*(1+ch)))
        if "fair" in L: L["fair"]=max(10000,int(L["fair"]*(1+ch*0.6)))
        # 상가 월세 부스트
        if L["type"]=="상가" and news.get("rent_boost"):
            L["monthly"]=int(L["monthly"]*(1+news["rent_boost"]))

def make_quiz(method):
    opts=list(APPRAISAL.keys()); random.shuffle(opts)
    return {"answer":method,"definition":APPRAISAL[method]["def"],"options":opts,"tries":0}

def turn_finance():
    """연 단위 정산 — 자본 폭증 버그 수정: 소득 연1배만"""
    interest_year=int(S["debt"]*(S["loan_rate"]/100))
    S["total_interest"]+=interest_year
    rent_year=sum(L["monthly"]*12 for L in S["owned"])
    net=S["income_year"]+rent_year-interest_year
    S["capital"]+=net
    # 이자가 (소득+임대)를 초과하는 영끌 상태 → HP 감소
    if interest_year > S["income_year"]+rent_year:
        over=interest_year-(S["income_year"]+rent_year)
        S["hp"]=max(0,S["hp"]-max(5,min(25,over//1000)))

def new_turn():
    S["news"]=S["next_news"] or random.choice(NEWS_POOL)
    S["next_news"]=random.choice(NEWS_POOL)
    apply_market(S["news"], S["region"])
    if S["news"]["rate"]: S["loan_rate"]=max(1.0,S["loan_rate"]+S["news"]["rate"])
    if S["news"]["hp"]: S["hp"]=max(0,S["hp"]-S["news"]["hp"])
    scout(S["region"])
    turn_finance()
    S["selected"]=None; S["quiz"]=None; S["appraised"]=None; S["appraisal_steps"]=[]; S["appraisal_method"]=None
    if S["hp"]<=0: S["game_over"]=True; S["phase"]="end"

def do_appraise(method,L):
    cap=round(random.uniform(0.04,0.065),3)
    if method=="수익환원법":
        annual=L["monthly"]*12
        v=int(annual/cap)
        steps=[f"1. 연 임대료: {L['monthly']:,}만 × 12 = {annual:,}만원",
               f"2. 환원율 {cap*100:.1f}% 적용",
               f"🎯 적정가치 = {annual:,} ÷ {cap*100:.1f}% = {v:,}만원"]
        good = L["type"] in APPRAISAL["수익환원법"]["best_for"]
        tip = "✅ 월세수익형 매물에 적합한 평가법!" if good else "⚠️ 시세차익형(아파트)엔 부정확할 수 있어요"
    elif method=="거래사례비교법":
        adj=round(random.uniform(0.95,1.15),2); v=int(L["current"]*adj)
        steps=[f"1. 인근 유사 거래 기준가: {L['current']:,}만원",
               f"2. 입지·층·향 보정계수 {adj:.2f} 적용",
               f"🎯 적정가치 = {v:,}만원"]
        good = L["type"]=="아파트"
        tip = "✅ 아파트(시세차익형)에 가장 적합!" if good else "📊 거래사례가 충분하면 유효해요"
    else:  # 원가법 — 항상 불리
        land=int(L["current"]*0.50); build=int(L["current"]*0.45)
        dep=int(build*random.uniform(0.25,0.45))  # 감가 크게
        v=land+build-dep
        steps=[f"1. 토지가격: {land:,}만원",
               f"2. 건축비 {build:,}만 − 감가상각 {dep:,}만원",
               f"🎯 재조달원가 = {v:,}만원 (시장가 대비 낮음)"]
        tip = "⚠️ 원가법은 시장 프리미엄·입지 가치를 반영 못해 항상 낮게 나와요. 통건물 매입이 아니면 실거래엔 부적합!"
    return v,steps,tip

def buy(lid):
    L=next(x for x in S["market"] if x["id"]==lid)
    cost=L["current"]  # 매매가 (보증금은 별도 회수 개념이라 단순화)
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
# CSS · Navy&Red + 밝은 배경 + sticky 스탯 + 폰트 통일(13px)
# ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Urbanist:wght@400;600;700;900&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
html,body,.stApp{font-family:'Urbanist','Noto Sans KR',sans-serif !important;
    background:#16273f !important;color:#eaf0f8 !important;font-size:13px;}
#MainMenu,footer{display:none !important;}
.main .block-container{padding:1rem 1.5rem 2rem !important;max-width:1500px !important;}
/* 전역 최소 폰트 13px 통일 */
.stApp p,.stApp span,.stApp div,.stApp label,.stApp button,.stApp td,.stApp th,.stCaption,
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{font-size:13px !important;}
.g-title{font-size:22px !important;font-weight:900;color:#fff;display:flex;align-items:center;gap:8px;margin-bottom:2px;}
.g-sub{font-size:13px !important;color:#9fb4d0;margin-bottom:12px;}

/* 밝은 하늘색 배경 컨테이너 (제목~보유매물) - 시장 디스플레이와 확연히 구분 */
.bright-bg{background:linear-gradient(160deg,#3d6fa5 0%,#4a7fb8 100%);
    border:1px solid #6a9fd0;border-radius:18px;padding:18px;margin-bottom:14px;}

.panel{background:#28456680;border:1px solid #3a5a80;border-radius:14px;padding:14px 16px;margin-bottom:12px;}
.panel-red{background:#284566;border:1px solid #FF4136;border-radius:14px;padding:14px 16px;margin-bottom:12px;}
.ptitle{font-size:14px !important;font-weight:700;color:#FF6b5e;margin-bottom:10px;display:flex;align-items:center;gap:6px;}

/* sticky 스탯 */
.sticky-stat{position:sticky;top:0;z-index:999;background:#16273f;
    border:1px solid #3a5a80;border-radius:14px;padding:10px;margin-bottom:12px;box-shadow:0 6px 20px rgba(0,0,0,.45);}
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;}
.stat-card{background:#2d4a6b;border:1px solid #3a5a80;border-radius:10px;padding:7px 8px;text-align:center;}
.stat-card .sl{font-size:11px !important;color:#9fb4d0;margin-bottom:2px;}
.stat-card .sv{font-size:14px !important;font-weight:800;color:#fff;}
.sv.danger{color:#FF6b5e;} .sv.warn{color:#FFC233;}

.news{border-radius:12px;padding:12px 14px;margin-bottom:10px;}
.news-good{background:rgba(46,204,113,.14);border:1px solid #2ecc71;}
.news-bad{background:rgba(255,99,72,.14);border:1px solid #FF6347;}
.news-head{font-size:14px !important;font-weight:700;color:#fff;margin-bottom:6px;}
.news-info{font-size:13px !important;color:#cfe0f2;padding:2px 0;}

.li-card{background:#2d4a6b;border:1px solid #3a5a80;border-radius:12px;padding:11px 13px;margin-bottom:7px;}
.li-card.sel{border-color:#FF4136;background:#34557a;}
.li-name{font-size:13px !important;font-weight:700;color:#fff;}
.li-tag{font-size:11px !important;font-weight:700;padding:1px 8px;border-radius:100px;margin-left:6px;}
.tag-cap{background:rgba(52,152,219,.25);color:#5dade2;}
.tag-rent{background:rgba(46,204,113,.25);color:#58d68d;}
.li-price{font-size:13px !important;color:#bdd0e8;margin-top:3px;}

.quiz-box{background:#34557a;border:1px solid #FF4136;border-radius:12px;padding:14px;margin:10px 0;}
.quiz-def{font-size:13px !important;color:#e4eef8;line-height:1.7;background:#1a2e4a;border-radius:10px;padding:11px;margin-bottom:8px;border:1px dashed #4a6a90;}
.ap-box{background:#34557a;border:1px solid #2ecc71;border-radius:12px;padding:14px;margin:10px 0;}
.ap-step{font-size:13px !important;color:#cfe0f2;padding:4px 0;border-bottom:1px solid #3a5a80;}
.ap-step:last-child{border-bottom:none;font-size:14px !important;font-weight:800;color:#2ecc71;padding-top:8px;}

.inv-item{border-radius:10px;padding:9px 11px;margin-bottom:6px;font-size:13px !important;font-weight:600;}
.inv-profit{background:rgba(46,204,113,.12);border:1px solid #2ecc71;}
.inv-loss{background:rgba(255,99,72,.12);border:1px solid #FF6347;}

.display{background:#284566;border:1px solid #3a5a80;border-radius:14px;padding:16px;}
.disp-item{font-size:13px !important;color:#cfe0f2;padding:6px 0;border-bottom:1px solid #3a5a80;}
.disp-item:last-child{border-bottom:none;}
.disp-label{color:#9fb4d0;font-size:12px !important;}
.forecast{background:rgba(255,194,51,.12);border:1px solid #FFC233;border-radius:12px;padding:13px;margin-top:10px;}
.forecast-head{font-size:13px !important;font-weight:700;color:#FFC233;margin-bottom:6px;}
.forecast-body{font-size:13px !important;color:#f0e0b0;line-height:1.6;}
.log-item{font-size:12px !important;color:#9fb4d0;padding:3px 0;border-bottom:1px solid #2a4565;}

.stButton>button{font-family:'Urbanist','Noto Sans KR',sans-serif !important;font-weight:700 !important;font-size:13px !important;
    border-radius:10px !important;background:#2d4a6b !important;border:1px solid #3a5a80 !important;
    color:#fff !important;transition:.12s !important;}
.stButton>button:hover{background:#FF4136 !important;border-color:#FF4136 !important;transform:translateY(-1px);}
[data-testid="stMetric"]{background:#284566;border:1px solid #3a5a80;border-radius:12px;padding:10px 14px;}
[data-testid="stMetricValue"]{color:#fff !important;} [data-testid="stMetricLabel"]{color:#9fb4d0 !important;}

/* 설명서 팝업 (반투명) */
.manual-pop{background:#1a2e4af2;border:2px solid #FF4136;border-radius:16px;padding:20px 24px;margin-bottom:14px;backdrop-filter:blur(6px);}
.manual-pop h4{color:#FF6b5e;font-size:15px !important;margin:0 0 12px;}
.manual-cols{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
.manual-item{font-size:13px !important;color:#e4eef8;padding:6px 0;line-height:1.6;display:flex;gap:10px;}
.manual-item .num{color:#FF6b5e;font-weight:800;flex:0 0 22px;}

.intro-hero{text-align:center;padding:30px 0 10px;}
.intro-stage{width:100%;min-height:620px;border-radius:18px;overflow:hidden;
    display:flex;flex-direction:column;justify-content:flex-end;margin-bottom:10px;
    box-shadow:0 8px 32px rgba(0,0,0,.4);}
.intro-overlay{padding:0 22px 22px;}
.intro-manual{background:rgba(16,28,48,.82);border:1.5px solid #FF4136;border-radius:14px;
    padding:16px 20px;backdrop-filter:blur(4px);}
.intro-manual h4{color:#FF8b7e;font-size:15px !important;margin:0 0 10px;font-weight:800;}
.intro-logo{font-size:40px !important;font-weight:900;color:#fff;letter-spacing:-0.02em;}
.intro-logo .red{color:#FF6b5e;}
.intro-tag{font-size:14px !important;color:#9fb4d0;margin-top:8px;}
.region-card{background:#284566;border:2px solid #3a5a80;border-radius:16px;padding:20px;text-align:center;height:100%;}
.rc-icon{font-size:38px !important;} .rc-name{font-size:19px !important;font-weight:900;color:#fff;margin-top:6px;}
.rc-level{display:inline-block;font-size:12px !important;font-weight:700;padding:2px 12px;border-radius:100px;margin:6px 0;}
.rc-desc{font-size:12px !important;color:#9fb4d0;line-height:1.6;}

.report-hero{text-align:center;padding:24px;border-radius:18px;margin-bottom:20px;}
/* 결과 이미지 풀 배경 + 카드 오버레이 */
.result-stage{width:100%;min-height:600px;border-radius:18px;overflow:hidden;
    display:flex;align-items:center;justify-content:center;padding:30px 20px;margin-bottom:20px;
    box-shadow:0 8px 32px rgba(0,0,0,.45);}
.result-card{background:rgba(12,22,38,.86);border:2.5px solid #2ecc71;border-radius:18px;
    padding:24px 28px 22px;max-width:480px;width:100%;text-align:center;backdrop-filter:blur(6px);
    box-shadow:0 12px 40px rgba(0,0,0,.5);position:relative;}
.result-badge{display:inline-block;color:#fff;font-weight:900;font-size:15px !important;
    padding:4px 22px;border-radius:100px;margin-bottom:14px;letter-spacing:.05em;}
.result-headline{font-size:42px !important;font-weight:900;line-height:1.1;text-shadow:0 2px 14px rgba(0,0,0,.6);}
.result-sub{font-size:14px !important;color:#dce6f2;margin:8px 0 18px;font-weight:600;}
.result-rows{text-align:left;}
.rrow{display:flex;justify-content:space-between;align-items:center;padding:9px 4px;
    border-bottom:1px solid rgba(255,255,255,.1);font-size:14px !important;color:#cfe0f2;font-weight:600;}
.rrow .rval{font-weight:800;color:#fff;font-size:15px !important;}
.rrow.total{border-bottom:none;margin-top:6px;padding-top:12px;font-size:15px !important;}
.report-big{font-size:52px !important;font-weight:900;line-height:1;}
.report-label{font-size:14px !important;margin-top:10px;font-weight:600;}
.profit{background:linear-gradient(135deg,rgba(46,204,113,.15),rgba(46,204,113,.05));border:2px solid #2ecc71;}
.profit .report-big{color:#2ecc71;} .profit .report-label{color:#82e0aa;}
.loss{background:linear-gradient(135deg,rgba(255,99,72,.15),rgba(255,99,72,.05));border:2px solid #FF6347;}
.loss .report-big{color:#FF6347;} .loss .report-label{color:#ff9b8b;}
.calc-table{width:100%;border-collapse:collapse;margin:14px 0;}
.calc-table td{padding:10px 14px;border-bottom:1px solid #3a5a80;font-size:14px !important;color:#e4eef8;}
.calc-table td.r{text-align:right;font-weight:700;color:#fff;}
.calc-table tr.total td{border-top:2px solid #FF4136;border-bottom:none;font-size:16px !important;font-weight:900;color:#fff;padding-top:14px;}
</style>
""", unsafe_allow_html=True)

MANUAL_ITEMS = [
    ("목표","초기자본으로 10턴(10년) 동안 순자산을 최대한 불리세요. 지역마다 난이도가 다릅니다."),
    ("시장 원리","아파트는 <b>시세차익형</b>(가격 상승), 오피스텔·상가·빌라는 <b>월세수익형</b>입니다. 뉴스가 큰 변수예요!"),
    ("매물 스카우팅","매 턴 무작위 3개 매물만 공개됩니다. 호가와 적정가치를 비교하세요."),
    ("감정평가 퀴즈","평가법 정의를 읽고 이름을 맞히면 <b>영구 해금</b>. 유형에 맞는 평가법을 쓰세요 (원가법은 시장가 반영이 약함!)."),
    ("영끌(대출)","자본이 부족해도 매수 가능. 단, 이자가 소득+월세를 넘으면 멘탈(HP)이 깎여 0이면 파산!"),
    ("시장 예측","우측 '다음 턴 예고'를 보고 전략적으로 매수/매도하세요."),
    ("실질 수익","종료 후 대출이자와 인플레이션을 뺀 '진짜 수익'으로 평가됩니다."),
]

def render_manual_popup():
    half1="".join(f'<div class="manual-item"><span class="num">{i+1}</span><span><b>{t}</b> — {d}</span></div>'
                  for i,(t,d) in enumerate(MANUAL_ITEMS[:4]))
    half2="".join(f'<div class="manual-item"><span class="num">{i+5}</span><span><b>{t}</b> — {d}</span></div>'
                  for i,(t,d) in enumerate(MANUAL_ITEMS[4:]))
    st.markdown(f'''<div class="manual-pop"><h4>📖 게임 설명서</h4>
      <div class="manual-cols"><div class="manual-col">{half1}</div><div class="manual-col">{half2}</div></div>
    </div>''', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# 화면 A: 인트로
# ─────────────────────────────────────────────────────
if S["phase"]=="intro":
    intro_img=img_b64("intro.png")
    half1="".join(f'<div class="manual-item"><span class="num">{i+1}</span><span><b>{t}</b> — {d}</span></div>'
                  for i,(t,d) in enumerate(MANUAL_ITEMS[:4]))
    half2="".join(f'<div class="manual-item"><span class="num">{i+5}</span><span><b>{t}</b> — {d}</span></div>'
                  for i,(t,d) in enumerate(MANUAL_ITEMS[4:]))
    manual_html=f'''<div class="intro-manual"><h4>📖 게임 설명서</h4>
      <div class="manual-cols"><div class="manual-col">{half1}</div><div class="manual-col">{half2}</div></div></div>'''

    if intro_img:
        # 이미지를 배경으로, 위쪽엔 이미지가 보이고 아래쪽에 설명서 오버레이
        st.markdown(f'''
        <div class="intro-stage" style="background:linear-gradient(to bottom, rgba(22,39,63,0) 35%, rgba(22,39,63,.55) 55%, rgba(22,39,63,.97) 100%), url('{intro_img}') top center/cover;">
          <div class="intro-overlay">{manual_html}</div>
        </div>''', unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="intro-hero">
          <div class="intro-logo">🏠 슬기로운 <span class="red">영끌</span>생활</div>
          <div class="intro-tag">부동산 투자 전략 시뮬레이션 · 시장 원리를 게임으로 배우다</div>
        </div>{manual_html}""", unsafe_allow_html=True)

    st.markdown('<div style="font-size:17px;font-weight:800;color:#fff;margin:4px 0 8px;text-align:center;">🗺️ 지역을 선택하고 START</div>', unsafe_allow_html=True)
    cols=st.columns(3)
    lc={"서울":"#3498db","대전":"#FFC233","제주":"#FF6347"}
    for col,(k,r) in zip(cols,REGIONS.items()):
        with col:
            c=lc[k]
            st.markdown(f"""<div class="region-card"><div class="rc-icon">{r['icon']}</div>
              <div class="rc-name">{k}</div><div class="rc-level" style="background:{c}22;color:{c};">{r['level']}</div>
              <div class="rc-desc">{r['desc']}<br><b style="color:#fff;">초기자본 {won(r['capital'])}</b></div></div>""", unsafe_allow_html=True)
            if st.button(f"▶ {k} START", key=f"go_{k}", use_container_width=True):
                S["region"]=k; S["phase"]="play"; S["capital"]=r["capital"]
                ph=st.empty()
                for msg in ["🗺️ 지도 로딩 중...","🏢 매물 스카우팅 중...","📊 시장 분석 중..."]:
                    ph.markdown(f'<div style="text-align:center;padding:40px;font-size:18px;font-weight:700;color:#FF6b5e;">{msg}</div>', unsafe_allow_html=True)
                    time.sleep(0.5)
                ph.empty()
                S["next_news"]=random.choice(NEWS_POOL); new_turn(); st.rerun()

# ─────────────────────────────────────────────────────
# 화면 B: 플레이
# ─────────────────────────────────────────────────────
elif S["phase"]=="play":
    rk=S["region"]; R=REGIONS[rk]
    top1,top2=st.columns([3,1])
    with top1:
        st.markdown(f'<div class="g-title">{R["icon"]} 슬기로운 영끌생활 — {rk} <span style="color:#FF6b5e;font-size:14px;">{R["level"]}</span></div>', unsafe_allow_html=True)
    with top2:
        if st.button("📖 설명서 " + ("닫기" if S["show_manual"] else "열기"), use_container_width=True):
            S["show_manual"]=not S["show_manual"]; st.rerun()

    if S["show_manual"]:
        render_manual_popup()

    # sticky 스탯 (스크롤 따라옴)
    mi=int(S["debt"]*(S["loan_rate"]/100)/12); rent=sum(L["monthly"] for L in S["owned"])
    hpc="danger" if S["hp"]<=30 else ("warn" if S["hp"]<=60 else "")
    st.markdown(f"""<div class="sticky-stat"><div class="stat-grid">
      <div class="stat-card"><div class="sl">자본금</div><div class="sv">{won(S['capital'])}</div></div>
      <div class="stat-card"><div class="sl">대출</div><div class="sv {'danger' if S['debt']>0 else ''}">{won(S['debt'])}</div></div>
      <div class="stat-card"><div class="sl">월이자</div><div class="sv {'danger' if mi>0 else ''}">{won(mi)}</div></div>
      <div class="stat-card"><div class="sl">대출이율</div><div class="sv">{S['loan_rate']:.1f}%</div></div>
      <div class="stat-card"><div class="sl">멘탈</div><div class="sv {hpc}">{S['hp']}</div></div>
      <div class="stat-card"><div class="sl">월세수입</div><div class="sv">{won(rent)}</div></div>
      <div class="stat-card"><div class="sl">보유</div><div class="sv">{len(S['owned'])}건</div></div>
      <div class="stat-card"><div class="sl">턴</div><div class="sv">{S['turn']}/10</div></div>
    </div></div>""", unsafe_allow_html=True)

    left,right=st.columns([1.15,0.85],gap="large")

    with left:
        st.markdown('<div class="bright-bg">', unsafe_allow_html=True)
        if S["news"]:
            nc="news-good" if S["news"]["mood"]=="good" else "news-bad"
            st.markdown(f"""<div class="news {nc}"><div class="news-head">{S['news']['head']}</div>
              <div class="news-info">📌 {S['news']['i1']}</div>
              <div class="news-info">📌 {S['news']['i2']}</div></div>""", unsafe_allow_html=True)

        st.markdown('<div class="ptitle">🏢 이번 턴 매물 (3건 스카우팅)</div>', unsafe_allow_html=True)
        for L in S["market"]:
            sel=S["selected"]==L["id"]
            tcls="tag-cap" if L["tag"]=="시세차익형" else "tag-rent"
            st.markdown(f"""<div class="li-card {'sel' if sel else ''}">
              <div class="li-name">{L['name']} · {L['type']}<span class="li-tag {tcls}">{L['tag']}</span></div>
              <div class="li-price">호가 {won(L['current'])} · {L['area']}㎡ · 월세 {L['monthly']}만 (보증금 {won(L['deposit'])})</div>
            </div>""", unsafe_allow_html=True)
            if st.button("이 매물 선택", key=f"sel_{L['id']}"):
                S["selected"]=L["id"]; S["quiz"]=None; S["appraised"]=None; S["appraisal_steps"]=[]; st.rerun()

        # 감정평가 도구창
        if S["selected"] and any(x["id"]==S["selected"] for x in S["market"]):
            L=next(x for x in S["market"] if x["id"]==S["selected"])
            st.markdown('<div class="ptitle" style="margin-top:14px;">🎯 감정평가 도구</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:13px;color:#bdd0e8;margin-bottom:8px;">선택: <b style="color:#fff;">{L["name"]}</b> ({L["tag"]}) · 호가 {won(L["current"])}</div>', unsafe_allow_html=True)

            if S["appraised"] is None:
                st.caption(f"해금된 도구: {', '.join(S['unlocked']) if S['unlocked'] else '없음 (퀴즈로 해금)'}")
                ac=st.columns(3)
                for i,(m,info) in enumerate(APPRAISAL.items()):
                    with ac[i]:
                        unlocked=m in S["unlocked"]
                        if st.button(f"{info['icon']} {m}" + (" ✓" if unlocked else " 🔒"), key=f"tool_{m}"):
                            if unlocked:
                                ph=st.empty()
                                for d in [".","..","..."]:
                                    ph.markdown(f'<div style="text-align:center;padding:12px;font-weight:800;color:#FF6b5e;">🎲 감정평가 중{d}</div>', unsafe_allow_html=True)
                                    time.sleep(0.4)
                                v,steps,tip=do_appraise(m,L); S["appraised"]=v; S["appraisal_steps"]=steps; S["appraisal_method"]=(m,tip)
                                ph.empty(); st.rerun()
                            else:
                                S["quiz"]=make_quiz(m); st.rerun()
                if S["quiz"]:
                    q=S["quiz"]
                    st.markdown(f'<div class="quiz-box"><div style="font-weight:800;color:#fff;margin-bottom:6px;">📖 이 설명은 어떤 감정평가 방식?</div><div class="quiz-def">{q["definition"]}</div></div>', unsafe_allow_html=True)
                    oc=st.columns(3)
                    for i,opt in enumerate(q["options"]):
                        with oc[i]:
                            if st.button(opt, key=f"ans_{opt}_{q['tries']}"):
                                if opt==q["answer"]:
                                    if q["answer"] not in S["unlocked"]: S["unlocked"].append(q["answer"])
                                    S["quiz"]=None; st.rerun()
                                else:
                                    S["hp"]=max(0,S["hp"]-5); S["quiz"]["tries"]+=1
                                    if S["hp"]<=0: S["game_over"]=True; S["phase"]="end"
                                    st.rerun()
                    if q["tries"]>0: st.warning(f"❌ 오답! HP -5 (현재 {S['hp']}) · 다시 시도")
            else:
                st.markdown('<div class="ap-box">'+"".join(f'<div class="ap-step">{s}</div>' for s in S["appraisal_steps"])+'</div>', unsafe_allow_html=True)
                if S["appraisal_method"]:
                    m,tip=S["appraisal_method"]
                    if "⚠️" in tip: st.warning(tip)
                    else: st.info(tip)
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

        # 인벤토리
        st.markdown('<div class="ptitle" style="margin-top:14px;">🏦 보유 매물 (인벤토리)</div>', unsafe_allow_html=True)
        if S["owned"]:
            for i,L in enumerate(S["owned"]):
                p=L["current"]-L["purchase_price"]
                st.markdown(f'<div class="inv-item {"inv-profit" if p>=0 else "inv-loss"}">{"🟢" if p>=0 else "🔴"} {L["name"]} ({L["type"]}) · 현재 {won(L["current"])} · 월세 {L["monthly"]}만 · 손익 {"+" if p>=0 else ""}{won(p)}</div>', unsafe_allow_html=True)
                if st.button("매도",key=f"sl_{i}"): sell(i); st.rerun()
        else:
            st.caption("아직 보유한 매물이 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)  # bright-bg 닫기

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⏭️ 다음 턴으로 진행", use_container_width=True): advance()

    with right:
        st.markdown('<div class="ptitle">📊 시장 디스플레이</div>', unsafe_allow_html=True)
        total_asset=S["capital"]+sum(L["current"] for L in S["owned"])
        st.markdown(f"""<div class="display">
          <div class="disp-item"><span class="disp-label">총 자산</span><br>{won(total_asset)}</div>
          <div class="disp-item"><span class="disp-label">순자산 (자산-부채)</span><br>{won(total_asset-S['debt'])}</div>
          <div class="disp-item"><span class="disp-label">누적 대출이자</span><br>{won(S['total_interest'])}</div>
          <div class="disp-item"><span class="disp-label">해금 감정평가</span><br>{', '.join(S['unlocked']) if S['unlocked'] else '없음'}</div>
        </div>""", unsafe_allow_html=True)
        if S["next_news"]:
            nn=S["next_news"]
            arrow="📈 상승 신호" if nn["mood"]=="good" else "📉 하락 신호"
            st.markdown(f"""<div class="forecast"><div class="forecast-head">🔮 다음 턴 시장 예측</div>
              <div class="forecast-body">{arrow}<br>예상 이슈: {nn['head'].split(' ',1)[1] if ' ' in nn['head'] else nn['head']}<br>
              <span style="color:#FFC233;">{nn['i1']} · {nn['i2']}</span></div></div>""", unsafe_allow_html=True)
            st.caption("💡 예측을 보고 이번 턴 매수/매도를 결정하세요")
        if S["log"]:
            st.markdown('<div class="ptitle" style="margin-top:12px;">📜 거래 기록</div>', unsafe_allow_html=True)
            for e in reversed(S["log"][-6:]):
                st.markdown(f'<div class="log-item">{e}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# 화면 C: 결산 리포트
# ─────────────────────────────────────────────────────
elif S["phase"]=="end":
    if not S.get("_report_shown"):
        ph=st.empty()
        for msg in ["📊 최종 자산 집계 중...","🧮 실질 수익 계산 중...","📑 리포트 생성 중..."]:
            ph.markdown(f'<div style="text-align:center;padding:60px;font-size:20px;font-weight:800;color:#FF6b5e;">{msg}</div>', unsafe_allow_html=True)
            time.sleep(0.6)
        ph.empty(); S["_report_shown"]=True

    assets=S["capital"]+sum(L["current"] for L in S["owned"])
    net_worth=assets-S["debt"]
    start=REGIONS[S["region"]]["capital"]
    inflation_adj=int(start*((1+INFLATION)**10-1))
    nominal=net_worth-start
    real=nominal-S["total_interest"]-inflation_adj
    rate=real/start*100
    win = real>=0 and not S.get("game_over")

    cls="profit" if win else "loss"; sign="+" if real>=0 else ""
    result_img = img_b64("win.png") if win else img_b64("lose.png")

    # 등급 메시지
    if S.get("game_over"): headline,sub="💔 파산했다…","대출 이자를 감당하지 못했습니다"
    elif rate>=40: headline,sub="🏆 성공했다!","당신은 현명한 영끌러가 되었습니다!"
    elif rate>=10: headline,sub="💼 성공했다!","인플레이션을 이기는 실질 수익을 냈습니다!"
    elif rate>=0: headline,sub="👍 본전 사수","원금은 지켰지만 인플레를 겨우 따라갔어요"
    else: headline,sub="📉 실패했다…","다시 전략을 세워 도전해보세요!"

    acc = "#2ecc71" if win else "#FF4136"
    bigcol = "#7CFFAA" if win else "#FF8b7b"

    if result_img:
        ov = "rgba(14,28,20,.62)" if win else "rgba(34,12,12,.66)"
        st.markdown(f'''
        <div class="result-stage" style="background:linear-gradient({ov},{ov}),url('{result_img}') center/cover;">
          <div class="result-card" style="border-color:{acc};">
            <div class="result-badge" style="background:{acc};">결과</div>
            <div class="result-headline" style="color:{bigcol};">{headline}</div>
            <div class="result-sub">{sub}</div>
            <div class="result-rows">
              <div class="rrow"><span>💰 실질 수익</span><span class="rval" style="color:{bigcol};">{sign}{won(real)}</span></div>
              <div class="rrow"><span>🏠 보유 자산 가치</span><span class="rval">{won(assets)}</span></div>
              <div class="rrow"><span>📊 투자 수익률</span><span class="rval" style="color:{bigcol};">{rate:+.1f}%</span></div>
              <div class="rrow"><span>📑 총 대출 (부채)</span><span class="rval">-{won(S['debt'])}</span></div>
              <div class="rrow total" style="border-top:2px solid {acc};"><span>🪙 최종 순자산</span><span class="rval" style="color:{bigcol};">{won(net_worth)}</span></div>
            </div>
          </div>
        </div>''', unsafe_allow_html=True)
    else:
        st.markdown('<div class="g-title">🏁 최종 수익 리포트</div>', unsafe_allow_html=True)
        if S.get("game_over"): st.error("💔 파산 엔딩!")
        st.markdown(f"""<div class="report-hero {cls}">
          <div class="report-big">{sign}{won(real)}</div>
          <div class="report-label">실질 수익 (대출이자·인플레이션 반영)</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="ptitle" style="margin-top:18px;">🧮 실질 수익 상세 계산</div>', unsafe_allow_html=True)
    st.markdown(f"""<table class="calc-table">
      <tr><td>최종 순자산 (자산 − 부채)</td><td class="r">{won(net_worth)}</td></tr>
      <tr><td>(−) 초기 자본금</td><td class="r">− {won(start)}</td></tr>
      <tr><td>= 명목 수익</td><td class="r">{'+' if nominal>=0 else ''}{won(nominal)}</td></tr>
      <tr><td>(−) 누적 대출 이자</td><td class="r">− {won(S['total_interest'])}</td></tr>
      <tr><td>(−) 인플레이션 보정 (연 {INFLATION*100:.1f}%·10년)</td><td class="r">− {won(inflation_adj)}</td></tr>
      <tr class="total"><td>= 실질 수익</td><td class="r">{sign}{won(real)}</td></tr>
    </table>""", unsafe_allow_html=True)

    if S.get("game_over"): grade,msg="💔 파산","대출 관리에 실패했습니다. 다음엔 영끌을 조심하세요!"
    elif rate>=40: grade,msg="🏆 부동산 마스터","시장 원리와 감정평가를 완벽히 활용했습니다!"
    elif rate>=10: grade,msg="💼 유능한 투자자","인플레이션을 이기는 실질 수익을 냈습니다!"
    elif rate>=0: grade,msg="👍 본전 사수","원금은 지켰지만 인플레를 겨우 따라갔어요."
    else: grade,msg="📚 수업료를 낸 새내기","손실도 경험! 시장 원리의 중요성을 배웠습니다."
    st.markdown(f"""<div class="panel-red" style="text-align:center;margin-top:8px;">
      <div style="font-size:22px;font-weight:900;color:#fff;">{grade}</div>
      <div style="font-size:13px;color:#bdd0e8;margin-top:6px;">{msg}</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="ptitle">📜 전체 거래 기록</div>', unsafe_allow_html=True)
    for e in S["log"]: st.markdown(f'<div class="log-item">{e}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 다시 시작", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
