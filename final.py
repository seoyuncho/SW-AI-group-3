import streamlit as st
from openai import OpenAI
import ast
import requests
import datetime
from datetime import timedelta
from datetime import time
import pandas as pd
import json
import re
from deep_translator import GoogleTranslator
import os

# 기상청 API 키
serviceKey = 'MjwzsGnby0UOkBp9eGkr4Jhzy7IO3vOyrQRvCHB%2BEwsZeNzKYHXFVAavYiLExcmp%2BJ9h88jXnadALImgUiCWrQ%3D%3D'

# 기상청 좌표 얻는 함수
def get_coordinates(do, city):
    filtered_df = df[(df['do'] == do) & (df['city'] == city)]
    x = filtered_df.iloc[0]['x']
    y = filtered_df.iloc[0]['y']
    return x, y

# 기상청 예보 값 얻는 함수
def get_fcst_value(json_data, fcst_date, fcst_time, category):
    items = json_data['response']['body']['items']['item']
    for item in items:
        if item['fcstDate'] == fcst_date and item['fcstTime'] == fcst_time and item['category'] == category:
            return item['fcstValue']
    return None

# 사용자 계정 정보 로드
with open('./user_account.txt','r',encoding='UTF-8') as f:
    user_account = ast.literal_eval(f.read())
with open('./user_is_first.txt','r',encoding='UTF-8') as f:
    user_is_first = ast.literal_eval(f.read())
with open('./user_info.txt','r',encoding='UTF-8') as f:
    user_info = ast.literal_eval(f.read())
with open('./user_info_optional.txt','r',encoding='UTF-8') as f:
    user_info_optional = ast.literal_eval(f.read())

# 로그인 함수
def login(username, password):
    if username in user_account and user_account[username] == password:
        return True
    else:
        return False

# 이미지 다운로드 함수
def download_image(image_url, folder_path):
    # 폴더가 없으면 생성
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # 현재 시간을 이용하여 유니크한 파일명 생성
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"outfit_{timestamp}.png"
    save_path = os.path.join(folder_path, file_name)
    
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Image successfully downloaded: {save_path}")
        return save_path
    else:
        print(f"Failed to download image. Status code: {response.status_code}")
        return None

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""

if 'username' not in st.session_state:
    st.session_state.username = ""

if 'add_cloths' not in st.session_state:
    st.session_state.add_cloths = False

# 로그인 화면
if not st.session_state.logged_in:
    st.title("👕 오늘 뭐 입지?")

    openai_api_key = st.text_input("OpenAI API Key", type="password")
    username = st.text_input("아이디")
    password = st.text_input("비밀번호", type="password")
    login_button = st.button("로그인")
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.", icon="🗝️")
    else:
        if login_button:
            if login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.openai_api_key = openai_api_key
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 잘못되었습니다.")

