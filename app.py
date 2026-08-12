import streamlit as st
import pandas as pd
import random
import os
import json
import base64
from datetime import datetime

st.set_page_config(page_title="배그 경매 시스템", layout="wide")

DATA_FILE = "data_store.json"

# 여백 및 간격 줄이기 커스텀 스타일 (CSS)
st.markdown("""
    <style>
    /* 1. 상단 화면 여백을 4.5rem으로 늘려서 Streamlit UI 상단바 가림 방지 */
    .block-container {
        padding-top: 4.5rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    
    /* 2. 카드(container) 내부 여백 축소 */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        padding: 8px 10px !important;
    }

    /* 3. 요소 간 상하 간격(Gap) 줄이기 */
    div[data-testid="stVerticalBlock"] {
        gap: 0.4rem !important;
    }
    
    /* 4. 컬럼(Column) 사이의 좌우 간격 줄이기 */
    div[data-testid="column"] {
        padding: 0px 3px !important;
    }

    /* 5. 로스터 보기(Expander) 내부 간격 및 여백 축소 */
    .stExpander details summary {
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }
    div[data-testid="stExpander"] div[role="region"] {
        padding: 4px 8px !important;
    }
    div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
        gap: 0.15rem !important;
    }
    div[data-testid="stExpander"] div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 0.2rem !important;
    }
    div[data-testid="stExpander"] button {
        padding: 2px 6px !important;
        font-size: 12px !important;
        min-height: 0px !important;
        line-height: 1.2 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 맵별 기본 랜드마크 초기값
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

def save_data_to_file():
    """현재 세션 상태를 JSON 파일로 자동 저장"""
    players_data = []
    if hasattr(st.session_state, "players") and not st.session_state.players.empty:
        for _, row in st.session_state.players.iterrows():
            img_b64 = None
            if row["사진"] is not None:
                try:
                    img_b64 = base64.b64encode(row["사진"]).decode("utf-8")
                except Exception:
                    img_b64 = None
            players_data.append({
                "선수명": row["선수명"],
                "상태": row["상태"],
                "사진": img_b64
            })
            
    store = {
        "num_teams": st.session_state.num_teams,
        "max_roster_size": st.session_state.max_roster_size,
        "teams": st.session_state.teams,
        "custom_landmarks": st.session_state.custom_landmarks,
        "history": st.session_state.history,
        "landmark_assignments": st.session_state.landmark_assignments,
        "players": players_data
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)

def load_data_from_file():
    """JSON 파일이 존재하면 불러와서 세션에 복원"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                store = json.load(f)
                st.session_state.num_teams = store.get("num_teams", 16)
                st.session_state.max_roster_size = store.get("max_roster_size", 7)
                st.session_state.teams = store.get("teams", {f"팀 {i}": {"name": "", "budget": 1000, "roster": []} for i in range(1, 21)})
                st.session_state.custom_landmarks = store.get("custom_landmarks", {k: list(v) for k, v in DEFAULT_MAP_LANDMARKS.items()})
                st.session_state.history = store.get("history", [])
                st.session_state.landmark_assignments = store.get("landmark_assignments", {})
                
                # 팀장 이름 입력 위젯 키 세션 복원
                for i in range(20):
                    t_key = f"팀 {i+1}"
                    st.session_state[f"team_name_input_{i}"] = st.session_state.teams[t_key]["name"]
                
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
                        df_rows.append({"선수명": p["선수명"], "상태": p["상태"], "사진": img_bytes})
                    st.session_state.players = pd.DataFrame(df_rows)
                else:
                    st.session_state.players = pd.DataFrame(columns=["선수명", "상태", "사진"])
                return True
        except Exception:
            pass
    return False

def reset_all_data():
    """초기화 버튼 클릭 시 실행되는 콜백 함수 (화면이 그려지기 전 실행)"""
    if os.path.exists(DATA_FILE):
        try:
            os.remove(DATA_FILE)
        except Exception:
            pass
            
    st.session_state.num_teams = 16
    st.session_state.max_roster_size = 7
    st.session_state.teams = {f"팀 {i}": {"name": "", "budget": 1000, "roster": []} for i in range(1, 21)}
    st.session_state.custom_landmarks = {k: list(v) for k, v in DEFAULT_MAP_LANDMARKS.items()}
    st.session_state.history = []
    st.session_state.landmark_assignments = {}
    st.session_state.players = pd.DataFrame(columns=["선수명", "상태", "사진"])
    st.session_state.current_player = None
    st.session_state.temp_bids = {}
    st.session_state.forced_player = None
    
    # 20개 팀장 입력창 키 초기화
    for i in range(20):
        st.session_state[f"team_name_input_{i}"] = ""

# 세션 상태 초기화 및 데이터 로드
if "initialized" not in st.session_state:
    if not load_data_from_file():
        reset_all_data()
    st.session_state.initialized = True

active_team_keys = [f"팀 {i}" for i in range(1, st.session_state.num_teams + 1)]

st.title("🏆 배틀그라운드 팀장 드래프트 경매 시스템")

# 1. 페이지 탭 구성
tab_set, tab_auction, tab_random, tab_landmark = st.tabs([
    "설정 (팀수/팀장/선수 입력)", "경매 진행", "🎲 랜덤 선수 추첨", "🗺️ 랜드마크 추첨"
])

# 탭 1: 설정
with tab_set:
    st.subheader("⚙️ 대회 기본 설정")
    cfg_col1, cfg_col2 = st.columns(2)
    with cfg_col1:
        new_num_teams = st.number_input("진행할 총 팀 수", min_value=2, max_value=20, value=st.session_state.num_teams, step=1)
        if new_num_teams != st.session_state.num_teams:
            st.session_state.num_teams = new_num_teams
            save_data_to_file()
            st.rerun()
    with cfg_col2:
        new_max_roster = st.number_input("팀 당 최대 인원수", min_value=1, max_value=10, value=st.session_state.max_roster_size, step=1)
        if new_max_roster != st.session_state.max_roster_size:
            st.session_state.max_roster_size = new_max_roster
            save_data_to_file()

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"👤 팀장 이름 설정 ({st.session_state.num_teams}개 팀)")
        team_name_changed = False
        for i in range(st.session_state.num_teams):
            t_key = f"팀 {i+1}"
            input_key = f"team_name_input_{i}"
            
            if input_key not in st.session_state:
                st.session_state[input_key] = st.session_state.teams[t_key]["name"]
                
            new_val = st.text_input(
                f"{t_key} 팀장명", 
                key=input_key
            )
            if new_val != st.session_state.teams[t_key]["name"]:
                st.session_state.teams[t_key]["name"] = new_val
                team_name_changed = True
                
        if team_name_changed:
            save_data_to_file()
    
    with col2:
        st.subheader("📝 선수 명단 및 사진 추가")
        
        with st.form(key="player_add_form", clear_on_submit=True):
            new_player = st.text_input("추가할 선수 이름 입력 (엔터 입력 가능)")
            player_img = st.file_uploader("선수 사진 첨부 (선택사항)", type=["png", "jpg", "jpeg", "webp"])
            submit_player = st.form_submit_button("선수 추가")
            
            if submit_player and new_player:
                if new_player not in st.session_state.players["선수명"].values:
                    img_bytes = player_img.getvalue() if player_img is not None else None
                    new_row = pd.DataFrame([{"선수명": new_player, "상태": "대기중", "사진": img_bytes}])
                    st.session_state.players = pd.concat([st.session_state.players, new_row], ignore_index=True)
                    save_data_to_file()
                    st.success(f"'{new_player}' 추가 완료!")
                else:
                    st.warning("이미 등록된 선수 이름입니다.")

        st.write(f"현재 등록된 선수: **{len(st.session_state.players)}명**")
        
        # 선수 삭제 기능
        if not st.session_state.players.empty:
            st.markdown("---")
            st.subheader("🗑️ 등록된 선수 삭제")
            del_player = st.selectbox("삭제할 선수 선택", st.session_state.players["선수명"].tolist(), key="delete_player_select")
            
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                if st.button("선수 삭제", key="del_player_btn"):
                    st.session_state.players = st.session_state.players[st.session_state.players["선수명"] != del_player].reset_index(drop=True)
                    save_data_to_file()
                    st.success(f"'{del_player}' 선수를 삭제했습니다.")
                    st.rerun()
            with col_del2:
                if st.button("⚠️ 명단 전체 삭제", key="clear_all_players_btn"):
                    st.session_state.players = pd.DataFrame(columns=["선수명", "상태", "사진"])
                    save_data_to_file()
                    st.success("선수 명단을 모두 초기화했습니다.")
                    st.rerun()

    st.markdown("---")
    st.subheader("🚨 전체 시스템 데이터 초기화")
    st.write("모든 팀 정보, 팀장명, 경매 결과, 랜드마크 추첨 기록을 삭제하고 처음 상태로 되돌립니다.")
    st.button("⚠️ 전체 시스템 데이터 완전 초기화", type="primary", key="reset_all_system_data", on_click=reset_all_data)

