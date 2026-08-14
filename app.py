import streamlit as st
import streamlit.components.v1 as components
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
        padding-top: 4.0rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
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

def init_defaults():
    if "reset_count" not in st.session_state:
        st.session_state.reset_count = 0
    if "num_teams" not in st.session_state:
        st.session_state.num_teams = 16
    if "max_roster_size" not in st.session_state:
        st.session_state.max_roster_size = 7
    if "initial_budget" not in st.session_state:
        st.session_state.initial_budget = 1000
    if "teams" not in st.session_state:
        st.session_state.teams = {f"팀 {i}": {"name": "", "budget": 1000, "roster": []} for i in range(1, 21)}
    if "custom_landmarks" not in st.session_state:
        st.session_state.custom_landmarks = {k: list(v) for k, v in DEFAULT_MAP_LANDMARKS.items()}
    if "history" not in st.session_state:
        st.session_state.history = []
    if "landmark_assignments" not in st.session_state:
        st.session_state.landmark_assignments = {}
    if "players" not in st.session_state:
        st.session_state.players = pd.DataFrame(columns=["선수명", "티어", "상태", "사진"])
    if "current_player" not in st.session_state:
        st.session_state.current_player = None
    if "temp_bids" not in st.session_state:
        st.session_state.temp_bids = {}
    if "forced_player" not in st.session_state:
        st.session_state.forced_player = None
    if "timer_set_seconds" not in st.session_state:
        st.session_state.timer_set_seconds = 15
    if "timer_running" not in st.session_state:
        st.session_state.timer_running = False
    if "timer_start_timestamp" not in st.session_state:
        st.session_state.timer_start_timestamp = 0
    if "show_budget" not in st.session_state:
        st.session_state.show_budget = True
    if "show_roster" not in st.session_state:
        st.session_state.show_roster = True
    if "show_history" not in st.session_state:
        st.session_state.show_history = True

def save_data_to_file():
    players_data = []
    if hasattr(st.session_state, "players") and not st.session_state.players.empty:
        for _, row in st.session_state.players.iterrows():
            img_b64 = None
            if row["사진"] is not None:
                if isinstance(row["사진"], bytes):
                    try:
                        img_b64 = base64.b64encode(row["사진"]).decode("utf-8")
                    except Exception:
                        img_b64 = None
                elif isinstance(row["사진"], str):
                    img_b64 = row["사진"]
            players_data.append({
                "선수명": row["선수명"],
                "티어": int(row.get("티어", 1)),
                "상태": row["상태"],
                "사진": img_b64
            })
            
    store = {
        "num_teams": st.session_state.get("num_teams", 16),
        "max_roster_size": st.session_state.get("max_roster_size", 7),
        "initial_budget": st.session_state.get("initial_budget", 1000),
        "teams": st.session_state.get("teams", {}),
        "custom_landmarks": st.session_state.get("custom_landmarks", DEFAULT_MAP_LANDMARKS),
        "history": st.session_state.get("history", []),
        "landmark_assignments": st.session_state.get("landmark_assignments", {}),
        "players": players_data,
        "current_player": st.session_state.get("current_player", None),
        "temp_bids": st.session_state.get("temp_bids", {}),
        "forced_player": st.session_state.get("forced_player", None),
        "timer_set_seconds": st.session_state.get("timer_set_seconds", 15),
        "timer_running": st.session_state.get("timer_running", False),
        "timer_start_timestamp": st.session_state.get("timer_start_timestamp", 0)
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)

