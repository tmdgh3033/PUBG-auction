import streamlit as st
import pandas as pd
import random
import os
import json
import base64
import time
from datetime import datetime

st.set_page_config(page_title="배그 경매 시스템", layout="wide")

DATA_FILE = "data_store.json"

st.markdown("""
    <style>
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    .timer-container {
        background: linear-gradient(135deg, #1f2937, #111827);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin-bottom: 10px;
    }
    .timer-display {
        font-size: 36px;
        font-weight: 800;
        color: #10b981;
        letter-spacing: 1px;
    }
    .timer-display-warn {
        font-size: 36px;
        font-weight: 800;
        color: #f87171;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-radius: 10px !important;
        padding: 12px 14px !important;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.4rem !important;
    }
    div[data-testid="column"] {
        padding: 0px 4px !important;
    }
    </style>
""", unsafe_allow_html=True)

DEFAULT_MAP_LANDMARKS = {
    "에란겔 (Erangel)": [
        "로족", "강남", "야스나야", "밀베", "밀타", "포친키", "강북", "리포브카", 
        "노보", "프리모스크", "밀타파워", "페리", "서버니 / 사격장", 
        "멘션 / 프리즌 / 쉘터", "학교 / 아파트", "병원 / 각카"
    ],
    "미라마 (Mirama)": [
        "푸에르토", "파워그리드", "라코브레리아", "몬테 누에보", "그레이브 / 미나스", 
        "엘 아자르", "페카도", "캄포밀타", "하시엔다", "엘 포조", 
        "발레 델 마르 / 프리즌", "산마르틴", "츄마세라", "임팔라", "로스 레온스", "크루즈 델 발레"
    ],
    "태이고 (Taego)": [
        "해무사", "영천", "에어포트", "십야드", "북산사", "호산프리즌", "하포", 
        "간녕", "아미베이스", "월송", "팔라스", "오향", "터미널", "스쿨 / 송암", "호산", "고독"
    ]
}

@st.cache_resource
def get_global_db():
    return {
        "num_teams": 16,
        "max_roster_size": 7,
        "initial_budget": 1000,
        "teams": {f"팀 {i}": {"name": "", "budget": 1000, "roster": []} for i in range(1, 21)},
        "custom_landmarks": {k: list(v) for k, v in DEFAULT_MAP_LANDMARKS.items()},
        "history": [],
        "landmark_assignments": {},
        "players": [],
        "current_player": None,
        "temp_bids": {},
        "forced_player": None,
        "timer_set_seconds": 7,
        "timer_end_timestamp": 0,
        "timer_running": False,
        "version": 1
    }

global_db = get_global_db()

def load_file_to_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    global_db[k] = v
        except Exception:
            pass

if "file_loaded" not in st.session_state:
    load_file_to_db()
    st.session_state.file_loaded = True

