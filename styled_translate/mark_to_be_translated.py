import re
from typing import List, Dict



def getBlockText(block: Dict):
    text = ""
    for line in block["lines"]:
       for span in line["spans"]:
          text += span["text"]
    return text
    

def isToBeTranslated(block: Dict) -> bool:
    # Picture 또는 Formula 블락이면 False
    if block.get("class_name", "Text") in ["Picture", "Formula"]:
        return False

    # block의 텍스트 내 영 대소문자가 없으면 False
    text = getBlockText(block)
    if not re.search(r'[A-Za-z]', text):
        return False

    return True
  
  
'''
번역 보내야 할 블락인지 아닌지 마킹하는 함수.
나중에 번역 보내야 할 블락들은 기존 블락 지운 후, 번역된 블락으로 대체되고,
그렇지 않은 블락은 원래 형태 그대로 놔둠.

번역 보내지 않을 블락 기준:
  - Picture 블락 (block["class_name"] 확인)
  - Formula 블락 (block["class_name"] 확인)
  - block 내에 있는 텍스트에 영 대소문자가 없는 경우.
  
번역 보내야 할 블락은 block["to_be_translated"]에 True를
아니면 False를 할당.
'''


def assignToBeTranslated(blocks: List[Dict]) -> List[Dict]:
    for block in blocks:
        block["to_be_translated"] = isToBeTranslated(block)
    return blocks