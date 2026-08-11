import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime

st.set_page_config(page_title="배그 경매 시스템", layout="wide")

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

# 세션 상태 초기화 및 players.csv 자동 읽기
if "initialized" not in st.session_state:
    st.session_state.teams = {f"팀 {i}": {"name": "", "budget": 1000, "roster": []} for i in range(1, 17)}
    st.session_state.history = []
    st.session_state.current_player = None
    st.session_state.temp_bids = {} 
    st.session_state.forced_player = None 
    
    # GitHub에 함께 올린 players.csv 파일이 있으면 자동으로 불러옴
    if os.path.exists("players.csv"):
        try:
            df_csv = pd.read_csv("players.csv")
            if "상태" not in df_csv.columns:
                df_csv["상태"] = "대기중"
            if "사진" not in df_csv.columns:
                df_csv["사진"] = None
            st.session_state.players = df_csv
        except Exception:
            st.session_state.players = pd.DataFrame(columns=["선수명", "상태", "사진"])
    else:
        st.session_state.players = pd.DataFrame(columns=["선수명", "상태", "사진"])
        
    st.session_state.initialized = True

st.title("🏆 배틀그라운드 팀장 드래프트 경매 시스템")

# 1. 페이지 탭 구성
tab_set, tab_auction, tab_random = st.tabs(["설정 (팀장/선수 입력)", "경매 진행", "🎲 랜덤 선수 추첨"])

# 탭 1: 설정
with tab_set:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👤 팀장 이름 설정")
        for i in range(16):
            t_key = f"팀 {i+1}"
            st.session_state.teams[t_key]["name"] = st.text_input(f"{t_key} 팀장명", st.session_state.teams[t_key]["name"], key=f"team_name_{i}")
    
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
                    st.success(f"'{del_player}' 선수를 삭제했습니다.")
                    st.rerun()
            with col_del2:
                if st.button("⚠️ 명단 전체 삭제", key="clear_all_players_btn"):
                    st.session_state.players = pd.DataFrame(columns=["선수명", "상태", "사진"])
                    st.success("선수 명단을 모두 초기화했습니다.")
                    st.rerun()

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
            
            team_options = {name: info for name, info in st.session_state.teams.items() if len(info["roster"]) < 7}
            
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
                    
                    final_winning_team = st.selectbox(
                        "최종 낙찰 팀 선택", 
                        sorted_teams, 
                        format_func=lambda x: f"{x} ({st.session_state.teams[x]['name']}) - {current_bids[x]}P",
                        key="final_winning_team_select"
                    )
                    final_bid = current_bids[final_winning_team]
                    team_budget = st.session_state.teams[final_winning_team]["budget"]
                    
                    if st.button("최종 낙찰 확정", key="confirm_final_bid_btn"):
                        if final_bid > team_budget:
                            st.error(f"⚠️ 낙찰 실패: {final_winning_team}의 잔액({team_budget}P)보다 낙찰가({final_bid}P)가 더 높습니다!")
                        else:
                            st.session_state.teams[final_winning_team]["budget"] -= final_bid
                            st.session_state.teams[final_winning_team]["roster"].append({"name": selected_player, "bid": final_bid})
                            st.session_state.teams[final_winning_team]["roster"].sort(key=lambda x: x["name"])
                            
                            st.session_state.players.loc[st.session_state.players["선수명"] == selected_player, "상태"] = "완료"
                            st.session_state.history.append({"시간": datetime.now().strftime("%H:%M:%S"), "팀": f"{final_winning_team}({st.session_state.teams[final_winning_team]['name']})", "선수": selected_player, "낙찰가": final_bid})
                            
                            if selected_player in st.session_state.temp_bids:
                                del st.session_state.temp_bids[selected_player]
                            st.session_state.current_player = None
                            st.session_state.forced_player = None
                            st.rerun()
                else:
                    st.info("아직 입찰한 팀이 없습니다. 팀별로 입찰가를 적고 [입찰하기]를 눌러주세요.")

    with col_right:
        st.subheader("📊 팀 현황 (낙찰자 확인)")
        for i in range(0, 16, 4):
            cols = st.columns(4)
            for j in range(4):
                if i+j < 16:
                    t_key = f"팀 {i+j+1}"
                    t = st.session_state.teams[t_key]
                    with cols[j].container(border=True):
                        st.markdown(f"**{t_key} ({t['name']})**")
                        st.caption(f"잔액: {t['budget']}P | 인원: {len(t['roster'])}/7")
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