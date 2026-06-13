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
    "수익환원법": {"icon":"💰","weapon":"⚔️ 검 투자법","easy":"월세를 보고 계산해요. \"이 건물 사면 몇 년 만에 본전 뽑을까?\"",
                  "def":"장래 임대수익(월세)을 환원율로 나누어 가치를 구하는 방식","best_for":["오피스텔","상가","빌라"],"best_txt":"오피스텔·상가"},
    "거래사례비교법":{"icon":"📊","weapon":"🏹 활 투자법","easy":"주변 거래 가격을 보고 계산해요. \"비슷한 건물이 얼마에 팔렸을까?\"",
                  "def":"인근의 실제 거래 사례를 보정하여 가치를 구하는 방식","best_for":["아파트"],"best_txt":"아파트"},
    "원가법":     {"icon":"🏗️","weapon":"🛡️ 방패 투자법","easy":"다시 지으면 얼마 들지 계산해요. \"똑같은 건물 새로 지으면 얼마?\"",
                  "def":"토지가격에 건축비를 더하고 감가상각을 빼서 가치를 구하는 방식","best_for":[],"best_txt":"신축 건물"},
}
LTV = 0.60  # 대출 한도: 건물 가격의 60%까지

NEWS_POOL = [
    {"head":"📈 한국은행 기준금리 인하","i1":"전체 집값 +6%","i2":"대출이자 -0.5%","mood":"good","delta":0.06,"rate":-0.5,"apt_boost":0.02,
     "impact":"집 사기 좋아졌어요! 대출이자도 싸지고 집값도 오를 거예요."},
    {"head":"📉 기준금리 인상","i1":"전체 집값 -8%","i2":"대출이자 +1.0%","mood":"bad","delta":-0.08,"rate":1.0,"apt_boost":-0.02,
     "impact":"대출이자가 비싸져요. 빚이 많으면 부담이 커집니다."},
    {"head":"🚇 수도권 GTX 신규 노선 확정","i1":"아파트 +12%","i2":"역세권 기대감 ↑","mood":"good","delta":0.04,"rate":0,"apt_boost":0.08,
     "impact":"아파트값이 크게 올라요! 아파트 가진 사람은 이득."},
    {"head":"🚨 토지거래허가구역 확대","i1":"전체 집값 -7%","i2":"거래 위축","mood":"bad","delta":-0.07,"rate":0,"apt_boost":0,
     "impact":"규제로 거래가 막혀 집값이 내려가요. 매수는 신중히."},
    {"head":"🏗️ 재건축 안전진단 완화","i1":"아파트 +9%","i2":"노후단지 프리미엄","mood":"good","delta":0.03,"rate":0,"apt_boost":0.06,
     "impact":"오래된 아파트값이 올라요! 재건축 기대감 덕분."},
    {"head":"💸 DSR 대출 규제 강화","i1":"전체 집값 -5%","i2":"대출한도 축소","mood":"bad","delta":-0.05,"rate":0,"apt_boost":0,
     "impact":"대출받기가 어려워져요. 집 사기가 조금 까다로워집니다."},
    {"head":"🏪 상권 활성화 정책 발표","i1":"상가 월세 +15%","i2":"임대수익 ↑","mood":"good","delta":0.02,"rate":0,"apt_boost":0,"rent_boost":0.15,
     "impact":"상가 월세가 올라요! 상가 가진 사람은 월세 수입 증가."},
    {"head":"📰 미분양 8만 가구 돌파","i1":"전체 집값 -6%","i2":"공급과잉","mood":"bad","delta":-0.06,"rate":0,"apt_boost":-0.04,
     "impact":"집이 너무 많이 남아돌아 값이 떨어져요. 특히 아파트 주의."},
    {"head":"🏦 특례보금자리론 재출시","i1":"전체 집값 +4%","i2":"대출이자 -0.3%","mood":"good","delta":0.04,"rate":-0.3,"apt_boost":0.02,
     "impact":"싼 이자 대출이 나와서 집 사기 좋아져요!"},
    {"head":"🌊 전세사기 여파·빌라 기피","i1":"빌라 -10%","i2":"비아파트 수요 ↓","mood":"bad","delta":-0.02,"rate":0,"apt_boost":0,"villa_hit":-0.10,
     "impact":"빌라값이 크게 떨어져요. 빌라 투자는 조심하세요."},
]
INFLATION = 0.025
TURN_MAX = 5  # 총 플레이 턴 (테스트 결과 49분→단축)
START_YEAR = 2026  # 게임 시작 연도

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
    {"icon":"👶","name":"결혼·출산","effect":"행복하지만 생활비가 늘었어요","cap":-3000},
    {"icon":"👔","name":"승진!","effect":"연봉이 올라 보너스가 들어왔어요","cap":+4000},
    {"icon":"🚗","name":"자동차 구매","effect":"새 차를 뽑아 목돈이 나갔어요","cap":-2500},
    {"icon":"🏥","name":"병원비 발생","effect":"갑자기 아파서 현금이 나갔어요","cap":-2000},
    {"icon":"🎁","name":"보너스 지급","effect":"뜻밖의 보너스가 들어왔어요","cap":+3000},
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
       "deposit_total":0,"turn":1,"income_year":3000,"market":[],"owned":[],
       "my_method":None,"news":None,"next_news":None,"selected":None,"quiz":None,
       "appraised":None,"log":[],
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
       "npcs":{}, "npc_comments":{}, "show_ranking":False, "ai_cache":{}, "prev_market":[],
       "networth_history":[],  # 연도별 순자산 추이 [(연도, 순자산), ...]
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
    """Gemini API 호출. 429 시 1회 자동 재시도. 키 없거나 오류 시 안내 (앱 안 깨짐)"""
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return "⚠️ Gemini API 키가 설정되지 않았습니다. Streamlit secrets에 GEMINI_API_KEY를 입력하세요."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    body = {"contents":[{"parts":[{"text": prompt}]}],
            "generationConfig":{"maxOutputTokens": max_tokens, "temperature": 0.7,
                                "thinkingConfig":{"thinkingBudget": 0}}}
    for attempt in range(2):  # 429면 한 번 더
        try:
            r = requests.post(url, json=body, timeout=20)
            if r.status_code==429 and attempt==0:
                time.sleep(3); continue
            r.raise_for_status()
            cand = r.json()["candidates"][0]
            parts = cand.get("content",{}).get("parts",[])
            text = "".join(p.get("text","") for p in parts)
            return text.strip() if text.strip() else "⚠️ AI 응답이 비어 있습니다. 다시 시도해주세요."
        except Exception as e:
            if attempt==0 and "429" in str(e):
                time.sleep(3); continue
            return f"⚠️ AI 응답 오류: {str(e)[:80]}"
    return "⚠️ AI 요청량이 많습니다. 잠시 후 다시 시도해주세요."

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
    """연 단위 정산 — 소득 연1배 + 월세 - 이자"""
    interest_year=int(S["debt"]*(S["loan_rate"]/100))
    S["total_interest"]+=interest_year
    rent_year=sum(L["monthly"]*12 for L in S["owned"])
    net=S["income_year"]+rent_year-interest_year
    S["capital"]+=net
    # 현금이 바닥나고 빚이 자산을 초과하면 파산 위기
    assets=S["capital"]+sum(L["current"] for L in S["owned"])
    if S["capital"]<0 and S["debt"]>assets:
        S["game_over"]=True; S["phase"]="end"

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
    """룰 기반 NPC 의사결정 (API 호출 없음). 성향별 매물 선택."""
    npc_market_update()
    mood_good = S["news"]["mood"]=="good"
    for name, npc in S["npcs"].items():
        style = NPCS[name]["style"]
        cands = list(S["market"])
        pick = None; comment = ""
        if style=="공격형":
            # 아파트 우선, 상승장이면 공격 매수(대출 OK)
            apts = [L for L in cands if L["type"]=="아파트"]
            if apts and (mood_good or npc["capital"]>0):
                pick = max(apts, key=lambda x:x["current"])
                comment = "상승장 기대! 아파트를 공격적으로 매수합니다." if mood_good else "장기적으로 아파트가 답이죠."
            else:
                comment = "마땅한 아파트가 없어 이번엔 쉽니다."
        elif style=="안정형":
            # 현금 충분 + 안전할 때만, 대출 없이 살 수 있는 것만
            affordable = [L for L in cands if L["current"]<=npc["capital"]]
            if mood_good and affordable and npc["debt"]==0:
                pick = min(affordable, key=lambda x:x["current"])
                comment = "여유 자금으로 안전하게 한 채 담았습니다."
            else:
                comment = "시장이 불안정해 현금을 지키겠습니다."
        else:  # 수익형
            # 월세수익형(아파트 제외) 중 월세 높은 것
            rentals = [L for L in cands if L["type"]!="아파트"]
            if rentals:
                pick = max(rentals, key=lambda x:x["monthly"])
                comment = f"월세 {pick['monthly']}만원! 현금흐름 좋은 매물을 확보합니다."
            else:
                comment = "수익형 매물이 없어 관망합니다."
        # 매수 실행
        if pick:
            cost = pick["current"]
            if cost>npc["capital"]:
                # 공격형만 대출 감수, 나머지는 포기
                if style=="공격형":
                    npc["debt"] += cost-npc["capital"]; npc["capital"]=0
                else:
                    pick=None; comment="자금이 부족해 이번엔 매수를 보류합니다."
            else:
                npc["capital"]-=cost
            if pick:
                buy_copy=dict(pick); buy_copy["purchase_price"]=cost
                npc["owned"].append(buy_copy)
        S["npc_comments"][name]=comment

