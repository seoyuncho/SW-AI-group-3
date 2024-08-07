import streamlit as st
from PIL import Image
import os

# 이미지 디렉토리 경로 설정
image_dir = 'images'

st.title('추천 코디')

# 이미지 파일 목록 가져오기
image_files = [f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]

# 사이드바에서 선택한 이미지 파일
selected_image = st.sidebar.selectbox('이미지를 선택하세요', image_files)

# 선택된 이미지 파일의 전체 경로
image_path = os.path.join(image_dir, selected_image)

# 이미지 로드 및 표시
image = Image.open(image_path)
st.image(image, caption=selected_image, use_column_width=True)