def save_db_to_file():
    try:
        global_db["version"] = global_db.get("version", 1) + 1
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(dict(global_db), f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def do_reset_all_data():
    if os.path.exists(DATA_FILE):
        try:
            os.remove(DATA_FILE)
        except Exception:
            pass
    global_db.clear()
    global_db.update({
        "num_teams": 16,
        "max_roster_size": 7,
        "initial_budget": 1000,
        "teams": {f"팀 {i}": {"name": "", "budget": 1000, "roster": []} for i in range(1, 21)},
        "custom_landmarks": {k: list(v) for k, v in DEFAULT_MAP_LANDMARKS.items()},
        "history": [],
        "landmark_assignments": {},
        "players": [],
        "current_player": None,
        "temp_bids": {},
        "forced_player": None,
        "timer_set_seconds": 7,
        "timer_end_timestamp": 0,
        "timer_running": False,
        "version": 1
    })
    save_db_to_file()

if "reset_count" not in st.session_state:
    st.session_state.reset_count = 0
if "show_budget" not in st.session_state:
    st.session_state.show_budget = True
if "show_roster" not in st.session_state:
    st.session_state.show_roster = True
if "show_history" not in st.session_state:
    st.session_state.show_history = True

rc = st.session_state.reset_count

st.title("🏆 배틀그라운드 팀장 드래프트 경매 시스템")

active_team_keys = [f"팀 {i}" for i in range(1, global_db["num_teams"] + 1)]

tab_set, tab_auction, tab_random, tab_landmark = st.tabs([
    "설정 (팀수/팀장/선수 입력)", "경매 진행", "🎲 랜덤 선수 추첨", "🗺️ 랜드마크 추첨"
])

# 탭 1: 설정
with tab_set:
    st.subheader("⚙️ 대회 기본 설정")
    cfg_col1, cfg_col2, cfg_col3 = st.columns(3)
    with cfg_col1:
        new_num_teams = st.number_input("진행할 총 팀 수", min_value=2, max_value=20, value=global_db["num_teams"], step=1, key=f"num_teams_input_{rc}")
        if new_num_teams != global_db["num_teams"]:
            global_db["num_teams"] = new_num_teams
            save_db_to_file()
            st.rerun()
    with cfg_col2:
        new_max_roster = st.number_input("팀 당 최대 인원수", min_value=1, max_value=10, value=global_db["max_roster_size"], step=1, key=f"max_roster_input_{rc}")
        if new_max_roster != global_db["max_roster_size"]:
            global_db["max_roster_size"] = new_max_roster
            save_db_to_file()
    with cfg_col3:
        new_budget = st.number_input("팀 기본 시작 포인트 (예산)", min_value=100, max_value=10000, value=global_db["initial_budget"], step=100, key=f"initial_budget_input_{rc}")
        if new_budget != global_db["initial_budget"]:
            global_db["initial_budget"] = new_budget
            for k in global_db["teams"]:
                if not global_db["teams"][k]["roster"]:
                    global_db["teams"][k]["budget"] = new_budget
            save_db_to_file()
            st.success(f"기본 시작 포인트가 {new_budget}P로 변경되었습니다.")
            st.rerun()

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"👤 팀장 이름 설정 ({global_db['num_teams']}개 팀)")
        with st.form(key=f"team_names_form_{rc}"):
            new_names = {}
            for i in range(global_db["num_teams"]):
                t_key = f"팀 {i+1}"
                cur_name = global_db["teams"].get(t_key, {}).get("name", "")
                new_names[t_key] = st.text_input(f"{t_key} 팀장명", value=cur_name, key=f"form_team_input_{i}_{rc}")
                
            submit_team_names = st.form_submit_button("💾 팀장 명단 저장", type="primary", use_container_width=True)
            if submit_team_names:
                for k, v in new_names.items():
                    if k not in global_db["teams"]:
                        global_db["teams"][k] = {"name": "", "budget": global_db["initial_budget"], "roster": []}
                    global_db["teams"][k]["name"] = v.strip()
                save_db_to_file()
                st.success("팀장명 설정이 성공적으로 저장되었습니다!")
                st.rerun()

    with col2:
        st.subheader("📝 선수 명단 및 티어/사진 추가")
        with st.form(key=f"player_add_form_{rc}", clear_on_submit=True):
            p_col1, p_col2 = st.columns([2, 1])
            with p_col1:
                new_player = st.text_input("추가할 선수 이름 입력", placeholder="추가할 선수 이름 입력", key=f"new_player_name_{rc}")
            with p_col2:
                new_tier = st.number_input("선수 티어 (1=최상위)", min_value=1, max_value=20, value=1, step=1, key=f"new_player_tier_{rc}")
                
            player_img = st.file_uploader("선수 사진 첨부 (선택사항)", type=["png", "jpg", "jpeg", "webp"], key=f"player_img_{rc}")
            submit_player = st.form_submit_button("선수 추가")
            
            if submit_player and new_player.strip():
                clean_name = new_player.strip()
                existing_names = [p["선수명"] for p in global_db["players"]]
                if clean_name not in existing_names:
                    img_b64 = None
                    if player_img is not None:
                        try:
                            img_b64 = base64.b64encode(player_img.getvalue()).decode("utf-8")
                        except Exception:
                            img_b64 = None
                    global_db["players"].append({"선수명": clean_name, "티어": int(new_tier), "상태": "대기중", "사진": img_b64})
                    save_db_to_file()
                    st.success(f"'{clean_name}' 선수({new_tier}티어) 추가 완료!")
                    st.rerun()
                else:
                    st.warning("이미 등록된 선수 이름입니다.")

        st.write(f"현재 등록된 선수: **{len(global_db['players'])}명**")
        
        if global_db["players"]:
            st.markdown("---")
            st.subheader("🗑️ 등록된 선수 삭제")
            player_names = [p["선수명"] for p in global_db["players"]]
            del_player = st.selectbox("삭제할 선수 선택", player_names, key=f"delete_player_select_{rc}")
            
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                if st.button("선수 삭제", key=f"del_player_btn_{rc}"):
                    global_db["players"] = [p for p in global_db["players"] if p["선수명"] != del_player]
                    save_db_to_file()
                    st.success(f"'{del_player}' 선수를 삭제했습니다.")
                    st.rerun()
            with col_del2:
                if st.button("⚠️ 명단 전체 삭제", key=f"clear_all_players_btn_{rc}"):
                    global_db["players"] = []
                    save_db_to_file()
                    st.success("선수 명단을 모두 초기화했습니다.")
                    st.rerun()

    st.markdown("---")
    st.subheader("🚨 전체 시스템 데이터 초기화")
    st.write("모든 팀 정보, 팀장명, 경매 결과, 랜드마크 추첨 기록을 삭제하고 처음 상태로 되돌립니다.")
    if st.button("⚠️ 전체 시스템 데이터 완전 초기화", type="primary", key=f"reset_all_system_data_{rc}"):
        do_reset_all_data()
        st.success("모든 시스템 데이터가 완벽하게 초기화되었습니다.")
        st.rerun()

