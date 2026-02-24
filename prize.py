import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import re
from datetime import datetime
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(page_title="메리츠화재 시상 현황", layout="wide")

# --- 데이터 영구 저장을 위한 폴더 설정 ---
DATA_DIR = "app_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- 🔒 추가 기능: 접속 로그 저장 함수 ---
LOG_FILE = os.path.join(DATA_DIR, "access_log.csv")

def save_log(user_name, user_code, action_type):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_data = pd.DataFrame([[now, user_name, user_code, action_type]], 
                            columns=["시간", "이름/구분", "코드", "작업"])
    if not os.path.exists(LOG_FILE):
        log_data.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
    else:
        log_data.to_csv(LOG_FILE, mode='a', header=False, index=False, encoding="utf-8-sig")

# --- 📋 추가 기능: 카카오톡 원클릭 복사 컴포넌트 ---
def copy_btn_component(text):
    escaped_text = json.dumps(text, ensure_ascii=False)
    js_code = f"""
    <div id="copy-container">
        <button id="copy-btn">💬 카카오톡 메시지 원클릭 복사</button>
    </div>
    <script>
    document.getElementById("copy-btn").onclick = function() {{
        const text = {escaped_text};
        navigator.clipboard.writeText(text).then(function() {{
            alert("메시지가 복사되었습니다! 원하시는 채팅창에 붙여넣기(Ctrl+V) 하세요.");
        }}, function(err) {{
            console.error('복사 실패:', err);
        }});
    }}
    </script>
    <style>
        #copy-btn {{
            width: 100%; height: 55px; background-color: #FEE500; color: #3C1E1E;
            border: none; border-radius: 12px; font-weight: 800; font-size: 1.1rem;
            cursor: pointer; margin-top: 5px; margin-bottom: 20px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }}
        #copy-btn:active {{ transform: scale(0.98); }}
    </style>
    """
    components.html(js_code, height=85)

# 데이터 불러오기 로직
if 'raw_data' not in st.session_state:
    st.session_state['raw_data'] = {}
    for file in os.listdir(DATA_DIR):
        if file.endswith('.pkl'):
            st.session_state['raw_data'][file.replace('.pkl', '')] = pd.read_pickle(os.path.join(DATA_DIR, file))

