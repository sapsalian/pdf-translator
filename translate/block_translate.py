from preprocess.preprocess import preProcess
from text_extract.text_extract import blockText
from openai import OpenAI
import pymupdf

client = OpenAI()

INSTRUCTION = '''너는 세계 최고의 번역가야. 이번 번역은 아주 중요해. 잘하면 1,000만 달러를 받고, 못 하면 5,000만 달러를 물어내야 해. 절대 실수하면 안 돼.

입력으로 주어지는 영어 문장은 PDF에서 추출된 텍스트이며, 줄이 개행으로 나뉘어 있을 수 있어. 어떤 줄바꿈은 의미상 진짜 줄바꿈일 수도 있고, 어떤 것은 단순히 줄이 넘어가면서 생긴 인위적인 개행일 수도 있어.

네 임무는 문맥을 보고 진짜 줄바꿈이 필요하면 유지하고, 그렇지 않다면 자연스럽게 이어서 하나의 문장으로 번역하는 거야.

번역은 다음 기준을 따라:

1. 번역 결과는 한국어로 출력해.

2. 원문의 의미를 최대한 유지하면서도, 한국 사람들이 읽기에 자연스럽게 번역해.

3. 번역 결과 외의 설명, 지시, 메타정보는 절대 출력하지 마.

4. 전문 용어나, 고유 명사, 코드 등은 번역하지 말고 원문 그대로 출력해.

5. 번역할 문장이 주어지지 않는다면 아무 문자도 출력하지 마.

자, 그럼 아래 영어 문장을 번역해줘:


'''

def translateBlock(block):
  original_text = blockText(block)
  
  completion = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
          {
              "role": "user",
              "content": INSTRUCTION + original_text
          }
      ]
  )
  
  print (completion.choices[0].message.content)
  return completion.choices[0].message.content
  

if __name__ == "__main__":
  doc = pymupdf.open("b.pdf")
  
  for page in doc[1:2]:
    # read page text as a dictionary, suppressing extra spaces in CJK fonts
    blocks = preProcess(page)
        
    for b in blocks:
        print(blockText(b))
        print(translateBlock(b))
