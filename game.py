"""
슬기로운 영끌생활 · 부동산 투자 전략 게임 (캡스톤 최종판 v2)
시장원리 반영 · 영구해금 · 시장예측 · 실질수익 리포트 · sticky 스탯 · 설명서 팝업
"""
import streamlit as st
import random, time
import requests, json

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
    "아파트":   {"yield":(0.020,0.030),"appr":(0.03,0.12),"tag":"시세차익형","note":"입지·공급절벽으로 가격 상승 · 월세 수익률은 낮음","img":"apartment.png","emoji":"🏢","color":"#3498db"},
    "오피스텔": {"yield":(0.050,0.070),"appr":(-0.02,0.02),"tag":"월세수익형","note":"월세 수익률 높음 · 시세 상승 거의 없음","img":"officetel.png","emoji":"🏬","color":"#2ecc71"},
    "상가":     {"yield":(0.060,0.090),"appr":(-0.03,0.02),"tag":"월세수익형","note":"월세 최고 · 단, 공실 위험 존재","img":"commercial.png","emoji":"🏪","color":"#e67e22"},
    "빌라":     {"yield":(0.040,0.060),"appr":(-0.03,0.01),"tag":"월세수익형","note":"월세 중간 · 시세 하락 위험 주의","img":"villa.png","emoji":"🏘️","color":"#9b59b6"},
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

# 희귀 매물 (낮은 확률 등장 · 금테두리 연출)
RARE_LISTINGS = [
    {"name":"🌟 강남 재건축 예정 단지","type":"아파트","mult":1.8,"appr_bonus":0.10,"desc":"재건축 대박 기대주"},
    {"name":"🌟 GTX 초역세권 오피스텔","type":"오피스텔","mult":1.5,"appr_bonus":0.08,"desc":"교통 호재 직격"},
    {"name":"🌟 신도시 핵심 상권","type":"상가","mult":1.6,"appr_bonus":0.06,"desc":"유동인구 폭발 예정"},
    {"name":"🌟 국가산단 인접 부지","type":"빌라","mult":1.4,"appr_bonus":0.05,"desc":"개발 잠재력 보유"},
]
RARE_CHANCE = 0.30  # 약 3턴에 1번꼴로 희귀매물 등장 (3개 매물 중 1건 교체)

# AI NPC 투자자 (Gemini 기반 의사결정 에이전트)
NPCS = {
    "박과장": {"style":"공격형","desc":"레버리지 적극 활용·아파트 선호·상승 기대 시 공격 매수","emoji":"🔥"},
    "김부장": {"style":"안정형","desc":"현금 보유 선호·대출 최소화·위험 회피","emoji":"🛡️"},
    "이사장": {"style":"수익형","desc":"오피스텔·상가·빌라 선호·월세 현금흐름 중시","emoji":"💵"},
}

# 랜덤 인생 이벤트 (3~4턴마다)
LIFE_EVENTS = [
    {"icon":"👶","name":"결혼·출산","effect":"안정성 ↑ · 생활비 증가","cap":-3000,"hp":+5},
    {"icon":"👔","name":"승진!","effect":"연봉 인상 · 소득 증가","cap":+4000,"hp":+8},
    {"icon":"🚗","name":"차량 구매","effect":"자산 일부 감소","cap":-2500,"hp":+3},
    {"icon":"🏥","name":"병원비 발생","effect":"갑작스런 현금 지출","cap":-2000,"hp":-5},
    {"icon":"🎁","name":"보너스 지급","effect":"뜻밖의 현금 유입","cap":+3000,"hp":+5},
]

# 투자자 등급 (순자산 수익률 기준)
GRADES = [
    (0.0,  "🌱 새내기 투자자","새내기"),
    (0.15, "💼 실전 투자자","직장인"),
    (0.35, "🔥 영끌 고수","투자자"),
    (0.60, "👑 부동산 마스터","자산가"),
]

# 업적
ACHIEVEMENTS = {
    "first_buy":("🏆 첫 매수","첫 부동산을 매입했습니다!"),
    "first_loan":("🏦 첫 영끌","대출의 세계에 입문했습니다!"),
    "ten_eok":("💰 10억 클럽","순자산 10억을 돌파했습니다!"),
    "streak3":("🔥 3연속 수익","연속 3회 수익을 냈습니다!"),
    "rare_get":("🌟 희귀 매물 획득","전설의 매물을 손에 넣었습니다!"),
    "no_debt":("🛡️ 무대출 플레이","대출 없이 5턴을 버텼습니다!"),
}

# ─────────────────────────────────────────────────────
# 세션
# ─────────────────────────────────────────────────────
def init():
    D={"phase":"intro","region":None,"capital":100000,"debt":0,"loan_rate":5.0,
       "hp":100,"turn":1,"income_year":3000,"market":[],"owned":[],
       "news":None,"next_news":None,"unlocked":[],"selected":None,"quiz":None,
       "appraised":None,"appraisal_steps":[],"appraisal_method":None,"log":[],
       "total_interest":0,"game_over":False,"show_manual":False,"_report_shown":False,
       # 신규 시스템
       "news_popup":False,        # 턴 시작 뉴스 팝업 대기
       "confidence":60,           # 시장 신뢰도 0~100
       "buy_count":0,"win_streak":0,"last_profit":None,  # 등급/업적용
       "achievements":[],         # 획득 업적
       "new_achievements":[],     # 이번에 띄울 업적
       "life_event":None,         # 인생 이벤트
       "apt_count":0,"rent_count":0,"max_debt":0,  # 투자스타일 분석용
       # NPC 경쟁 시스템
       "npcs":{}, "npc_comments":{}, "show_ranking":False,
       }
    for k,v in D.items():
        if k not in st.session_state: st.session_state[k]=v
init()
S=st.session_state

def won(v):
    v=int(round(v)); neg=v<0; v=abs(v); eok=v//10000; man=v%10000
    s=(f"{eok}억 " if eok else "")+(f"{man:,}만" if man else "")
    return ("-" if neg else "")+(s.strip() or "0")

def get_grade():
    """현재 순자산 수익률 기준 투자자 등급"""
    assets=S["capital"]+sum(L["current"] for L in S["owned"])
    nw=assets-S["debt"]
    start=REGIONS[S["region"]]["capital"] if S["region"] else 100000
    rate=(nw-start)/start
    g=GRADES[0]
    for thr,name,avatar in GRADES:
        if rate>=thr: g=(thr,name,avatar)
    return g[1],g[2],rate

def unlock_achievement(key):
    if key not in S["achievements"]:
        S["achievements"].append(key)
        S["new_achievements"].append(key)

def check_achievements():
    assets=S["capital"]+sum(L["current"] for L in S["owned"])
    nw=assets-S["debt"]
    if S["buy_count"]>=1: unlock_achievement("first_buy")
    if S["debt"]>0: unlock_achievement("first_loan")
    if nw>=100000: unlock_achievement("ten_eok")
    if S["win_streak"]>=3: unlock_achievement("streak3")
    if S["turn"]>=5 and S["debt"]==0 and S["max_debt"]==0: unlock_achievement("no_debt")