if 'config' not in st.session_state:
    config_path = os.path.join(DATA_DIR, 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            st.session_state['config'] = json.load(f)
    else:
        st.session_state['config'] = []

# 기존 데이터 호환성 보장
for c in st.session_state['config']:
    if 'category' not in c:
        c['category'] = 'weekly'

# 🌟 [오류 해결] 엑셀 외계어(_xHHHH_) 복원 및 정제 함수 🌟
def safe_str(val):
    if pd.isna(val) or val is None: return ""
    
    try:
        # 소수점으로 읽힌 사번 복구 (예: 12345.0 -> 12345)
        if isinstance(val, (int, float)) and float(val).is_integer():
            val = int(float(val))
    except:
        pass
        
    s = str(val)
    
    # 1. 엑셀의 숨겨진 16진수 외계어(_x0033_ 등)를 원래 문자(3 등)로 완벽 복원
    s = re.sub(r'_[xX]([0-9A-Fa-f]{4})_', lambda m: chr(int(m.group(1), 16)), s)
    
    # 2. 보이지 않는 띄어쓰기, 엔터, 탭 강제 삭제
    s = re.sub(r'\s+', '', s)
    
    # 3. 문자열에 남은 .0 잔재 제거
    if s.endswith('.0'): 
        s = s[:-2]
        
    # 4. 알파벳 대문자 통일 (매칭률 100% 보장)
    return s.upper()

# 🌟 [속도 100배 향상 핵심] 정제된 데이터를 캐싱하여 중복 연산 완전 제거 🌟
def get_clean_series(df, col_name):
    clean_col_name = f"_clean_{col_name}"
    # 한 번 정제된 컬럼이 없다면 최초 1회만 정제 연산을 수행하여 데이터프레임에 저장
    if clean_col_name not in df.columns:
        df[clean_col_name] = df[col_name].apply(safe_str)
    return df[clean_col_name]

def safe_float(val):
    if pd.isna(val) or val is None: return 0.0
    s = str(val).replace(',', '').strip()
    try: return float(s)
    except: return 0.0

# --- 🎨 커스텀 CSS (라이트/다크모드 완벽 대응) ---
st.markdown("""
<style>
    /* ========================================= */
    /* ☀️ 기본 모드 (Light Mode) CSS             */
    /* ========================================= */
    [data-testid="stAppViewContainer"] { background-color: #f2f4f6; color: #191f28; }
    span.material-symbols-rounded, span[data-testid="stIconMaterial"] { display: none !important; }
    
    div[data-testid="stRadio"] > div {
        display: flex; justify-content: center; background-color: #ffffff; 
        padding: 10px; border-radius: 15px; margin-bottom: 20px; margin-top: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03); border: 1px solid #e5e8eb;
    }
    
    .title-band {
        background-color: rgb(128, 0, 0); color: #ffffff; font-size: 1.4rem; font-weight: 800;
        text-align: center; padding: 16px; border-radius: 12px; margin-bottom: 24px;
        letter-spacing: -0.5px; box-shadow: 0 4px 10px rgba(128, 0, 0, 0.2);
    }

    [data-testid="stForm"] { background-color: transparent; border: none; padding: 0; margin-bottom: 24px; }

    /* 공통 텍스트 타이틀 클래스 */
    .admin-title { color: #191f28; font-weight: 800; font-size: 1.8rem; margin-top: 20px; }
    .sub-title { color: #191f28; font-size: 1.4rem; margin-top: 30px; font-weight: 700; }
    .config-title { color: #191f28; font-size: 1.3rem; margin: 0; font-weight: 700; }
    .main-title { color: #191f28; font-weight: 800; font-size: 1.3rem; margin-bottom: 15px; }
    .blue-title { color: #1e3c72; font-size: 1.4rem; margin-top: 10px; font-weight: 800; }
    .agent-title { color: #3182f6; font-weight: 800; font-size: 1.5rem; margin-top: 0; text-align: center; }

    /* 공통 박스 클래스 */
    .config-box { background: #f9fafb; padding: 15px; border-radius: 15px; border: 1px solid #e5e8eb; margin-top: 15px; }
    .config-box-blue { background: #f0f4f8; padding: 15px; border-radius: 15px; border: 1px solid #c7d2fe; margin-top: 15px; }
    .detail-box { background: #ffffff; padding: 20px; border-radius: 20px; border: 2px solid #e5e8eb; margin-top: 10px; margin-bottom: 30px; }

    /* 시책 요약 카드 (상단) */
    .summary-card { 
        background: linear-gradient(135deg, rgb(160, 20, 20) 0%, rgb(128, 0, 0) 100%); 
        border-radius: 20px; padding: 32px 24px; margin-bottom: 24px; border: none;
        box-shadow: 0 10px 25px rgba(128, 0, 0, 0.25);
    }
    .cumulative-card { 
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
        border-radius: 20px; padding: 32px 24px; margin-bottom: 24px; border: none;
        box-shadow: 0 10px 25px rgba(30, 60, 114, 0.25);
    }
    .summary-label { color: rgba(255,255,255,0.85); font-size: 1.15rem; font-weight: 600; margin-bottom: 8px; }
    .summary-total { color: #ffffff; font-size: 2.6rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 24px; white-space: nowrap; word-break: keep-all; }
    .summary-item-name { color: rgba(255,255,255,0.95); font-size: 1.15rem; }
    .summary-item-val { color: #ffffff; font-size: 1.3rem; font-weight: 800; white-space: nowrap; }
    .summary-divider { height: 1px; background-color: rgba(255,255,255,0.2); margin: 16px 0; }
    
    /* 개별 상세 카드 */
    .toss-card { 
        background: #ffffff; border-radius: 20px; padding: 28px 24px; 
        margin-bottom: 16px; border: 1px solid #e5e8eb; box-shadow: 0 4px 20px rgba(0,0,0,0.03); 
    }
    .toss-title { font-size: 1.6rem; font-weight: 700; color: #191f28; margin-bottom: 6px; letter-spacing: -0.5px; }
    .toss-desc { font-size: 1.15rem; color: rgb(128, 0, 0); font-weight: 800; margin-bottom: 24px; letter-spacing: -0.3px; line-height: 1.4; word-break: keep-all; }
    
    .data-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; flex-wrap: nowrap; }
    .data-label { color: #8b95a1; font-size: 1.1rem; word-break: keep-all; }
    .data-value { color: #333d4b; font-size: 1.3rem; font-weight: 600; white-space: nowrap; }
    
    /* 상위 구간 부족 금액 강조 디자인 */
    .shortfall-row { background-color: #fff0f0; padding: 14px; border-radius: 12px; margin-top: 15px; margin-bottom: 5px; border: 2px dashed #ff4b4b; text-align: center; }
    .shortfall-text { color: #d9232e; font-size: 1.2rem; font-weight: 800; word-break: keep-all; }

    .prize-row { display: flex; justify-content: space-between; align-items: center; padding-top: 20px; margin-top: 12px; flex-wrap: nowrap; }
    .prize-label { color: #191f28; font-size: 1.3rem; font-weight: 700; word-break: keep-all; white-space: nowrap; }
    .prize-value { color: rgb(128, 0, 0); font-size: 1.8rem; font-weight: 800; white-space: nowrap; text-align: right; } 
    
    .toss-divider { height: 1px; background-color: #e5e8eb; margin: 16px 0; }
    .sub-data { font-size: 1rem; color: #8b95a1; margin-top: 4px; text-align: right; }
    
    /* 누계 전용 세로 정렬 박스 */
    .cumul-stack-box {
        background: #ffffff; border: 1px solid #e5e8eb; border-left: 6px solid #2a5298; 
        border-radius: 16px; padding: 20px 24px; margin-bottom: 16px; 
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }
    .cumul-stack-info { display: flex; flex-direction: column; gap: 4px; }
    .cumul-stack-title { font-size: 1.25rem; color: #1e3c72; font-weight: 800; word-break: keep-all; }
    .cumul-stack-val { font-size: 1.05rem; color: #8b95a1; }
    .cumul-stack-prize { font-size: 1.6rem; color: #d9232e; font-weight: 800; text-align: right; white-space: nowrap; }
    
    /* 입력 컴포넌트 */
    div[data-testid="stTextInput"] input {
        font-size: 1.3rem !important; padding: 15px !important; height: 55px !important;
        background-color: #ffffff !important; color: #191f28 !important; border: 1px solid #e5e8eb !important; border-radius: 12px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.02);
    }
    div[data-testid="stSelectbox"] > div { background-color: #ffffff !important; border: 1px solid #e5e8eb !important; border-radius: 12px !important; }
    div[data-testid="stSelectbox"] * { font-size: 1.1rem !important; }
    
    /* 버튼 */
    div.stButton > button[kind="primary"] {
        font-size: 1.4rem !important; font-weight: 800 !important; height: 60px !important;
        border-radius: 12px !important; background-color: rgb(128, 0, 0) !important; color: white !important; border: none !important; width: 100%; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(128, 0, 0, 0.2) !important;
    }
    
    div.stButton > button[kind="secondary"] {
        font-size: 1.2rem !important; font-weight: 700 !important; min-height: 60px !important; height: auto !important; padding: 10px !important;
        border-radius: 12px !important; background-color: #e8eaed !important; color: #191f28 !important; border: 1px solid #d1d6db !important; width: 100%; margin-top: 5px; margin-bottom: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important; white-space: normal !important; 
    }

    .del-btn-container button {
        background-color: #f2f4f6 !important; color: #dc3545 !important; border: 1px solid #dc3545 !important;
        height: 40px !important; font-size: 1rem !important; margin-top: 0 !important; box-shadow: none !important;
    }

    /* ========================================= */
    /* 🌙 다크 모드 (Dark Mode) CSS              */
    /* ========================================= */
    @media (prefers-color-scheme: dark) {
        [data-testid="stAppViewContainer"] { background-color: #121212 !important; color: #e0e0e0 !important; }
        label, p, .stMarkdown p { color: #e0e0e0 !important; }
        div[data-testid="stRadio"] > div { background-color: #1e1e1e !important; border-color: #333 !important; }
        .admin-title, .sub-title, .config-title, .main-title { color: #ffffff !important; }
        .blue-title, .agent-title { color: #66b2ff !important; }
        .config-box { background-color: #1a1a1a !important; border-color: #333 !important; }
        .config-box-blue { background-color: #121928 !important; border-color: #2a5298 !important; }
        .detail-box { background-color: #121212 !important; border-color: #333 !important; }
        .toss-card { background-color: #1e1e1e !important; border-color: #333 !important; box-shadow: 0 4px 15px rgba(0,0,0,0.5) !important; }
        .toss-title { color: #ffffff !important; }
        .toss-desc { color: #ff6b6b !important; }
        .data-label { color: #a0aab5 !important; }
        .data-value { color: #ffffff !important; }
        .prize-label { color: #ffffff !important; }
        .prize-value { color: #ff4b4b !important; }
        .toss-divider { background-color: #333 !important; }
        .shortfall-row { background-color: #2a1215 !important; border-color: #ff4b4b !important; }
        .shortfall-text { color: #ff6b6b !important; }
        .cumul-stack-box { background-color: #1e1e1e !important; border-color: #333 !important; border-left-color: #4da3ff !important; box-shadow: 0 4px 15px rgba(0,0,0,0.5) !important; }
        .cumul-stack-title { color: #4da3ff !important; }
        .cumul-stack-val { color: #a0aab5 !important; }
        .cumul-stack-prize { color: #ff4b4b !important; }
        div[data-testid="stTextInput"] input { background-color: #1e1e1e !important; color: #ffffff !important; border-color: #444 !important; }
        div[data-testid="stSelectbox"] > div { background-color: #1e1e1e !important; color: #ffffff !important; border-color: #444 !important; }
        div.stButton > button[kind="secondary"] { background-color: #2d2d2d !important; color: #ffffff !important; border-color: #444 !important; }
    }
    
    @media (max-width: 450px) {
        .summary-total { font-size: 2.1rem !important; }
        .summary-label { font-size: 1.05rem !important; }
        .prize-label { font-size: 1.1rem !important; }
        .prize-value { font-size: 1.45rem !important; }
        .data-label { font-size: 1rem !important; }
        .data-value { font-size: 1.15rem !important; }
        .toss-title { font-size: 1.4rem !important; }
        .shortfall-text { font-size: 1.05rem !important; }
        .cumul-stack-box { padding: 16px 20px; flex-direction: row; }
        .cumul-stack-title { font-size: 1.15rem; }
        .cumul-stack-val { font-size: 0.95rem; }
        .cumul-stack-prize { font-size: 1.4rem; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ 공통 함수 (데이터 계산)
# ==========================================
def calculate_agent_performance(target_code):
    calculated_results = []
    
    for cfg in st.session_state['config']:
        df = st.session_state['raw_data'].get(cfg['file'])
        if df is None: continue
        col_code = cfg.get('col_code', '')
        if not col_code or col_code not in df.columns: continue
        
        # 🌟 속도 개선: 캐싱된 컬럼에서 즉시 비교 🌟
        clean_codes = get_clean_series(df, col_code)
        match_df = df[clean_codes == safe_str(target_code)]
        if match_df.empty: continue
        
        cat = cfg.get('category', 'weekly')
        p_type = cfg.get('type', '구간 시책')
        
        if cat == 'weekly':
            if "1기간" in p_type: 
                raw_prev = match_df[cfg['col_val_prev']].values[0] if cfg.get('col_val_prev') in df.columns else 0
                raw_curr = match_df[cfg['col_val_curr']].values[0] if cfg.get('col_val_curr') in df.columns else 0
                val_prev = safe_float(raw_prev)
                val_curr = safe_float(raw_curr)
                
                curr_req = float(cfg.get('curr_req', 100000.0))
                calc_rate, tier_prev, prize = 0, 0, 0
                
                if val_curr >= curr_req:
                    for amt, rate in cfg['tiers']:
                        if val_prev >= amt:
                            tier_prev = amt
                            calc_rate = rate
                            prize = (tier_prev + curr_req) * (calc_rate / 100)
                            break
                            
                shortfall_curr = curr_req - val_curr if val_curr < curr_req else 0
                            
                calculated_results.append({
                    "name": cfg['name'], "desc": cfg.get('desc', ''), "category": "weekly", "type": "브릿지1",
                    "val_prev": val_prev, "tier_prev": tier_prev,
                    "val_curr": val_curr, "curr_req": curr_req,
                    "rate": calc_rate, "prize": prize, "shortfall_curr": shortfall_curr
                })
                
            elif "2기간" in p_type:
                raw_curr = match_df[cfg['col_val_curr']].values[0] if cfg.get('col_val_curr') in df.columns else 0
                val_curr = safe_float(raw_curr)
                
                curr_req = float(cfg.get('curr_req', 100000.0))
                calc_rate, tier_achieved, prize = 0, 0, 0
                
                for amt, rate in cfg['tiers']:
                    if val_curr >= amt:
                        tier_achieved = amt
                        calc_rate = rate
                        break
                        
                if tier_achieved > 0:
                    prize = (tier_achieved + curr_req) * (calc_rate / 100)
                    
                next_tier = None
                for amt, rate in reversed(cfg['tiers']):
                    if val_curr < amt:
                        next_tier = amt
                        break
                shortfall = next_tier - val_curr if next_tier else 0
                
                calculated_results.append({
                    "name": cfg['name'], "desc": cfg.get('desc', ''), "category": "weekly", "type": "브릿지2",
                    "val": val_curr, "tier": tier_achieved, "rate": calc_rate, "prize": prize, 
                    "curr_req": curr_req, "next_tier": next_tier, "shortfall": shortfall
                })

            else: 
                raw_val = match_df[cfg['col_val']].values[0] if cfg.get('col_val') in df.columns else 0
                val = safe_float(raw_val)
                
                calc_rate, tier_achieved, prize = 0, 0, 0
                for amt, rate in cfg['tiers']:
                    if val >= amt:
                        tier_achieved = amt
                        calc_rate = rate
                        prize = tier_achieved * (calc_rate / 100) 
                        break
                        
                next_tier = None
                for amt, rate in reversed(cfg['tiers']):
                    if val < amt:
                        next_tier = amt
                        break
                shortfall = next_tier - val if next_tier else 0
                
                calculated_results.append({
                    "name": cfg['name'], "desc": cfg.get('desc', ''), "category": "weekly", "type": "구간",
                    "val": val, "tier": tier_achieved, "rate": calc_rate, "prize": prize,
                    "next_tier": next_tier, "shortfall": shortfall
                })
        
        elif cat == 'cumulative':
            col_val = cfg.get('col_val', '')
            raw_val = match_df[col_val].values[0] if col_val and col_val in match_df.columns else 0
            val = safe_float(raw_val)
            
            col_prize = cfg.get('col_prize', '')
            raw_prize = match_df[col_prize].values[0] if col_prize and col_prize in match_df.columns else 0
            prize = safe_float(raw_prize)
            
            calculated_results.append({
                "name": cfg['name'], "desc": cfg.get('desc', ''), "category": "cumulative", "type": "누계",
                "val": val, "prize": prize
            })
            
    total_prize_sum = sum(r['prize'] for r in calculated_results)
    return calculated_results, total_prize_sum

def render_ui_cards(user_name, calculated_results, total_prize_sum, show_share_text=False):
    if len(calculated_results) == 0: return

    weekly_res = [r for r in calculated_results if r['category'] == 'weekly']
    cumul_res = [r for r in calculated_results if r['category'] == 'cumulative']
    
    weekly_total = sum(r['prize'] for r in weekly_res)
    cumul_total = sum(r['prize'] for r in cumul_res)

    share_text = f"🎯 [{user_name} 팀장님 실적 현황]\n"
    share_text += f"💰 총 합산 시상금: {total_prize_sum:,.0f}원\n"
    share_text += "────────────────\n"

    if weekly_res:
        summary_html = (
            f"<div class='summary-card'>"
            f"<div class='summary-label'>{user_name} 팀장님의 시책 현황</div>"
            f"<div class='summary-total'>{weekly_total:,.0f}원</div>"
            f"<div class='summary-divider'></div>"
        )
        share_text += f"📌 [진행 중인 시책]\n"
        
        for res in weekly_res:
            if res['type'] in ["구간", "브릿지1"]:
                summary_html += f"<div class='data-row' style='padding: 6px 0;'><span class='summary-item-name'>{res['name']}</span><span class='summary-item-val'>{res['prize']:,.0f}원</span></div>"
                share_text += f"🔹 {res['name']}: {res['prize']:,.0f}원\n"
            else: 
                summary_html += f"<div class='data-row' style='padding: 6px 0; align-items:flex-start;'><span class='summary-item-name'>{res['name']}<br><span style='font-size:0.95rem; color:rgba(255,255,255,0.7);'>(다음 달 {int(res['curr_req']//10000)}만 가동 조건)</span></span><span class='summary-item-val'>{res['prize']:,.0f}원</span></div>"
                share_text += f"🔹 {res['name']}: {res['prize']:,.0f}원 (다음 달 {int(res['curr_req']//10000)}만 가동 조건)\n"
                
        summary_html += "</div>"
        st.markdown(summary_html, unsafe_allow_html=True)
        
        for res in weekly_res:
            desc_html = res['desc'].replace('\n', '<br>')
            shortfall_html = ""
            if res.get('shortfall', 0) > 0 and res.get('next_tier'):
                shortfall_html = f"<div class='shortfall-row'><span class='shortfall-text'>🚀 다음 {int(res['next_tier']//10000)}만 구간까지 {res['shortfall']:,.0f}원 남음!</span></div>"
            elif res.get('shortfall_curr', 0) > 0 and res.get('curr_req'):
                shortfall_html = f"<div class='shortfall-row'><span class='shortfall-text'>🚨 당월 필수목표({int(res['curr_req']//10000)}만)까지 {res['shortfall_curr']:,.0f}원 부족!</span></div>"
            
            if res['type'] == "구간":
                card_html = (
                    f"<div class='toss-card'>"
                    f"<div class='toss-title'>{res['name']}</div>"
                    f"<div class='toss-desc'>{desc_html}</div>"
                    f"<div class='data-row'><span class='data-label'>현재 누적 실적</span><span class='data-value'>{res['val']:,.0f}원</span></div>"
                    f"<div class='data-row'><span class='data-label'>도달한 구간 기준</span><span class='data-value'>{res['tier']:,.0f}원</span></div>"
                    f"<div class='data-row'><span class='data-label'>적용 지급률</span><span class='data-value'>{res['rate']:g}%</span></div>"
                    f"{shortfall_html}"
                    f"<div class='toss-divider'></div>"
                    f"<div class='prize-row'><span class='prize-label'>확보한 시상금</span><span class='prize-value'>{res['prize']:,.0f}원</span></div>"
                    f"</div>"
                )
                share_text += f"\n[{res['name']}]\n- 현재실적: {res['val']:,.0f}원\n- 확보금액: {res['prize']:,.0f}원\n"
                if res.get('shortfall', 0) > 0: share_text += f"🚀 다음 {int(res['next_tier']//10000)}만 구간까지 {res['shortfall']:,.0f}원 남음!\n"
            
            elif res['type'] == "브릿지1":
                card_html = (
                    f"<div class='toss-card'>"
                    f"<div class='toss-title'>{res['name']}</div>"
                    f"<div class='toss-desc'>{desc_html}</div>"
                    f"<div class='data-row'><span class='data-label'>전월 실적 (인정구간)</span><div style='text-align:right;'><div class='data-value'>{res['val_prev']:,.0f}원</div><div class='sub-data'>({res['tier_prev']:,.0f}원 구간)</div></div></div>"
                    f"<div class='data-row'><span class='data-label'>당월 실적 (목표 {res['curr_req']:,.0f}원)</span><span class='data-value'>{res['val_curr']:,.0f}원</span></div>"
                    f"<div class='data-row'><span class='data-label'>적용 지급률</span><span class='data-value'>{res['rate']:g}%</span></div>"
                    f"{shortfall_html}"
                    f"<div class='toss-divider'></div>"
                    f"<div class='prize-row'><span class='prize-label'>확보한 시상금</span><span class='prize-value'>{res['prize']:,.0f}원</span></div>"
                    f"</div>"
                )
                share_text += f"\n[{res['name']}]\n- 당월실적: {res['val_curr']:,.0f}원\n- 확보금액: {res['prize']:,.0f}원\n"
                if res.get('shortfall_curr', 0) > 0: share_text += f"🚨 당월 목표까지 {res['shortfall_curr']:,.0f}원 부족!\n"
                
            elif res['type'] == "브릿지2":
                card_html = (
                    f"<div class='toss-card'>"
                    f"<div class='toss-title'>{res['name']}</div>"
                    f"<div class='toss-desc'>{desc_html}</div>"
                    f"<div class='data-row'><span class='data-label'>당월 누적 실적</span><span class='data-value'>{res['val']:,.0f}원</span></div>"
                    f"<div class='data-row'><span class='data-label'>확보한 구간 기준</span><span class='data-value'>{res['tier']:,.0f}원</span></div>"
                    f"<div class='data-row'><span class='data-label'>예상 적용 지급률</span><span class='data-value'>{res['rate']:g}%</span></div>"
                    f"{shortfall_html}"
                    f"<div class='toss-divider'></div>"
                    f"<div class='prize-row'><span class='prize-label'>다음 달 {int(res['curr_req']//10000)}만 가동 시<br>시상금</span><span class='prize-value'>{res['prize']:,.0f}원</span></div>"
                    f"</div>"
                )
                share_text += f"\n[{res['name']}]\n- 당월실적: {res['val']:,.0f}원\n- 예상시상: {res['prize']:,.0f}원 (차월조건)\n"
                if res.get('shortfall', 0) > 0: share_text += f"🚀 다음 {int(res['next_tier']//10000)}만 구간까지 {res['shortfall']:,.0f}원 남음!\n"
                
            st.markdown(card_html, unsafe_allow_html=True)

    if cumul_res:
        cumul_html = (
            f"<div class='cumulative-card'>"
            f"<div class='summary-label'>{user_name} 팀장님의 월간 누계 시상</div>"
            f"<div class='summary-total'>{cumul_total:,.0f}원</div>"
            f"<div class='summary-divider'></div>"
        )
        
        share_text += f"\n🏆 [월간 확정 누계 시상]\n"
        for res in cumul_res:
            cumul_html += f"<div class='data-row' style='padding: 6px 0;'><span class='summary-item-name'>{res['name']}</span><span class='summary-item-val'>{res['prize']:,.0f}원</span></div>"
            share_text += f"🔹 {res['name']}: {res['prize']:,.0f}원 (누계 {res['val']:,.0f}원)\n"
        cumul_html += "</div>"
        st.markdown(cumul_html, unsafe_allow_html=True)
        
        st.markdown("<h3 class='blue-title'>📈 세부 항목별 시상금</h3>", unsafe_allow_html=True)
        
        stack_html = ""
        for res in cumul_res:
            stack_html += (
                f"<div class='cumul-stack-box'>"
                f"<div class='cumul-stack-info'>"
                f"<span class='cumul-stack-title'>{res['name']}</span>"
                f"<span class='cumul-stack-val'>누계실적: {res['val']:,.0f}원</span>"
                f"</div>"
                f"<div class='cumul-stack-prize'>{res['prize']:,.0f}원</div>"
                f"</div>"
            )
        st.markdown(stack_html, unsafe_allow_html=True)

    # 🌟 [수정된 부분] 텍스트 박스 대신 카카오톡 원클릭 복사 버튼 렌더링
    if show_share_text:
        st.markdown("<h4 class='main-title' style='margin-top:10px;'>💬 카카오톡 바로 공유하기</h4>", unsafe_allow_html=True)
        copy_btn_component(share_text)


# ==========================================
# 📱 1. 최상단: 메뉴 선택 탭
# ==========================================
mode = st.radio("화면 선택", ["📊 내 실적 조회", "👥 매니저 관리", "⚙️ 시스템 관리자"], horizontal=True, label_visibility="collapsed")

# ==========================================
# 👥 2. 매니저 관리 페이지 
# ==========================================
if mode == "👥 매니저 관리":
    st.markdown('<div class="title-band">매니저 소속 실적 관리</div>', unsafe_allow_html=True)
    
    if 'mgr_logged_in' not in st.session_state: st.session_state.mgr_logged_in = False
    
    if not st.session_state.mgr_logged_in:
        mgr_code = st.text_input("지원매니저 사번(코드)을 입력하세요", type="password", placeholder="예: 12345")
        if st.button("로그인", type="primary"):
            if not mgr_code:
                st.warning("지원매니저 코드를 입력해주세요.")
            else:
                is_valid = False
                safe_input_code = safe_str(mgr_code)
                all_valid_codes = set()
                
                # 🌟 속도 개선: 캐싱된 컬럼에서 검증 수행 🌟
                for cfg in st.session_state['config']:
                    mgr_col = cfg.get('col_manager_code', '') or cfg.get('col_manager', '')
                    if mgr_col:
                        df = st.session_state['raw_data'].get(cfg['file'])
                        if df is not None and mgr_col in df.columns:
                            clean_mgr_codes = get_clean_series(df, mgr_col)
                            for clean_val in clean_mgr_codes.unique():
                                if clean_val: all_valid_codes.add(clean_val)
                
                if safe_input_code in all_valid_codes:
                    is_valid = True
                
                if is_valid:
                    st.session_state.mgr_logged_in = True
                    st.session_state.mgr_code = safe_input_code 
                    st.session_state.mgr_step = 'main'
                    # 🌟 [로그 저장] 매니저 로그인 기록 🌟
                    save_log("매니저", safe_input_code, "MANAGER_LOGIN")
                    st.rerun()
                else:
                    st.error(f"❌ 입력하신 코드({mgr_code})가 등록된 실적 데이터에 존재하지 않습니다.")
                    st.info("💡 관리자 화면에서 '지원매니저코드 컬럼'이 정확히 지정되었는지 확인해주세요.")
                    if all_valid_codes:
                        sample_codes = ", ".join(list(all_valid_codes)[:10])
                        st.warning(f"🧐 (참고) 현재 시스템이 복원하여 인식하고 있는 정상 코드 예시:\n{sample_codes}")
    else:
        if st.button("🚪 로그아웃"):
            st.session_state.mgr_logged_in = False
            st.rerun()
        st.markdown('<br>', unsafe_allow_html=True)
        
        step = st.session_state.get('mgr_step', 'main')
        
        # --- (1) 메인 폴더 선택 ---
        if step == 'main':
            st.markdown("<h3 class='main-title'>어떤 실적을 확인하시겠습니까?</h3>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📁 구간실적 관리", use_container_width=True):
                    st.session_state.mgr_step = 'tiers'
                    st.session_state.mgr_category = '구간'
                    st.rerun()
            with col2:
                if st.button("📁 브릿지실적 관리", use_container_width=True):
                    st.session_state.mgr_step = 'tiers'
                    st.session_state.mgr_category = '브릿지'
                    st.rerun()
                
        # --- (2) 금액별 폴더 선택 ---
        elif step == 'tiers':
            if st.button("⬅️ 뒤로가기", use_container_width=False):
                st.session_state.mgr_step = 'main'
                st.rerun()
            
            cat = st.session_state.mgr_category
            
            my_agents = set()
            safe_login_code = st.session_state.mgr_code
            
            # 🌟 속도 개선: 캐싱된 컬럼 필터링으로 0.1초 만에 인원 수집 🌟
            for cfg in st.session_state['config']:
                if cfg.get('category') == 'cumulative': continue
                
                mgr_col = cfg.get('col_manager_code', '') or cfg.get('col_manager', '')
                col_code = cfg.get('col_code', '')
                if not mgr_col or not col_code: continue 
                
                df = st.session_state['raw_data'].get(cfg['file'])
                if df is None or mgr_col not in df.columns or col_code not in df.columns: continue
                
                clean_mgr_codes = get_clean_series(df, mgr_col)
                mask = clean_mgr_codes == safe_login_code
                
                clean_col_codes = get_clean_series(df, col_code)
                for ac in clean_col_codes[mask]:
                    if ac: my_agents.add(ac)
            
            st.markdown(f"<h3 class='main-title'>📁 {cat}실적 근접자 조회 (소속: 총 {len(my_agents)}명)</h3>", unsafe_allow_html=True)
            
            ranges = {
                500000: (300000, float('inf')),
                300000: (200000, 300000), 
                200000: (100000, 200000), 
                100000: (0, 100000)        
            }
            counts = {500000: 0, 300000: 0, 200000: 0, 100000: 0}
            
            for agent_code in my_agents:
                calc_results, _ = calculate_agent_performance(agent_code)
                matched_folders = set()
                
                for res in calc_results:
                    if cat == "구간" and "구간" not in res['type']: continue
                    if cat == "브릿지" and "브릿지" not in res['type']: continue
                    
                    val = res.get('val') if 'val' in res else res.get('val_curr', 0.0)
                    if val is None: val = 0.0
                    
                    for t, (min_v, max_v) in ranges.items():
                        if min_v <= val < max_v:
                            matched_folders.add(t)
                            break
                            
                for t in matched_folders:
                    counts[t] += 1
            
            for t, (min_v, max_v) in ranges.items():
                count = counts[t]
                if t == 500000: label = f"📁 50만 구간 근접 및 달성 (30만 이상) - 총 {count}명"
                else: label = f"📁 {int(t//10000)}만 구간 근접자 ({int(min_v//10000)}만 이상 ~ {int(max_v//10000)}만 미만) - 총 {count}명"
                
                if st.button(label, use_container_width=True, key=f"t_{t}"):
                    st.session_state.mgr_step = 'list'
                    st.session_state.mgr_target = t
                    st.session_state.mgr_min_v = min_v
                    st.session_state.mgr_max_v = max_v
                    st.session_state.mgr_agents = my_agents 
                    st.rerun()
                
# --- (3) 선택한 폴더 내 설계사 명단 확인 (내림차순 정렬 및 전월실적 추가) ---
        elif step == 'list':
            if st.button("⬅️ 폴더로 돌아가기", use_container_width=False):
                st.session_state.mgr_step = 'tiers'
                st.rerun()
            
            cat = st.session_state.mgr_category
            target = st.session_state.mgr_target
            min_v = st.session_state.mgr_min_v
            max_v = st.session_state.mgr_max_v
            my_agents = st.session_state.mgr_agents
            
            if target == 500000: st.markdown(f"<h3 class='main-title'>👥 50만 구간 근접 및 달성자 명단</h3>", unsafe_allow_html=True)
            else: st.markdown(f"<h3 class='main-title'>👥 {int(target//10000)}만 구간 근접자 명단</h3>", unsafe_allow_html=True)
            
            st.info("💡 이름을 클릭하면 상세 실적을 확인하고 카톡으로 전송할 수 있습니다.")
            
            near_agents = []
            for code in my_agents:
                calc_results, _ = calculate_agent_performance(code)
                
                agent_name = "이름없음"
                agent_agency = ""
                prev_val = 0  # 전월 실적 변수 추가
                
                for cfg in st.session_state['config']:
                    if cfg.get('col_code') and cfg.get('col_name'):
                        df = st.session_state['raw_data'].get(cfg['file'])
                        if df is not None and cfg['col_code'] in df.columns:
                            clean_col_codes = get_clean_series(df, cfg['col_code'])
                            mask = clean_col_codes == code
                            match_df = df[mask]
                            
                            if not match_df.empty:
                                if cfg['col_name'] in match_df.columns:
                                    agent_name = safe_str(match_df[cfg['col_name']].values[0])
                                br = cfg.get('col_branch','')
                                ag = cfg.get('col_agency','')
                                if ag and ag in df.columns: agent_agency = safe_str(match_df[ag].values[0])
                                elif br and br in df.columns: agent_agency = safe_str(match_df[br].values[0])
                                break

                current_val = 0
                for res in calc_results:
                    if cat == "구간" and "구간" not in res['type']: continue
                    if cat == "브릿지" and "브릿지" not in res['type']: continue
                    
                    val = res.get('val') if 'val' in res else res.get('val_curr', 0.0)
                    if val is None: val = 0.0
                    
                    if 'val_prev' in res:
                        prev_val = res['val_prev']
                        
                    if min_v <= val < max_v:
                        current_val = val
                        near_agents.append((code, agent_name, agent_agency, current_val, prev_val))
                        break
            
            if not near_agents:
                st.info(f"해당 구간에 소속 설계사가 없습니다.")
            else:
                # 실적(current_val) 기준 내림차순 정렬
                near_agents.sort(key=lambda x: x[3], reverse=True)
                
                for code, name, agency, val, p_val in near_agents:
                    prev_text = f" (전월: {p_val:,.0f})" if p_val > 0 else ""
                    display_text = f"👤 [{agency}] {name} ({val:,.0f}원){prev_text}"
                    if st.button(display_text, use_container_width=True, key=f"btn_{code}"):
                        st.session_state.mgr_selected_code = code
                        st.session_state.mgr_selected_name = f"[{agency}] {name}"
                        st.session_state.mgr_step = 'detail'
                        st.rerun()
        # --- (4) 상세 내역 및 카톡 공유 ---
        elif step == 'detail':
            if st.button("⬅️ 명단으로 돌아가기", use_container_width=False):
                st.session_state.mgr_step = 'list'
                st.rerun()
            
            code = st.session_state.mgr_selected_code
            name = st.session_state.mgr_selected_name
            
            st.markdown(f"<div class='detail-box'>", unsafe_allow_html=True)
            st.markdown(f"<h4 class='agent-title'>👤 {name} 설계사님</h4>", unsafe_allow_html=True)
            
            calc_results, total_prize = calculate_agent_performance(code)
            render_ui_cards(name, calc_results, total_prize, show_share_text=True)
            
            user_leaflet_path = os.path.join(DATA_DIR, "leaflet.png")
            if os.path.exists(user_leaflet_path):
                st.image(user_leaflet_path, use_container_width=True)
                
            st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 🔒 3. 시스템 관리자 모드
# ==========================================
elif mode == "⚙️ 시스템 관리자":
    st.markdown("<h2 class='admin-title'>관리자 설정</h2>", unsafe_allow_html=True)
    
    admin_pw = st.text_input("관리자 비밀번호를 입력하세요", type="password")
    
    # 🌟 [보안 로직 추가] 시크릿 키로 비밀번호 확인, 설정되지 않은 경우 기본 비밀번호 사용
    try:
        real_pw = st.secrets["admin_password"]
    except:
        real_pw = "meritz0085"
        
    if admin_pw != real_pw:
        if admin_pw: st.error("비밀번호가 일치하지 않습니다.")
        st.stop()
        
    st.success("인증 성공! 변경 사항은 가장 아래 [서버에 반영하기] 버튼을 눌러야 저장됩니다.")

    # 🌟 [로그 다운로드 버튼 추가]
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "rb") as f:
            st.download_button(
                label="📊 사용자 접속 기록 (로그) 다운로드", 
                data=f, 
                file_name=f"access_log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    
    # ---------------------------------------------------------
    # [영역 1] 파일 업로드 및 관리
    # ---------------------------------------------------------
    st.markdown("<h3 class='sub-title'>📂 1. 실적 파일 업로드 및 관리</h3>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("CSV/엑셀 파일 업로드", accept_multiple_files=True, type=['csv', 'xlsx'])
    
    if uploaded_files:
        new_upload = False
        for file in uploaded_files:
            if file.name not in st.session_state['raw_data']:
                if file.name.endswith('.csv'):
                    try: df = pd.read_csv(file)
                    except:
                        file.seek(0)
                        try: df = pd.read_csv(file, sep='\t')
                        except:
                            file.seek(0)
                            try: df = pd.read_csv(file, encoding='cp949')
                            except:
                                file.seek(0)
                                df = pd.read_csv(file, sep='\t', encoding='cp949')
                else: df = pd.read_excel(file)
                
                st.session_state['raw_data'][file.name] = df
                df.to_pickle(os.path.join(DATA_DIR, f"{file.name}.pkl"))
                new_upload = True
                
        if new_upload:
            st.success("✅ 파일 업로드 및 저장이 완료되었습니다.")
            st.rerun()

    col1, col2 = st.columns([7, 3])
    with col1:
        st.markdown(f"**현재 저장된 파일 ({len(st.session_state['raw_data'])}개)**")
    with col2:
        if st.button("🗑️ 전체 파일 삭제", use_container_width=True):
            st.session_state['raw_data'].clear()
            for f in os.listdir(DATA_DIR):
                if f.endswith('.pkl'): os.remove(os.path.join(DATA_DIR, f))
            st.rerun()
            
    if not st.session_state['raw_data']:
        st.info("현재 업로드된 파일이 없습니다. 위에 파일을 추가해주세요.")
    else:
        for file_name in list(st.session_state['raw_data'].keys()):
            col_name, col_btn = st.columns([8, 2])
            with col_name: st.write(f"📄 {file_name}")
            with col_btn:
                if st.button("개별 삭제", key=f"del_file_{file_name}", use_container_width=True):
                    del st.session_state['raw_data'][file_name]
                    pkl_path = os.path.join(DATA_DIR, f"{file_name}.pkl")
                    if os.path.exists(pkl_path): os.remove(pkl_path)
                    st.rerun()
            st.markdown("<hr style='margin:5px 0; opacity:0.1;'>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 🌟 [영역 2] 주차/브릿지 시상 항목 관리
    # ---------------------------------------------------------
    st.divider()
    st.markdown("<h3 class='sub-title' style='margin-top:10px;'>🏆 2. 주차/브릿지 시상 항목 관리</h3>", unsafe_allow_html=True)
    
    col_add, col_del_all = st.columns(2)
    with col_add:
        if st.button("➕ 신규 주차/브릿지 시상 추가", type="primary", use_container_width=True):
            if not st.session_state['raw_data']:
                st.error("⚠️ 먼저 실적 파일을 1개 이상 업로드해야 시상을 추가할 수 있습니다.")
            else:
                first_file = list(st.session_state['raw_data'].keys())[0]
                st.session_state['config'].append({
                    "name": f"신규 주차 시책 {len(st.session_state['config'])+1}",
                    "desc": "", "category": "weekly", "type": "구간 시책", 
                    "file": first_file, "col_name": "", "col_code": "", "col_branch": "", "col_manager_code": "",
                    "col_val": "", "col_val_prev": "", "col_val_curr": "", "curr_req": 100000.0,
                    "tiers": [(100000, 100), (200000, 200), (300000, 200), (500000, 300)]
                })
                st.rerun()
                
    with col_del_all:
        if st.button("🗑️ 모든 시상 항목 일괄 삭제", use_container_width=True):
            st.session_state['config'] = [c for c in st.session_state['config'] if c.get('category') != 'weekly']
            with open(os.path.join(DATA_DIR, 'config.json'), 'w', encoding='utf-8') as f:
                json.dump(st.session_state['config'], f, ensure_ascii=False)
            st.rerun()

    weekly_cfgs = [(i, c) for i, c in enumerate(st.session_state['config']) if c.get('category', 'weekly') == 'weekly']
    if not weekly_cfgs:
        st.info("현재 설정된 주차/브릿지 시상이 없습니다.")

    for i, cfg in weekly_cfgs:
        if 'desc' not in cfg: cfg['desc'] = ""
        st.markdown(f"<div class='config-box'>", unsafe_allow_html=True)
        c_title, c_del = st.columns([8, 2])
        with c_title: st.markdown(f"<h3 class='config-title'>📌 {cfg['name']} 설정</h3>", unsafe_allow_html=True)
        with c_del:
            if st.button("개별 삭제", key=f"del_cfg_{i}", use_container_width=True):
                st.session_state['config'].pop(i)
                st.rerun()
        
        cfg['name'] = st.text_input(f"시책명", value=cfg['name'], key=f"name_{i}")
        cfg['desc'] = st.text_area("시책 설명 (적용 기간 등)", value=cfg.get('desc', ''), placeholder="엔터를 쳐서 문단을 나눌 수 있습니다.", key=f"desc_{i}", height=100)
        
        idx = 0
        if "1기간" in cfg['type']: idx = 1
        elif "2기간" in cfg['type']: idx = 2
            
        cfg['type'] = st.radio("시책 종류 선택", ["구간 시책", "브릿지 시책 (1기간: 시상 확정)", "브릿지 시책 (2기간: 차월 달성 조건)"], index=idx, horizontal=True, key=f"type_{i}")
        
        col1, col2 = st.columns(2)
        with col1:
            file_opts = list(st.session_state['raw_data'].keys())
            cfg['file'] = st.selectbox(f"대상 파일", file_opts, index=file_opts.index(cfg['file']) if cfg['file'] in file_opts else 0, key=f"file_{i}")
            cols = st.session_state['raw_data'][cfg['file']].columns.tolist() if file_opts else []
            def get_idx(val, opts): return opts.index(val) if val in opts else 0

            st.info("💡 식별을 위해 아래 컬럼들을 지정해주세요.")
            cfg['col_name'] = st.selectbox("성명 컬럼", cols, index=get_idx(cfg.get('col_name', ''), cols), key=f"cname_{i}")
            cfg['col_branch'] = st.selectbox("지점명(조직) 컬럼", cols, index=get_idx(cfg.get('col_branch', ''), cols), key=f"cbranch_{i}")
            cfg['col_agency'] = st.selectbox("대리점/지사명 컬럼", cols, index=get_idx(cfg.get('col_agency', ''), cols), key=f"cagency_{i}")
            cfg['col_code'] = st.selectbox("설계사코드(사번) 컬럼", cols, index=get_idx(cfg.get('col_code', ''), cols), key=f"ccode_{i}")
            cfg['col_manager_code'] = st.selectbox("지원매니저코드 컬럼", cols, index=get_idx(cfg.get('col_manager_code', cfg.get('col_manager', '')), cols), key=f"cmgrcode_{i}")
            
            if "1기간" in cfg['type']:
                cfg['col_val_prev'] = st.selectbox("전월 실적 컬럼", cols, index=get_idx(cfg.get('col_val_prev', ''), cols), key=f"cvalp_{i}")
                cfg['col_val_curr'] = st.selectbox("당월 실적 컬럼", cols, index=get_idx(cfg.get('col_val_curr', ''), cols), key=f"cvalc_{i}")
                cfg['curr_req'] = st.number_input("당월 필수 달성 금액", value=float(cfg.get('curr_req', 100000.0)), step=10000.0, key=f"creq_{i}")
            elif "2기간" in cfg['type']:
                cfg['col_val_curr'] = st.selectbox("당월 실적 수치 컬럼", cols, index=get_idx(cfg.get('col_val_curr', ''), cols), key=f"cvalc2_{i}")
                cfg['curr_req'] = st.number_input("차월 필수 달성 금액 (합산용)", value=float(cfg.get('curr_req', 100000.0)), step=10000.0, key=f"creq2_{i}")
            else: 
                cfg['col_val'] = st.selectbox("실적 수치 컬럼", cols, index=get_idx(cfg.get('col_val', ''), cols), key=f"cval_{i}")

        with col2:
            st.write("📈 구간 설정 (달성금액, 지급률%)")
            tier_str = "\n".join([f"{int(t[0])},{int(t[1])}" for t in cfg.get('tiers', [])])
            tier_input = st.text_area("엔터로 줄바꿈", value=tier_str, height=150, key=f"tier_{i}")
            try:
                new_tiers = []
                for line in tier_input.strip().split('\n'):
                    if ',' in line:
                        parts = line.split(',')
                        new_tiers.append((float(parts[0].strip()), float(parts[1].strip())))
                cfg['tiers'] = sorted(new_tiers, key=lambda x: x[0], reverse=True)
            except:
                st.error("형식이 올바르지 않습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 🌟 [영역 3] 월간 누계 시상 항목 관리
    # ---------------------------------------------------------
    st.divider()
    st.markdown("<h3 class='blue-title'>📈 3. 월간 누계 시상 항목 관리</h3>", unsafe_allow_html=True)
    
    if st.button("➕ 신규 누계 항목 추가", type="primary", use_container_width=True, key="add_cumul"):
        if not st.session_state['raw_data']:
            st.error("⚠️ 먼저 실적 파일을 1개 이상 업로드해야 합니다.")
        else:
            first_file = list(st.session_state['raw_data'].keys())[0]
            st.session_state['config'].append({
                "name": f"신규 누계 항목 {len(st.session_state['config'])+1}",
                "desc": "", "category": "cumulative", "type": "누계", 
                "file": first_file, "col_code": "", "col_val": "", "col_prize": ""
            })
            st.rerun()

    cumul_cfgs = [(i, c) for i, c in enumerate(st.session_state['config']) if c.get('category') == 'cumulative']
    if not cumul_cfgs:
        st.info("현재 설정된 누계 항목이 없습니다.")

    for i, cfg in cumul_cfgs:
        st.markdown(f"<div class='config-box-blue'>", unsafe_allow_html=True)
        c_title, c_del = st.columns([8, 2])
        with c_title: st.markdown(f"<h3 class='config-title' style='color:#1e3c72;'>📘 {cfg['name']} 설정</h3>", unsafe_allow_html=True)
        with c_del:
            if st.button("개별 삭제", key=f"del_cfg_{i}", use_container_width=True):
                st.session_state['config'].pop(i)
                st.rerun()
        
        cfg['name'] = st.text_input(f"누계 항목명", value=cfg['name'], key=f"name_{i}")
        
        col1, col2 = st.columns(2)
        with col1:
            file_opts = list(st.session_state['raw_data'].keys())
            cfg['file'] = st.selectbox(f"대상 파일", file_opts, index=file_opts.index(cfg['file']) if cfg['file'] in file_opts else 0, key=f"file_{i}")
            cols = st.session_state['raw_data'][cfg['file']].columns.tolist() if file_opts else []
            def get_idx(val, opts): return opts.index(val) if val in opts else 0

            cfg['col_code'] = st.selectbox("설계사코드(사번) 컬럼", cols, index=get_idx(cfg.get('col_code', ''), cols), key=f"ccode_{i}")
            cfg['col_val'] = st.selectbox("누계 실적 컬럼 (선택사항, 없으면 공란)", cols, index=get_idx(cfg.get('col_val', ''), cols), key=f"cval_{i}")
            cfg['col_prize'] = st.selectbox("확정 시상금 컬럼 (필수)", cols, index=get_idx(cfg.get('col_prize', ''), cols), key=f"cprize_{i}")

        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.info("✅ **구간 설정이 필요 없습니다.**\n\n지정한 파일에서 사번이 일치하는 사람의 **[누계 실적]**과 **[확정 시상금]**을 그대로 가져와 화면의 파란색 박스에 보여줍니다.")
            
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # [영역 4] 리플렛(안내 이미지) 관리
    # ---------------------------------------------------------
    st.divider()
    st.markdown("<h3 class='sub-title' style='margin-top:10px;'>🖼️ 4. 안내 리플렛(이미지) 등록</h3>", unsafe_allow_html=True)
    st.info("💡 실적 조회 결과 맨 아래에 보여줄 상품 안내장이나 리플렛 이미지를 등록할 수 있습니다.")
    
    leaflet_file = st.file_uploader("리플렛 이미지 업로드 (JPG, PNG)", type=['jpg', 'jpeg', 'png'])
    if leaflet_file:
        with open(os.path.join(DATA_DIR, "leaflet.png"), "wb") as f:
            f.write(leaflet_file.getbuffer())
        st.success("✅ 리플렛 이미지가 저장되었습니다!")
        st.rerun()

    leaflet_path = os.path.join(DATA_DIR, "leaflet.png")
    if os.path.exists(leaflet_path):
        st.markdown("<p style='color:#333d4b; font-weight:600;'>현재 등록된 리플렛 이미지:</p>", unsafe_allow_html=True)
        st.image(leaflet_path, width=250)
        
        if st.button("🗑️ 등록된 리플렛 삭제", use_container_width=False):
            os.remove(leaflet_path)
            st.rerun()

    if st.session_state['config']:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅ 모든 설정 완료 및 서버에 반영하기", type="primary", use_container_width=True):
            with open(os.path.join(DATA_DIR, 'config.json'), 'w', encoding='utf-8') as f:
                json.dump(st.session_state['config'], f, ensure_ascii=False)
            st.success("✅ 서버에 영구 반영되었습니다! 이제 조회 화면에서 확인 가능합니다.")

# ==========================================
# 🏆 4. 사용자 모드 (일반 설계사 조회) - [수정됨]
# ==========================================
else:
    st.markdown('<div class="title-band">메리츠화재 시상 현황 조회</div>', unsafe_allow_html=True)
    
    # [개선 1] 복잡한 지점코드/이름 대신 '설계사 코드' 단일 입력으로 변경
    st.markdown("<h3 class='main-title'>본인의 설계사 코드(사번)를 입력하세요.</h3>", unsafe_allow_html=True)
    
    # 비밀번호처럼 가리지 않고 보이게 입력 (type="default")
    user_code_input = st.text_input("설계사 코드 입력", placeholder="예: 123456", key="user_code_login")

    if st.button("내 실적 확인하기", type="primary"):
        if not user_code_input:
            st.warning("설계사 코드를 입력해주세요.")
        elif not st.session_state['config']:
            st.warning("현재 진행 중인 시책 데이터가 없습니다.")
        else:
            target_code = safe_str(user_code_input)
            
            # 해당 코드가 존재하는지 먼저 가볍게 체크 (데이터가 있는 파일 중 하나라도)
            found_name = None
            found_agency = None
            
            # 캐싱된 데이터에서 코드 검색
            for cfg in st.session_state['config']:
                if cfg.get('category') == 'cumulative': continue
                df = st.session_state['raw_data'].get(cfg['file'])
                if df is not None and cfg.get('col_code') and cfg.get('col_code') in df.columns:
                    clean_codes = get_clean_series(df, cfg['col_code'])
                    if target_code in clean_codes.values:
                        # 이름과 소속 찾기
                        idx = clean_codes[clean_codes == target_code].index[0]
                        if cfg.get('col_name') and cfg['col_name'] in df.columns:
                            found_name = safe_str(df.loc[idx, cfg['col_name']])
                        if cfg.get('col_agency') and cfg['col_agency'] in df.columns:
                            found_agency = safe_str(df.loc[idx, cfg['col_agency']])
                        elif cfg.get('col_branch') and cfg['col_branch'] in df.columns:
                            found_agency = safe_str(df.loc[idx, cfg['col_branch']])
                        break
            
            if found_name:
                st.success(f"반갑습니다! {found_agency} {found_name} 설계사님의 실적입니다.")
                calc_results, total_prize = calculate_agent_performance(target_code)
                
                # [로그 저장] 조회 성공 기록
                save_log(f"{found_name}({found_agency})", target_code, "USER_SEARCH_BY_CODE")
                
                render_ui_cards(found_name, calc_results, total_prize, show_share_text=False)
                
                user_leaflet_path = os.path.join(DATA_DIR, "leaflet.png")
                if os.path.exists(user_leaflet_path):
                    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
                    st.image(user_leaflet_path, use_container_width=True)
            else:
                st.error("입력하신 코드의 실적 데이터가 없습니다. 사번을 다시 확인해주세요.")