def new_turn():
    S["news"]=S["next_news"] or random.choice(NEWS_POOL)
    S["next_news"]=random.choice(NEWS_POOL)
    # 시장 신뢰도 갱신 (뉴스 호재/악재 반영)
    if S["news"]["mood"]=="good": S["confidence"]=min(100,S["confidence"]+random.randint(5,12))
    else: S["confidence"]=max(0,S["confidence"]-random.randint(5,12))
    apply_market(S["news"], S["region"])
    if S["news"]["rate"]: S["loan_rate"]=max(1.0,S["loan_rate"]+S["news"]["rate"])
    scout(S["region"])
    # NPC 투자자 의사결정 (룰 기반 · API 호출 없음)
    if S["npcs"]:
        try: run_npc_turn()
        except Exception: pass
    turn_finance()
    # 인생 이벤트 (매 턴 35% 확률 · 5턴이라 자주)
    S["life_event"]=None
    if S["turn"]>1 and random.random()<0.4:
        ev=random.choice(LIFE_EVENTS)
        S["capital"]=max(0,S["capital"]+ev["cap"])
        S["life_event"]=ev
        S["log"].append(f"{START_YEAR+S['turn']-1}년: {ev['icon']} {ev['name']}")
    S["max_debt"]=max(S["max_debt"],S["debt"])
    # 연도별 순자산 추이 기록 (그래프용)
    cur_year=START_YEAR+S["turn"]-1
    nw_now=S["capital"]+sum(L["current"] for L in S["owned"])-S["debt"]
    S["networth_history"]=[h for h in S["networth_history"] if h[0]!=cur_year]+[(cur_year, nw_now)]
    check_achievements()
    S["news_popup"]=True  # 턴 시작 뉴스 팝업
    S["selected"]=None; S["quiz"]=None; S["appraised"]=None

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

def max_loan_for(cost):
    """LTV 60%: 건물값의 60%까지만 대출 가능"""
    return int(cost*LTV)