# 로그인 성공 후
if st.session_state.logged_in:
    print(f"로그인 직후 : {st.session_state.add_cloths}")
    client = OpenAI(api_key=st.session_state.openai_api_key)
    translator = GoogleTranslator(source='ko', target='en')

    file_path = 'korea_administrative_division_latitude_longitude.xlsx' #시군구에 따른 x,y 좌표값 불러오기
    df = pd.read_excel(file_path)
    do_city_dict = df.groupby('do')['city'].apply(list).to_dict()
    do_tuple = tuple(df['do'].unique())

    for key, value in user_is_first.items():
        if  key == st.session_state['username']:
            st.session_state.is_first = value

    if st.session_state.is_first:
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
            st.write("거주지를 입력해주세요.")
            st.session_state.do = st.selectbox("도를 선택해주세요",do_tuple)
            st.session_state.city = st.selectbox("시/군/구를 선택해주세요",do_city_dict[st.session_state.do])
            # 상체, 하체, 발 사이즈는 일단 사용 안 할 예정
            # st.session_state.top = st.select_slider("상의 사이즈를 입력해주세요",options = [80,85,90,95,100,105,110,115,120,125,130])
            # st.session_state.bottom = st.slider("하의 사이즈를 입력해주세요", 24, 35)
            # st.session_state.foot = st.select_slider("발 사이즈를 입력해주세요", options = [230,235,240,245,250,255,260,265,270,275,280,285])

            if st.button("다음"):
                st.session_state.page = 1
                # st.rerun()
        
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
        if "material" not in st.session_state:
            st.session_state.material = ""
        if "color" not in st.session_state:
            st.session_state.color = ""
        for key, value in user_info_optional.items():
            if key == st.session_state.username:
                count = 0
                for match in user_info_optional[key]:
                    count += 1
                    st.write(f"## 옷 정보 {count}")
                    if match[0] == "Tops": st.write(f"상의")
                    elif match[0] == "Bottoms": st.write(f"하의")
                    elif match[0] == "Shoes": st.write(f"신발")
                    st.write(match[1])
                    st.write(match[2])
                    st.write(match[3])
                    if st.button("삭제",key=f"button{count}"):
                        user_info_optional[st.session_state.username].remove([match[0],match[1],match[2],match[3]])
                        new_text = str(user_info_optional)
                        with open('./user_info_optional.txt','w',encoding='UTF-8') as f:
                            f.write(new_text)
                        st.rerun()

        # 옷 정보 입력 부분
        st.session_state.cloths = st.selectbox("옷 구분", ("상의", "하의", "신발"))
        if st.session_state.cloths == "상의":
            st.session_state.cloths = "Tops"
            st.session_state.types = st.selectbox("상의 종류", ("반팔", "긴팔", "니트", "셔츠", "맨투맨", "후드티", "폴로 셔츠"))
            st.session_state.material = st.selectbox("상의 소재", ("면", "폴리에스터", "나일론", "울", "린넨"))

        elif st.session_state.cloths == "하의":
            st.session_state.cloths = "Bottoms"
            st.session_state.types = st.selectbox("하의 종류", ("반바지", "긴바지", "청바지", "치마", "슬랙스"))
            st.session_state.material = st.selectbox("하의 소재", ("면", "폴리에스터", "데님", "울", "린넨"))
        elif st.session_state.cloths == "신발":
            st.session_state.cloths = "Shoes"
            st.session_state.types = st.selectbox("신발 구분", ("운동화", "로퍼", "부츠", "슬리퍼", "구두"))
            st.session_state.material = st.selectbox("신발 소재", ("가죽", "캔버스", "스웨이드", "메쉬"))
        st.session_state.color = st.selectbox("색상", ("흰색", "검은색", "회색", "네이비", "베이지", "카키", "빨간색", "분홍색", "주황색", "노란색", "초록색", "하늘색", "파란색", "보라색"))

        # 선택된 값들을 영어로 변환하여 저장

        if st.button("추가"):
            if st.session_state.username not in user_info_optional.keys():
                user_info_optional[st.session_state.username] = [[st.session_state.cloths, st.session_state.types, st.session_state.material, st.session_state.color]]
            else:
                user_info_optional[st.session_state.username].append([st.session_state.cloths, st.session_state.types, st.session_state.material, st.session_state.color])
            new_text = str(user_info_optional)
            with open('./user_info_optional.txt', 'w', encoding='UTF-8') as f:
                f.write(new_text)
            st.rerun()


        if st.button("외출 정보 입력 페이지로"):
            st.session_state.add_cloths = False
            st.session_state.main_page = 0
            st.rerun()
            
        
    else: # 재방문 시 메인 페이지로 이동
        print(f"메인 페이지 : {st.session_state.add_cloths}")
        st.session_state.gender = user_info[st.session_state.username][0]
        st.session_state.do = user_info[st.session_state.username][1]
        st.session_state.city = user_info[st.session_state.username][2]
        if "main_page" not in st.session_state:
            st.session_state.main_page = 0
        if st.session_state.main_page == 0:
            st.title("외출 정보를 알려주세요!")
            st.session_state.outing = st.text_input("오늘은 무슨 일로 외출하시나요?")
            time_options = [time(hour, 0) for hour in range(24)]
            time = st.selectbox("시간 선택", time_options, format_func=lambda t: t.strftime('%H:%M'))
            st.session_state.time = f'{str(time)[0:2]}{str(time)[3:5]}' 

            if st.button("옷 추천"):
                st.session_state.main_page = 1
                st.rerun()
            if st.button("옷장 정보 추가"):
                st.session_state.add_cloths = True
                st.rerun()
        
        enough_cloths = True
        if st.session_state.main_page == 1:
            st.title("추천 코디 생성하는 중...")
            empty_closet = "옷장 정보가 존재하지 않습니다."
            if st.session_state.username not in user_info_optional.keys():
                st.session_state.closet = empty_closet
                enough_cloths = False
                st.write("옷장 정보가 충분하지 않기 때문에 무작위로 추천 코디를 생성합니다.")
                st.write("(상의 3종류, 바지 3종류, 신발 2종류 이상부터 옷장 정보에서 추천 코디가 가능합니다)")
            else:
                st.session_state.closet = user_info_optional[st.session_state.username]
            if st.session_state.closet != empty_closet:
                tops_count = 0
                bottoms_count = 0
                shoes_count = 0
                for match in st.session_state.closet:
                    if match[0] == "Tops": tops_count += 1
                    elif match[0] == "Bottoms": bottoms_count += 1
                    elif match[0] == "Shoes": shoes_count += 1
                
                if tops_count < 3 or bottoms_count < 3 or shoes_count < 2:
                    enough_cloths = False
                    st.write("옷장 정보가 충분하지 않기 때문에 무작위로 추천 코디를 생성합니다.")
                    st.write("(상의 3종류, 바지 3종류, 신발 2종류 이상부터 옷장 정보에서 추천 코디가 가능합니다)")

            today = datetime.date.today()
            yesterday = today - timedelta(days=1)
            month = ""
            day = ""
            if len(str(yesterday.month)) == 1: month = "0" + str(yesterday.month)
            if len(str(yesterday.day)) == 1: day = "0" + str(yesterday.day)
            base_date = str(yesterday.year) + month + day
            fcst_date = str(today).replace('-','')
            fcst_time = st.session_state.time
            x, y = get_coordinates(st.session_state.do, st.session_state.city)

            url = f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?serviceKey={serviceKey}&pageNo=1&numOfRows=1000&dataType=json&base_date={base_date}&base_time=2300&nx={x}&ny={y}"
            response = requests.get(url, verify=False)
            

            # 응답 상태 코드 확인 및 디버깅을 위한 출력
            if response.status_code == 200:
                try:
                    json_data = response.json()
                except json.JSONDecodeError as e:
                    st.error("JSON 디코딩 오류가 발생했습니다.")
                    st.write(response.text)  # 응답 내용을 출력하여 디버깅
                    st.stop()
            else:
                st.error("API 요청이 실패했습니다.")
                st.write(f"응답 코드: {response.status_code}")
                st.stop()

            # 1시간 기온 불러오기
            st.session_state.tmp_value = get_fcst_value(json_data, fcst_date, fcst_time, 'TMP')
            # 강수확률 불러오기
            st.session_state.pop_value = get_fcst_value(json_data, fcst_date, fcst_time, 'POP')

            # st.write(f"Forecast Value (TMP): {st.session_state.tmp_value}")
            # st.write(f"Forecast Value (POP): {st.session_state.pop_value}")
            # st.write(f"성별 : {st.session_state.gender}")
            # st.write(f"외출 목적 : {st.session_state.outing}")
            # st.write(f"시간 : {st.session_state.time}")
            # st.write(f"옷장 정보 : {st.session_state.closet}")

            # 옷장 번역 및 매핑
            if enough_cloths == True:
                clothes_mapping = {
                    "Tops": {
                        "반팔": "Short sleeves",
                        "긴팔": "Long sleeves",
                        "니트": "Knitwear",
                        "셔츠": "Shirts",
                        "맨투맨": "Sweatshirts",
                        "후드티": "Hoodie",
                        "폴로 셔츠": "Polo shirts"
                    },
                    "Bottoms": {
                        "반바지": "Shorts",
                        "긴바지": "Pants",
                        "청바지": "Jeans",
                        "치마": "Skirts",
                        "슬랙스": "Slacks"
                    },
                    "Shoes": {
                        "운동화": "Sneakers",
                        "로퍼": "Loafers",
                        "부츠": "Boots",
                        "슬리퍼": "Slippers",
                        "구두": "Formal Shoes"
                    }
                }

                material_mapping = {
                    "Tops":{
                        "면" : "Cotton",
                        "폴리에스터" : "Polyester",
                        "나일론" : "Nylon",
                        "울" : "Wool",
                        "린넨" : "Linen"
                    },
                    "Bottoms":{
                        "면" : "Cotton",
                        "폴리에스터" : "Polyester",
                        "데님" : "Denim",
                        "울" : "Wool",
                        "린넨" : "Linen"
                    },
                    "Shoes":{
                        "가죽": "Leather",
                        "캔버스": "Canvas",
                        "스웨이드": "Suede",
                        "메쉬": "Mesh"
                    }
                }

                trans_closet = []
                for item in st.session_state.closet:
                    trans_item = [
                        item[0],
                        clothes_mapping[item[0]][item[1]],
                        material_mapping[item[0]][item[2]],
                        translator.translate(item[3]) if not item[3].isascii() else item[3]
                    ]
                    trans_closet.append(trans_item)
                
                sysmsg = f"""Looking at the given information that user gives, and recommend clothes that fit the situation.
                You must follow the answer format, never give any further explanation:
                You have these kind of clothes: {trans_closet}
                Answer format should be like this form: (Kind of clothes / Material of clothes / Color of clothes).
                Answer format example) Tops : T-shirt / Cotton / Black, Bottoms : Pants / Denim / Blue, Shoes : Sneakers / Leather / White"""

            else:
                sysmsg = f"""Looking at the given information that user gives, and recommend clothes that fit the situation.
                You must follow the answer format, never give any further explanation:
                Answer format should be like this form: (Kind of clothes / Material of clothes / Color of clothes).
                Answer format example) Tops : T-shirt / Cotton / Black, Bottoms : Pants / Denim / Blue, Shoes : Sneakers / Leather / White"""

            transout = translator.translate(st.session_state.outing)  
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"{sysmsg}"},
                    {"role": "user", "content": f"{st.session_state.tmp_value} Celsius, {st.session_state.pop_value}% chance of rain. {transout}."},
                ]
            )

            response_content = response.choices[0].message.content

            tops_match = re.search(r"Tops\s*:\s*([^/]+)\s*/\s*([^/]+)\s*/\s*([^,]+)", response_content)
            bottoms_match = re.search(r"Bottoms\s*:\s*([^/]+)\s*/\s*([^/]+)\s*/\s*([^,]+)", response_content)
            shoes_match = re.search(r"Shoes\s*:\s*([^/]+)\s*/\s*([^/]+)\s*/\s*([^,]+)", response_content)

            if tops_match and bottoms_match and shoes_match:
                Tops = tops_match.group(1).strip()
                Topmaterial = tops_match.group(2).strip()
                Topcolor = tops_match.group(3).strip()
                Bottoms = bottoms_match.group(1).strip()
                Bottommaterial = bottoms_match.group(2).strip()
                Bottomcolor = bottoms_match.group(3).strip()
                Shoes = shoes_match.group(1).strip()
                Shoematerial = shoes_match.group(2).strip()
                Shoecolor = shoes_match.group(3).strip()

                # 추출된 변수 출력
                st.write(f"Tops: {Tops}, Material: {Topmaterial}, Color: {Topcolor}")
                st.write(f"Bottoms: {Bottoms}, Material: {Bottommaterial}, Color: {Bottomcolor}")
                st.write(f"Shoes: {Shoes}, Material: {Shoematerial}, Color: {Shoecolor}")
            else:
                st.write("Failed to extract one or more parts from the response.")

            st.write(response_content)

            # 이미지 생성 및 추천된 옷 정보 표시
            if st.button("이미지 생성 및 옷 추천 확인"):
                with st.spinner('옷 추천 중...'):
                    hs = 'He'
                    pgender = 'male'
                    if (st.session_state.gender == '여성'):
                        hs = 'She'
                        pgender = 'female'

                    imggen_male = f"""An image of 20-year-old {pgender}.
                    /*instructions*/
                    1. {hs} is wearing a {Topcolor} {Topmaterial} {Tops} and {Bottomcolor} {Bottommaterial} {Bottoms}, {Shoecolor} {Shoematerial} {Shoes}.
                    2. {hs} is standing vertically upright in a white background.
                    3. {hs} is in the center of this image.
                    4. The image must be full body view, from head to toe.
                    5. Just one person."""

                    response_male = client.images.generate(
                        model="dall-e-3",
                        prompt=imggen_male,
                        style='vivid',
                        size="1024x1024",
                        quality="hd",
                        n=1
                    )

                    image_url_male = response_male.data[0].url

                    st.session_state.image_url_male = image_url_male
                    st.session_state.recommendation = f"# 오늘 뭐 입지? 의 추천!\n\nTop: {Topcolor} {Topmaterial} {Tops}\nBottom: {Bottomcolor} {Bottommaterial} {Bottoms}\nShoes: {Shoecolor} {Shoematerial} {Shoes}"
                    st.session_state.page = "result"
                    st.rerun()

            # 결과 페이지
            if "page" in st.session_state and st.session_state.page == "result":
                st.image(st.session_state.image_url_male, caption="오늘 뭐 입지?")
                st.markdown(st.session_state.recommendation.replace("\n", "  \n"))

                # 이미지 저장
                images_folder = './images'
                saved_image_path = download_image(st.session_state.image_url_male, images_folder)
                
                if saved_image_path:
                    st.success(f"이미지가 성공적으로 저장되었습니다: {saved_image_path}")
                    
                    # 저장된 이미지 다운로드 버튼 추가
                    with open(saved_image_path, "rb") as file:
                        btn = st.download_button(
                            label="코디 이미지 다운로드",
                            data=file,
                            file_name=os.path.basename(saved_image_path),
                            mime="image/png"
                        )
                    if st.button("외출 정보 입력 페이지로"):
                        st.session_state.add_cloths = False
                        st.session_state.main_page = 0
                        st.rerun()
                else:
                    st.error("이미지 저장에 실패했습니다.")

