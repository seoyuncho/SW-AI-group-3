from openai import OpenAI
import requests
import re

# OpenAI API 클라이언트 초기화

client = OpenAI(api_key='apikey채워넣어주세요')


sysmsg = """Looking at the given information that user gives, and recommend clothes that fit the situation.
You must follow the answer format, never give any further explanation:
Answer format example) Tops : T-shirt / Black, Bottoms : Jeans / Blue, Shoes : Sneakers / White"""


response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[
    {"role": "system", "content": f"{sysmsg}"},
    {"role": "user", "content": f"Hot summer, For date with girlfriend."}
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

# 이미지 생성 프롬프트 (마른 체형)
imggen_male = f"""An image of 20-year-old male.
/*instructions*/
1. He is wearing a {Topcolor} {Tops} and {Bottomcolor} {Bottoms}, {Shoecolor} {Shoes}.
2. He is standing vertically upright in a white background.
3. He is in the center of this image.
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