def can_buy(L):
    """매수 가능 여부 (현금 + 최대대출 + 보증금회수 >= 건물값)"""
    cost=L["current"]
    return S["capital"]+max_loan_for(cost)+L["deposit"] >= cost

def buy(lid):
    L=next(x for x in S["market"] if x["id"]==lid)
    cost=L["current"]
    deposit=L["deposit"]  # 세입자 보증금 = 그만큼 현금 부담 감소
    # 실제 필요한 자기자본 = 건물값 - 보증금
    need_cash = cost - deposit
    year=START_YEAR+S["turn"]-1
    if need_cash > S["capital"]:
        loan = need_cash - S["capital"]
        max_l = max_loan_for(cost)
        if loan > max_l:
            return False  # LTV 초과 — 매수 불가
        S["debt"]+=loan; S["capital"]=0
        S["log"].append(f"{year}년: {L['name']} 매수 (대출 {won(loan)})")
    else:
        S["capital"]-=need_cash
        S["log"].append(f"{year}년: {L['name']} 매수")
    S["deposit_total"]+=deposit
    L["purchase_price"]=cost; S["owned"].append(L)
    S["market"]=[x for x in S["market"] if x["id"]!=lid]
    S["buy_count"]+=1
    if L["type"]=="아파트": S["apt_count"]+=1
    else: S["rent_count"]+=1
    S["max_debt"]=max(S["max_debt"],S["debt"])
    if L.get("rare"): unlock_achievement("rare_get")
    check_achievements()
    return True

def sell(i):
    L=S["owned"][i]; S["capital"]+=L["current"]-L["deposit"]
    S["deposit_total"]-=L["deposit"]
    p=L["current"]-L["purchase_price"]
    if p>=0: S["win_streak"]+=1
    else: S["win_streak"]=0
    year=START_YEAR+S["turn"]-1
    S["log"].append(f"{year}년: {L['name']} 매도 (손익 {'+' if p>=0 else ''}{won(p)})")
    S["owned"].pop(i)
    check_achievements()

