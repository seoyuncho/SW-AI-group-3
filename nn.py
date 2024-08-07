import streamlit as st
from openai import OpenAI
import ast
import requests
import datetime
from datetime import timedelta
import pandas as pd
import json
import re
from deep_translator import GoogleTranslator

# OpenAI API 클라이언트 초기화
client = OpenAI(api_key='채워넣어주쇼')

translator = GoogleTranslator(source='ko', target='en')


#이거 그 옷장 있는지
st.session_state.closet = [["Tops","니트","흰색"],["Tops","스웨트셔츠","파란색"],["Bottoms","청바지","파란색"],["Shoes","운동화","검은색"]]
okay = True

if okay == True:
    # 번역된 사용자 정보를 저장할 리스트
    trans_closet = []
    # 각 항목을 번역하여 리스트에 추가
    for item in st.session_state.closet:
        trans_item = [translator.translate(text) if not text.isascii() else text for text in item]
        trans_closet.append(trans_item)
    
    sysmsg = f"""Looking at the given information that user gives, and recommend clothes that fit the situation.
    You must follow the answer format, never give any further explanation:
    You have these kind of clothes: {trans_closet}
    Answer format example) Tops : T-shirt / Black, Bottoms : Jeans / Blue, Shoes : Sneakers / White"""

elif okay == False:
    sysmsg = """Looking at the given information that user gives, and recommend clothes that fit the situation.
    You must follow the answer format, never give any further explanation:
    Answer format example) Tops : T-shirt / Black, Bottoms : Jeans / Blue, Shoes : Sneakers / White"""


st.session_state.temp_value = '17'
st.session_state.pop_value = '80'
st.session_state.outing = '여자친구와 카페 데이트'

transout = translator.translate(st.session_state.outing)  
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[
    {"role": "system", "content": f"{sysmsg}"},
    {"role": "user", "content": f"{st.session_state.temp_value} Celsius, {st.session_state.pop_value}% chance of rain. {transout}."},
  ]
)

response_content = response.choices[0].message.content

tops_match = re.search(r"Tops\s*:\s*([^/]+)\s*/\s*([^,]+)", response_content)
bottoms_match = re.search(r"Bottoms\s*:\s*([^/]+)\s*/\s*([^,]+)", response_content)
shoes_match = re.search(r"Shoes\s*:\s*([^/]+)\s*/\s*([^,]+)", response_content)

if tops_match and bottoms_match and shoes_match:
    Tops = tops_match.group(1).strip()
    Topcolor = tops_match.group(2).strip()
    Bottoms = bottoms_match.group(1).strip()
    Bottomcolor = bottoms_match.group(2).strip()
    Shoes = shoes_match.group(1).strip()
    Shoecolor = shoes_match.group(2).strip()

    # 추출된 변수 출력
    print(f"Tops = '{Tops}'")
    print(f"Topcolor = '{Topcolor}'")
    print(f"Bottoms = '{Bottoms}'")
    print(f"Bottomcolor = '{Bottomcolor}'")
    print(f"Shoes = '{Shoes}'")
    print(f"Shoecolor = '{Shoecolor}'")
else:
    print("Failed to extract one or more parts from the response.")

print(response_content)

st.session_state.gender = 'male'
if (st.session_state.gender == 'female'):
    hs = 'She'
else :
    hs = 'He'

# mmg = 'obese'
# 이미지 생성 프롬프트 (마른 체형)
imggen_male = f"""An image of 20-year-old {st.session_state.gender}.
/*instructions*/
1. {hs} is wearing a {Topcolor} {Tops} and {Bottomcolor} {Bottoms}, {Shoecolor} {Shoes}.
2. {hs} is standing vertically upright in a white background.
3. {hs} is in the center of this image.
4. The image must be full body view, from head to toe.
5. Just one person. """

# 이미지 생성 요청 (마른 체형)
response_male = client.images.generate(
    model="dall-e-3",
    prompt=imggen_male,
    style='vivid',
    size="1024x1024",
    quality="hd",
    n=1
)

# 생성된 이미지 URL 출력 (마른 체형)
image_url_male = response_male.data[0].url
print(image_url_male)


def download_image(image_url, save_path):
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Image successfully downloaded: {save_path}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")

# 이미지 다운로드 경로 설정
save_path = '/Users/apple/Desktop/projectpicutre/finalimg.png'

# 이미지 다운로드 실행
download_image(image_url_male, save_path)