# ⚡ 서버 대상 선수 변경 시 관전자 화면 자동 연동
@st.fragment(run_every="1s")
def render_live_player_card():
    load_file_to_db()
    players_list = global_db.get("players", [])
    cur_player = global_db.get("current_player")
    
    if cur_player and st.session_state.get("last_synced_player") != cur_player:
        st.session_state["last_synced_player"] = cur_player
        st.rerun()
    
    p_match = next((p for p in players_list if p["선수명"] == cur_player), None)
    
    if p_match:
        p_tier_val = p_match.get("티어", 1)
        p_img_b64 = p_match.get("사진")
        with st.container(border=True):
            p_col1, p_col2 = st.columns([1, 2])
            with p_col1:
                if p_img_b64:
                    try:
                        st.image(base64.b64decode(p_img_b64.encode("utf-8")), use_container_width=True)
                    except Exception:
                        pass
            with p_col2:
                st.markdown(f"### **{cur_player}**")
                st.caption(f"티어 정보: **{p_tier_val}티어**")

# ⚡ 고정 7초 타이머 1초 자동 연동
@st.fragment(run_every="1s")
def render_live_timer_display():
    load_file_to_db()
    is_running = global_db.get("timer_running", False)
    set_sec = 7
    end_ts = global_db.get("timer_end_timestamp", 0)
    
    if is_running:
        rem = max(0, int(end_ts - time.time()))
        if rem == 0 and global_db.get("timer_running"):
            global_db["timer_running"] = False
            save_db_to_file()
    else:
        rem = set_sec
        
    t_disp_class = "timer-display-warn" if rem <= 3 and rem > 0 else "timer-display"
    t_msg = f"{rem}초" if (is_running and rem > 0) else ("⏰ 시간 종료!" if is_running else f"{rem}초")
    
    st.markdown(f'<div class="timer-container"><div class="{t_disp_class}">{t_msg}</div></div>', unsafe_allow_html=True)
    st.progress(max(0.0, min(1.0, rem / set_sec)) if set_sec > 0 else 0.0)