def load_data_from_file():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                store = json.load(f)
                st.session_state.num_teams = store.get("num_teams", 16)
                st.session_state.max_roster_size = store.get("max_roster_size", 7)
                st.session_state.initial_budget = store.get("initial_budget", 1000)
                st.session_state.teams = store.get("teams", {})
                st.session_state.custom_landmarks = store.get("custom_landmarks", DEFAULT_MAP_LANDMARKS)
                st.session_state.history = store.get("history", [])
                st.session_state.landmark_assignments = store.get("landmark_assignments", {})
                st.session_state.current_player = store.get("current_player", None)
                st.session_state.temp_bids = store.get("temp_bids", {})
                st.session_state.forced_player = store.get("forced_player", None)
                st.session_state.timer_set_seconds = store.get("timer_set_seconds", 15)
                st.session_state.timer_running = store.get("timer_running", False)
                st.session_state.timer_start_timestamp = store.get("timer_start_timestamp", 0)
                
                players_list = store.get("players", [])
                if players_list:
                    df_rows = []
                    for p in players_list:
                        img_bytes = None
                        if p["사진"]:
                            try:
                                img_bytes = base64.b64decode(p["사진"].encode("utf-8"))
                            except Exception:
                                img_bytes = None
                        df_rows.append({"선수명": p["선수명"], "티어": p.get("티어", 1), "상태": p.get("상태", "대기중"), "사진": img_bytes})
                    st.session_state.players = pd.DataFrame(df_rows)
        except Exception:
            pass

def do_reset_all_data():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_defaults()

def add_bid_amount(target_key, amount, max_limit):
    cur_val = st.session_state.get(target_key, 10)
    st.session_state[target_key] = min(max_limit, cur_val + amount)

# HTML/JS 실시간 타이머 컴포넌트
def render_js_timer(duration_sec, is_running, start_time_ms):
    timer_html = f"""
    <div style="
        background: linear-gradient(135deg, #1f2937, #111827);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        font-family: sans-serif;
    ">
        <div id="js-timer-display" style="
            font-size: 38px;
            font-weight: 800;
            color: #10b981;
            letter-spacing: 1px;
        ">{duration_sec}초</div>
        <div style="background-color: #374151; border-radius: 8px; height: 10px; width: 100%; margin-top: 8px; overflow: hidden;">
            <div id="js-timer-bar" style="background-color: #10b981; height: 100%; width: 100%; transition: width 0.2s linear;"></div>
        </div>
    </div>

    <script>
        (function() {{
            const totalDuration = {duration_sec};
            const isRunning = {str(is_running).lower()};
            const startTime = {start_time_ms};
            
            const display = document.getElementById('js-timer-display');
            const bar = document.getElementById('js-timer-bar');
            
            if (!isRunning || startTime === 0) {{
                display.innerText = totalDuration + "초";
                display.style.color = totalDuration <= 5 ? "#f87171" : "#10b981";
                bar.style.width = "100%";
                return;
            }}

            function updateTimer() {{
                const now = Date.now();
                const elapsedSec = (now - startTime) / 1000;
                const remaining = Math.max(0, Math.ceil(totalDuration - elapsedSec));
                const pct = Math.max(0, Math.min(100, (remaining / totalDuration) * 100));

                if (remaining <= 0) {{
                    display.innerText = "⏰ 시간 종료!";
                    display.style.color = "#f87171";
                    bar.style.width = "0%";
                    bar.style.backgroundColor = "#f87171";
                }} else {{
                    display.innerText = remaining + "초";
                    if (remaining <= 5) {{
                        display.style.color = "#f87171";
                        bar.style.backgroundColor = "#f87171";
                    }} else {{
                        display.style.color = "#10b981";
                        bar.style.backgroundColor = "#10b981";
                    }}
                    bar.style.width = pct + "%";
                    requestAnimationFrame(updateTimer);
                }}
            }}
            updateTimer();
        }})();
    </script>
    """
    components.html(timer_html, height=105)

# 초기화
init_defaults()
if "data_loaded" not in st.session_state:
    load_data_from_file()
    st.session_state.data_loaded = True

rc = st.session_state.reset_count

st.title("🏆 배틀그라운드 팀장 드래프트 경매 시스템")

active_team_keys = [f"팀 {i}" for i in range(1, st.session_state.num_teams + 1)]

tab_set, tab_auction, tab_random, tab_landmark = st.tabs([
    "설정 (팀수/팀장/선수 입력)", "경매 진행", "🎲 랜덤 선수 추첨", "🗺️ 랜드마크 추첨"
])