# 탭 2: 경매 진행
with tab_auction:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("📢 경매 진행 및 입찰")
        
        available_players = st.session_state.players[st.session_state.players["상태"] == "추첨완료"]
        available_players_sorted = available_players.sort_values(by="선수명")
        waiting_list = available_players_sorted["선수명"].tolist()
        
        if not waiting_list:
            st.info("현재 경매 진행 중인 선수가 없습니다. '🎲 랜덤 선수 추첨' 탭에서 다음 선수를 뽑아주세요.")
        else:
            default_idx = 0
            if st.session_state.forced_player in waiting_list:
                default_idx = waiting_list.index(st.session_state.forced_player)
                
            selected_player = st.selectbox("경매 선수 선택", waiting_list, index=default_idx, key="selected_auction_player")
            
            player_info = st.session_state.players[st.session_state.players["선수명"] == selected_player]
            if not player_info.empty and player_info.iloc[0]["사진"] is not None:
                st.image(player_info.iloc[0]["사진"], width=200, caption=f"선수: {selected_player}")
            
            if st.session_state.current_player != selected_player:
                st.session_state.current_player = selected_player
                if selected_player not in st.session_state.temp_bids:
                    st.session_state.temp_bids[selected_player] = {}
            
            step_unit = st.radio("낙찰가 조정 단위", [5, 10, 25, 50, 100, 500], horizontal=True, key="bid_step_unit")
            
            team_options = {
                k: st.session_state.teams[k] 
                for k in active_team_keys 
                if len(st.session_state.teams[k]["roster"]) < st.session_state.max_roster_size
            }
            
            if team_options:
                st.markdown("---")
                st.markdown("##### 📌 실시간 입찰 등록")
                bidding_team = st.selectbox("입찰 팀 선택", list(team_options.keys()), format_func=lambda x: f"{x} ({st.session_state.teams[x]['name']})", key="bidding_team_select")
                bid_amount = st.number_input("입찰가", min_value=0, max_value=st.session_state.teams[bidding_team]["budget"], step=step_unit, key="bid_amount_input")
                
                if st.button("입찰하기", key="submit_bid_btn"):
                    st.session_state.temp_bids[selected_player][bidding_team] = bid_amount
                    st.success(f"{bidding_team} 입찰 완료: {bid_amount}P")
                    st.rerun()
                
                current_bids = st.session_state.temp_bids.get(selected_player, {})
                if current_bids:
                    st.markdown("##### 📋 현재 선수 입찰 현황")
                    bid_df = pd.DataFrame([
                        {"팀": k, "팀장": st.session_state.teams[k]['name'], "입찰가": v} 
                        for k, v in current_bids.items()
                    ]).sort_values(by="입찰가", ascending=False)
                    st.dataframe(bid_df, hide_index=True)
                    
                    st.markdown("---")
                    st.markdown("##### 👑 최종 낙찰 확정")
                    
                    sorted_bids = sorted(current_bids.items(), key=lambda x: x[1], reverse=True)
                    sorted_teams = [team for team, amount in sorted_bids]
                    
                    manual_override = st.checkbox("⚙️ 낙찰 팀 수동 변경하기", key="manual_override_check")
                    
                    if manual_override:
                        final_winning_team = st.selectbox(
                            "낙찰 팀 수동 선택", 
                            sorted_teams, 
                            index=0,
                            format_func=lambda x: f"{x} ({st.session_state.teams[x]['name']}) - {current_bids[x]}P",
                            key=f"final_winning_team_select_manual_{selected_player}"
                        )
                    else:
                        final_winning_team = sorted_teams[0]
                        top_team_leader = st.session_state.teams[final_winning_team]["name"]
                        st.info(f"자동 선택된 1위 팀: **{final_winning_team} ({top_team_leader})** - **{current_bids[final_winning_team]}P**")
                    
                    final_bid = current_bids[final_winning_team]
                    team_budget = st.session_state.teams[final_winning_team]["budget"]
                    winning_leader = st.session_state.teams[final_winning_team]["name"]
                    
                    if st.button(f"👑 '{final_winning_team}'({winning_leader}) 낙찰 확정!", type="primary", use_container_width=True, key="confirm_final_bid_btn"):
                        if final_bid > team_budget:
                            st.error(f"⚠️ 낙찰 실패: {final_winning_team}의 잔액({team_budget}P)보다 낙찰가({final_bid}P)가 더 높습니다!")
                        else:
                            st.session_state.teams[final_winning_team]["budget"] -= final_bid
                            st.session_state.teams[final_winning_team]["roster"].append({"name": selected_player, "bid": final_bid})
                            st.session_state.teams[final_winning_team]["roster"].sort(key=lambda x: x["name"])
                            
                            st.session_state.players.loc[st.session_state.players["선수명"] == selected_player, "상태"] = "완료"
                            st.session_state.history.append({
                                "시간": datetime.now().strftime("%H:%M:%S"), 
                                "팀": f"{final_winning_team}({winning_leader})", 
                                "선수": selected_player, 
                                "낙찰가": final_bid
                            })
                            
                            if selected_player in st.session_state.temp_bids:
                                del st.session_state.temp_bids[selected_player]
                            st.session_state.current_player = None
                            st.session_state.forced_player = None
                            save_data_to_file()
                            st.rerun()
                else:
                    st.info("아직 입찰한 팀이 없습니다. 팀별로 입찰가를 적고 [입찰하기]를 눌러주세요.")

    with col_right:
        st.subheader(f"📊 팀 현황 ({st.session_state.num_teams}개 팀)")
        for i in range(0, st.session_state.num_teams, 4):
            cols = st.columns(4)
            for j in range(4):
                if i+j < st.session_state.num_teams:
                    t_key = f"팀 {i+j+1}"
                    t = st.session_state.teams[t_key]
                    with cols[j].container(border=True):
                        st.markdown(f"**{t_key} ({t['name']})**")
                        st.caption(f"잔액: {t['budget']}P | 인원: {len(t['roster'])}/{st.session_state.max_roster_size}")
                        if t['roster']:
                            with st.expander("로스터 보기"):
                                for member in t['roster']:
                                    c1, c2 = st.columns([3, 1])
                                    c1.write(f"- {member['name']} ({member['bid']}P)")
                                    if c2.button("취소", key=f"cancel_{t_key}_{member['name']}"):
                                        t["budget"] += member["bid"]
                                        t["roster"].remove(member)
                                        st.session_state.players.loc[st.session_state.players["선수명"] == member["name"], "상태"] = "추첨완료"
                                        st.session_state.history.append({"시간": datetime.now().strftime("%H:%M:%S"), "팀": f"{t_key}({t['name']})", "선수": f"{member['name']} (낙찰취소)", "낙찰가": -member["bid"]})
                                        save_data_to_file()
                                        st.rerun()
        
        st.markdown("---")
        st.subheader("📜 전체 경매 기록")
        if st.session_state.history:
            st.table(pd.DataFrame(st.session_state.history))