import os, base64
def img_b64(path):
    """이미지가 있으면 base64 data URI 반환, 없으면 None"""
    if os.path.exists(path):
        with open(path,"rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return None

# ── Gemini API 공통 호출 함수 ──────────────────────────
def call_gemini(prompt: str, max_tokens: int = 2048) -> str:
    """Gemini API 호출. 키 없거나 오류 시 안내 메시지 반환 (앱 안 깨짐)"""
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return "⚠️ Gemini API 키가 설정되지 않았습니다. Streamlit secrets에 GEMINI_API_KEY를 입력하세요."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    body = {"contents":[{"parts":[{"text": prompt}]}],
            "generationConfig":{"maxOutputTokens": max_tokens, "temperature": 0.7,
                                "thinkingConfig":{"thinkingBudget": 0}}}
    try:
        r = requests.post(url, json=body, timeout=20)
        r.raise_for_status()
        data = r.json()
        cand = data["candidates"][0]
        # 응답 텍스트 추출 (parts가 여러 개일 수 있어 합침)
        parts = cand.get("content",{}).get("parts",[])
        text = "".join(p.get("text","") for p in parts)
        return text.strip() if text.strip() else "⚠️ AI 응답이 비어 있습니다. 다시 시도해주세요."
    except Exception as e:
        return f"⚠️ AI 응답 오류: {str(e)[:80]}"

def type_thumb(t, h=60):
    """매물 유형별 썸네일 — 이미지 있으면 이미지, 없으면 이모지+색 그라데이션 폴백"""
    spec=TYPE_SPEC[t]
    src=img_b64(spec["img"])
    if src:
        return f'<div class="thumb" style="background:url(\'{src}\') center/cover;height:{h}px;"></div>'
    c=spec["color"]
    return f'<div class="thumb" style="background:linear-gradient(135deg,{c}cc,{c}66);height:{h}px;font-size:{int(h*0.5)}px;">{spec["emoji"]}</div>'

def new_listing(rk, rare=False):
    if rare:
        r=random.choice(RARE_LISTINGS); t=r["type"]; spec=TYPE_SPEC[t]
        area=random.randint(80,160)
        base=int(random.randint(80000,160000)*r["mult"])
        y=random.uniform(*spec["yield"]); monthly=max(50,min(400,int(base*y/12)))
        return {"id":random.randint(10000,99999),"name":r["name"],"type":t,"tag":spec["tag"],
                "base":base,"fair":int(base*1.40),"current":base,"monthly":monthly,
                "deposit":monthly*12,"area":area,"purchase_price":0,"rare":True,
                "appr_bonus":r["appr_bonus"],"rare_desc":r["desc"]}
    t=random.choice(list(TYPE_SPEC.keys()))
    spec=TYPE_SPEC[t]
    area=random.randint(60,140)
    base=random.randint(50000,150000)
    y=random.uniform(*spec["yield"])
    monthly=max(50,min(400,int(base*y/12)))
    deposit=monthly*12
    fair=int(base*random.uniform(0.85,1.18))
    return {"id":random.randint(10000,99999),"name":random.choice(BRANDS[t]),"type":t,
            "tag":spec["tag"],"base":base,"fair":fair,"current":base,
            "monthly":monthly,"deposit":deposit,"area":area,"purchase_price":0,"rare":False}

def scout(rk):
    listings=[new_listing(rk) for _ in range(3)]
    # 희귀 매물 확률 등장 (3개 중 1개 교체)
    if random.random()<RARE_CHANCE:
        listings[random.randint(0,2)]=new_listing(rk, rare=True)
    S["market"]=listings

def apply_market(news, rk):
    R=REGIONS[rk]
    # 시장 신뢰도가 낮을수록 변동성 증폭 (불안정), 높으면 안정
    conf=S["confidence"]
    vol_mult = 1.0 + (60-conf)/100  # 신뢰도 60 기준, 낮으면 변동성↑
    for L in S["market"]+S["owned"]:
        spec=TYPE_SPEC[L["type"]]
        if L["type"]=="아파트":
            ch=random.uniform(*spec["appr"])+R["apt_trend"]+news.get("apt_boost",0)
        else:
            ch=random.uniform(*spec["appr"])+R["yield_trend"]
        ch+=news["delta"]
        if L["type"]=="빌라" and news.get("villa_hit"): ch+=news["villa_hit"]
        # 희귀 매물 보너스
        if L.get("rare"): ch+=L.get("appr_bonus",0)
        ch*=vol_mult
        L["current"]=max(10000,int(L["current"]*(1+ch)))
        if "fair" in L: L["fair"]=max(10000,int(L["fair"]*(1+ch*0.6)))
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

# ── NPC 경쟁 시스템 (Gemini 기반 AI 에이전트) ──────────
def init_npcs():
    start=REGIONS[S["region"]]["capital"]
    S["npcs"]={name:{"capital":start,"debt":0,"owned":[],"style":info["style"]}
               for name,info in NPCS.items()}
    S["npc_comments"]={}

def npc_networth(npc):
    return npc["capital"]+sum(o["current"] for o in npc["owned"])-npc["debt"]

def npc_market_update():
    """NPC 보유 매물도 시장 변동 반영 (플레이어와 동일 알고리즘 간이 적용)"""
    for npc in S["npcs"].values():
        for o in npc["owned"]:
            spec=TYPE_SPEC[o["type"]]
            if o["type"]=="아파트": ch=random.uniform(*spec["appr"])+S["news"]["delta"]
            else: ch=random.uniform(*spec["appr"])+S["news"]["delta"]
            o["current"]=max(10000,int(o["current"]*(1+ch)))
        # 월세·이자 정산
        rent=sum(o["monthly"]*12 for o in npc["owned"])
        interest=int(npc["debt"]*(S["loan_rate"]/100))
        npc["capital"]+=3000+rent-interest

def run_npc_turn():
    """Gemini 호출 1회로 NPC 3명의 의사결정을 JSON 배열로 받음"""
    market_str="\n".join(f"- {L['name']} ({L['type']}, {L['tag']}) 호가 {won(L['current'])}, 월세 {L['monthly']}만"
                         for L in S["market"])
    npc_state=""
    for name,npc in S["npcs"].items():
        owned=", ".join(o["name"] for o in npc["owned"]) or "없음"
        npc_state+=f"\n[{name}/{NPCS[name]['style']}] 현금 {won(npc['capital'])}, 대출 {won(npc['debt'])}, 보유: {owned}"
    prompt=f"""당신은 부동산 투자 시뮬레이션 게임의 AI 투자자 3명을 동시에 연기합니다.
각 투자자는 자신의 성향에 따라 이번 턴 행동을 결정합니다.

[시장 상황] 턴 {S['turn']}/10
- 뉴스: {S['news']['head']} ({S['news']['i1']}, {S['news']['i2']})
- 시장 신뢰도: {S['confidence']}/100, 대출이율: {S['loan_rate']:.1f}%

[현재 공개 매물 3개]
{market_str}

[투자자별 성향과 현황]
- 박과장(공격형): 레버리지 적극·아파트 선호·상승기대 시 공격매수{npc_state.split(chr(10))[1] if len(npc_state.split(chr(10)))>1 else ''}
- 김부장(안정형): 현금보유·대출최소·위험회피{npc_state.split(chr(10))[2] if len(npc_state.split(chr(10)))>2 else ''}
- 이사장(수익형): 오피스텔/상가/빌라 선호·월세 중시{npc_state.split(chr(10))[3] if len(npc_state.split(chr(10)))>3 else ''}

각 투자자의 결정을 아래 JSON 배열로만 답하세요. 다른 텍스트 없이 JSON만:
[
 {{"name":"박과장","action":"BUY|HOLD|SELL","target":"매물명 또는 빈칸","comment":"한 문장 코멘트"}},
 {{"name":"김부장","action":"BUY|HOLD|SELL","target":"","comment":"한 문장"}},
 {{"name":"이사장","action":"BUY|HOLD|SELL","target":"","comment":"한 문장"}}
]"""
    raw=call_gemini(prompt,1500)
    npc_market_update()
    try:
        js=raw[raw.find("["):raw.rfind("]")+1]
        decisions=json.loads(js)
    except Exception:
        decisions=[]
    # 결정 실행
    decided={d.get("name"):d for d in decisions} if decisions else {}
    for name,npc in S["npcs"].items():
        d=decided.get(name)
        if not d:
            S["npc_comments"][name]="(시장을 관망하고 있습니다.)"
            continue
        act=d.get("action","HOLD"); tgt=d.get("target","")
        S["npc_comments"][name]=d.get("comment","")
        if act=="BUY" and tgt:
            match=next((L for L in S["market"] if tgt in L["name"] or L["name"] in tgt),None)
            if match:
                cost=match["current"]
                if cost>npc["capital"]:
                    npc["debt"]+=cost-npc["capital"]; npc["capital"]=0
                else: npc["capital"]-=cost
                buy_copy=dict(match); buy_copy["purchase_price"]=cost
                npc["owned"].append(buy_copy)
        elif act=="SELL" and npc["owned"]:
            sold=npc["owned"].pop(0); npc["capital"]+=sold["current"]

def new_turn():
    S["news"]=S["next_news"] or random.choice(NEWS_POOL)
    S["next_news"]=random.choice(NEWS_POOL)
    # 시장 신뢰도 갱신 (뉴스 호재/악재 반영)
    if S["news"]["mood"]=="good": S["confidence"]=min(100,S["confidence"]+random.randint(5,12))
    else: S["confidence"]=max(0,S["confidence"]-random.randint(5,12))
    apply_market(S["news"], S["region"])
    if S["news"]["rate"]: S["loan_rate"]=max(1.0,S["loan_rate"]+S["news"]["rate"])
    if S["news"]["hp"]: S["hp"]=max(0,S["hp"]-S["news"]["hp"])
    scout(S["region"])
    # NPC 투자자 의사결정 (Gemini 기반) — 키 있을 때만
    if S["npcs"] and st.secrets.get("GEMINI_API_KEY",""):
        try: run_npc_turn()
        except Exception: pass
    turn_finance()
    # 인생 이벤트 (3~4턴마다)
    S["life_event"]=None
    if S["turn"]>1 and S["turn"]%3==0 and random.random()<0.7:
        ev=random.choice(LIFE_EVENTS)
        S["capital"]=max(0,S["capital"]+ev["cap"])
        S["hp"]=max(0,min(100,S["hp"]+ev["hp"]))
        S["life_event"]=ev
        S["log"].append(f"턴{S['turn']}: {ev['icon']} {ev['name']}")
    S["max_debt"]=max(S["max_debt"],S["debt"])
    check_achievements()
    S["news_popup"]=True  # 턴 시작 뉴스 팝업
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
    # 희귀 매물: 개발 호재 등 미래가치를 반영해 감정가에 프리미엄 (항상 저평가로 평가됨)
    if L.get("rare"):
        v = int(max(v, L["current"]) * (1.18 + L.get("appr_bonus",0)))
        steps.append(f"🌟 희귀매물 미래가치 프리미엄 반영 → 최종 {v:,}만원")
        tip = "🌟 개발 호재가 반영된 희귀 매물! 현재 호가보다 미래가치가 높습니다."
    return v,steps,tip

def buy(lid):
    L=next(x for x in S["market"] if x["id"]==lid)
    cost=L["current"]
    if cost>S["capital"]:
        need=cost-S["capital"]; S["debt"]+=need; S["capital"]=0
        S["log"].append(f"턴{S['turn']}: {L['name']} 영끌매수 (대출 {won(need)})")
    else:
        S["capital"]-=cost; S["log"].append(f"턴{S['turn']}: {L['name']} 매수")
    L["purchase_price"]=cost; S["owned"].append(L)
    S["market"]=[x for x in S["market"] if x["id"]!=lid]
    # 카운트·업적
    S["buy_count"]+=1
    if L["type"]=="아파트": S["apt_count"]+=1
    else: S["rent_count"]+=1
    S["max_debt"]=max(S["max_debt"],S["debt"])
    if L.get("rare"): unlock_achievement("rare_get")
    check_achievements()

def sell(i):
    L=S["owned"][i]; S["capital"]+=L["current"]
    p=L["current"]-L["purchase_price"]
    # 연속 수익 카운트
    if p>=0: S["win_streak"]+=1
    else: S["win_streak"]=0
    S["log"].append(f"턴{S['turn']}: {L['name']} 매도 (손익 {'+' if p>=0 else ''}{won(p)})")
    S["owned"].pop(i)
    check_achievements()

def advance():
    if S["turn"]>=10:
        S["phase"]="end"; st.rerun()
    else:
        # 턴 종료 3단계 연출
        ph=st.empty()
        for msg in ["📊 시장 분석 중...","🏗️ 개발 호재 반영 중...","💰 자산 재계산 중..."]:
            ph.markdown(f'<div class="turn-loading">{msg}</div>', unsafe_allow_html=True)
            time.sleep(0.5)
        ph.empty()
        S["turn"]+=1; new_turn(); st.rerun()

# ─────────────────────────────────────────────────────
# CSS · Navy&Red + 밝은 배경 + sticky 스탯 + 폰트 통일(13px)
# ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Urbanist:wght@400;600;700;900&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
html,body,.stApp{font-family:'Urbanist','Noto Sans KR',sans-serif !important;
    background:#16273f !important;color:#eaf0f8 !important;font-size:15px;}
#MainMenu,footer{display:none !important;}
.main .block-container{padding:1rem 1.5rem 2rem !important;max-width:1500px !important;}
/* 전역 최소 폰트 13px 통일 */
.stApp p,.stApp span,.stApp div,.stApp label,.stApp button,.stApp td,.stApp th,.stCaption,
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{font-size:15px !important;}
.g-title{font-size:24px !important;font-weight:900;color:#fff;display:flex;align-items:center;gap:8px;margin-bottom:2px;}
.g-sub{font-size:15px !important;color:#9fb4d0;margin-bottom:12px;}

/* 밝은 하늘색 배경 컨테이너 - 빈 div 렌더 방지 (높이 0) */
.bright-bg{display:none;}

.panel{background:#28456680;border:1px solid #3a5a80;border-radius:14px;padding:14px 16px;margin-bottom:12px;}
.panel-red{background:#284566;border:1px solid #FF4136;border-radius:14px;padding:14px 16px;margin-bottom:12px;}
.ptitle{font-size:16px !important;font-weight:700;color:#FF6b5e;margin-bottom:10px;display:flex;align-items:center;gap:6px;}

/* sticky 스탯 */
.sticky-stat{position:sticky;top:0;z-index:999;background:#16273f;
    border:1px solid #3a5a80;border-radius:14px;padding:10px;margin-bottom:12px;box-shadow:0 6px 20px rgba(0,0,0,.45);}
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;}
.stat-card{background:#2d4a6b;border:1px solid #3a5a80;border-radius:10px;padding:7px 8px;text-align:center;}
.stat-card .sl{font-size:13px !important;color:#9fb4d0;margin-bottom:2px;}
.stat-card .sv{font-size:16px !important;font-weight:800;color:#fff;}
.sv.danger{color:#FF6b5e;} .sv.warn{color:#FFC233;}

.news{border-radius:12px;padding:12px 14px;margin-bottom:10px;}
.news-good{background:rgba(46,204,113,.14);border:1px solid #2ecc71;}
.news-bad{background:rgba(255,99,72,.14);border:1px solid #FF6347;}
.news-head{font-size:16px !important;font-weight:700;color:#fff;margin-bottom:6px;}
.news-info{font-size:15px !important;color:#cfe0f2;padding:2px 0;}

.li-card{background:#2d4a6b;border:1px solid #3a5a80;border-radius:12px;padding:11px 13px;margin-bottom:7px;display:flex;gap:12px;align-items:center;}
.li-card.sel{border-color:#FF4136;background:#34557a;box-shadow:0 0 0 2px rgba(255,65,54,.3);}
/* 뉴스 팝업 */
.popup-stage{display:flex;justify-content:center;padding:30px 0;}
.popup-card{background:#1a2e4a;border:2.5px solid #FF4136;border-radius:18px;padding:26px 30px;max-width:460px;width:100%;text-align:center;box-shadow:0 12px 40px rgba(0,0,0,.5);}
.popup-badge{display:inline-block;color:#fff;font-weight:900;font-size:16px !important;padding:5px 22px;border-radius:100px;margin-bottom:14px;letter-spacing:.05em;}
.popup-head{font-size:26px !important;font-weight:900;color:#fff;margin-bottom:16px;line-height:1.3;}
.popup-info{font-size:16px !important;color:#dce6f2;padding:5px 0;font-weight:600;}
.life-toast{background:rgba(155,89,182,.18);border:1px solid #9b59b6;border-radius:12px;padding:12px 16px;margin:10px auto;max-width:460px;text-align:center;font-size:16px !important;color:#e8d8f8;}
/* 업적 토스트 */
.ach-wrap{position:relative;z-index:100;}
.ach-toast{background:linear-gradient(135deg,#FFD700,#FFA500);border-radius:14px;padding:14px 20px;margin:8px auto;max-width:420px;text-align:center;box-shadow:0 6px 24px rgba(255,180,0,.4);animation:achpop .5s ease;}
@keyframes achpop{0%{transform:scale(.7);opacity:0;}100%{transform:scale(1);opacity:1;}}
.ach-title{font-size:19px !important;font-weight:900;color:#3a2800;}
.ach-desc{font-size:15px !important;color:#5a4200;margin-top:3px;font-weight:600;}
/* 프로필 바 */
.profile-bar{display:flex;align-items:center;gap:14px;background:linear-gradient(135deg,#2d4a6b,#1a2e4a);border:1px solid #3a5a80;border-radius:14px;padding:12px 18px;margin-bottom:12px;}
.pb-avatar{font-size:34px !important;}
.pb-info{flex:1;}
.pb-grade{font-size:19px !important;font-weight:900;color:#FFD700;}
.pb-sub{font-size:14px !important;color:#9fb4d0;margin-top:2px;}
.pb-conf{min-width:140px;text-align:right;}
.pb-conf-label{font-size:13px !important;color:#9fb4d0;}
.conf-bar{height:8px;background:#1a2e4a;border-radius:100px;overflow:hidden;margin:4px 0;}
.conf-fill{height:100%;border-radius:100px;transition:width .4s;}
.pb-conf-val{font-size:15px !important;font-weight:800;color:#fff;}
/* AI 예측 카드 */
.predict-card{background:linear-gradient(135deg,rgba(124,77,255,.16),rgba(255,194,51,.08));border:1.5px solid #FFC233;border-radius:14px;padding:14px 16px;margin-bottom:12px;}
.pred-head{font-size:16px !important;font-weight:800;color:#FFC233;margin-bottom:8px;}
.pred-row{display:flex;justify-content:space-between;font-size:15px !important;color:#dce6f2;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.08);}
.pred-row:last-child{border-bottom:none;}
/* 매물 게임 카드 */
.game-card{background:#2d4a6b;border:1.5px solid #3a5a80;border-radius:14px;padding:12px;margin-bottom:6px;display:flex;gap:14px;align-items:flex-start;transition:.15s;}
.game-card.sel{border-color:#FF4136;background:#34557a;box-shadow:0 0 0 2px rgba(255,65,54,.35),0 4px 16px rgba(0,0,0,.3);transform:scale(1.01);}
.game-card.rare{border:2px solid #FFD700;background:linear-gradient(135deg,#3a3420,#2d2a1a);box-shadow:0 0 16px rgba(255,215,0,.35);}
.gc-thumb{flex:0 0 auto;}
.gc-body{flex:1;min-width:0;}
.gc-name{font-size:17px !important;font-weight:800;color:#fff;}
.rare-badge{background:#FFD700;color:#3a2800;font-size:12px !important;font-weight:900;padding:1px 7px;border-radius:100px;margin-left:6px;}
.gc-meta{font-size:14px !important;color:#9fb4d0;margin:2px 0 6px;}
.gc-stars{font-size:14px !important;color:#bdd0e8;display:flex;gap:8px;padding:1px 0;}
.gc-stars span{flex:0 0 48px;}
.gc-price{font-size:15px !important;color:#dce6f2;margin-top:6px;}
.gc-price b{color:#fff;font-size:17px !important;}
/* 턴 종료 연출 */
.turn-loading{text-align:center;padding:50px;font-size:22px !important;font-weight:800;color:#FFC233;text-shadow:0 2px 12px rgba(255,194,51,.4);}
.ach-badges{display:flex;flex-wrap:wrap;gap:8px;}
.ach-badge{background:linear-gradient(135deg,#FFD700,#FFA500);color:#3a2800;font-size:14px !important;font-weight:800;padding:5px 12px;border-radius:100px;}
/* AI 응답 박스 */
.ai-box{background:linear-gradient(135deg,rgba(124,77,255,.15),rgba(124,77,255,.05));border:1.5px solid #9b59b6;border-radius:14px;padding:16px;margin:10px 0;white-space:pre-wrap;font-size:15px !important;color:#e4eef8;line-height:1.7;}
.ai-title{font-size:16px !important;font-weight:800;color:#c39bd3;margin-bottom:10px;}
/* AI 투자 리그 랭킹 */
.rank-board{background:linear-gradient(135deg,#1a2e4a,#0f2238);border:1.5px solid #FFD700;border-radius:14px;padding:14px 16px;margin-bottom:10px;}
.rank-title{font-size:16px !important;font-weight:800;color:#FFD700;margin-bottom:10px;}
.rank-row{display:flex;align-items:center;gap:10px;padding:7px 8px;border-radius:8px;margin-bottom:3px;}
.rank-medal{font-size:20px !important;flex:0 0 26px;}
.rank-name{flex:1;font-size:15px !important;font-weight:700;color:#fff;}
.rank-nw{font-size:15px !important;font-weight:700;color:#dce6f2;flex:0 0 100px;text-align:right;}
.rank-rate{font-size:15px !important;font-weight:800;flex:0 0 64px;text-align:right;}
.npc-cmt-box{background:#1a2e4a;border:1px solid #3a5a80;border-radius:12px;padding:12px 14px;margin-bottom:10px;}
.npc-cmt{font-size:14px !important;color:#cfe0f2;padding:4px 0;line-height:1.5;}
.li-thumb{flex:0 0 auto;}
.thumb{width:64px;border-radius:10px;display:flex;align-items:center;justify-content:center;
    box-shadow:0 2px 8px rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.15);}
.li-body{flex:1;min-width:0;}
.inv-card{border-radius:12px;padding:10px 12px;margin-bottom:7px;display:flex;gap:10px;align-items:center;}
.inv-profit{background:rgba(46,204,113,.12);border:1px solid #2ecc71;}
.inv-loss{background:rgba(255,99,72,.12);border:1px solid #FF6347;}
.empty-box{background:#2d4a6b;border:1px dashed #4a6a90;border-radius:12px;padding:18px;text-align:center;font-size:15px !important;color:#9fb4d0;line-height:1.7;}
.log-card{background:#28456680;border-radius:8px;padding:7px 10px;margin-bottom:5px;font-size:14px !important;color:#cfe0f2;}
.li-name{font-size:15px !important;font-weight:700;color:#fff;}
.li-tag{font-size:13px !important;font-weight:700;padding:1px 8px;border-radius:100px;margin-left:6px;}
.tag-cap{background:rgba(52,152,219,.25);color:#5dade2;}
.tag-rent{background:rgba(46,204,113,.25);color:#58d68d;}
.li-price{font-size:15px !important;color:#bdd0e8;margin-top:3px;}

.quiz-box{background:#34557a;border:1px solid #FF4136;border-radius:12px;padding:14px;margin:10px 0;}
.quiz-def{font-size:15px !important;color:#e4eef8;line-height:1.7;background:#1a2e4a;border-radius:10px;padding:11px;margin-bottom:8px;border:1px dashed #4a6a90;}
.ap-box{background:#34557a;border:1px solid #2ecc71;border-radius:12px;padding:14px;margin:10px 0;}
.ap-step{font-size:15px !important;color:#cfe0f2;padding:4px 0;border-bottom:1px solid #3a5a80;}
.ap-step:last-child{border-bottom:none;font-size:16px !important;font-weight:800;color:#2ecc71;padding-top:8px;}

.inv-item{border-radius:10px;padding:9px 11px;margin-bottom:6px;font-size:15px !important;font-weight:600;}
.inv-profit{background:rgba(46,204,113,.12);border:1px solid #2ecc71;}
.inv-loss{background:rgba(255,99,72,.12);border:1px solid #FF6347;}

.display{background:#284566;border:1px solid #3a5a80;border-radius:14px;padding:16px;}
.disp-item{font-size:15px !important;color:#cfe0f2;padding:6px 0;border-bottom:1px solid #3a5a80;}
.disp-item:last-child{border-bottom:none;}
.disp-label{color:#9fb4d0;font-size:14px !important;}
.forecast{background:rgba(255,194,51,.12);border:1px solid #FFC233;border-radius:12px;padding:13px;margin-top:10px;}
.forecast-head{font-size:15px !important;font-weight:700;color:#FFC233;margin-bottom:6px;}
.forecast-body{font-size:15px !important;color:#f0e0b0;line-height:1.6;}
.log-item{font-size:14px !important;color:#9fb4d0;padding:3px 0;border-bottom:1px solid #2a4565;}

.stButton>button{font-family:'Urbanist','Noto Sans KR',sans-serif !important;font-weight:700 !important;font-size:15px !important;
    border-radius:10px !important;background:#2d4a6b !important;border:1px solid #3a5a80 !important;
    color:#fff !important;transition:.12s !important;}
.stButton>button:hover{background:#FF4136 !important;border-color:#FF4136 !important;transform:translateY(-1px);}
[data-testid="stMetric"]{background:#284566;border:1px solid #3a5a80;border-radius:12px;padding:10px 14px;}
[data-testid="stMetricValue"]{color:#fff !important;} [data-testid="stMetricLabel"]{color:#9fb4d0 !important;}

/* 설명서 팝업 (반투명) */
.manual-pop{background:#1a2e4af2;border:2px solid #FF4136;border-radius:16px;padding:20px 24px;margin-bottom:14px;backdrop-filter:blur(6px);}
.manual-pop h4{color:#FF6b5e;font-size:17px !important;margin:0 0 12px;}
.manual-cols{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
.manual-item{font-size:15px !important;color:#e4eef8;padding:6px 0;line-height:1.6;display:flex;gap:10px;}
.manual-item .num{color:#FF6b5e;font-weight:800;flex:0 0 22px;}

.intro-hero{text-align:center;padding:30px 0 10px;}
.intro-stage{width:100%;height:58vh;min-height:340px;border-radius:16px;overflow:hidden;
    display:flex;flex-direction:column;justify-content:flex-end;margin-bottom:8px;
    box-shadow:0 8px 32px rgba(0,0,0,.4);}
.intro-overlay{padding:0 20px 16px;}
.intro-manual{background:rgba(16,28,48,.88);border:1.5px solid #FF4136;border-radius:12px;
    padding:12px 18px;backdrop-filter:blur(4px);}
.intro-manual summary{color:#FF8b7e;font-size:17px !important;font-weight:800;cursor:pointer;list-style:none;}
.intro-manual summary::-webkit-details-marker{display:none;}
.intro-manual[open] summary{margin-bottom:10px;}
.intro-manual .manual-item{padding:3px 0;line-height:1.45;}
.intro-logo{font-size:40px !important;font-weight:900;color:#fff;letter-spacing:-0.02em;}
.intro-logo .red{color:#FF6b5e;}
.intro-tag{font-size:16px !important;color:#9fb4d0;margin-top:8px;}
.region-card{background:#284566;border:2px solid #3a5a80;border-radius:16px;padding:20px;text-align:center;height:100%;}
.rc-icon{font-size:38px !important;} .rc-name{font-size:21px !important;font-weight:900;color:#fff;margin-top:6px;}
.rc-level{display:inline-block;font-size:14px !important;font-weight:700;padding:2px 12px;border-radius:100px;margin:6px 0;}
.rc-desc{font-size:14px !important;color:#9fb4d0;line-height:1.6;}

.report-hero{text-align:center;padding:24px;border-radius:18px;margin-bottom:20px;}
/* 결과 이미지 풀 배경 + 카드 오버레이 */
.result-stage{width:100%;min-height:600px;border-radius:18px;overflow:hidden;
    display:flex;align-items:center;justify-content:center;padding:30px 20px;margin-bottom:20px;
    box-shadow:0 8px 32px rgba(0,0,0,.45);}
.result-card{background:rgba(12,22,38,.86);border:2.5px solid #2ecc71;border-radius:18px;
    padding:24px 28px 22px;max-width:480px;width:100%;text-align:center;backdrop-filter:blur(6px);
    box-shadow:0 12px 40px rgba(0,0,0,.5);position:relative;}
.result-badge{display:inline-block;color:#fff;font-weight:900;font-size:17px !important;
    padding:4px 22px;border-radius:100px;margin-bottom:14px;letter-spacing:.05em;}
.result-headline{font-size:42px !important;font-weight:900;line-height:1.1;text-shadow:0 2px 14px rgba(0,0,0,.6);}
.result-sub{font-size:16px !important;color:#dce6f2;margin:8px 0 18px;font-weight:600;}
.result-rows{text-align:left;}
.rrow{display:flex;justify-content:space-between;align-items:center;padding:9px 4px;
    border-bottom:1px solid rgba(255,255,255,.1);font-size:16px !important;color:#cfe0f2;font-weight:600;}
.rrow .rval{font-weight:800;color:#fff;font-size:17px !important;}
.rrow.total{border-bottom:none;margin-top:6px;padding-top:12px;font-size:17px !important;}
.report-big{font-size:52px !important;font-weight:900;line-height:1;}
.report-label{font-size:16px !important;margin-top:10px;font-weight:600;}
.profit{background:linear-gradient(135deg,rgba(46,204,113,.15),rgba(46,204,113,.05));border:2px solid #2ecc71;}
.profit .report-big{color:#2ecc71;} .profit .report-label{color:#82e0aa;}
.loss{background:linear-gradient(135deg,rgba(255,99,72,.15),rgba(255,99,72,.05));border:2px solid #FF6347;}
.loss .report-big{color:#FF6347;} .loss .report-label{color:#ff9b8b;}
.calc-table{width:100%;border-collapse:collapse;margin:14px 0;}
.calc-table td{padding:10px 14px;border-bottom:1px solid #3a5a80;font-size:16px !important;color:#e4eef8;}
.calc-table td.r{text-align:right;font-weight:700;color:#fff;}
.calc-table tr.total td{border-top:2px solid #FF4136;border-bottom:none;font-size:18px !important;font-weight:900;color:#fff;padding-top:14px;}
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
    manual_html=f'''<details class="intro-manual"><summary>📖 게임 설명서 (눌러서 펼치기)</summary>
      <div class="manual-cols"><div class="manual-col">{half1}</div><div class="manual-col">{half2}</div></div></details>'''

    if intro_img:
        # 이미지 배경(상단 33vh, 원본비율 확대 cover) + 설명서 반투명 오버레이
        st.markdown(f'''
        <div class="intro-stage" style="background:linear-gradient(to bottom, rgba(22,39,63,0) 40%, rgba(22,39,63,.6) 62%, rgba(22,39,63,.97) 100%), url('{intro_img}') top center/cover;">
          <div class="intro-overlay">{manual_html}</div>
        </div>''', unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="intro-hero">
          <div class="intro-logo">🏠 슬기로운 <span class="red">영끌</span>생활</div>
          <div class="intro-tag">부동산 투자 전략 시뮬레이션 · 시장 원리를 게임으로 배우다</div>
        </div>{manual_html}""", unsafe_allow_html=True)

    # 지역 선택 버튼
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
                init_npcs()
                ph=st.empty()
                for msg in ["🗺️ 지도 로딩 중...","🏢 매물 스카우팅 중...","📊 시장 분석 중..."]:
                    ph.markdown(f'<div style="text-align:center;padding:40px;font-size:20px;font-weight:700;color:#FF6b5e;">{msg}</div>', unsafe_allow_html=True)
                    time.sleep(0.5)
                ph.empty()
                S["next_news"]=random.choice(NEWS_POOL); new_turn(); st.rerun()

# ─────────────────────────────────────────────────────
# 화면 B: 플레이
# ─────────────────────────────────────────────────────
elif S["phase"]=="play":
    rk=S["region"]; R=REGIONS[rk]

    # ===== 턴 시작 뉴스 팝업 (확인 눌러야 진입) =====
    if S["news_popup"] and S["news"]:
        n=S["news"]
        is_good=n["mood"]=="good"
        badge="📈 속보" if is_good else "🚨 긴급 속보"
        acc="#2ecc71" if is_good else "#FF4136"
        st.markdown(f"""
        <div class="popup-stage">
          <div class="popup-card" style="border-color:{acc};">
            <div class="popup-badge" style="background:{acc};">{badge}</div>
            <div class="popup-head">{n['head']}</div>
            <div class="popup-info"><span style="color:{acc};">▸</span> {n['i1']}</div>
            <div class="popup-info"><span style="color:{acc};">▸</span> {n['i2']}</div>
          </div>
        </div>""", unsafe_allow_html=True)
        # 인생 이벤트도 같이 알림
        if S["life_event"]:
            ev=S["life_event"]
            st.markdown(f"""<div class="life-toast">{ev['icon']} <b>인생 이벤트: {ev['name']}</b> — {ev['effect']}</div>""", unsafe_allow_html=True)
        c1,c2,c3=st.columns([1,1,1])
        with c2:
            if st.button("✅ 확인하고 시작", use_container_width=True, key="news_ok"):
                S["news_popup"]=False; st.rerun()
        st.stop()

    # ===== 업적 토스트 (화면 중앙 연출) =====
    if S["new_achievements"]:
        toasts=""
        for key in S["new_achievements"]:
            title,desc=ACHIEVEMENTS[key]
            toasts+=f'<div class="ach-toast"><div class="ach-title">{title}</div><div class="ach-desc">{desc}</div></div>'
        st.markdown(f'<div class="ach-wrap">{toasts}</div>', unsafe_allow_html=True)
        S["new_achievements"]=[]

    # ===== 등급/아바타 프로필 바 =====
    grade_name,avatar,grate=get_grade()
    av_emoji={"새내기":"🐣","직장인":"👔","투자자":"📈","자산가":"💎"}.get(avatar,"🐣")
    st.markdown(f"""<div class="profile-bar">
      <div class="pb-avatar">{av_emoji}</div>
      <div class="pb-info"><div class="pb-grade">{grade_name}</div>
        <div class="pb-sub">{rk} {R['level']} · 수익률 {grate*100:+.1f}%</div></div>
      <div class="pb-conf"><div class="pb-conf-label">시장 신뢰도</div>
        <div class="conf-bar"><div class="conf-fill" style="width:{S['confidence']}%;background:{'#2ecc71' if S['confidence']>=60 else ('#FFC233' if S['confidence']>=35 else '#FF4136')};"></div></div>
        <div class="pb-conf-val">{S['confidence']}</div></div>
    </div>""", unsafe_allow_html=True)

    top1,top2,top3=st.columns([2,1,1])
    with top1:
        st.markdown(f'<div class="g-title">{R["icon"]} 슬기로운 영끌생활 — {rk}</div>', unsafe_allow_html=True)
    with top2:
        if st.button("🏆 투자 리그 " + ("닫기" if S["show_ranking"] else "열기"), use_container_width=True):
            S["show_ranking"]=not S["show_ranking"]; st.rerun()
    with top3:
        if st.button("📖 설명서 " + ("닫기" if S["show_manual"] else "열기"), use_container_width=True):
            S["show_manual"]=not S["show_manual"]; st.rerun()

    if S["show_manual"]:
        render_manual_popup()

    # ── AI 투자 리그 랭킹 (실시간) ──
    if S["show_ranking"] and S["npcs"]:
        player_nw=S["capital"]+sum(L["current"] for L in S["owned"])-S["debt"]
        start=REGIONS[rk]["capital"]
        board=[("🙋 플레이어(나)", player_nw, "나")]
        for name,npc in S["npcs"].items():
            board.append((f"{NPCS[name]['emoji']} {name}({NPCS[name]['style']})", npc_networth(npc), name))
        board.sort(key=lambda x:x[1], reverse=True)
        medals=["🥇","🥈","🥉","4️⃣"]
        rows=""
        for i,(label,nw,key) in enumerate(board):
            rate=(nw-start)/start*100
            hl="background:rgba(255,215,0,.12);" if key=="나" else ""
            rows+=f"""<div class="rank-row" style="{hl}">
              <span class="rank-medal">{medals[i]}</span>
              <span class="rank-name">{label}</span>
              <span class="rank-nw">{won(nw)}</span>
              <span class="rank-rate" style="color:{'#2ecc71' if rate>=0 else '#FF6347'};">{rate:+.1f}%</span>
            </div>"""
        st.markdown(f'<div class="rank-board"><div class="rank-title">🏆 AI 투자 리그 · 실시간 순위 (턴 {S["turn"]}/10)</div>{rows}</div>', unsafe_allow_html=True)
        # NPC 코멘트
        if S["npc_comments"]:
            cmts=""
            for name,cmt in S["npc_comments"].items():
                if cmt: cmts+=f'<div class="npc-cmt">{NPCS[name]["emoji"]} <b>{name}</b>: "{cmt}"</div>'
            if cmts: st.markdown(f'<div class="npc-cmt-box">{cmts}</div>', unsafe_allow_html=True)


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
        # 1) 현재 뉴스 (상황 인식)
        if S["news"]:
            nc="news-good" if S["news"]["mood"]=="good" else "news-bad"
            st.markdown(f"""<div class="news {nc}"><div class="news-head">{S['news']['head']}</div>
              <div class="news-info">📌 {S['news']['i1']}</div>
              <div class="news-info">📌 {S['news']['i2']}</div></div>""", unsafe_allow_html=True)

        # 2) AI 시장 예측 카드 (미래 예측)
        if S["next_news"]:
            nn=S["next_news"]
            is_good=nn["mood"]=="good"
            mood_txt="강세 ▲" if is_good else "약세 ▼"
            mood_col="#2ecc71" if is_good else "#FF4136"
            risk = 2 if is_good else 4
            risk_stars="★"*risk+"☆"*(5-risk)
            strat="적극 매수 기회" if is_good else "현금 확보·관망"
            ev_short=nn['head'].split(' ',1)[1] if ' ' in nn['head'] else nn['head']
            st.markdown(f"""<div class="predict-card">
              <div class="pred-head">🔮 AI 시장 예측</div>
              <div class="pred-row"><span>시장 분위기</span><span style="color:{mood_col};font-weight:800;">{mood_txt}</span></div>
              <div class="pred-row"><span>다음 턴 위험도</span><span style="color:#FFC233;">{risk_stars}</span></div>
              <div class="pred-row"><span>예상 이벤트</span><span>{ev_short}</span></div>
              <div class="pred-row"><span>추천 전략</span><span style="color:{mood_col};font-weight:700;">{strat}</span></div>
            </div>""", unsafe_allow_html=True)

        # 3) 이번 턴 매물 (게임 카드)
        st.markdown('<div class="ptitle">🏢 이번 턴 매물 (3건 스카우팅)</div>', unsafe_allow_html=True)
        for L in S["market"]:
            sel=S["selected"]==L["id"]
            spec=TYPE_SPEC[L["type"]]
            rare=L.get("rare",False)
            # ★ 레이팅: 성장성(시세변동 상단)·안정성(변동성 역)·월세(수익률)
            growth=min(5,max(1,int((spec["appr"][1])*40)))
            stable=min(5,max(1,6-int(R["vol"]*30)))
            rent_r=min(5,max(1,int(spec["yield"][1]*70)))
            def stars(n): return "★"*n+"☆"*(5-n)
            card_cls="game-card rare" if rare else "game-card"
            if sel: card_cls+=" sel"
            rare_tag='<span class="rare-badge">RARE</span>' if rare else ""
            st.markdown(f"""<div class="{card_cls}">
              <div class="gc-thumb">{type_thumb(L['type'],72)}</div>
              <div class="gc-body">
                <div class="gc-name">{L['name']}{rare_tag}</div>
                <div class="gc-meta">{L['type']} · {L['tag']} · {L['area']}㎡</div>
                <div class="gc-stars"><span>성장성</span> <b style="color:#FF6b5e;">{stars(growth)}</b></div>
                <div class="gc-stars"><span>안정성</span> <b style="color:#3498db;">{stars(stable)}</b></div>
                <div class="gc-stars"><span>월세력</span> <b style="color:#2ecc71;">{stars(rent_r)}</b></div>
                <div class="gc-price">호가 <b>{won(L['current'])}</b> · 월세 {L['monthly']}만</div>
              </div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"{'✓ 선택됨' if sel else '🔍 투자 검토'}", key=f"sel_{L['id']}", use_container_width=True):
                S["selected"]=L["id"]; S["quiz"]=None; S["appraised"]=None; S["appraisal_steps"]=[]; st.rerun()

        # 감정평가 도구창
        if S["selected"] and any(x["id"]==S["selected"] for x in S["market"]):
            L=next(x for x in S["market"] if x["id"]==S["selected"])
            st.markdown('<div class="ptitle" style="margin-top:14px;">🎯 감정평가 도구</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:15px;color:#bdd0e8;margin-bottom:8px;">선택: <b style="color:#fff;">{L["name"]}</b> ({L["tag"]}) · 호가 {won(L["current"])}</div>', unsafe_allow_html=True)

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
                        ph=st.empty()
                        for m in ["💰 계약 체결 중...","✍️ 계약서 작성 중...","🏠 소유권 이전 완료!"]:
                            ph.markdown(f'<div class="turn-loading">{m}</div>', unsafe_allow_html=True)
                            time.sleep(0.45)
                        ph.empty()
                        buy(S["selected"]); S["selected"]=None; S["appraised"]=None; st.rerun()
                with bc[1]:
                    if st.button("⏭️ 패스",key="pass",use_container_width=True):
                        S["selected"]=None; S["appraised"]=None; st.rerun()

        # 인벤토리
        st.markdown('<div class="ptitle" style="margin-top:14px;">🏦 보유 매물 (인벤토리)</div>', unsafe_allow_html=True)
        if S["owned"]:
            for i,L in enumerate(S["owned"]):
                p=L["current"]-L["purchase_price"]
                rate=round(p/L["purchase_price"]*100,1) if L["purchase_price"] else 0
                # 상태: 상승/정체/하락
                if rate>3: status,scol="🟢 상승세","#2ecc71"
                elif rate<-3: status,scol="🔴 하락세","#FF6347"
                else: status,scol="🟡 정체","#FFC233"
                st.markdown(f"""<div class="inv-card {"inv-profit" if p>=0 else "inv-loss"}">
                  <div class="li-thumb">{type_thumb(L['type'],52)}</div>
                  <div class="li-body">
                    <div class="li-name">{L['name']} <span style="font-size:14px;color:#9fb4d0;">({L['type']})</span> <span style="float:right;color:{scol};font-size:14px;">{status}</span></div>
                    <div class="li-price">현재 {won(L['current'])} · 월세 {L['monthly']}만</div>
                    <div class="li-price" style="font-weight:800;color:{'#2ecc71' if p>=0 else '#FF6347'};">손익 {"+" if p>=0 else ""}{won(p)} ({rate:+.1f}%)</div>
                  </div>
                </div>""", unsafe_allow_html=True)
                if st.button("💸 매도",key=f"sl_{i}", use_container_width=True): sell(i); st.rerun()
        else:
            st.markdown('<div class="empty-box">아직 보유한 매물이 없습니다.<br>저평가 매물을 찾아 매수해보세요!</div>', unsafe_allow_html=True)
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
        if S["log"]:
            st.markdown('<div class="ptitle" style="margin-top:12px;">📜 거래 기록</div>', unsafe_allow_html=True)
            for e in reversed(S["log"][-6:]):
                if "매수" in e: lc="#2ecc71"
                elif "매도" in e: lc="#FF6347"
                else: lc="#9fb4d0"
                st.markdown(f'<div class="log-card" style="border-left:3px solid {lc};">{e}</div>', unsafe_allow_html=True)

        # ── AI 기능 패널 ──
        st.markdown('<div class="ptitle" style="margin-top:14px;">🤖 AI 어시스턴트</div>', unsafe_allow_html=True)

        # 1) AI 투자 코치
        if st.button("🤖 AI 투자 코치", use_container_width=True, key="ai_coach"):
            total_asset=S["capital"]+sum(L["current"] for L in S["owned"])
            owned_str="\n".join(f"- {L['name']}({L['type']}) 현재가 {won(L['current'])}" for L in S["owned"]) or "없음"
            news_str=S["news"]["head"] if S["news"] else "없음"
            next_str=S["next_news"]["head"] if S["next_news"] else "없음"
            prompt=f"""당신은 한국 부동산 투자 전문가 코치입니다. 다음 상황을 분석하고 투자 전략을 조언해주세요.

[현재 게임 상황]
- 턴: {S['turn']}/10 (1턴=1년)
- 보유 현금: {won(S['capital'])}
- 총 자산: {won(total_asset)}
- 대출 잔액: {won(S['debt'])} (연이율 {S['loan_rate']:.1f}%)
- 멘탈(HP): {S['hp']}/100
- 시장 신뢰도: {S['confidence']}/100
- 보유 매물:
{owned_str}
- 이번 턴 뉴스: {news_str}
- 다음 턴 예상: {next_str}

다음 4가지를 간결하게 한국어로 답해주세요:
1. 현재 시장 상황 분석 (2~3문장)
2. 추천 투자 전략 (2~3문장)
3. 위험도: 상/중/하 + 이유 한 줄
4. 추천 행동: 매수 / 관망 / 매도 중 하나 + 이유 한 줄"""
            with st.spinner("🤖 AI 분석 중..."):
                result = call_gemini(prompt, 2048)
            st.markdown(f'<div class="ai-box"><div class="ai-title">🤖 AI 투자 코치</div>{result}</div>', unsafe_allow_html=True)

        # 2) AI 감정평가사 (매물 선택된 경우만)
        if S["selected"] and any(x["id"]==S["selected"] for x in S["market"]):
            L_sel=next(x for x in S["market"] if x["id"]==S["selected"])
            if st.button("🤖 AI 감정평가 의견", use_container_width=True, key="ai_appraise"):
                news_str=S["news"]["head"] if S["news"] else "없음"
                prompt=f"""당신은 한국 부동산 감정평가 전문가입니다. 다음 매물을 분석해주세요.

[매물 정보]
- 매물명: {L_sel['name']}
- 유형: {L_sel['type']} ({L_sel['tag']})
- 면적: {L_sel['area']}㎡
- 호가: {won(L_sel['current'])}
- 월세: {L_sel['monthly']}만원 (보증금 {won(L_sel['deposit'])})
- 지역: {S['region']} ({REGIONS[S['region']]['level']})
- 현재 시장: {news_str}
- 시장 신뢰도: {S['confidence']}/100

다음 4가지를 간결하게 한국어로 답해주세요:
1. 적정성 평가: 호가가 적정한지 판단 (2문장)
2. 고평가/저평가 여부: 명확히 판단 + 근거 한 줄
3. 투자 적합도: 이 매물 유형({L_sel['type']})의 수익 원천 설명 (2문장)
4. 종합 의견: 매수 추천 여부 한 줄"""
                with st.spinner("🤖 감정평가 분석 중..."):
                    result = call_gemini(prompt, 2048)
                st.markdown(f'<div class="ai-box"><div class="ai-title">🤖 AI 감정평가사</div>{result}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# 화면 C: 결산 리포트
# ─────────────────────────────────────────────────────
elif S["phase"]=="end":
    if not S.get("_report_shown"):
        ph=st.empty()
        for msg in ["📊 최종 자산 집계 중...","🧮 실질 수익 계산 중...","📑 리포트 생성 중..."]:
            ph.markdown(f'<div style="text-align:center;padding:60px;font-size:22px;font-weight:800;color:#FF6b5e;">{msg}</div>', unsafe_allow_html=True)
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
      <div style="font-size:24px;font-weight:900;color:#fff;">{grade}</div>
      <div style="font-size:15px;color:#bdd0e8;margin-top:6px;">{msg}</div></div>""", unsafe_allow_html=True)

    # ── AI 투자 리그 최종 결과 ──
    if S["npcs"]:
        st.markdown('<div class="ptitle" style="margin-top:16px;">🏆 AI 투자 리그 최종 결과</div>', unsafe_allow_html=True)
        start=REGIONS[S["region"]]["capital"]
        player_nw=S["capital"]+sum(L["current"] for L in S["owned"])-S["debt"]
        board=[("🙋 플레이어(나)", player_nw, "나", "-")]
        for name,npc in S["npcs"].items():
            board.append((f"{NPCS[name]['emoji']} {name}", npc_networth(npc), name, NPCS[name]['style']))
        board.sort(key=lambda x:x[1], reverse=True)
        medals=["🥇","🥈","🥉","4️⃣"]
        rows=""
        for i,(label,nw,key,style) in enumerate(board):
            rate=(nw-start)/start*100
            hl="background:rgba(255,215,0,.15);" if key=="나" else ""
            rows+=f"""<div class="rank-row" style="{hl}">
              <span class="rank-medal">{medals[i]}</span>
              <span class="rank-name">{label} <span style="font-size:13px;color:#9fb4d0;">{style if style!='-' else '플레이어'}</span></span>
              <span class="rank-nw">{won(nw)}</span>
              <span class="rank-rate" style="color:{'#2ecc71' if rate>=0 else '#FF6347'};">{rate:+.1f}%</span>
            </div>"""
        st.markdown(f'<div class="rank-board">{rows}</div>', unsafe_allow_html=True)

        # Gemini 승패 분석
        if "ai_league_analysis" not in st.session_state:
            player_rank=next(i for i,(_,_,k,_) in enumerate(board) if k=="나")+1
            board_str="\n".join(f"{i+1}위 {lbl} 순자산 {won(nw)} 수익률 {(nw-start)/start*100:+.1f}%" for i,(lbl,nw,k,s) in enumerate(board))
            prompt=f"""부동산 투자 시뮬레이션 게임이 끝났습니다. 플레이어와 AI 투자자 3명의 최종 성적입니다.

[최종 순위]
{board_str}

플레이어는 {player_rank}위입니다.
플레이어와 AI 투자자들의 전략을 비교하여, 플레이어가 왜 이 순위가 되었는지(승리 또는 패배 요인) 5줄 내외로 한국어로 분석해주세요. 구체적인 투자 행동 차이를 근거로 설명하세요."""
            with st.spinner("🤖 투자 리그 분석 중..."):
                st.session_state["ai_league_analysis"]=call_gemini(prompt,1500)
        st.markdown(f'<div class="ai-box"><div class="ai-title">🤖 AI 리그 분석 — 승패 요인</div>{st.session_state.get("ai_league_analysis","")}</div>', unsafe_allow_html=True)

    # AI 투자 성향 분석 (게임 종료 시 자동 생성)
    st.markdown('<div class="ptitle" style="margin-top:16px;">🤖 AI 투자 성향 분석</div>', unsafe_allow_html=True)
    if "ai_style_result" not in st.session_state:
        log_str="\n".join(S["log"][-10:]) or "없음"
        assets_end=S["capital"]+sum(L["current"] for L in S["owned"])
        nw_end=assets_end-S["debt"]
        prompt=f"""당신은 한국 부동산 투자 행동 분석 전문가입니다. 플레이어의 10턴 투자 행동을 분석해주세요.

[플레이어 투자 기록]
- 지역: {S['region']} ({REGIONS[S['region']]['level']})
- 총 매수 횟수: {S['buy_count']}회
- 아파트 매수: {S['apt_count']}건 / 수익형 매수: {S['rent_count']}건
- 최대 대출 규모: {won(S['max_debt'])}
- 최종 순자산: {won(nw_end)}
- 연속 수익: {S['win_streak']}회
- 획득 업적: {', '.join(S['achievements']) if S['achievements'] else '없음'}
- 거래 기록:
{log_str}

다음 4가지를 한국어로 분석해주세요:
1. 투자 성향 유형: 공격형/보수형/레버리지형/가치투자형/임대사업형 중 하나 + 이유 (2문장)
2. 강점: 이 플레이어가 잘한 점 (2문장)
3. 개선점: 다음 게임에서 보완할 점 (2문장)
4. 실제 투자 조언: 이 성향의 투자자에게 주는 현실적 조언 (2~3문장)"""
        with st.spinner("🤖 투자 성향 분석 중..."):
            result=call_gemini(prompt, 2048)
        st.session_state["ai_style_result"]=result
    st.markdown(f'<div class="ai-box"><div class="ai-title">🤖 AI 투자 성향 분석 결과</div>{st.session_state.get("ai_style_result","")}</div>', unsafe_allow_html=True)

    # 투자 스타일 분석 (rule-based)
    if S["apt_count"]>S["rent_count"]: style,sdesc="📈 가치투자자","아파트 시세차익 중심으로 투자했습니다"
    elif S["rent_count"]>S["apt_count"]: style,sdesc="🏠 임대사업가","월세수익형 매물로 안정적 현금흐름을 추구했습니다"
    else: style,sdesc="⚖️ 균형투자자","시세차익과 월세수익을 고르게 노렸습니다"
    if S["max_debt"]>=50000: style2="· 레버리지 적극 활용형"
    elif S["max_debt"]==0: style2="· 무대출 보수형"
    else: style2="· 적정 레버리지형"
    st.markdown(f"""<div class="panel" style="text-align:center;margin-top:10px;">
      <div style="font-size:15px;color:#9fb4d0;">나의 투자 스타일</div>
      <div style="font-size:20px;font-weight:900;color:#FFD700;margin:4px 0;">{style}</div>
      <div style="font-size:14px;color:#bdd0e8;">{sdesc} {style2}</div>
    </div>""", unsafe_allow_html=True)

    # 획득 업적
    if S["achievements"]:
        badges="".join(f'<span class="ach-badge">{ACHIEVEMENTS[k][0]}</span>' for k in S["achievements"])
        st.markdown(f'<div class="ptitle" style="margin-top:14px;">🏆 획득 업적 ({len(S["achievements"])}개)</div><div class="ach-badges">{badges}</div>', unsafe_allow_html=True)

    st.markdown('<div class="ptitle" style="margin-top:14px;">📜 전체 거래 기록</div>', unsafe_allow_html=True)
    for e in S["log"]: st.markdown(f'<div class="log-card">{e}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 다시 시작", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
