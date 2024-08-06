import streamlit as st
from openai import OpenAI
import ast
import requests
import datetime
from datetime import timedelta
import pandas as pd
import json

url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0'
serviceKey = 'MjwzsGnby0UOkBp9eGkr4Jhzy7IO3vOyrQRvCHB%2BEwsZeNzKYHXFVAavYiLExcmp%2BJ9h88jXnadALImgUiCWrQ%3D%3D'
params = {'serviceKey':serviceKey, 'pageNo' : '1','numOfRows' : '1000','dataType' : 'XML','base_date':'','nx':'','ny':''}


def get_coordinates(do, city):
    filtered_df = df[(df['do'] == do) & (df['city'] == city)]
    x = filtered_df.iloc[0]['x']
    y = filtered_df.iloc[0]['y']
    return x, y

with open('./user_account.txt','r',encoding='UTF-8') as f:
    user_account = ast.literal_eval(f.read()) #계정 정보
with open('./user_is_first.txt','r',encoding='UTF-8') as f:
    user_is_first = ast.literal_eval(f.read()) #고객의 첫 방문 여부
with open('./user_info.txt','r',encoding='UTF-8') as f:
    user_info = ast.literal_eval(f.read()) #[성별, 도, 시/군/구, 상의 사이즈, 허리 사이즈, 신발 사이즈]
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

if 'add_cloths' not in st.session_state:
    st.session_state.add_cloths = False

if not st.session_state.logged_in: # 로그인 화면
    st.title("오늘 뭐 입지?")

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
    client = OpenAI(api_key=st.session_state.openai_api_key)

    file_path = 'korea_administrative_division_latitude_longitude.xlsx' #시군구에 따른 x,y 좌표값 불러오기
    df = pd.read_excel(file_path)
    do_city_dict = df.groupby('do')['city'].apply(list).to_dict()
    do_tuple = tuple(df['do'].unique())

    for key, value in user_is_first.items():
        if  key == st.session_state['username']: st.session_state.is_first = value
    if st.session_state.is_first: # 첫 방문 시 사전 정보 입력 페이지로 이동
        st.title("사전 정보 입력")
        if "page" not in st.session_state:
            st.session_state.page = 0
        if "gender" not in st.session_state:
            st.session_state.gender = ""
        if "do" not in st.session_state:
            st.session_state.do = ""
        if "city" not in st.session_state:
            st.session_state.city = ""
        if "top" not in st.session_state:
            st.session_state.top = 0
        if "bottom" not in st.session_state:
            st.session_state.bottom = 0
        if "foot" not in st.session_state:
            st.session_state.foot = 0
        if st.session_state.page == 0:
            st.session_state.gender = st.radio("성별을 선택해주세요",["**남성**", "**여성**"])
            st.session_state.do = st.selectbox("도를 선택해주세요",do_tuple)
            st.session_state.city = st.selectbox("시/군/구를 선택해주세요",do_city_dict[st.session_state.do])
            st.session_state.top = st.select_slider("상의 사이즈를 입력해주세요",options = [80,85,90,95,100,105,110,115,120,125,130])
            st.session_state.bottom = st.slider("하의 사이즈를 입력해주세요", 24, 35)
            st.session_state.foot = st.select_slider("발 사이즈를 입력해주세요", options = [230,235,240,245,250,255,260,265,270,275,280,285])

            if st.button("다음"):
                st.session_state.page = 1
                st.rerun()
        
        if st.session_state.page == 1: # 입력한 정보 확인 페이지
            st.write(f"{st.session_state.username}님의 정보")
            st.write(f"성별 : {st.session_state.gender}")
            st.write(f"거주지 : {st.session_state.do}, {st.session_state.city}")
            st.write(f"상의 사이즈 : {st.session_state.top}")
            st.write(f"하의 사이즈 : {st.session_state.bottom}")
            st.write(f"발 사이즈 : {st.session_state.foot}")
            st.write("입력한 내용이 확실합니까?")
            if st.button("예"):
                user_info[f"{st.session_state.username}"] = [st.session_state.gender,st.session_state.do, st.session_state.city,st.session_state.top,st.session_state.bottom,st.session_state.foot]
                new_text = str(user_info)
                with open('./user_info.txt','w',encoding='UTF-8') as f:
                    f.write(new_text)
                st.session_state.page = 2
                st.rerun()
            if st.button("아니오"):
                st.session_state.page = 0
                st.rerun()

        if st.session_state.page == 2: # 옷 정보 입력 선택 페이지
            user_is_first[f"{st.session_state.username}"] = False
            new_text = str(user_is_first)
            with open('./user_is_first.txt','w',encoding='UTF-8') as f:
                f.write(new_text)
            st.write("(선택) 가지고 있는 옷 정보를 입력하시겠습니까? (나중에 언제든지 다시 입력할 수 있습니다.)")
            if st.button("예"):
                st.session_state.add_cloths = True
                st.rerun()
            if st.button("아니오"):
                st.rerun()

    elif st.session_state.add_cloths == True:
        st.write("옷 정보 입력하는 화면")
        st.write("추후 구현 예정")
        
    else: # 재방문 시 메인 페이지로 이동
        st.session_state.gender = user_info[st.session_state.username][0]
        st.session_state.do = user_info[st.session_state.username][1]
        st.session_state.city = user_info[st.session_state.username][2]
        st.session_state.top = user_info[st.session_state.username][3]
        st.session_state.bottom = user_info[st.session_state.username][4]
        st.session_state.foot = user_info[st.session_state.username][5]
        st.title("메인 페이지")
        if "main_page" not in st.session_state:
            st.session_state.main_page = 0
        if st.session_state.main_page == 0:
            st.session_state.outing = st.selectbox("오늘은 무슨 일로 외출하시나요?",("가족 모임", "친구들 모임 or 동창회", "생일파티", "데이트", "학교", "아르바이트"))
            st.session_state.date = st.date_input("날짜 선택")
            st.session_state.time = st.time_input("시간 선택")
            st.session_state.item = st.text_input("착용하고 싶은 아이템이 있나요?")
            if st.button("옷 추천"):
                st.session_state.main_page = 1
                st.rerun()
            if st.button("옷 추가"):
                st.session_state.add_cloths = True
                st.rerun()
        
        if st.session_state.main_page == 1:
            today = datetime.date.today()
            yesterday = today - timedelta(days=1)
            month = ""
            day = ""
            if len(str(today.month)) == 1: month = "0" + str(today.month)
            if len(str(today.day)) == 1: day = "0" + str(today.day)
            base_date = str(today.year) + month + day
            print(base_date)
            params["base_date"] = base_date
            x,y = get_coordinates(st.session_state.do, st.session_state.city)
            params["nx"] = x
            params["ny"] = y
            url = f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst?serviceKey={serviceKey}&numOfRows=1000&pageNo=10&dataType=json&base_date={base_date}&base_time=0200&nx={x}&ny={y}"
            response = requests.get(url, verify=False)
            res = json.loads(response.text)
            st.write(res)
            
            st.write(f"외출 목적 : {st.session_state.outing}")
            st.write(f"시간 : {st.session_state.time}")
            st.write(f"착용 아이템 : {st.session_state.item}")
            st.write("\n추후 구현 예정")