# ⚡ 실시간 입찰 현황 및 최고가 1초 자동 연동
@st.fragment(run_every="1s")
def render_live_bids_display():
    load_file_to_db()
    selected_player = global_db.get("current_player")
    if selected_player:
        current_bids = global_db.get("temp_bids", {}).get(selected_player, {})
        if current_bids:
            with st.container(border=True):
                st.markdown("##### 📋 현재 실시간 입찰 현황")
                bid_rows = []
                for k, v in current_bids.items():
                    t_name = global_db.get("teams", {}).get(k, {}).get("name", "")
                    bid_rows.append({"팀": k, "팀장": t_name, "입찰가": f"{v}P"})
                bid_df = pd.DataFrame(bid_rows).sort_values(by="입찰가", ascending=False)
                st.dataframe(bid_df, hide_index=True, use_container_width=True)

                sorted_bids = sorted(current_bids.items(), key=lambda x: x[1], reverse=True)
                top_team = sorted_bids[0][0]
                top_leader = global_db.get("teams", {}).get(top_team, {}).get("name", "")
                top_bid = current_bids[top_team]
                st.info(f"🏆 현재 최고 입찰: **{top_team}({top_leader})** - **{top_bid}P**")

# ⚡ 우측 팀 예산 및 로스터 1초 자동 연동
@st.fragment(run_every="1s")
def render_live_right_panel():
    load_file_to_db()
    
    bgt_hdr_col1, bgt_hdr_col2 = st.columns([3, 1])
    bgt_hdr_col1.subheader("📊 팀별 남은 예산 현황")
    btn_budget_label = "간소화(숨기기)" if st.session_state.show_budget else "펼쳐보기"
    if bgt_hdr_col2.button(btn_budget_label, key=f"toggle_budget_btn_{rc}"):
        st.session_state.show_budget = not st.session_state.show_budget
        st.rerun()
        
    if st.session_state.show_budget:
        for i in range(0, global_db["num_teams"], 4):
            m_cols = st.columns(4)
            for j in range(4):
                if i + j < global_db["num_teams"]:
                    k = active_team_keys[i + j]
                    t = global_db["teams"][k]
                    t_label = f"{k} ({t['name']})" if t['name'] else k
                    m_cols[j].metric(label=t_label, value=f"{t['budget']}P")
    
    st.markdown("---")
    
    rst_hdr_col1, rst_hdr_col2 = st.columns([3, 1])
    rst_hdr_col1.subheader(f"👥 팀 로스터 현황 ({global_db['num_teams']}개 팀)")
    btn_roster_label = "간소화(숨기기)" if st.session_state.show_roster else "펼쳐보기"
    if rst_hdr_col2.button(btn_roster_label, key=f"toggle_roster_btn_{rc}"):
        st.session_state.show_roster = not st.session_state.show_roster
        st.rerun()
        
    if st.session_state.show_roster:
        for i in range(0, global_db["num_teams"], 4):
            cols = st.columns(4)
            for j in range(4):
                if i+j < global_db["num_teams"]:
                    t_key = f"팀 {i+j+1}"
                    t = global_db["teams"][t_key]
                    with cols[j].container(border=True):
                        t_display_title = f"{t_key} ({t['name']})" if t['name'] else t_key
                        st.markdown(f"**{t_display_title}**")
                        st.caption(f"잔액: {t['budget']}P | {len(t['roster'])}/{global_db['max_roster_size']}명")
                        if t['roster']:
                            sorted_roster = sorted(t['roster'], key=lambda x: (x.get("tier", 1), x["name"]))
                            with st.expander("로스터 보기", expanded=True):
                                for member in sorted_roster:
                                    c1, c2 = st.columns([3, 1])
                                    m_tier_str = f"{member.get('tier', 1)}티어, " if 'tier' in member else ""
                                    c1.write(f"- {member['name']} ({m_tier_str}{member['bid']}P)")
                                    if c2.button("취소", key=f"cancel_{t_key}_{member['name']}_{rc}"):
                                        t["budget"] += member["bid"]
                                        t["roster"].remove(member)
                                        for p in global_db["players"]:
                                            if p["선수명"] == member["name"]:
                                                p["상태"] = "추첨완료"
                                        global_db["history"].append({"시간": datetime.now().strftime("%H:%M:%S"), "팀": f"{t_key}({t['name']})", "선수": f"{member['name']} (낙찰취소)", "낙찰가": -member["bid"]})
                                        save_db_to_file()
                                        st.rerun()
    
    st.markdown("---")
    
    hist_hdr_col1, hist_hdr_col2 = st.columns([3, 1])
    hist_hdr_col1.subheader("📜 전체 경매 기록 및 CSV 내보내기")
    btn_history_label = "간소화(숨기기)" if st.session_state.show_history else "펼쳐보기"
    if hist_hdr_col2.button(btn_history_label, key=f"toggle_history_btn_{rc}"):
        st.session_state.show_history = not st.session_state.show_history
        st.rerun()
        
    if st.session_state.show_history:
        if global_db["history"]:
            history_df = pd.DataFrame(global_db["history"])
            st.table(history_df)
            
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                csv_history = history_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 경매 히스토리 CSV 다운로드",
                    data=csv_history,
                    file_name=f"경매기록_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key=f"download_csv_hist_{rc}"
                )
            with col_exp2:
                roster_export = []
                for k in active_team_keys:
                    t = global_db["teams"][k]
                    sorted_m_list = sorted(t["roster"], key=lambda x: (x.get("tier", 1), x["name"]))
                    members_str = ", ".join([f"{m['name']}({m.get('tier', 1)}티어/{m['bid']}P)" for m in sorted_m_list])
                    roster_export.append({
                        "팀": k,
                        "팀장명": t["name"],
                        "잔여 포인트": t["budget"],
                        "영입 인원": len(t["roster"]),
                        "영입 선수 명단 (티어순)": members_str
                    })
                roster_df = pd.DataFrame(roster_export)
                csv_rosters = roster_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 최종 로스터 CSV 다운로드",
                    data=csv_rosters,
                    file_name=f"최종로스터_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key=f"download_csv_roster_{rc}"
                )