# 탭 3: 랜덤 선수 추첨 페이지
with tab_random:
    st.subheader("🎲 대기 중인 선수 중 랜덤 추첨")
    st.write("아직 경매에 오르지 않은 대기 중인 선수들 중에서 중복 없이 랜덤으로 다음 경매 대상자를 뽑습니다.")
    
    waiting_df = st.session_state.players[st.session_state.players["상태"] == "대기중"]
    
    if not waiting_df.empty:
        st.info(f"현재 추첨 가능한 대기 선수: 총 **{len(waiting_df)}명**")
        
        if st.button("🎲 랜덤 선수 뽑기 돌리기!", type="primary", use_container_width=True):
            chosen = random.choice(waiting_df["선수명"].tolist())
            st.session_state.forced_player = chosen
            st.session_state.players.loc[st.session_state.players["선수명"] == chosen, "상태"] = "추첨완료"
            save_data_to_file()
            st.rerun()
    else:
        st.warning("모든 선수가 추첨되었습니다!")
        
    if st.session_state.forced_player:
        st.markdown("---")
        st.markdown("### 🎰 이번에 뽑힌 경매 대상자")
        
        forced_info = st.session_state.players[st.session_state.players["선수명"] == st.session_state.forced_player]
        if not forced_info.empty and forced_info.iloc[0]["사진"] is not None:
            st.image(forced_info.iloc[0]["사진"], width=240, caption=st.session_state.forced_player)
            
        st.markdown(f"## **{st.session_state.forced_player}** 🎉")
        st.write("상단 **[경매 진행]** 탭으로 이동하시면 해당 선수가 자동으로 선택되어 있습니다!")

