import streamlit as st
from openai import OpenAI
import ast
import requests
import datetime
from datetime import timedelta
import pandas as pd
import json

serviceKey = 'MjwzsGnby0UOkBp9eGkr4Jhzy7IO3vOyrQRvCHB%2BEwsZeNzKYHXFVAavYiLExcmp%2BJ9h88jXnadALImgUiCWrQ%3D%3D'
#params = {'serviceKey':serviceKey, 'pageNo' : '1','numOfRows' : '1000','dataType' : 'XML','base_date':'','nx':'','ny':''}

def get_coordinates(do, city):
    filtered_df = df[(df['do'] == do) & (df['city'] == city)]
    x = filtered_df.iloc[0]['x']
    y = filtered_df.iloc[0]['y']
    return x, y

def get_fcst_value(json_data, fcst_time, category):
    items = json_data['response']['body']['items']['item']
    for item in items:
        if item['fcstTime'] == fcst_time and item['category'] == category:
            return item['fcstValue']
    return None

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
        if st.session_state.page == 0:
            st.session_state.gender = st.radio("성별을 선택해주세요",["남성", "여성"])
            st.session_state.do = st.selectbox("도를 선택해주세요",do_tuple)
            st.session_state.city = st.selectbox("시/군/구를 선택해주세요",do_city_dict[st.session_state.do])
            # 상체, 하체, 발 사이즈는 일단 사용 안 할 예정
            # st.session_state.top = st.select_slider("상의 사이즈를 입력해주세요",options = [80,85,90,95,100,105,110,115,120,125,130])
            # st.session_state.bottom = st.slider("하의 사이즈를 입력해주세요", 24, 35)
            # st.session_state.foot = st.select_slider("발 사이즈를 입력해주세요", options = [230,235,240,245,250,255,260,265,270,275,280,285])

            if st.button("다음"):
                st.session_state.page = 1
                st.rerun()
        
        if st.session_state.page == 1: # 입력한 정보 확인 페이지
            st.write(f"{st.session_state.username}님의 정보")
            st.write(f"성별 : {st.session_state.gender}")
            st.write(f"거주지 : {st.session_state.do}, {st.session_state.city}")
            st.write("입력한 내용이 확실합니까?")
            if st.button("예"):
                user_info[f"{st.session_state.username}"] = [st.session_state.gender,st.session_state.do, st.session_state.city]
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
        st.title("옷장 정보 입력")
        if "cloths" not in st.session_state:
            st.session_state.cloths = ""
        if "types" not in st.session_state:
            st.session_state.types = ""
        if "color" not in st.session_state:
            st.session_state.color = ""
        for key, value in user_info_optional.items():
            if key == st.session_state.username:
                count = 0
                for cloths, types, color in user_info_optional[key]:
                    count += 1
                    st.write(f"## 옷 정보 {count}")
                    st.write(f"{cloths}")
                    st.write(f"{types}")
                    st.write(f"{color}")
                    if st.button("삭제",key=f"button{count}"):
                        user_info_optional[st.session_state.username].remove([cloths,types,color])
                        new_text = str(user_info_optional)
                        with open('./user_info_optional.txt','w',encoding='UTF-8') as f:
                            f.write(new_text)
                        st.rerun()

        st.session_state.cloths = st.selectbox("옷 구분",("상의","하의","신발"))
        if st.session_state.cloths == "상의":
            st.session_state.types = st.selectbox("상의 종류",("반팔","긴팔","니트","셔츠","면티"))
        elif st.session_state.cloths == "하의":
            st.session_state.types = st.selectbox("하의 종류",("반바지","긴바지","5부 바지"))
        elif st.session_state.cloths == "신발":
            st.session_state.types = st.selectbox("신발 구분",("운동화","로퍼","부츠","슬리퍼"))
        st.session_state.color = st.selectbox("색상",("흰색","검은색","회색","네이비","베이지","카키","빨간색","분홍색","주황색","노란색","초록색","하늘색","파란색","보라색"))

        if st.button("추가"):
            user_info_optional[st.session_state.username].append([st.session_state.cloths,st.session_state.types,st.session_state.color])
            new_text = str(user_info_optional)
            with open('./user_info_optional.txt','w',encoding='UTF-8') as f:
                f.write(new_text)
            st.rerun()

        if st.button("메인 페이지로"):
            st.session_state.add_cloths = False
            st.rerun()
            
        
    else: # 재방문 시 메인 페이지로 이동
        st.session_state.gender = user_info[st.session_state.username][0]
        st.session_state.do = user_info[st.session_state.username][1]
        st.session_state.city = user_info[st.session_state.username][2]
        # st.session_state.top = user_info[st.session_state.username][3]
        # st.session_state.bottom = user_info[st.session_state.username][4]
        # st.session_state.foot = user_info[st.session_state.username][5]
        st.title("메인 페이지")
        if "main_page" not in st.session_state:
            st.session_state.main_page = 0
        if st.session_state.main_page == 0:
            st.session_state.outing = st.text_input("오늘은 무슨 일로 외출하시나요?")
            st.session_state.time = st.time_input("시간 선택")
            if st.button("옷 추천"):
                st.session_state.main_page = 1
                st.rerun()
            if st.button("옷장 정보 추가"):
                st.session_state.add_cloths = True
                st.rerun()
        
        if st.session_state.main_page == 1:
            today = datetime.date.today()
            yesterday = today - timedelta(days=1)
            month = ""
            day = ""
            if len(str(yesterday.month)) == 1: month = "0" + str(yesterday.month)
            if len(str(yesterday.day)) == 1: day = "0" + str(yesterday.day)
            base_date = str(yesterday.year) + month + day
            print(base_date)
            fcst_time = str(st.session_state.time).replace(":","")[:2] + "00"
            print(fcst_time)

            x,y = get_coordinates(st.session_state.do, st.session_state.city)

            url = f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?serviceKey={serviceKey}&pageNo=1&numOfRows=1000&dataType=json&base_date={base_date}&base_time=2300&nx={x}&ny={y}"
            response = requests.get(url, verify=False)
            json_data = response.json()
            # st.write(json_data)

            # 1시간 기온 불러오기
            tmp_value = get_fcst_value(json_data, fcst_time, 'TMP')
            st.write(f"Forecast Value (TMP): {tmp_value}")
            # 강수확률 불러오기
            pop_value = get_fcst_value(json_data, fcst_time, 'POP')
            st.write(f"Forecast Value (POP): {pop_value}")

            st.write(f"외출 목적 : {st.session_state.outing}")
            st.write(f"시간 : {st.session_state.time}")
            st.write("\n추후 구현 예정")