# 탭 1: 설정
with tab_set:
    st.subheader("⚙️ 대회 기본 설정")
    cfg_col1, cfg_col2, cfg_col3 = st.columns(3)
    with cfg_col1:
        new_num_teams = st.number_input("진행할 총 팀 수", min_value=2, max_value=20, value=st.session_state.num_teams, step=1, key=f"num_teams_input_{rc}")
        if new_num_teams != st.session_state.num_teams:
            st.session_state.num_teams = new_num_teams
            save_data_to_file()
            st.rerun()
    with cfg_col2:
        new_max_roster = st.number_input("팀 당 최대 인원수", min_value=1, max_value=10, value=st.session_state.max_roster_size, step=1, key=f"max_roster_input_{rc}")
        if new_max_roster != st.session_state.max_roster_size:
            st.session_state.max_roster_size = new_max_roster
            save_data_to_file()
    with cfg_col3:
        new_budget = st.number_input("팀 기본 시작 포인트 (예산)", min_value=100, max_value=10000, value=st.session_state.initial_budget, step=100, key=f"initial_budget_input_{rc}")
        if new_budget != st.session_state.initial_budget:
            st.session_state.initial_budget = new_budget
            for k in st.session_state.teams:
                if not st.session_state.teams[k]["roster"]:
                    st.session_state.teams[k]["budget"] = new_budget
            save_data_to_file()
            st.success(f"기본 시작 포인트가 {new_budget}P로 변경되었습니다.")
            st.rerun()

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"👤 팀장 이름 설정 ({st.session_state.num_teams}개 팀)")
        with st.form(key=f"team_names_form_{rc}"):
            new_names = {}
            for i in range(st.session_state.num_teams):
                t_key = f"팀 {i+1}"
                cur_name = st.session_state.teams[t_key]["name"]
                new_names[t_key] = st.text_input(f"{t_key} 팀장명", value=cur_name, key=f"form_team_input_{i}_{rc}")
                
            submit_team_names = st.form_submit_button("💾 팀장 명단 저장", type="primary", use_container_width=True)
            if submit_team_names:
                for k, v in new_names.items():
                    st.session_state.teams[k]["name"] = v.strip()
                save_data_to_file()
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
                if clean_name not in st.session_state.players["선수명"].values:
                    img_bytes = player_img.getvalue() if player_img is not None else None
                    new_row = pd.DataFrame([{"선수명": clean_name, "티어": int(new_tier), "상태": "대기중", "사진": img_bytes}])
                    st.session_state.players = pd.concat([st.session_state.players, new_row], ignore_index=True)
                    save_data_to_file()
                    st.success(f"'{clean_name}' 선수({new_tier}티어) 추가 완료!")
                    st.rerun()
                else:
                    st.warning("이미 등록된 선수 이름입니다.")

        st.write(f"현재 등록된 선수: **{len(st.session_state.players)}명**")
        
        if not st.session_state.players.empty:
            st.markdown("---")
            st.subheader("🗑️ 등록된 선수 삭제")
            del_player = st.selectbox("삭제할 선수 선택", st.session_state.players["선수명"].tolist(), key=f"delete_player_select_{rc}")
            
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                if st.button("선수 삭제", key=f"del_player_btn_{rc}"):
                    st.session_state.players = st.session_state.players[st.session_state.players["선수명"] != del_player].reset_index(drop=True)
                    save_data_to_file()
                    st.success(f"'{del_player}' 선수를 삭제했습니다.")
                    st.rerun()
            with col_del2:
                if st.button("⚠️ 명단 전체 삭제", key=f"clear_all_players_btn_{rc}"):
                    st.session_state.players = pd.DataFrame(columns=["선수명", "티어", "상태", "사진"])
                    save_data_to_file()
                    st.success("선수 명단을 모두 초기화했습니다.")
                    st.rerun()

    st.markdown("---")
    st.subheader("🚨 전체 시스템 데이터 초기화")
    st.write("모든 팀 정보, 팀장명, 경매 결과, 랜드마크 추첨 기록을 삭제하고 처음 상태로 되돌립니다.")
    if st.button("⚠️ 전체 시스템 데이터 완전 초기화", type="primary", key=f"reset_all_system_data_{rc}"):
        do_reset_all_data()
        st.success("모든 시스템 데이터가 완벽하게 초기화되었습니다.")
        st.rerun()