# 탭 4: 🗺️ 랜드마크 추첨 페이지
with tab_landmark:
    st.subheader(f"🗺️ 맵별 팀 랜드마크 랜덤 배정 ({st.session_state.num_teams}개 팀)")
    
    selected_map = st.selectbox("추첨 및 편집할 맵을 선택하세요", list(st.session_state.custom_landmarks.keys()), key="selected_map_box")
    
    with st.expander(f"✏️ '{selected_map}' 랜드마크 목록 수정하기"):
        current_lm_text = "\n".join(st.session_state.custom_landmarks[selected_map])
        edited_lm_text = st.text_area("랜드마크 목록 (한 줄에 하나씩 입력)", value=current_lm_text, height=200)
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("💾 랜드마크 목록 저장", key="save_landmarks_btn"):
                new_lm_list = [line.strip() for line in edited_lm_text.split("\n") if line.strip()]
                st.session_state.custom_landmarks[selected_map] = new_lm_list
                save_data_to_file()
                st.success(f"'{selected_map}' 랜드마크 {len(new_lm_list)}개가 성공적으로 저장되었습니다!")
                st.rerun()
        with col_btn2:
            if st.button("🔄 기본 랜드마크로 초기화", key="reset_landmarks_btn"):
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
        
        if st.button(f"🎲 {st.session_state.num_teams}개 팀 랜드마크 전체 추첨!", type="primary", use_container_width=True, key="draw_landmark_btn"):
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