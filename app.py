import streamlit as st
from openai import OpenAI
import ast

with open('./user_account.txt','r',encoding='UTF-8') as f:
    user_account = ast.literal_eval(f.read()) #계정 정보
with open('./user_is_first.txt','r',encoding='UTF-8') as f:
    user_is_first = ast.literal_eval(f.read()) #고객의 첫 방문 여부
with open('./user_info.txt','r',encoding='UTF-8') as f:
    user_info = ast.literal_eval(f.read()) #[성별, 인종, 상의 사이즈, 허리 사이즈, 신발 사이즈]
with open('./user_info_optional.txt','r',encoding='UTF-8') as f:
    user_info_optional = ast.literal_eval(f.read())#[[옷 구분1, 옷 종류1, 색상1], [옷 구분2, 옷 종류2, 색상2], ...]

def login(username, password):
    if username in user_account and user_account[username] == password:
        return True
    else:
        return False

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""

if 'username' not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in: # 로그인 화면
    st.title("코디 추천 앱 demo")

    openai_api_key = st.text_input("OpenAI API Key", type="password")
    username = st.text_input("아이디")
    password = st.text_input("비밀번호", type="password")
    login_button = st.button("로그인")
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.", icon="🗝️")
    else:
        if login_button:
            if login(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state.openai_api_key = openai_api_key
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 잘못되었습니다.")

if st.session_state.logged_in: # 로그인 시 다음 페이지로 이동
    is_first = True
    openai_api_key =""
    for key, value in st.session_state.items():
        if key == "openai_api_key": openai_api_key = value

    client = OpenAI(api_key=openai_api_key)
    for key, value in user_is_first.items():
        if  key == st.session_state['username']: st.session_state.is_first = value
    if st.session_state.is_first: # 첫 방문 시 사전 정보 입력 페이지로 이동
        st.title("사전 정보 입력")
        st.session_state.check
        if "page" not in st.session_state:
            st.session_state.page = 0
        if "gender" not in st.session_state:
            st.session_state.gender = ""
        if "race" not in st.session_state:
            st.session_state.race = ""
        if "top" not in st.session_state:
            st.session_state.top = 0
        if "bottom" not in st.session_state:
            st.session_state.bottom = 0
        if "foot" not in st.session_state:
            st.session_state.foot = 0
        if st.session_state.page == 0:
            st.session_state.gender = st.radio("성별을 선택해주세요",["**남성**", "**여성**"])
            st.session_state.race = st.radio("인종을 선택해주세요",["**동양인**", "**서양인**"])
            st.session_state.top = st.select_slider("상의 사이즈를 입력해주세요",options = [80,85,90,95,100,105,110,115,120,125,130])
            st.session_state.bottom = st.slider("하의 사이즈를 입력해주세요", 24, 35)
            st.session_state.foot = st.select_slider("발 사이즈를 입력해주세요", options = [230,235,240,245,250,255,260,265,270,275,280,285])

            if st.button("다음"):
                st.session_state.page = 1
                st.rerun()
        
        if st.session_state.page == 1: # 입력한 정보 확인 페이지
            st.write(f"{st.session_state.username}님의 정보")
            st.write(f"성별 : {st.session_state.gender}")
            st.write(f"인종 : {st.session_state.race}")
            st.write(f"상의 사이즈 : {st.session_state.top}")
            st.write(f"하의 사이즈 : {st.session_state.bottom}")
            st.write(f"발 사이즈 : {st.session_state.foot}")
            st.write("입력한 내용이 확실합니까?")
            if st.button("예"):
                st.session_state.page = 2
                st.rerun()
            if st.button("아니오"):
                st.session_state.page = 0
                st.rerun()

        if st.session_state.page == 2: # 옷 정보 입력 선택 페이지
            st.write("(선택) 가지고 있는 옷 정보를 입력하시겠습니까? (나중에 언제든지 다시 입력할 수 있습니다.)")
            if st.button("예"):
                st.session_state.page = 3
                st.rerun()
            if st.button("아니오"):
                user_is_first[f"{st.session_state.username}"] = False
                new_text = str(user_is_first)
                with open('./user_is_first.txt','w',encoding='UTF-8') as f:
                    f.write(new_text)
                st.rerun()

        if st.session_state.page == 3:
            st.write("옷 정보 입력하는 화면")

        
    else: # 재방문 시 메인 페이지로 이동
        st.title("메인 페이지")
        if "main_page" not in st.session_state:
            st.session_state.main_page = 0
        if st.session_state.main_page == 0:
            st.session_state.outing = st.selectbox("오늘은 무슨 일로 외출하시나요?",("가족 모임", "친구들 모임 or 동창회", "생일파티", "데이트", "학교", "아르바이트"))
            st.session_state.where = st.text_input("목적지를 알려주세요!")
            st.session_state.time = st.time_input("시간 선택")
            st.session_state.item = st.text_input("착용하고 싶은 아이템이 있나요?")
            if st.button("옷 추천"):
                st.session_state.main_page = 1
                st.rerun()
        
        if st.session_state.main_page == 1:
            st.write(f"외출 목적 : {st.session_state.outing}")
            st.write(f"목적지 : {st.session_state.where}")
            st.write(f"시간 : {st.session_state.time}")
            st.write(f"착용 아이템 : {st.session_state.item}")