# ⚡ 랜드마크 결과표 1초 자동 연동
@st.fragment(run_every="1s")
def render_landmark_results(selected_map):
    load_file_to_db()
    st.markdown(f"##### 🏆 {selected_map} 팀별 배정 결과")
    if selected_map in global_db.get("landmark_assignments", {}):
        res_df = pd.DataFrame(global_db["landmark_assignments"][selected_map])
        st.table(res_df)
    else:
        st.info("아직 추첨 결과가 없습니다. 왼쪽의 [🎲 랜드마크 전체 추첨!] 버튼을 눌러주세요.")

# 탭 2: 경매 진행
with tab_auction:
    col_left, col_right = st.columns([5, 6])
    
    with col_left:
        load_file_to_db()
        players_list = global_db.get("players", [])
        waiting_players = [p for p in players_list if p.get("상태") == "추첨완료"]
        waiting_players.sort(key=lambda x: (x.get("티어", 1), x.get("선수명", "")))
        waiting_list = [p["선수명"] for p in waiting_players]
        
        if not waiting_list:
            st.info("현재 경매 대상 선수가 없습니다. '🎲 랜덤 선수 추첨' 탭에서 뽑아주세요.")
        else:
            select_key = f"selected_auction_player_{rc}"

            srv_player = global_db.get("current_player")
            if srv_player and srv_player in waiting_list:
                if st.session_state.get("last_synced_player") != srv_player:
                    st.session_state[select_key] = srv_player
                    st.session_state["last_synced_player"] = srv_player
            elif select_key not in st.session_state or st.session_state[select_key] not in waiting_list:
                st.session_state[select_key] = waiting_list[0]
                st.session_state["last_synced_player"] = waiting_list[0]

            selected_player = st.selectbox(
                "🎯 경매 진행 대상 선택", 
                waiting_list, 
                key=select_key,
                format_func=lambda x: f"{x} ({next((p['티어'] for p in waiting_players if p['선수명']==x), 1)}티어)"
            )
            
            if global_db.get("current_player") != selected_player:
                global_db["current_player"] = selected_player
                global_db["timer_running"] = False
                global_db["timer_end_timestamp"] = 0
                if selected_player not in global_db["temp_bids"]:
                    global_db["temp_bids"][selected_player] = {}
                save_db_to_file()

            p_match = next((p for p in players_list if p["선수명"] == selected_player), None)
            p_tier_val = p_match.get("티어", 1) if p_match else 1

            # 실시간 선수 프로필 카드 및 자동 동기화
            render_live_player_card()

            # ⚡ 타이머 1초 자동 연동
            render_live_timer_display()

            # 타이머 제어 버튼
            with st.container(border=True):
                col_ctrl1, col_ctrl2 = st.columns(2)
                with col_ctrl1:
                    if st.button(f"⚠️ '{selected_player}' 유찰 처리", key=f"pass_auction_player_btn_{rc}", use_container_width=True):
                        for p in global_db["players"]:
                            if p["선수명"] == selected_player:
                                p["상태"] = "유찰"
                        global_db["history"].append({
                            "시간": datetime.now().strftime("%H:%M:%S"), 
                            "팀": "-", 
                            "선수": f"{selected_player} ({p_tier_val}티어 / 유찰)", 
                            "낙찰가": 0
                        })
                        if selected_player in global_db["temp_bids"]:
                            del global_db["temp_bids"][selected_player]
                        global_db["current_player"] = None
                        global_db["forced_player"] = None
                        global_db["timer_running"] = False
                        save_db_to_file()
                        st.success(f"'{selected_player}' 선수 유찰 완료")
                        st.rerun()

                with col_ctrl2:
                    if not global_db.get("timer_running", False):
                        if st.button("▶️ 7초 카운트다운 시작", type="primary", use_container_width=True, key=f"timer_start_btn_{rc}"):
                            global_db["timer_running"] = True
                            global_db["timer_end_timestamp"] = time.time() + 7
                            save_db_to_file()
                            st.rerun()
                    else:
                        if st.button("⏸️ 일시정지", type="secondary", use_container_width=True, key=f"timer_pause_btn_{rc}"):
                            global_db["timer_running"] = False
                            save_db_to_file()
                            st.rerun()

                if st.button("🔄 타이머 리셋", use_container_width=True, key=f"timer_reset_btn_{rc}"):
                    global_db["timer_running"] = False
                    global_db["timer_end_timestamp"] = 0
                    save_db_to_file()
                    st.rerun()

            team_options = {
                k: global_db["teams"][k] 
                for k in active_team_keys 
                if len(global_db["teams"][k]["roster"]) < global_db["max_roster_size"]
            }
            
            if team_options:
                # 🔥 [핵심 수정] st.form으로 입찰 입력 영역 보호 (수동 타이핑 시 새로고침 방지)
                with st.form(key=f"bidding_form_{rc}"):
                    st.markdown("##### 📌 입찰 등록")
                    
                    team_list = list(team_options.keys())
                    bidding_team = st.selectbox(
                        "입찰할 팀 선택", 
                        team_list, 
                        format_func=lambda x: f"{x} ({global_db['teams'][x]['name']}) - 잔액: {global_db['teams'][x]['budget']}P", 
                        key=f"bidding_team_select_{rc}"
                    )
                    
                    max_b_limit = global_db["teams"][bidding_team]["budget"]
                    
                    entered_bid = st.number_input(
                        "입찰 금액(P)", 
                        min_value=0, 
                        max_value=max_b_limit, 
                        value=10,
                        step=5,
                        key=f"bid_input_num_{rc}"
                    )
                    
                    submit_bid = st.form_submit_button("🚀 입찰 제출", type="primary", use_container_width=True)
                    
                    if submit_bid:
                        if selected_player not in global_db["temp_bids"]:
                            global_db["temp_bids"][selected_player] = {}
                        global_db["temp_bids"][selected_player][bidding_team] = entered_bid
                        
                        global_db["timer_running"] = True
                        global_db["timer_end_timestamp"] = time.time() + 7
                        save_db_to_file()
                        st.success(f"{bidding_team} ({global_db['teams'][bidding_team]['name']}) {entered_bid}P 입찰 완료!")
                        st.rerun()

            # ⚡ 실시간 입찰 현황판 1초 자동 연동
            render_live_bids_display()

            current_bids = global_db.get("temp_bids", {}).get(selected_player, {})
            if current_bids:
                sorted_bids = sorted(current_bids.items(), key=lambda x: x[1], reverse=True)
                final_winning_team = sorted_bids[0][0]
                top_leader = global_db["teams"].get(final_winning_team, {}).get("name", "")
                final_bid = current_bids[final_winning_team]

                if st.button(f"👑 '{final_winning_team}' 낙찰 확정!", type="primary", use_container_width=True, key=f"confirm_final_bid_btn_{rc}"):
                    team_budget = global_db["teams"][final_winning_team]["budget"]
                    if final_bid > team_budget:
                        st.error(f"낙찰 실패: {final_winning_team}의 잔액({team_budget}P) 부족")
                    else:
                        global_db["teams"][final_winning_team]["budget"] -= final_bid
                        global_db["teams"][final_winning_team]["roster"].append({"name": selected_player, "bid": final_bid, "tier": p_tier_val})
                        global_db["teams"][final_winning_team]["roster"].sort(key=lambda x: (x.get("tier", 1), x["name"]))
                        
                        for p in global_db["players"]:
                            if p["선수명"] == selected_player:
                                p["상태"] = "완료"
                                
                        global_db["history"].append({
                            "시간": datetime.now().strftime("%H:%M:%S"), 
                            "팀": f"{final_winning_team}({top_leader})", 
                            "선수": f"{selected_player} ({p_tier_val}티어)", 
                            "낙찰가": final_bid
                        })
                        
                        if selected_player in global_db["temp_bids"]:
                            del global_db["temp_bids"][selected_player]
                        global_db["current_player"] = None
                        global_db["forced_player"] = None
                        global_db["timer_running"] = False
                        
                        save_db_to_file()
                        st.rerun()

    with col_right:
        # ⚡ 우측 예산/로스터 패널 실시간 1초 자동 연동
        render_live_right_panel()