# 탭 2: 경매 진행
with tab_auction:
    col_left, col_right = st.columns([5, 6])
    
    with col_left:
        # 1. HTML5/JS 기반 고성능 클라이언트 타이머 (멈춤 현상 차단)
        with st.container(border=True):
            set_sec = st.session_state.timer_set_seconds
            is_running = st.session_state.timer_running
            start_ts = st.session_state.timer_start_timestamp

            # 브라우저 타이머 렌더링
            render_js_timer(set_sec, is_running, start_ts)
            
            t_btn_col1, t_btn_col2, t_btn_col3 = st.columns([2, 1, 1])
            if not is_running:
                if t_btn_col1.button("▶️ 카운트다운 시작", type="primary", use_container_width=True, key=f"timer_start_btn_{rc}"):
                    st.session_state.timer_start_timestamp = int(time.time() * 1000)
                    st.session_state.timer_running = True
                    save_data_to_file()
                    st.rerun()
            else:
                if t_btn_col1.button("⏸️ 일시정지 / 멈춤", type="secondary", use_container_width=True, key=f"timer_pause_btn_{rc}"):
                    st.session_state.timer_running = False
                    save_data_to_file()
                    st.rerun()
                    
            if t_btn_col2.button("🔄 리셋", use_container_width=True, key=f"timer_reset_btn_{rc}"):
                st.session_state.timer_running = False
                st.session_state.timer_start_timestamp = 0
                save_data_to_file()
                st.rerun()
                
            if t_btn_col3.button("+5초 추가", use_container_width=True, key=f"timer_add5_btn_{rc}"):
                st.session_state.timer_set_seconds += 5
                if is_running:
                    st.session_state.timer_start_timestamp += 5000
                save_data_to_file()
                st.rerun()

            # 타이머 직접 수기 입력 및 설정
            with st.expander("⚙️ 타이머 시간 직접 설정 / 변경"):
                p_c1, p_c2, p_c3, p_c4 = st.columns(4)
                if p_c1.button("10초", use_container_width=True, key=f"t_10s_{rc}"):
                    st.session_state.timer_set_seconds = 10
                    st.session_state.timer_running = False
                    save_data_to_file()
                    st.rerun()
                if p_c2.button("15초", use_container_width=True, key=f"t_15s_{rc}"):
                    st.session_state.timer_set_seconds = 15
                    st.session_state.timer_running = False
                    save_data_to_file()
                    st.rerun()
                if p_c3.button("30초", use_container_width=True, key=f"t_30s_{rc}"):
                    st.session_state.timer_set_seconds = 30
                    st.session_state.timer_running = False
                    save_data_to_file()
                    st.rerun()
                if p_c4.button("60초", use_container_width=True, key=f"t_60s_{rc}"):
                    st.session_state.timer_set_seconds = 60
                    st.session_state.timer_running = False
                    save_data_to_file()
                    st.rerun()

                custom_sec = st.number_input("타이머 초 수기 입력", min_value=3, max_value=300, value=st.session_state.timer_set_seconds, step=1, key=f"custom_timer_sec_{rc}")
                if custom_sec != st.session_state.timer_set_seconds:
                    st.session_state.timer_set_seconds = custom_sec
                    st.session_state.timer_running = False
                    save_data_to_file()
                    st.rerun()

        # 2. 선수 선택 카드
        available_players = st.session_state.players[st.session_state.players["상태"] == "추첨완료"]
        if "티어" not in available_players.columns:
            available_players["티어"] = 1
        available_players_sorted = available_players.sort_values(by=["티어", "선수명"])
        waiting_list = available_players_sorted["선수명"].tolist()
        
        if not waiting_list:
            st.info("현재 경매 대상 선수가 없습니다. '🎲 랜덤 선수 추첨' 탭에서 뽑아주세요.")
        else:
            default_idx = 0
            if st.session_state.forced_player in waiting_list:
                default_idx = waiting_list.index(st.session_state.forced_player)
                
            selected_player = st.selectbox(
                "🎯 경매 진행 대상 선택", 
                waiting_list, 
                index=default_idx, 
                format_func=lambda x: f"{x} ({available_players[available_players['선수명']==x]['티어'].values[0]}티어)",
                key=f"selected_auction_player_{rc}"
            )
            
            player_info = st.session_state.players[st.session_state.players["선수명"] == selected_player]
            player_tier_val = int(player_info.iloc[0]["티어"]) if not player_info.empty and "티어" in player_info.columns else 1
            
            with st.container(border=True):
                p_col1, p_col2 = st.columns([1, 2])
                with p_col1:
                    if not player_info.empty and player_info.iloc[0]["사진"] is not None:
                        st.image(player_info.iloc[0]["사진"], use_container_width=True)
                with p_col2:
                    st.markdown(f"### **{selected_player}**")
                    st.caption(f"티어 정보: **{player_tier_val}티어**")
                    
                    if st.button(f"⚠️ 유찰 처리 (대기 명단으로)", key=f"pass_auction_player_btn_{rc}"):
                        st.session_state.players.loc[st.session_state.players["선수명"] == selected_player, "상태"] = "유찰"
                        st.session_state.history.append({
                            "시간": datetime.now().strftime("%H:%M:%S"), 
                            "팀": "-", 
                            "선수": f"{selected_player} ({player_tier_val}티어 / 유찰)", 
                            "낙찰가": 0
                        })
                        if selected_player in st.session_state.temp_bids:
                            del st.session_state.temp_bids[selected_player]
                        st.session_state.current_player = None
                        st.session_state.forced_player = None
                        st.session_state.timer_running = False
                        save_data_to_file()
                        st.success(f"'{selected_player}' 선수 유찰 완료")
                        st.rerun()

            if st.session_state.current_player != selected_player:
                st.session_state.current_player = selected_player
                st.session_state.timer_running = False
                if selected_player not in st.session_state.temp_bids:
                    st.session_state.temp_bids[selected_player] = {}
                save_data_to_file()

            # 3. 입찰 등록 카드
            team_options = {
                k: st.session_state.teams[k] 
                for k in active_team_keys 
                if len(st.session_state.teams[k]["roster"]) < st.session_state.max_roster_size
            }
            
            if team_options:
                with st.container(border=True):
                    st.markdown("##### 📌 입찰 등록")
                    
                    team_list = list(team_options.keys())
                    bidding_team = st.selectbox(
                        "입찰할 팀 선택", 
                        team_list, 
                        format_func=lambda x: f"{x} ({st.session_state.teams[x]['name']}) - 잔액: {st.session_state.teams[x]['budget']}P", 
                        key=f"bidding_team_select_{rc}"
                    )
                    
                    max_b_limit = st.session_state.teams[bidding_team]["budget"]
                    bid_num_key = f"bid_input_num_{rc}"
                    
                    if bid_num_key not in st.session_state:
                        st.session_state[bid_num_key] = 10

                    st.session_state[bid_num_key] = min(max_b_limit, max(0, st.session_state[bid_num_key]))
                    
                    # 입찰 버튼 4종 (+10P ~ +500P)
                    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
                    quick_col1.button("+10P", key=f"btn_add_10_{rc}", on_click=add_bid_amount, args=(bid_num_key, 10, max_b_limit))
                    quick_col2.button("+50P", key=f"btn_add_50_{rc}", on_click=add_bid_amount, args=(bid_num_key, 50, max_b_limit))
                    quick_col3.button("+100P", key=f"btn_add_100_{rc}", on_click=add_bid_amount, args=(bid_num_key, 100, max_b_limit))
                    quick_col4.button("+500P", key=f"btn_add_500_{rc}", on_click=add_bid_amount, args=(bid_num_key, 500, max_b_limit))
                        
                    entered_bid = st.number_input(
                        "입찰 금액(P)", 
                        min_value=0, 
                        max_value=max_b_limit, 
                        step=5,
                        key=bid_num_key
                    )
                    
                    if st.button("🚀 입찰 제출", type="primary", use_container_width=True, key=f"submit_bid_btn_{rc}"):
                        st.session_state.temp_bids[selected_player][bidding_team] = entered_bid
                        # 입찰 제출 시 설정된 초로 리셋 및 카운트다운 자동 시작
                        st.session_state.timer_start_timestamp = int(time.time() * 1000)
                        st.session_state.timer_running = True
                        save_data_to_file()
                        st.success(f"{bidding_team} ({st.session_state.teams[bidding_team]['name']}) {entered_bid}P 입찰 제출 완료!")
                        st.rerun()

                # 입찰 현황 및 낙찰
                current_bids = st.session_state.temp_bids.get(selected_player, {})
                if current_bids:
                    with st.container(border=True):
                        st.markdown("##### 📋 현재 선수 입찰 현황")
                        bid_df = pd.DataFrame([
                            {"팀": k, "팀장": st.session_state.teams[k]['name'], "입찰가": f"{v}P"} 
                            for k, v in current_bids.items()
                        ]).sort_values(by="입찰가", ascending=False)
                        st.dataframe(bid_df, hide_index=True, use_container_width=True)
                        
                        st.markdown("---")
                        
                        sorted_bids = sorted(current_bids.items(), key=lambda x: x[1], reverse=True)
                        sorted_teams = [team for team, amount in sorted_bids]
                        
                        final_winning_team = sorted_teams[0]
                        top_leader = st.session_state.teams[final_winning_team]["name"]
                        final_bid = current_bids[final_winning_team]
                        
                        st.info(f"🏆 최고 입찰: **{final_winning_team}({top_leader})** - **{final_bid}P**")
                        
                        if st.button(f"👑 '{final_winning_team}' 낙찰 확정!", type="primary", use_container_width=True, key=f"confirm_final_bid_btn_{rc}"):
                            team_budget = st.session_state.teams[final_winning_team]["budget"]
                            if final_bid > team_budget:
                                st.error(f"낙찰 실패: {final_winning_team}의 잔액({team_budget}P) 부족")
                            else:
                                st.session_state.teams[final_winning_team]["budget"] -= final_bid
                                st.session_state.teams[final_winning_team]["roster"].append({"name": selected_player, "bid": final_bid, "tier": player_tier_val})
                                st.session_state.teams[final_winning_team]["roster"].sort(key=lambda x: (x.get("tier", 1), x["name"]))
                                
                                st.session_state.players.loc[st.session_state.players["선수명"] == selected_player, "상태"] = "완료"
                                st.session_state.history.append({
                                    "시간": datetime.now().strftime("%H:%M:%S"), 
                                    "팀": f"{final_winning_team}({top_leader})", 
                                    "선수": f"{selected_player} ({player_tier_val}티어)", 
                                    "낙찰가": final_bid
                                })
                                
                                if selected_player in st.session_state.temp_bids:
                                    del st.session_state.temp_bids[selected_player]
                                st.session_state.current_player = None
                                st.session_state.forced_player = None
                                st.session_state.timer_running = False
                                
                                save_data_to_file()
                                st.rerun()

    with col_right:
        # 1. 팀별 남은 예산 현황
        bgt_hdr_col1, bgt_hdr_col2 = st.columns([3, 1])
        bgt_hdr_col1.subheader("📊 팀별 남은 예산 현황")
        btn_budget_label = "간소화(숨기기)" if st.session_state.show_budget else "펼쳐보기"
        if bgt_hdr_col2.button(btn_budget_label, key=f"toggle_budget_btn_{rc}"):
            st.session_state.show_budget = not st.session_state.show_budget
            st.rerun()
            
        if st.session_state.show_budget:
            for i in range(0, st.session_state.num_teams, 4):
                m_cols = st.columns(4)
                for j in range(4):
                    if i + j < st.session_state.num_teams:
                        k = active_team_keys[i + j]
                        t = st.session_state.teams[k]
                        t_label = f"{k} ({t['name']})" if t['name'] else k
                        m_cols[j].metric(label=t_label, value=f"{t['budget']}P")
        
        st.markdown("---")
        
        # 2. 팀 로스터 현황
        rst_hdr_col1, rst_hdr_col2 = st.columns([3, 1])
        rst_hdr_col1.subheader(f"👥 팀 로스터 현황 ({st.session_state.num_teams}개 팀)")
        btn_roster_label = "간소화(숨기기)" if st.session_state.show_roster else "펼쳐보기"
        if rst_hdr_col2.button(btn_roster_label, key=f"toggle_roster_btn_{rc}"):
            st.session_state.show_roster = not st.session_state.show_roster
            st.rerun()
            
        if st.session_state.show_roster:
            for i in range(0, st.session_state.num_teams, 4):
                cols = st.columns(4)
                for j in range(4):
                    if i+j < st.session_state.num_teams:
                        t_key = f"팀 {i+j+1}"
                        t = st.session_state.teams[t_key]
                        with cols[j].container(border=True):
                            t_display_title = f"{t_key} ({t['name']})" if t['name'] else t_key
                            st.markdown(f"**{t_display_title}**")
                            st.caption(f"잔액: {t['budget']}P | {len(t['roster'])}/{st.session_state.max_roster_size}명")
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
                                            st.session_state.players.loc[st.session_state.players["선수명"] == member["name"], "상태"] = "추첨완료"
                                            st.session_state.history.append({"시간": datetime.now().strftime("%H:%M:%S"), "팀": f"{t_key}({t['name']})", "선수": f"{member['name']} (낙찰취소)", "낙찰가": -member["bid"]})
                                            save_data_to_file()
                                            st.rerun()
        
        st.markdown("---")
        
        # 3. 전체 경매 기록
        hist_hdr_col1, hist_hdr_col2 = st.columns([3, 1])
        hist_hdr_col1.subheader("📜 전체 경매 기록 및 CSV 내보내기")
        btn_history_label = "간소화(숨기기)" if st.session_state.show_history else "펼쳐보기"
        if hist_hdr_col2.button(btn_history_label, key=f"toggle_history_btn_{rc}"):
            st.session_state.show_history = not st.session_state.show_history
            st.rerun()
            
        if st.session_state.show_history:
            if st.session_state.history:
                history_df = pd.DataFrame(st.session_state.history)
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
                        t = st.session_state.teams[k]
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

