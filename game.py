"""
슬기로운 영끌생활 · 부동산 투자 전략 게임
감정평가 획득 퀴즈(도구 게이팅) · 영끌 생존 로직 · 픽셀/일러스트 감성
"""
import streamlit as st
import random, time

st.set_page_config(page_title="슬기로운 영끌생활", page_icon="🏠",
                   layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────────────
# 데이터
# ─────────────────────────────────────────────────────
REGIONS = {
    "서울": {"desc":"높은 수요·강한 상승 모멘텀","level":"초급","vol":0.07,"trend":0.05,"icon":"🏙️",
             "img":"seoul_map.png","bg":"linear-gradient(135deg,#a8d5a8 0%,#7cb87c 50%,#5a9e5a 100%)"},
    "대전": {"desc":"신도시 개발·구도심 리스크","level":"중급","vol":0.12,"trend":0.01,"icon":"🌆",
             "img":"daejeon_map.png","bg":"linear-gradient(135deg,#c2d6a0 0%,#9bbf6f 50%,#7aa34f 100%)"},
    "제주": {"desc":"수요 한정·유동성 낮음","level":"고급","vol":0.18,"trend":-0.01,"icon":"🏝️",
             "img":"jeju_map.png","bg":"linear-gradient(135deg,#a0d6c2 0%,#6fbf9b 50%,#4fa37a 100%)"},
}
BRANDS = ["e편한세상","래미안","힐스테이트","자이","아이파크","롯데캐슬","푸르지오","더샵"]

# 감정평가 3방식 정의 (퀴즈용)
APPRAISAL = {
    "수익환원법": {"icon":"💰","def":"부동산이 장래 산출할 것으로 기대되는 순수익(임대료)을 환원율로 나누어 가치를 구하는 방식","calc":"income"},
    "거래사례비교법":{"icon":"📊","def":"대상과 유사한 인근의 실제 거래 사례를 수집해 입지·층·향 등을 보정하여 가치를 구하는 방식","calc":"compare"},
    "원가법":     {"icon":"🏗️","def":"대상을 다시 짓는다고 가정해 토지가격에 건축비를 더하고 감가상각을 뺀 재조달원가로 가치를 구하는 방식","calc":"cost"},
}

NEWS_POOL = [
    {"head":"📈 한국은행 기준금리 0.25%p 인하","effect":"대출이율 -0.5% · 시장 회복 기대","mood":"good","delta":0.06,"rate":-0.5,"hp":0},
    {"head":"📉 기준금리 0.5%p 인상","effect":"대출이율 +1.0% · 이자 부담 가중 · HP -5","mood":"bad","delta":-0.08,"rate":1.0,"hp":5},
    {"head":"🚇 수도권 GTX 신규 노선 확정","effect":"역세권 수혜 · 전체 매물 +8%","mood":"good","delta":0.09,"rate":0,"hp":0},
    {"head":"🚨 토지거래허가구역 확대","effect":"갭투자 제한 · 매물 가치 -7%","mood":"bad","delta":-0.07,"rate":0,"hp":0},
    {"head":"🏗️ 재건축 안전진단 기준 완화","effect":"노후단지 호재 · 전체 +5%","mood":"good","delta":0.06,"rate":0,"hp":0},
    {"head":"💸 DSR 3단계 전면 시행","effect":"대출 한도 축소 · HP -10","mood":"bad","delta":-0.05,"rate":0,"hp":10},
    {"head":"🌊 전세 시장 안정세","effect":"임대수익 안정 · 소폭 상승","mood":"good","delta":0.03,"rate":0,"hp":0},
    {"head":"📰 미분양 8만 가구 돌파","effect":"공급 과잉 우려 · 매물 -6%","mood":"bad","delta":-0.07,"rate":0,"hp":0},
    {"head":"🏦 특례보금자리론 재출시","effect":"실수요 대출 완화 · 매수심리 개선","mood":"good","delta":0.04,"rate":-0.3,"hp":0},
    {"head":"📊 소비자물가 3% 돌파","effect":"인플레 헤지 수요 · 전체 +4%","mood":"good","delta":0.05,"rate":0,"hp":0},
]
POSITIONS = [(x,y) for x in range(4) for y in range(4)]

# ─────────────────────────────────────────────────────
# 세션
# ─────────────────────────────────────────────────────
def init():
    D = {"phase":"intro","region":None,"capital":100000,"debt":0,"loan_rate":5.0,
         "hp":100,"turn":1,"monthly_income":200,"listings":{},"owned":[],"news":None,
         "selected":None,"quiz":None,"tool_unlocked":None,"appraised":None,
         "appraisal_steps":[],"log":[],"game_over":False}
    for k,v in D.items():
        if k not in st.session_state: st.session_state[k]=v
init()
S = st.session_state

def pk(p): return f"{p[0]}_{p[1]}"

def won(v):
    v=int(v); neg=v<0; v=abs(v); eok=v//10000; man=v%10000
    s=(f"{eok}억 " if eok else "")+(f"{man:,}만" if man else "")
    return ("-" if neg else "")+(s.strip() or "0")

def new_listing(pos, rk):
    base=random.randint(50000,150000)
    fair=int(base*random.uniform(0.82,1.22))
    rent=int(base*random.uniform(0.035,0.055))
    area=random.randint(60,140)
    return {"name":random.choice(BRANDS),"type":random.choice(["아파트","오피스텔","상가","빌라"]),
            "base":base,"fair":fair,"current":base,"rent":rent,"area":area,
            "pos":pos,"owned":False,"purchase_price":0}

def spawn(rk,count=5):
    used=set(S["listings"].keys())|{pk(l["pos"]) for l in S["owned"]}
    avail=[p for p in POSITIONS if pk(p) not in used]
    random.shuffle(avail)
    for p in avail[:count]:
        S["listings"][pk(p)]=new_listing(p,rk)

def apply_delta(d):
    for k in S["listings"]:
        L=S["listings"][k]; n=random.uniform(-0.02,0.02)
        L["current"]=max(10000,int(L["current"]*(1+d+n)))
        L["fair"]=max(10000,int(L["fair"]*(1+d*0.5+n)))
    for L in S["owned"]:
        n=random.uniform(-0.02,0.02)
        L["current"]=max(10000,int(L["current"]*(1+d+n)))

def make_quiz(method):
    """method가 정답인 3지선다 — 정의를 보여주고 이름 맞히기"""
    options=list(APPRAISAL.keys())
    random.shuffle(options)
    return {"answer":method,"definition":APPRAISAL[method]["def"],"options":options,"tries":0}

def turn_finance():
    mi=int(S["debt"]*(S["loan_rate"]/100)/12)
    rent=sum(L["rent"] for L in S["owned"])
    net=S["monthly_income"]+rent-mi
    S["capital"]+=net
    if net<0:
        S["hp"]=max(0,S["hp"]-max(3,min(20,abs(net)//1000)))

def new_turn():
    S["news"]=random.choice(NEWS_POOL)
    apply_delta(S["news"]["delta"])
    if S["news"]["rate"]: S["loan_rate"]=max(1.0,S["loan_rate"]+S["news"]["rate"])
    if S["news"]["hp"]: S["hp"]=max(0,S["hp"]-S["news"]["hp"])
    spawn(S["region"],random.randint(1,3))
    turn_finance()
    S["selected"]=None; S["quiz"]=None; S["tool_unlocked"]=None
    S["appraised"]=None; S["appraisal_steps"]=[]
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

def buy(k):
    L=S["listings"][k]; cost=L["current"]
    if cost>S["capital"]:
        need=cost-S["capital"]; S["debt"]+=need; S["capital"]=0
        S["log"].append(f"턴{S['turn']}: {L['name']} 영끌매수 (대출 {won(need)})")
    else:
        S["capital"]-=cost; S["log"].append(f"턴{S['turn']}: {L['name']} 매수")
    L["owned"]=True; L["purchase_price"]=cost; S["owned"].append(L); del S["listings"][k]

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
# CSS (밝은 아이보리 + 픽셀/일러스트)
# ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&family=Galmuri11&display=swap');
html,body,.stApp{font-family:'Noto Sans KR',sans-serif !important;background:#FFFDF5 !important;color:#3a3226 !important;}
#MainMenu,footer{display:none !important;}
.main .block-container{padding:1rem 1.5rem 2rem !important;}
.g-title{font-size:22px;font-weight:900;color:#3a3226;display:flex;align-items:center;gap:8px;margin-bottom:2px;}
.g-sub{font-size:12px;color:#9a8f7a;margin-bottom:12px;}
.stat-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px;}
.stat-card{background:#fff;border:2px solid #ece3d0;border-radius:14px;padding:9px 10px;text-align:center;box-shadow:0 2px 0 #ece3d0;}
.stat-card .sl{font-size:11px;color:#a89c84;margin-bottom:3px;}
.stat-card .sv{font-size:15px;font-weight:800;color:#3a3226;}
.sv.danger{color:#e74c3c;} .sv.warn{color:#e67e22;}
.news-good{background:#f3fbf0;border:2px solid #7cc47c;border-radius:14px;padding:11px 14px;margin-bottom:10px;box-shadow:0 2px 0 #cfe8cf;}
.news-bad{background:#fdf2f0;border:2px solid #e89080;border-radius:14px;padding:11px 14px;margin-bottom:10px;box-shadow:0 2px 0 #f2d2cc;}
.news-head{font-size:14px;font-weight:800;color:#3a3226;margin-bottom:3px;}
.news-effect{font-size:12px;color:#6a6052;}
.quiz-box{background:#fffaf0;border:2px solid #f0c040;border-radius:14px;padding:14px 16px;margin:10px 0;box-shadow:0 2px 0 #f0e0b0;}
.quiz-def{font-size:13px;color:#5a5142;line-height:1.7;background:#fff;border-radius:10px;padding:10px 12px;margin-bottom:8px;border:1px dashed #d0c4a0;}
.appraisal-box{background:#f5f0ff;border:2px solid #9b7cd4;border-radius:14px;padding:14px;margin:10px 0;box-shadow:0 2px 0 #ddd0f0;}
.ap-step{font-size:12px;color:#5a5142;padding:4px 0;border-bottom:1px solid #e8e0d0;}
.ap-step:last-child{border-bottom:none;font-size:14px;font-weight:800;color:#7c4dff;padding-top:8px;}
.li-card{background:#fff;border:2px solid #ece3d0;border-radius:14px;padding:11px 13px;margin-bottom:7px;box-shadow:0 2px 0 #ece3d0;}
.li-card.sel{border-color:#f0a830;background:#fffaf0;box-shadow:0 2px 0 #f0d8a0;}
.li-name{font-size:14px;font-weight:800;color:#3a3226;}
.li-price{font-size:12px;color:#6a6052;margin-top:2px;}
.owned-item{border-radius:12px;padding:9px 11px;margin-bottom:6px;font-size:12px;font-weight:600;}
.owned-profit{background:#f3fbf0;border:2px solid #4caf50;}
.owned-loss{background:#fdf2f0;border:2px solid #e74c3c;}
.log-item{font-size:11px;color:#9a8f7a;padding:3px 0;border-bottom:1px solid #f2ece0;}

/* 픽셀 타일맵 */
.map-frame{border:4px solid #5a4a32;border-radius:12px;overflow:hidden;box-shadow:0 4px 0 #3a2e1e;background:#7cb87c;}
.map-grid{position:relative;width:100%;padding-bottom:100%;}
.map-inner{position:absolute;inset:0;display:grid;grid-template-columns:repeat(4,1fr);grid-template-rows:repeat(4,1fr);}
.tile{position:relative;display:flex;align-items:center;justify-content:center;
    background-image:radial-gradient(circle at 30% 30%, rgba(255,255,255,.08) 2px, transparent 2px),
        radial-gradient(circle at 70% 70%, rgba(0,0,0,.06) 2px, transparent 2px);
    background-size:14px 14px;border:1px solid rgba(0,0,0,.06);}
.bld{width:62%;height:62%;border-radius:6px;display:flex;flex-direction:column;align-items:center;justify-content:center;
    font-size:8px;font-weight:800;color:#fff;cursor:pointer;transition:.15s;
    image-rendering:pixelated;box-shadow:0 4px 0 rgba(0,0,0,.35);border:2px solid rgba(255,255,255,.5);}
.bld:hover{transform:translateY(-3px);box-shadow:0 7px 0 rgba(0,0,0,.35);}
.bld-avail{background:linear-gradient(135deg,#ff8a5c,#e8590c);}
.bld-sel{background:linear-gradient(135deg,#ffd54f,#ff9800);box-shadow:0 4px 0 rgba(0,0,0,.35),0 0 0 3px #fff,0 0 0 6px #ffd54f;}
.bld-profit{background:linear-gradient(135deg,#66bb6a,#2e7d32);border-color:#a5f5a5;}
.bld-loss{background:linear-gradient(135deg,#ef5350,#c62828);border-color:#ffb3b3;}
.bubble{position:absolute;top:2px;left:50%;transform:translateX(-50%);background:#fff;border:2px solid #5a4a32;
    border-radius:8px;padding:2px 6px;white-space:nowrap;font-size:9px;font-weight:800;z-index:5;box-shadow:0 2px 0 rgba(0,0,0,.2);}
.bubble.up{color:#2e7d32;} .bubble.down{color:#c62828;} .bubble.price{color:#3a3226;}
.tree{position:absolute;font-size:13px;opacity:.55;pointer-events:none;}
.map-legend{text-align:center;margin-top:8px;font-size:11px;color:#9a8f7a;}

.region-card{background:#fff;border:3px solid #ece3d0;border-radius:18px;padding:22px;text-align:center;box-shadow:0 4px 0 #ece3d0;height:100%;}
.rc-icon{font-size:42px;} .rc-name{font-size:20px;font-weight:900;color:#3a3226;margin-top:6px;}
.rc-level{display:inline-block;font-size:11px;font-weight:800;padding:2px 12px;border-radius:100px;margin:6px 0;}
.rc-desc{font-size:12px;color:#9a8f7a;line-height:1.6;}
.stButton>button{font-family:'Noto Sans KR',sans-serif !important;font-weight:800 !important;border-radius:12px !important;
    background:#fff !important;border:2px solid #d8ccb0 !important;color:#3a3226 !important;box-shadow:0 3px 0 #d8ccb0 !important;transition:.1s !important;}
.stButton>button:hover{background:#fff8e8 !important;border-color:#f0a830 !important;box-shadow:0 3px 0 #f0c060 !important;transform:translateY(-1px);}
[data-testid="stMetric"]{background:#fff;border:2px solid #ece3d0;border-radius:12px;padding:8px 12px;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# 화면 A: 인트로
# ─────────────────────────────────────────────────────
if S["phase"]=="intro":
    st.markdown('<div class="g-title">🏠 슬기로운 영끌생활</div>', unsafe_allow_html=True)
    st.markdown('<div class="g-sub">감정평가 퀴즈를 풀고 저평가 매물을 찾아라 · 영끌도 가능, 단 멘탈 관리는 필수!</div>', unsafe_allow_html=True)
    st.markdown("---")
    cols=st.columns(3)
    lc={"서울":"#3498db","대전":"#e67e22","제주":"#e74c3c"}
    for col,(k,r) in zip(cols,REGIONS.items()):
        with col:
            c=lc[k]
            st.markdown(f"""<div class="region-card"><div class="rc-icon">{r['icon']}</div>
              <div class="rc-name">{k}</div><div class="rc-level" style="background:{c}22;color:{c};">{r['level']}</div>
              <div class="rc-desc">{r['desc']}</div></div>""", unsafe_allow_html=True)
            if st.button(f"{k} 시작", key=f"go_{k}", use_container_width=True):
                S["region"]=k; S["phase"]="play"; spawn(k,5); new_turn(); st.rerun()

# ─────────────────────────────────────────────────────
# 화면 B: 플레이
# ─────────────────────────────────────────────────────
elif S["phase"]=="play":
    rk=S["region"]; R=REGIONS[rk]
    st.markdown(f'<div class="g-title">{R["icon"]} 슬기로운 영끌생활 — {rk} ({R["level"]})</div>', unsafe_allow_html=True)
    left,right=st.columns([1,1],gap="large")

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
            st.markdown(f'<div class="{nc}"><div class="news-head">{S["news"]["head"]}</div><div class="news-effect">💡 {S["news"]["effect"]}</div></div>', unsafe_allow_html=True)

        st.markdown("**🏢 매물 목록**")
        for k,L in list(S["listings"].items()):
            sel=S["selected"]==k
            st.markdown(f"""<div class="li-card {'sel' if sel else ''}">
              <div class="li-name">{L['name']} · {L['type']} ({L['area']}㎡)</div>
              <div class="li-price">호가 {won(L['current'])} · {int(L['current']/L['area']):,}만원/㎡ · 월세 {L['rent']:,}만</div>
            </div>""", unsafe_allow_html=True)
            if st.button("이 매물 선택", key=f"selp_{k}"):
                S["selected"]=k; S["quiz"]=None; S["tool_unlocked"]=None
                S["appraised"]=None; S["appraisal_steps"]=[]; st.rerun()

        # ── 선택된 매물: 감정평가 퀴즈 게이팅 ──
        if S["selected"] and S["selected"] in S["listings"]:
            L=S["listings"][S["selected"]]
            st.markdown("---")
            st.markdown(f"**🎯 {L['name']}** 감정평가하기")

            if S["appraised"] is None:
                if S["tool_unlocked"] is None:
                    if S["quiz"] is None:
                        st.caption("감정평가 도구를 쓰려면 먼저 퀴즈를 통과해야 해요!")
                        qc=st.columns(3)
                        for i,(m,info) in enumerate(APPRAISAL.items()):
                            with qc[i]:
                                if st.button(f"{info['icon']} {m}", key=f"pick_{m}"):
                                    S["quiz"]=make_quiz(m); st.rerun()
                    else:
                        q=S["quiz"]
                        st.markdown(f'<div class="quiz-box"><div style="font-weight:800;margin-bottom:6px;">📖 다음 설명은 어떤 감정평가 방식일까요?</div><div class="quiz-def">{q["definition"]}</div></div>', unsafe_allow_html=True)
                        oc=st.columns(3)
                        for i,opt in enumerate(q["options"]):
                            with oc[i]:
                                if st.button(opt, key=f"ans_{opt}_{q['tries']}"):
                                    if opt==q["answer"]:
                                        S["tool_unlocked"]=q["answer"]; S["quiz"]=None; st.rerun()
                                    else:
                                        S["hp"]=max(0,S["hp"]-5); S["quiz"]["tries"]+=1
                                        if S["hp"]<=0: S["game_over"]=True; S["phase"]="end"
                                        st.rerun()
                        if q["tries"]>0:
                            st.warning(f"❌ 오답! HP -5 (멘탈 {S['hp']}) · 다시 골라보세요")
                else:
                    m=S["tool_unlocked"]
                    st.success(f"✅ 퀴즈 통과! [{m}] 도구 활성화")
                    if st.button(f"🎲 {m}으로 감정평가 실행", key="run_ap", use_container_width=True):
                        ph=st.empty()
                        for d in [".","..","..."]:
                            ph.markdown(f'<div style="text-align:center;padding:14px;font-weight:800;">🎲 감정평가 중{d}</div>', unsafe_allow_html=True)
                            time.sleep(0.45)
                        v,steps=do_appraise(m,L); S["appraised"]=v; S["appraisal_steps"]=steps
                        ph.empty(); st.rerun()
            else:
                st.markdown('<div class="appraisal-box">'+"".join(f'<div class="ap-step">{s}</div>' for s in S["appraisal_steps"])+'</div>', unsafe_allow_html=True)
                diff=S["appraised"]-L["current"]
                if diff>2000: st.success(f"💎 저평가! 적정가 대비 {won(abs(diff))} 저렴")
                elif diff<-2000: st.warning(f"⚠️ 고평가! 적정가 대비 {won(abs(diff))} 비쌈")
                else: st.info("📊 적정 가격대")
                bc=st.columns(2)
                with bc[0]:
                    msg=f"💰 매수 ({won(L['current'])})"
                    if L["current"]>S["capital"]:
                        msg=f"🏦 영끌매수 (+대출 {won(L['current']-S['capital'])})"
                    if st.button(msg, key="buy", use_container_width=True):
                        buy(S["selected"]); S["selected"]=None; S["appraised"]=None; st.rerun()
                with bc[1]:
                    if st.button("⏭️ 패스 → 다음 턴", key="pass", use_container_width=True):
                        advance()

        if S["owned"]:
            st.markdown("---"); st.markdown("**🏦 보유 매물**")
            for i,L in enumerate(S["owned"]):
                p=L["current"]-L["purchase_price"]
                st.markdown(f'<div class="owned-item {"owned-profit" if p>=0 else "owned-loss"}">{"🟢" if p>=0 else "🔴"} {L["name"]} · 현재 {won(L["current"])} · 손익 {"+" if p>=0 else ""}{won(p)}</div>', unsafe_allow_html=True)
                if st.button("매도", key=f"sl_{i}"):
                    sell(i); st.rerun()

        if not S["selected"]:
            st.markdown("---")
            if st.button("⏭️ 다음 턴으로", use_container_width=True):
                advance()

    # ── 우측: 픽셀 타일맵 ──
    with right:
        import os, base64
        img={"서울":"seoul_map.png","대전":"daejeon_map.png","제주":"jeju_map.png"}[rk]
        if os.path.exists(img):
            with open(img,"rb") as f: b64=base64.b64encode(f.read()).decode()
            inner_bg=f'background:url("data:image/png;base64,{b64}") center/cover;'
        else:
            inner_bg=f"background:{R['bg']};"
        trees="🌳🌲🌴🌳"
        tiles=""
        for y in range(4):
            for x in range(4):
                k=pk((x,y))
                owned_here=next((l for l in S["owned"] if l["pos"]==(x,y)),None)
                deco=f'<span class="tree" style="top:4px;left:4px;">{random.choice("🌿🌱🍀")}</span>' if (x+y)%3==0 and k not in S["listings"] and not owned_here else ""
                if k in S["listings"]:
                    L=S["listings"][k]; sel=S["selected"]==k
                    cls="bld bld-sel" if sel else "bld bld-avail"
                    bub=f'<div class="bubble price">{won(L["current"])}</div>'
                    tiles+=f'<div class="tile">{bub}<div class="{cls}">{L["name"][:2]}</div></div>'
                elif owned_here:
                    p=owned_here["current"]-owned_here["purchase_price"]
                    rate=round(p/owned_here["purchase_price"]*100,1) if owned_here["purchase_price"] else 0
                    cls="bld bld-profit" if p>=0 else "bld bld-loss"
                    bub=f'<div class="bubble {"up" if p>=0 else "down"}">{"+" if p>=0 else ""}{rate:.0f}%</div>'
                    tiles+=f'<div class="tile">{bub}<div class="{cls}">{owned_here["name"][:2]}</div></div>'
                else:
                    tiles+=f'<div class="tile">{deco}</div>'
        st.markdown(f'<div class="map-frame"><div class="map-grid"><div class="map-inner" style="{inner_bg}">{tiles}</div></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="map-legend">🟠 매물 · 🟡 선택 · 🟢 보유(수익) · 🔴 보유(손실)</div>', unsafe_allow_html=True)
        if S["log"]:
            st.markdown("**📜 기록**")
            for e in reversed(S["log"][-5:]):
                st.markdown(f'<div class="log-item">{e}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# 화면 C: 결과
# ─────────────────────────────────────────────────────
elif S["phase"]=="end":
    assets=S["capital"]+sum(L["current"] for L in S["owned"]); nw=assets-S["debt"]
    rate=(nw-100000)/100000*100
    st.markdown('<div class="g-title">🏁 게임 종료!</div>', unsafe_allow_html=True)
    if S.get("game_over"): st.error("💔 멘탈 0 → 파산! 이자를 감당하지 못했습니다.")
    elif rate>=50: st.success(f"🏆 부동산 마스터! 순자산 수익률 {rate:+.1f}%")
    elif rate>=0: st.info(f"👍 안정형 투자자 · 수익률 {rate:+.1f}%")
    else: st.warning(f"📚 수업료를 낸 새내기 · {rate:+.1f}%")
    c=st.columns(4)
    c[0].metric("총자산",won(assets)); c[1].metric("부채",won(S["debt"]))
    c[2].metric("순자산",won(nw)); c[3].metric("보유매물",f"{len(S['owned'])}건")
    st.markdown("**📜 전체 기록**")
    for e in S["log"]: st.markdown(f'<div class="log-item">{e}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 다시 시작", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