# 탭 3: 랜덤 선수 추첨 페이지
with tab_random:
    st.subheader("🎲 대기 중인 선수 중 랜덤 추첨")
    st.write("1티어~N티어 순으로 미추첨 선수를 우선 추첨하며, 신규 선수가 모두 소진된 후 유찰 선수들이 추첨됩니다.")
    
    players_list = global_db.get("players", [])
    new_waiting = [p for p in players_list if p.get("상태") == "대기중"]
    passed_waiting = [p for p in players_list if p.get("상태") == "유찰"]
    
    new_waiting.sort(key=lambda x: (x.get("티어", 1), x.get("선수명", "")))
    passed_waiting.sort(key=lambda x: (x.get("티어", 1), x.get("선수명", "")))
    
    num_new = len(new_waiting)
    num_passed = len(passed_waiting)
    
    if num_new > 0 or num_passed > 0:
        if num_new > 0:
            st.info(f"현재 추첨 가능: **신규 대기 선수 {num_new}명** (티어 순 무작위 뽑기)")
        else:
            st.warning(f"신규 대기 선수가 모두 소진되었습니다! **유찰 대기 선수 {num_passed}명** 중에서 추첨합니다.")
            
        if st.button("🎲 랜덤 선수 뽑기 돌리기!", type="primary", use_container_width=True, key=f"random_pick_btn_{rc}"):
            chosen_obj = random.choice(new_waiting) if num_new > 0 else random.choice(passed_waiting)
            chosen_name = chosen_obj["선수명"]
            
            global_db["forced_player"] = chosen_name
            global_db["current_player"] = chosen_name
            
            select_key = f"selected_auction_player_{rc}"
            st.session_state[select_key] = chosen_name
            
            for p in global_db["players"]:
                if p["선수명"] == chosen_name:
                    p["상태"] = "추첨완료"
            save_db_to_file()
            st.rerun()
    else:
        st.success("🎉 모든 선수가 추첨되었습니다!")
        
    if global_db.get("forced_player"):
        st.markdown("---")
        st.markdown("### 🎰 이번에 뽑힌 경매 대상자")
        
        f_name = global_db["forced_player"]
        f_match = next((p for p in players_list if p["선수명"] == f_name), None)
        f_tier = f_match.get("티어", 1) if f_match else 1
        f_img_b64 = f_match.get("사진") if f_match else None
        
        if f_img_b64:
            try:
                st.image(base64.b64decode(f_img_b64.encode("utf-8")), width=240, caption=f_name)
            except Exception:
                pass
            
        st.markdown(f"## **{f_name}** ({f_tier}티어) 🎉")
        st.write("상단 **[경매 진행]** 탭으로 이동하시면 해당 선수가 자동으로 선택되어 있습니다!")