# 탭 3: 랜덤 선수 추첨 페이지
with tab_random:
    st.subheader("🎲 대기 중인 선수 중 랜덤 추첨")
    st.write("1티어~N티어 순으로 미추첨 선수를 우선 추첨하며, 신규 선수가 모두 소진된 후 유찰 선수들이 추첨됩니다.")
    
    if "티어" not in st.session_state.players.columns:
        st.session_state.players["티어"] = 1
    new_waiting_df = st.session_state.players[st.session_state.players["상태"] == "대기중"].sort_values(by=["티어", "선수명"])
    passed_waiting_df = st.session_state.players[st.session_state.players["상태"] == "유찰"].sort_values(by=["티어", "선수명"])
    
    num_new = len(new_waiting_df)
    num_passed = len(passed_waiting_df)
    
    if num_new > 0 or num_passed > 0:
        if num_new > 0:
            st.info(f"현재 추첨 가능: **신규 대기 선수 {num_new}명** (티어 순 무작위 뽑기)")
        else:
            st.warning(f"신규 대기 선수가 모두 소진되었습니다! **유찰 대기 선수 {num_passed}명** 중에서 추첨합니다.")
            
        if st.button("🎲 랜덤 선수 뽑기 돌리기!", type="primary", use_container_width=True, key=f"random_pick_btn_{rc}"):
            if num_new > 0:
                chosen = random.choice(new_waiting_df["선수명"].tolist())
            else:
                chosen = random.choice(passed_waiting_df["선수명"].tolist())
                
            st.session_state.forced_player = chosen
            st.session_state.players.loc[st.session_state.players["선수명"] == chosen, "상태"] = "추첨완료"
            save_data_to_file()
            st.rerun()
    else:
        st.success("🎉 모든 선수가 추첨되었습니다!")
        
    if st.session_state.get("forced_player"):
        st.markdown("---")
        st.markdown("### 🎰 이번에 뽑힌 경매 대상자")
        
        forced_info = st.session_state.players[st.session_state.players["선수명"] == st.session_state.forced_player]
        forced_tier = int(forced_info.iloc[0]["티어"]) if not forced_info.empty and "티어" in forced_info.columns else 1
        
        if not forced_info.empty and forced_info.iloc[0]["사진"] is not None:
            st.image(forced_info.iloc[0]["사진"], width=240, caption=st.session_state.forced_player)
            
        st.markdown(f"## **{st.session_state.forced_player}** ({forced_tier}티어) 🎉")
        st.write("상단 **[경매 진행]** 탭으로 이동하시면 해당 선수가 자동으로 선택되어 있습니다!")