def advance():
    if S["turn"]>=TURN_MAX:
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
.popup-impact{font-size:15px !important;color:#FFE08a;margin-top:12px;line-height:1.5;font-weight:600;}
.news-impact{font-size:14px !important;color:#FFE08a;margin-top:6px;line-height:1.5;}
.pred-sub{font-size:12px !important;color:#bda8d8;margin-bottom:10px;}
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
.pred-block{padding:8px 0;border-bottom:1px solid rgba(255,255,255,.08);}
.pred-block:last-child{border-bottom:none;}
.pb-label{font-size:13px !important;color:#bda8d8;font-weight:700;margin-bottom:3px;}
.pb-main{font-size:15px !important;font-weight:800;color:#fff;}
.pb-desc{font-size:13px !important;color:#cfe0f2;margin-top:2px;line-height:1.4;}
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
.gc-rec{font-size:13px !important;color:#7CFFAA;font-weight:700;margin-top:6px;}
.ap-head{font-size:13px !important;font-weight:800;color:#FFC233;margin-bottom:6px;}
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
.graph-cap{text-align:center;font-size:15px !important;font-weight:700;margin-top:10px;}
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
/* 초간단 게임방법 박스 */
.quick-guide{background:linear-gradient(135deg,#FF4136,#FF6b5e);border-radius:14px;padding:14px 18px;margin-bottom:12px;box-shadow:0 4px 16px rgba(255,65,54,.3);}
.qg-title{font-size:17px !important;font-weight:900;color:#fff;margin-bottom:8px;}
.qg-steps{display:flex;flex-wrap:wrap;gap:8px 18px;}
.qg-steps span{font-size:14px !important;color:#fff;font-weight:600;}
.qg-steps b{color:#FFE08a;}
/* 시장 진행 경고 */
.turn-warn{background:rgba(255,194,51,.14);border:1px solid #FFC233;border-radius:10px;padding:10px 13px;margin-bottom:8px;font-size:13px !important;color:#FFE0a0;line-height:1.5;}
.appr-help{background:rgba(52,152,219,.1);border:1px solid #3498db;border-radius:10px;padding:9px 12px;margin-bottom:8px;font-size:12px !important;color:#bdd8f0;line-height:1.7;}
/* 무기 선택 화면 */
.weapon-intro{background:rgba(255,255,255,.06);border-radius:12px;padding:14px 18px;margin-bottom:16px;font-size:15px !important;color:#dce6f2;line-height:1.6;}
.weapon-card{background:linear-gradient(135deg,#243b5a,#1a2e4a);border:2px solid #3a5a80;border-radius:16px;padding:18px 14px;text-align:center;min-height:230px;margin-bottom:8px;}
.wc-icon{font-size:46px !important;}
.wc-name{font-size:19px !important;font-weight:900;color:#FFD700;margin:8px 0 2px;}
.wc-sub{font-size:13px !important;color:#9fb4d0;margin-bottom:10px;}
.wc-desc{font-size:14px !important;color:#e4eef8;line-height:1.5;min-height:66px;}
.wc-best{font-size:13px !important;color:#7CFFAA;font-weight:700;margin-top:8px;}
.weapon-picked{background:rgba(255,215,0,.12);border:1px solid #FFD700;border-radius:10px;padding:12px;text-align:center;font-size:16px !important;color:#fff;margin-bottom:14px;}
.quiz-box{background:#1a2e4a;border:1.5px solid #FF6b5e;border-radius:14px;padding:18px;margin-bottom:14px;text-align:center;}
.quiz-q{font-size:16px !important;font-weight:800;color:#FF8b7e;margin-bottom:10px;}
.quiz-def{font-size:18px !important;color:#fff;font-weight:600;line-height:1.5;}
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
    ("🎯 목표","<b>5년 동안 부동산 투자로 가장 부자가 되세요!</b> AI 투자자 3명과 경쟁합니다."),
    ("① 무기 고르기","게임 시작 전 <b>나만의 투자법(무기)</b>을 골라요. ⚔️검(월세)·🏹활(시세)·🛡️방패(건축비) 중 하나!"),
    ("② 매물 고르기","매년 부동산 3채가 나와요. <b>🟢 구매하기</b>를 누르면 바로 내 거! 한 해에 여러 채도 가능해요."),
    ("③ 감정평가","<b>🔍 내 무기로 감정평가</b>를 누르면 진짜 가치가 나와요. 가격보다 가치가 높으면 <b>이득</b>!"),
    ("④ 대출 (LTV 60%)","돈이 모자라면 대출! 단 <b>집값의 60%까지만</b> 빌릴 수 있어요. 무리한 빚은 위험해요."),
    ("📅 한 해 넘기기","<b>다음 해로 넘어가기</b>를 누르면 1년이 지나고 새 매물이 나와요. (이전 매물은 사라져요!)"),
    ("📢 뉴스와 인생","좋은 뉴스 나오면 집값 ↑, 나쁜 뉴스 나오면 집값 ↓. 갑자기 결혼·승진·병원비 같은 인생 이벤트도 생겨요. 항상 대비하세요!"),
]

# 감정평가법 쉬운 설명 (툴팁용)
APPRAISAL_EASY = {
    "수익환원법":"💰 수익환원법 → 월세 수익으로 값을 매겨요 (오피스텔·상가에 적합)",
    "거래사례비교법":"📊 거래사례비교법 → 주변 비슷한 거래로 값을 매겨요 (아파트에 적합)",
    "원가법":"🏗 원가법 → 건축비로 값을 매겨요 (시세 반영이 약해 참고용)",
}

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

    # 🎮 초간단 설명 (항상 노출 · 중학생도 1분 이해)
    st.markdown('''<div class="quick-guide">
      <div class="qg-title">🎮 30초 요약</div>
      <div class="qg-steps">
        <span><b>1.</b> 투자 무기 고르기 ⚔️</span>
        <span><b>2.</b> 매물 보고 🟢 구매하기</span>
        <span><b>3.</b> 📅 다음 해로 넘기기</span>
        <span><b>4.</b> 5년 동안 가장 부자 되면 승리 🏆</span>
      </div>
    </div>''', unsafe_allow_html=True)

    # 지역 선택 버튼
    cols=st.columns(3)
    lc={"서울":"#3498db","대전":"#FFC233","제주":"#FF6347"}
    for col,(k,r) in zip(cols,REGIONS.items()):
        with col:
            c=lc[k]
            st.markdown(f"""<div class="region-card"><div class="rc-icon">{r['icon']}</div>
              <div class="rc-name">{k}</div><div class="rc-level" style="background:{c}22;color:{c};">{r['level']}</div>
              <div class="rc-desc">{r['desc']}<br><b style="color:#fff;">초기자본 {won(r['capital'])}</b></div></div>""", unsafe_allow_html=True)
            if st.button(f"▶ {k} 시작하기", key=f"go_{k}", use_container_width=True):
                S["region"]=k; S["phase"]="weapon"; S["capital"]=r["capital"]
                st.rerun()

# ─────────────────────────────────────────────────────
# 화면 A-2: 투자법(무기) 선택 + 자격 퀴즈
# ─────────────────────────────────────────────────────
elif S["phase"]=="weapon":
    rk=S["region"]; R=REGIONS[rk]
    st.markdown(f'<div class="g-title">⚔️ 나의 투자 무기를 골라라! — {rk}</div>', unsafe_allow_html=True)
    st.markdown('''<div class="weapon-intro">부동산의 <b>진짜 가치</b>를 계산하는 나만의 방법을 하나 고르세요.<br>
      게임 내내 이 방법으로 매물을 감정합니다. <b>매물 종류에 맞는 무기</b>를 고르면 더 정확해요!</div>''', unsafe_allow_html=True)

    if not S.get("my_method"):
        wc=st.columns(3)
        for col,(m,info) in zip(wc, APPRAISAL.items()):
            with col:
                st.markdown(f"""<div class="weapon-card">
                  <div class="wc-icon">{info['weapon'].split()[0]}</div>
                  <div class="wc-name">{info['weapon']}</div>
                  <div class="wc-sub">({m})</div>
                  <div class="wc-desc">{info['easy']}</div>
                  <div class="wc-best">👍 추천: {info['best_txt']}</div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"이 무기 선택", key=f"wp_{m}", use_container_width=True):
                    S["my_method"]=m; S["quiz"]=None; st.rerun()
    else:
        # 자격 퀴즈 (선택한 방법 1문제)
        m=S["my_method"]; info=APPRAISAL[m]
        st.markdown(f'<div class="weapon-picked">선택한 무기: <b>{info["weapon"]}</b> ({m})</div>', unsafe_allow_html=True)
        if S.get("quiz") is None:
            # 선택지: 정답 + 오답 2개
            others=[x for x in APPRAISAL if x!=m]
            opts=[m]+random.sample(others,2); random.shuffle(opts)
            S["quiz"]={"opts":opts,"done":False}
        q=S["quiz"]
        st.markdown(f'''<div class="quiz-box"><div class="quiz-q">📝 자격 시험: 다음 설명에 맞는 투자법은?</div>
          <div class="quiz-def">"{info['easy']}"</div></div>''', unsafe_allow_html=True)
        qc=st.columns(3)
        for col,opt in zip(qc,q["opts"]):
            with col:
                if st.button(APPRAISAL[opt]["weapon"], key=f"qz_{opt}", use_container_width=True):
                    if opt==m:
                        ph=st.empty()
                        for msg in ["📜 채점 중...","🎉 정답!","🏅 평가사 자격 취득!"]:
                            ph.markdown(f'<div style="text-align:center;padding:30px;font-size:22px;font-weight:800;color:#2ecc71;">{msg}</div>', unsafe_allow_html=True)
                            time.sleep(0.5)
                        ph.empty()
                        S["phase"]="play"; init_npcs()
                        S["next_news"]=random.choice(NEWS_POOL); new_turn(); st.rerun()
                    else:
                        st.error("❌ 다시 골라보세요! (선택한 무기 설명을 다시 읽어보세요)")
        if st.button("← 다른 무기 다시 고르기", key="wp_reset"):
            S["my_method"]=None; S["quiz"]=None; st.rerun()

# ─────────────────────────────────────────────────────
# 화면 B: 플레이
# ─────────────────────────────────────────────────────
elif S["phase"]=="play":
    rk=S["region"]; R=REGIONS[rk]

    # ===== 턴 시작 뉴스 팝업 (확인 눌러야 진입) =====
    if S["news_popup"] and S["news"]:
        n=S["news"]
        is_good=n["mood"]=="good"
        cur_year=START_YEAR+S["turn"]-1
        badge=f"📈 {cur_year}년 좋은 소식" if is_good else f"🚨 {cur_year}년 주의 소식"
        acc="#2ecc71" if is_good else "#FF4136"
        st.markdown(f"""
        <div class="popup-stage">
          <div class="popup-card" style="border-color:{acc};">
            <div class="popup-badge" style="background:{acc};">{badge}</div>
            <div class="popup-head">{n['head']}</div>
            <div class="popup-info"><span style="color:{acc};">▸</span> {n['i1']} · {n['i2']}</div>
            <div class="popup-impact">💡 {n.get('impact','')}</div>
          </div>
        </div>""", unsafe_allow_html=True)
        # 인생 이벤트 알림
        if S["life_event"]:
            ev=S["life_event"]
            cap_txt = f"현금 {'+' if ev['cap']>=0 else '−'}{won(abs(ev['cap']))}" if ev['cap'] else ""
            st.markdown(f"""<div class="life-toast">{ev['icon']} <b>인생 이벤트: {ev['name']}</b><br>
              <span style="font-size:14px;">{ev['effect']}</span><br>
              <span style="font-size:15px;font-weight:800;color:#fff;">{cap_txt}</span></div>""", unsafe_allow_html=True)
        c1,c2,c3=st.columns([1,1,1])
        with c2:
            if st.button("✅ 확인!", use_container_width=True, key="news_ok"):
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
        st.markdown(f'<div class="rank-board"><div class="rank-title">🏆 AI 투자 리그 · 실시간 순위 (턴 {S["turn"]}/{TURN_MAX})</div>{rows}</div>', unsafe_allow_html=True)
        # NPC 코멘트
        if S["npc_comments"]:
            cmts=""
            for name,cmt in S["npc_comments"].items():
                if cmt: cmts+=f'<div class="npc-cmt">{NPCS[name]["emoji"]} <b>{name}</b>: "{cmt}"</div>'
            if cmts: st.markdown(f'<div class="npc-cmt-box">{cmts}</div>', unsafe_allow_html=True)


    # sticky 스탯 (스크롤 따라옴)
    mi=int(S["debt"]*(S["loan_rate"]/100)/12); rent=sum(L["monthly"] for L in S["owned"])
    cur_year=START_YEAR+S["turn"]-1
    st.markdown(f"""<div class="sticky-stat"><div class="stat-grid">
      <div class="stat-card"><div class="sl">💰 현금</div><div class="sv">{won(S['capital'])}</div></div>
      <div class="stat-card"><div class="sl">🏦 대출</div><div class="sv {'danger' if S['debt']>0 else ''}">{won(S['debt'])}</div></div>
      <div class="stat-card"><div class="sl">🔐 보증금</div><div class="sv">{won(S['deposit_total'])}</div></div>
      <div class="stat-card"><div class="sl">월이자</div><div class="sv {'danger' if mi>0 else ''}">{won(mi)}</div></div>
      <div class="stat-card"><div class="sl">대출이율</div><div class="sv">{S['loan_rate']:.1f}%</div></div>
      <div class="stat-card"><div class="sl">월세수입</div><div class="sv">{won(rent)}</div></div>
      <div class="stat-card"><div class="sl">보유</div><div class="sv">{len(S['owned'])}채</div></div>
      <div class="stat-card"><div class="sl">📅 연도</div><div class="sv">{cur_year}</div></div>
    </div></div>""", unsafe_allow_html=True)

    left,right=st.columns([1.15,0.85],gap="large")

    with left:
        st.markdown('<div class="bright-bg">', unsafe_allow_html=True)
        # 1) 현재 뉴스 (상황 인식)
        if S["news"]:
            nc="news-good" if S["news"]["mood"]=="good" else "news-bad"
            st.markdown(f"""<div class="news {nc}"><div class="news-head">{S['news']['head']}</div>
              <div class="news-info">📌 {S['news']['i1']} · {S['news']['i2']}</div>
              <div class="news-impact">💡 {S['news'].get('impact','')}</div></div>""", unsafe_allow_html=True)

        # 2) 내년 시장 예측 카드 (사용자 친화적)
        if S["next_news"]:
            nn=S["next_news"]
            next_year=START_YEAR+S["turn"]
            is_good=nn["mood"]=="good"
            # 시장 분위기 (쉬운 문장)
            if is_good:
                mood_line="📈 내년에 부동산 가격 상승 예상"; mood_col="#2ecc71"
                advice_t="올해 매수 추천"; advice_d="가격 오르기 전에 미리 사두는 게 유리할 수 있어요."
            else:
                mood_line="📉 내년에 부동산 가격 하락 예상"; mood_col="#FF4136"
                advice_t="올해는 관망 추천"; advice_d="내년에 더 싸고 좋은 매물이 나올 수 있어요."
            # AI 예측 신뢰도 (위험도 대신) — 턴마다 안정적
            conf_lv = 4 if is_good else 3
            conf_stars="★"*conf_lv+"☆"*(5-conf_lv)
            conf_txt="AI가 비교적 높은 확률로 예측하고 있어요." if conf_lv>=4 else "AI 예측이지만 빗나갈 수도 있어요."
            # 예상 이슈 = 다음 뉴스 제목 + 영향
            issue=nn['head'].split(' ',1)[1] if ' ' in nn['head'] else nn['head']
            issue_effect=nn.get('impact','')
            st.markdown(f"""<div class="predict-card">
              <div class="pred-head">🔮 {next_year}년 부동산 시장 예측 AI 리포트</div>
              <div class="pred-sub">AI가 내년 시장을 분석했어요. (실제 결과와 다를 수 있어요)</div>
              <div class="pred-block">
                <div class="pb-label">🏘️ 부동산 시장 분위기</div>
                <div class="pb-main" style="color:{mood_col};">{mood_line}</div>
              </div>
              <div class="pred-block">
                <div class="pb-label">🎯 AI 예측 신뢰도</div>
                <div class="pb-main" style="color:#FFC233;">{conf_stars}</div>
                <div class="pb-desc">{conf_txt}</div>
              </div>
              <div class="pred-block">
                <div class="pb-label">📌 내년도 예상 이슈</div>
                <div class="pb-main">{issue}</div>
                <div class="pb-desc">{issue_effect}</div>
              </div>
              <div class="pred-block">
                <div class="pb-label">💡 AI 추천 행동</div>
                <div class="pb-main" style="color:{mood_col};">{advice_t}</div>
                <div class="pb-desc">{advice_d}</div>
              </div>
            </div>""", unsafe_allow_html=True)

        # 3) 이번 턴 매물 (게임 카드 · 구매 버튼 직결)
        st.markdown('<div class="ptitle">🏢 올해 나온 매물 3채 (골라서 바로 구매!)</div>', unsafe_allow_html=True)
        my_m = S["my_method"]; my_info = APPRAISAL[my_m]
        for L in S["market"]:
            spec=TYPE_SPEC[L["type"]]
            rare=L.get("rare",False)
            growth=min(5,max(1,int((spec["appr"][1])*40)))
            stable=min(5,max(1,6-int(R["vol"]*30)))
            rent_r=min(5,max(1,int(spec["yield"][1]*70)))
            def stars(n): return "★"*n+"☆"*(5-n)
            # 추천 투자법 (이 매물 유형에 맞는 무기)
            rec_method = next((m for m,info in APPRAISAL.items() if L["type"] in info["best_for"]), "거래사례비교법")
            rec_w = APPRAISAL[rec_method]["weapon"]
            rare_tag='<span class="rare-badge">🌟 희귀 투자 기회</span>' if rare else ""
            card_cls="game-card rare" if rare else "game-card"
            # 대출 안내
            max_l = max_loan_for(L["current"])
            need_cash = max(0, L["current"]-L["deposit"]-S["capital"])
            buyable = can_buy(L)
            st.markdown(f"""<div class="{card_cls}">
              <div class="gc-thumb">{type_thumb(L['type'],72)}</div>
              <div class="gc-body">
                <div class="gc-name">{L['name']}{rare_tag}</div>
                <div class="gc-meta">{L['type']} · {L['area']}㎡</div>
                <div class="gc-stars"><span>성장성</span> <b style="color:#FF6b5e;">{stars(growth)}</b></div>
                <div class="gc-stars"><span>안정성</span> <b style="color:#3498db;">{stars(stable)}</b></div>
                <div class="gc-stars"><span>월세력</span> <b style="color:#2ecc71;">{stars(rent_r)}</b></div>
                <div class="gc-price">💵 가격 <b>{won(L['current'])}</b> · 🏠 월세 {L['monthly']}만 · 🔐 보증금 {won(L['deposit'])}</div>
                <div class="gc-rec">👍 이 매물 추천 투자법: {rec_w}</div>
              </div>
            </div>""", unsafe_allow_html=True)
            b1,b2=st.columns(2)
            with b1:
                if st.button(f"🔍 내 무기로 감정평가", key=f"ap_{L['id']}", use_container_width=True):
                    v,steps,tip=do_appraise(my_m,L)
                    S["appraised"]={"id":L["id"],"v":v,"steps":steps,"tip":tip}
                    st.rerun()
            with b2:
                if st.button(f"🟢 구매하기", key=f"buy_{L['id']}", use_container_width=True, disabled=not buyable):
                    ph=st.empty()
                    for msg in ["💰 계약 체결 중...","✍️ 계약서 작성 중...","🏠 소유권 이전 완료!"]:
                        ph.markdown(f'<div class="turn-loading">{msg}</div>', unsafe_allow_html=True)
                        time.sleep(0.4)
                    ph.empty()
                    buy(L["id"]); S["appraised"]=None; st.rerun()
            if not buyable:
                st.caption(f"⚠️ 현금이 부족해요. 대출은 집값의 60%({won(max_l)})까지만 가능합니다.")
            # 감정평가 결과 (이 매물 것만)
            if S.get("appraised") and S["appraised"]["id"]==L["id"]:
                ap=S["appraised"]
                st.markdown(f'<div class="ap-box"><div class="ap-head">{my_info["weapon"]}로 감정평가한 결과</div>'+"".join(f'<div class="ap-step">{s}</div>' for s in ap["steps"])+'</div>', unsafe_allow_html=True)
                diff=ap["v"]-L["current"]
                if diff>2000: st.success(f"💎 저평가! 진짜 가치가 가격보다 {won(abs(diff))} 높아요 (사면 이득!)")
                elif diff<-2000: st.warning(f"⚠️ 고평가! 진짜 가치가 가격보다 {won(abs(diff))} 낮아요 (비싼 편)")
                else: st.info("📊 적정 가격대예요")
                if "⚠️" in ap["tip"]: st.caption(ap["tip"])
                else: st.caption(ap["tip"])
            st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

        # 인벤토리
        st.markdown('<div class="ptitle" style="margin-top:14px;">🏦 보유 매물 (인벤토리)</div>', unsafe_allow_html=True)
        if S["owned"]:
            st.caption("🟢 상승세 = 산 값보다 올랐어요 · 🟡 정체 = 거의 그대로 · 🔴 하락세 = 산 값보다 떨어졌어요")
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
        st.markdown('''<div class="turn-warn">⚠️ 다음 해로 넘어가면 <b>현재 매물 3채는 사라지고</b> 새 매물이 나옵니다.<br>사고 싶은 매물은 <b>먼저 구매</b>하세요!</div>''', unsafe_allow_html=True)
        cur_y=START_YEAR+S["turn"]-1
        if S["turn"]<TURN_MAX:
            if st.button(f"📅 {cur_y+1}년으로 넘어가기", use_container_width=True): advance()
        else:
            if st.button(f"🏁 게임 끝내고 결과 보기", use_container_width=True): advance()

    with right:
        st.markdown('<div class="ptitle">📊 시장 디스플레이</div>', unsafe_allow_html=True)
        total_asset=S["capital"]+sum(L["current"] for L in S["owned"])
        my_w = APPRAISAL[S["my_method"]]["weapon"] if S.get("my_method") else "미선택"
        st.markdown(f"""<div class="display">
          <div class="disp-item"><span class="disp-label">총 자산</span><br>{won(total_asset)}</div>
          <div class="disp-item"><span class="disp-label">순자산 (자산-부채)</span><br>{won(total_asset-S['debt'])}</div>
          <div class="disp-item"><span class="disp-label">누적 대출이자</span><br>{won(S['total_interest'])}</div>
          <div class="disp-item"><span class="disp-label">내 투자 무기</span><br>{my_w}</div>
        </div>""", unsafe_allow_html=True)
        if S["log"]:
            st.markdown('<div class="ptitle" style="margin-top:12px;">📜 거래 기록</div>', unsafe_allow_html=True)
            for e in reversed(S["log"][-6:]):
                if "매수" in e: lc="#2ecc71"
                elif "매도" in e: lc="#FF6347"
                else: lc="#9fb4d0"
                st.markdown(f'<div class="log-card" style="border-left:3px solid {lc};">{e}</div>', unsafe_allow_html=True)

        # ── AI 기능 패널 (통합 + 캐싱으로 429 방지) ──
        st.markdown('<div class="ptitle" style="margin-top:14px;">🤖 AI 투자 분석</div>', unsafe_allow_html=True)
        sel_obj = next((x for x in S["market"] if x["id"]==S["selected"]), None)
        st.caption("선택한 매물 + 현재 시장을 종합 분석합니다 (매수·보류·주의 판단)" if sel_obj
                   else "왼쪽에서 매물을 먼저 선택하면, 그 매물까지 함께 분석합니다.")

        if st.button("🤖 AI 투자 분석 실행", use_container_width=True, key="ai_analyze"):
            total_asset=S["capital"]+sum(L["current"] for L in S["owned"])
            owned_str="\n".join(f"- {L['name']}({L['type']}) 현재가 {won(L['current'])}" for L in S["owned"]) or "없음"
            news_str=S["news"]["head"] if S["news"] else "없음"
            next_str=S["next_news"]["head"] if S["next_news"] else "없음"
            # 캐시 키: 턴 + 선택매물 (같은 상황 재호출 방지)
            cache_key=f"ai_{S['turn']}_{S['selected']}"
            sel_block = (f"\n[선택한 매물]\n- {sel_obj['name']} ({sel_obj['type']}/{sel_obj['tag']}), "
                         f"호가 {won(sel_obj['current'])}, 월세 {sel_obj['monthly']}만, {sel_obj['area']}㎡" ) if sel_obj else "\n[선택한 매물] 없음 (시장 전체 관점에서 조언)"
            if cache_key in S.get("ai_cache",{}):
                result = S["ai_cache"][cache_key]
            else:
                prompt=f"""당신은 한국 부동산 투자 전문가입니다. 게임 플레이어에게 조언하세요.

[현재 상황] 턴 {S['turn']}/{TURN_MAX} · 현금 {won(S['capital'])} · 총자산 {won(total_asset)} · 대출 {won(S['debt'])}(이율 {S['loan_rate']:.1f}%) · 시장신뢰도 {S['confidence']}/100
[뉴스] 이번턴: {news_str} / 다음턴 예상: {next_str}
[보유매물]
{owned_str}{sel_block}

아래 형식으로 간결하게 한국어로 답하세요:
■ 투자 등급: (매수 추천 / 보류 / 주의) 중 하나
■ 추천 이유: 2문장
■ 위험 요인: 1~2가지
■ 한줄 총평: 한 문장"""
                with st.spinner("🤖 AI가 분석 중입니다..."):
                    result = call_gemini(prompt, 2048)
                if "ai_cache" not in S: S["ai_cache"]={}
                # 오류(429 등)는 캐시 안 함 → 다음에 재시도 가능
                if not result.startswith("⚠️"):
                    S["ai_cache"][cache_key]=result
            st.markdown(f'<div class="ai-box"><div class="ai-title">🤖 AI 투자 분석</div>{result}</div>', unsafe_allow_html=True)
            if result.startswith("⚠️"):
                st.caption("⏳ AI 요청이 잠시 몰렸어요. 10~20초 후 다시 눌러주세요. (무료 AI 사용량 제한)")

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
    inflation_adj=int(start*((1+INFLATION)**TURN_MAX-1))
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
      <tr><td>(−) 인플레이션 보정 (연 {INFLATION*100:.1f}%·{TURN_MAX}년)</td><td class="r">− {won(inflation_adj)}</td></tr>
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

        # 결산 AI 분석 (리그 승패 + 투자 성향을 한 번에 호출 → API 절약)
        if "ai_end_analysis" not in st.session_state:
            player_rank=next(i for i,(_,_,k,_) in enumerate(board) if k=="나")+1
            board_str="\n".join(f"{i+1}위 {lbl} 순자산 {won(nw)} 수익률 {(nw-start)/start*100:+.1f}%" for i,(lbl,nw,k,s) in enumerate(board))
            nw_end=player_nw
            prompt=f"""부동산 투자 시뮬레이션 게임({TURN_MAX}턴)이 끝났습니다. 아래 결과를 분석해주세요.

[최종 순위]
{board_str}
플레이어는 {player_rank}위입니다.

[플레이어 투자 기록]
- 총 매수 {S['buy_count']}회 (아파트 {S['apt_count']} / 수익형 {S['rent_count']})
- 최대 대출 {won(S['max_debt'])}, 최종 순자산 {won(nw_end)}
- 획득 업적: {', '.join(S['achievements']) if S['achievements'] else '없음'}

아래 두 부분으로 한국어로 답하세요:

【승패 요인】 플레이어가 왜 {player_rank}위가 되었는지 AI 투자자들과 비교해 4줄 내외로.
【투자 성향】 플레이어 성향(공격형/보수형/레버리지형/가치투자형/임대사업형 중 하나)과 강점·개선점을 3줄 내외로."""
            with st.spinner("🤖 게임 결과 분석 중..."):
                st.session_state["ai_end_analysis"]=call_gemini(prompt,2048)
        _end_ai = st.session_state.get("ai_end_analysis","")
        st.markdown(f'<div class="ai-box"><div class="ai-title">🤖 AI 게임 분석 — 승패 요인 & 투자 성향</div>{_end_ai}</div>', unsafe_allow_html=True)
        if _end_ai.startswith("⚠️"):
            st.caption("⏳ AI 요청이 몰렸어요. 페이지를 새로고침하면 다시 시도합니다.")

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

    # ── 연도별 자산 추이 그래프 ──
    # 최종 시점(현재 연도) 순자산도 반영
    final_year=START_YEAR+S["turn"]-1
    final_nw=S["capital"]+sum(L["current"] for L in S["owned"])-S["debt"]
    hist=[h for h in S["networth_history"] if h[0]!=final_year]+[(final_year, final_nw)]
    hist=sorted(hist, key=lambda x:x[0])
    if len(hist)>=2:
        st.markdown('<div class="ptitle" style="margin-top:16px;">📈 연도별 순자산 추이</div>', unsafe_allow_html=True)
        W,H,PAD=560,220,46
        ys=[nw for _,nw in hist]; xs=[y for y,_ in hist]
        ymin,ymax=min(ys),max(ys)
        if ymax==ymin: ymax=ymin+1
        def px(i): return PAD+(W-2*PAD)*i/(len(hist)-1)
        def py(v): return H-PAD-(H-2*PAD)*(v-ymin)/(ymax-ymin)
        # 시작자본 기준선
        start_cap=REGIONS[S["region"]]["capital"]
        pts=" ".join(f"{px(i):.0f},{py(v):.0f}" for i,(yr,v) in enumerate(hist))
        # 면적 채우기 경로
        area=f"M {px(0):.0f},{H-PAD} " + " ".join(f"L {px(i):.0f},{py(v):.0f}" for i,(yr,v) in enumerate(hist)) + f" L {px(len(hist)-1):.0f},{H-PAD} Z"
        dots=""; labels=""
        for i,(yr,v) in enumerate(hist):
            up = v>=start_cap
            dots+=f'<circle cx="{px(i):.0f}" cy="{py(v):.0f}" r="4.5" fill="{"#2ecc71" if up else "#FF6347"}" stroke="#fff" stroke-width="1.5"/>'
            labels+=f'<text x="{px(i):.0f}" y="{py(v)-12:.0f}" text-anchor="middle" font-size="12" font-weight="800" fill="#fff">{won(v)}</text>'
            labels+=f'<text x="{px(i):.0f}" y="{H-PAD+20:.0f}" text-anchor="middle" font-size="12" fill="#9fb4d0">{yr}년</text>'
        base_y=py(start_cap)
        svg=f'''<svg viewBox="0 0 {W} {H}" width="100%" style="background:#16273f;border-radius:14px;border:1px solid #2a4565;">
          <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#1B64DA" stop-opacity="0.4"/><stop offset="100%" stop-color="#1B64DA" stop-opacity="0"/>
          </linearGradient></defs>
          <line x1="{PAD}" y1="{base_y:.0f}" x2="{W-PAD}" y2="{base_y:.0f}" stroke="#FFC233" stroke-width="1" stroke-dasharray="5,4" opacity="0.6"/>
          <text x="{W-PAD}" y="{base_y-6:.0f}" text-anchor="end" font-size="11" fill="#FFC233">시작자본 {won(start_cap)}</text>
          <path d="{area}" fill="url(#g)"/>
          <polyline points="{pts}" fill="none" stroke="#3498db" stroke-width="3" stroke-linejoin="round"/>
          {dots}{labels}
        </svg>'''
        st.markdown(svg, unsafe_allow_html=True)
        # 한줄 요약
        change=final_nw-start_cap
        if change>=0:
            st.markdown(f'<div class="graph-cap" style="color:#2ecc71;">📈 {len(hist)}년 동안 순자산이 <b>{won(abs(change))}</b> 늘었어요!</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="graph-cap" style="color:#FF6347;">📉 {len(hist)}년 동안 순자산이 <b>{won(abs(change))}</b> 줄었어요.</div>', unsafe_allow_html=True)

    st.markdown('<div class="ptitle" style="margin-top:14px;">📜 전체 거래 기록</div>', unsafe_allow_html=True)
    for e in S["log"]: st.markdown(f'<div class="log-card">{e}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 다시 시작", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