# 탭 4: 🗺️ 랜드마크 추첨 페이지
with tab_landmark:
    st.subheader(f"🗺️ 맵별 팀 랜드마크 랜덤 배정 ({global_db['num_teams']}개 팀)")
    
    selected_map = st.selectbox("추첨 및 편집할 맵을 선택하세요", list(global_db["custom_landmarks"].keys()), key=f"selected_map_box_{rc}")
    
    with st.expander(f"✏️ '{selected_map}' 랜드마크 목록 수정하기"):
        current_lm_text = "\n".join(global_db["custom_landmarks"].get(selected_map, []))
        edited_lm_text = st.text_area("랜드마크 목록 (한 줄에 하나씩 입력)", value=current_lm_text, height=200, key=f"lm_text_area_{rc}")
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("💾 랜드마크 목록 저장", key=f"save_landmarks_btn_{rc}"):
                new_lm_list = [line.strip() for line in edited_lm_text.split("\n") if line.strip()]
                global_db["custom_landmarks"][selected_map] = new_lm_list
                save_db_to_file()
                st.success(f"'{selected_map}' 랜드마크 {len(new_lm_list)}개가 성공적으로 저장되었습니다!")
                st.rerun()
        with col_btn2:
            if st.button("🔄 기본 랜드마크로 초기화", key=f"reset_landmarks_btn_{rc}"):
                global_db["custom_landmarks"][selected_map] = list(DEFAULT_MAP_LANDMARKS[selected_map])
                save_db_to_file()
                st.success(f"'{selected_map}' 랜드마크가 기본 설정으로 초기화되었습니다.")
                st.rerun()

    st.markdown("---")
    
    col_lm1, col_lm2 = st.columns([1, 1])
    
    with col_lm1:
        lm_list = global_db["custom_landmarks"].get(selected_map, [])
        st.markdown(f"##### 📌 {selected_map} 주요 랜드마크 목록 ({len(lm_list)}개)")
        st.dataframe(pd.DataFrame({"번호": range(1, len(lm_list) + 1), "랜드마크": lm_list}), hide_index=True, height=350)
        
        if st.button(f"🎲 {global_db['num_teams']}개 팀 랜드마크 전체 추첨!", type="primary", use_container_width=True, key=f"draw_landmark_btn_{rc}"):
            if len(lm_list) < global_db["num_teams"]:
                st.error(f"⚠️ 랜드마크 개수({len(lm_list)}개)가 팀 수({global_db['num_teams']}개)보다 적어 추첨할 수 없습니다! 상단 편집기에서 랜드마크를 추가해 주세요.")
            else:
                shuffled_landmarks = random.sample(lm_list, global_db["num_teams"])
                assignments = []
                for i in range(global_db["num_teams"]):
                    t_key = f"팀 {i+1}"
                    t_name = global_db["teams"].get(t_key, {}).get("name", "")
                    t_display = f"{t_key} ({t_name})" if t_name else t_key
                    assignments.append({
                        "팀": t_display,
                        "배정된 랜드마크": shuffled_landmarks[i]
                    })
                global_db["landmark_assignments"][selected_map] = assignments
                save_db_to_file()
                st.rerun()

    with col_lm2:
        # ⚡ 랜드마크 결과표 1초 자동 연동
        render_landmark_results(selected_map)