# 탭 4: 🗺️ 랜드마크 추첨 페이지
with tab_landmark:
    st.subheader(f"🗺️ 맵별 팀 랜드마크 랜덤 배정 ({st.session_state.num_teams}개 팀)")
    
    selected_map = st.selectbox("추첨 및 편집할 맵을 선택하세요", list(st.session_state.custom_landmarks.keys()), key=f"selected_map_box_{rc}")
    
    with st.expander(f"✏️ '{selected_map}' 랜드마크 목록 수정하기"):
        current_lm_text = "\n".join(st.session_state.custom_landmarks[selected_map])
        edited_lm_text = st.text_area("랜드마크 목록 (한 줄에 하나씩 입력)", value=current_lm_text, height=200, key=f"lm_text_area_{rc}")
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("💾 랜드마크 목록 저장", key=f"save_landmarks_btn_{rc}"):
                new_lm_list = [line.strip() for line in edited_lm_text.split("\n") if line.strip()]
                st.session_state.custom_landmarks[selected_map] = new_lm_list
                save_data_to_file()
                st.success(f"'{selected_map}' 랜드마크 {len(new_lm_list)}개가 성공적으로 저장되었습니다!")
                st.rerun()
        with col_btn2:
            if st.button("🔄 기본 랜드마크로 초기화", key=f"reset_landmarks_btn_{rc}"):
                st.session_state.custom_landmarks[selected_map] = list(DEFAULT_MAP_LANDMARKS[selected_map])
                save_data_to_file()
                st.success(f"'{selected_map}' 랜드마크가 기본 설정으로 초기화되었습니다.")
                st.rerun()

    st.markdown("---")
    
    col_lm1, col_lm2 = st.columns([1, 1])
    
    with col_lm1:
        lm_list = st.session_state.custom_landmarks[selected_map]
        st.markdown(f"##### 📌 {selected_map} 주요 랜드마크 목록 ({len(lm_list)}개)")
        st.dataframe(pd.DataFrame({"번호": range(1, len(lm_list) + 1), "랜드마크": lm_list}), hide_index=True, height=350)
        
        if st.button(f"🎲 {st.session_state.num_teams}개 팀 랜드마크 전체 추첨!", type="primary", use_container_width=True, key=f"draw_landmark_btn_{rc}"):
            if len(lm_list) < st.session_state.num_teams:
                st.error(f"⚠️ 랜드마크 개수({len(lm_list)}개)가 팀 수({st.session_state.num_teams}개)보다 적어 추첨할 수 없습니다! 상단 편집기에서 랜드마크를 추가해 주세요.")
            else:
                shuffled_landmarks = random.sample(lm_list, st.session_state.num_teams)
                assignments = []
                for i in range(st.session_state.num_teams):
                    t_key = f"팀 {i+1}"
                    t_name = st.session_state.teams[t_key]["name"]
                    t_display = f"{t_key} ({t_name})" if t_name else t_key
                    assignments.append({
                        "팀": t_display,
                        "배정된 랜드마크": shuffled_landmarks[i]
                    })
                st.session_state.landmark_assignments[selected_map] = assignments
                save_data_to_file()
                st.rerun()

    with col_lm2:
        st.markdown(f"##### 🏆 {selected_map} 팀별 배정 결과")
        if selected_map in st.session_state.landmark_assignments:
            res_df = pd.DataFrame(st.session_state.landmark_assignments[selected_map])
            st.table(res_df)
        else:
            st.info("아직 추첨 결과가 없습니다. 왼쪽의 [🎲 랜드마크 전체 추첨!] 버튼을 눌러주세요.")