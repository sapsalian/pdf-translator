import re
from typing import Dict, List
from text_extract.text_extract import lineText

def getFirstXExceptBullet(line):
    """
    line["spans"] 안에서 글머리 기호 패턴을 제거한 후, 남은 첫 글자의 x0 좌표를 반환
    """
    if not startsWithBullet(None, line) and not startsWithNumberedList(None, line):
      return line["spans"][0]["bbox"][0]
    
    # bullet-like 패턴 목록(공백 없는 경우 포함)
    BULLET_PATTERNS = [
        r"^\s*(\d+\.)+\s*",          # 1.3.2. 1.3.3. ...
        r"^\s*\d+\.\s*",             # 1. 2. ...
        r"^\s*\(\d+\)\s*",           # (1)
        r"^\s*\[\d+\]\s*",           # [1]
        r"^\s*\d+\)\s*",             # 1)
        r"^\s*[a-z]\.\s*",           # a.
        r"^\s*\([a-zA-Z]\)\s*",      # (a) (B)
        r"^\s*[①-⑳]\s*",            # 특수 숫자 (① ~ ⑳)
        r"^\s*[가-힣]\.\s*",         # 가. 나. ...
        r"^\s*\([가-힣]\)\s*",       # (가)
        r"^\s*[\u2013\u2192\u2022\u2023\u25AA\u25CF\u25E6\u25BA\u25B6\u002D\u002A\u0022\u002B\u25CE\u2219\u25CB\u2192\u2714\u2726]\s*",
        r"^[\u0022]\s+",
    ]


    text = ""
    for span in line.get("spans", []):
        text += span.get("text", "")

    # 글머리 기호 제거
    cleaned_text = text
    for pattern in BULLET_PATTERNS:
        if re.match(pattern, cleaned_text):
            cleaned_text = re.sub(pattern, "", cleaned_text, count=1)
            break
    cleaned_text = cleaned_text.lstrip()

    # 남은 글자의 첫 x0 찾기
    target_index = len(text) - len(cleaned_text)
    # print(cleaned_text + "/////" + text, target_index)
    char_count = 0
    for span in line.get("spans", []):
        span_text = span.get("text", "")
        span_len = len(span_text)
        if char_count + span_len > target_index:
            offset = target_index - char_count
            if offset < len(span_text):
                return span["bbox"][0] + offset * ((span["bbox"][2] - span["bbox"][0]) / max(len(span_text), 1))
        char_count += span_len

    return line.get("spans", [])[-1]["bbox"][2]  # 못 찾았을 경우

def getFirstCharacterWidth(line):
  # bullet-like 패턴 목록
    BULLET_PATTERNS = [
        r"^(\d+\.)+\s+",          # 1.3.2. 1.3.3. ...
        r"^\d+\.\s+",             # 1. 2. ...
        r"^\(\d+\)\s+",           # (1)
        r"^\[\d+\]\s+",           # [1]
        r"^\d+\)\s+",             # 1)
        r"^[a-z]\.\s+",        # a.
        r"^\([a-zA-Z]\)\s+",      # (a) (B)
        r"^[①-⑳]\s+",            # 특수 숫자 (① ~ ⑳)
        r"^[가-힣]\.\s+",         # 가. 나. ...
        r"^\([가-힣]\)\s+",       # (가)
        r"^[\u2013\u2192\u2022\u2023\u25AA\u25CF\u25E6\u25BA\u25B6\u002D\u002A\u002B\u25CE\u2219\u25CB\u2192\u2714\u2726]\s*",
        r"^[\u0022]\s+",
    ]

    text = ""
    for span in line.get("spans", []):
        text += span.get("text", "")

    # 글머리 기호 제거
    cleaned_text = text
    for pattern in BULLET_PATTERNS:
        if re.match(pattern, cleaned_text):
            cleaned_text = re.sub(pattern, "", cleaned_text, count=1)
            break

    # 남은 첫글자의 width 찾기
    target_index = len(text) - len(cleaned_text)
    char_count = 0
    for span in line.get("spans", []):
        span_text = span.get("text", "")
        span_len = len(span_text)
        if char_count + span_len > target_index:
            return ((span["bbox"][2] - span["bbox"][0]) / max(len(span_text), 1))
        char_count += span_len

    return 0  # 못 찾았을 경우
  
def isLinesStartWithSameX(line1, line2, bullet_remove=True):
  x1 = line1["bbox"][0]
  x2 = line2["bbox"][0]
  
  if bullet_remove:
    x1 = getFirstXExceptBullet(line1)
    x2 = getFirstXExceptBullet(line2)
  
  char_width = min(getFirstCharacterWidth(line1), getFirstCharacterWidth(line2))
  # print(x1, x2, char_width)
  return abs(x1 - x2) <= char_width * 1.5

def startsWithBullet(_, line):
    # 현재 줄이 불릿 기호로 시작하는가
    text = lineText(line).strip()
    return bool(re.match(r"^[\u2013\u2192\u2022\u2023\u25AA\u25CF\u25E6\u25BA\u25B6\u002D\u002A\u002B\u25CE\u2219\u25CB\u2192\u2714\u2726]\s*", text)) or bool(re.match(r"^[\u0022]\s+", text))

def isShortLine(prev_line, line, block_bbox, src_lang, target_lang, ratio=0.9):
    # 이전 줄이 전체 block 너비의 90% 이하에서 끝나면서, 다음줄이 대문자로 시작하는가
    block_x0 = block_bbox[0]
    block_x2 = block_bbox[2]
    
    x0, x2 = prev_line["bbox"][0], prev_line["bbox"][2]
    prev_width = x2 - block_x0
    block_width = block_x2 - block_x0

    # if src_lang == "English":
    #     return (prev_width < block_width * ratio) and startsWithUpper(prev_line, line)
    # if src_lang == "한국어":
    #     return (prev_width < block_width * ratio)
    
    return (prev_width < block_width * ratio)


def getFirstFontSizeExcludingBullet(line):
    """ 글머리 기호 제거 후 남은 첫 글자의 span의 폰트 사이즈 반환 """
    BULLET_PATTERNS = [
        r"^\s*(\d+\.)+\s*",          # 1.3.2. 1.3.3. ...
        r"^\s*\d+\.\s*",             # 1. 2. ...
        r"^\s*\(\d+\)\s*",           # (1)
        r"^\s*\[\d+\]\s*",           # [1]
        r"^\s*\d+\)\s*",             # 1)
        r"^\s*[a-z]\.\s*",           # a.
        r"^\s*\([a-zA-Z]\)\s*",      # (a) (B)
        r"^\s*[①-⑳]\s*",            # 특수 숫자 (① ~ ⑳)
        r"^\s*[가-힣]\.\s*",         # 가. 나. ...
        r"^\s*\([가-힣]\)\s*",       # (가)
        r"^\s*[\u2013\u2192\u2022\u2023\u25AA\u25CF\u25E6\u25BA\u25B6\u002D\u002A\u0022\u002B\u25CE\u2219\u25CB\u2192\u2714\u2726]\s*"
    ]
    text = ""
    for span in line.get("spans", []):
        text += span.get("text", "")

    cleaned_text = text
    for pattern in BULLET_PATTERNS:
        if re.match(pattern, cleaned_text):
            cleaned_text = re.sub(pattern, "", cleaned_text, count=1)
            break
    cleaned_text = cleaned_text.lstrip()

    if not cleaned_text:
        return None

    # 남은 첫 글자가 등장하는 span의 폰트 사이즈 구하기
    target_index = len(text) - len(cleaned_text)
    char_count = 0

    for span in line.get("spans", []):
        span_text = span.get("text", "")
        span_len = len(span_text)
        if char_count + span_len > target_index:
            return span.get("size", None)
        char_count += span_len

    return None


def isSameFontSize(prev_line, curr_line) -> bool:
    """ 글머리 기호 제외 후, 첫 번째 실제 글자의 폰트 사이즈가 같은지 확인 """
    try:
        prev_size = getFirstFontSizeExcludingBullet(prev_line)
        curr_size = getFirstFontSizeExcludingBullet(curr_line)
        if prev_size is None or curr_size is None:
            return False
        return abs(prev_size - curr_size) < 0.1
    except Exception:
        return False



def startsWithUpper(_, line):
    # 현재 줄이 대문자로 시작하는가
    text = "".join(span["text"] for span in line["spans"]).strip()
    return bool(re.match(r"[A-Z][a-z]", text))

def isLineFull(line, block_bbox):
  block_x0 = block_bbox[0]
  block_x2 = block_bbox[2]
  
  x0, x2 = line["bbox"][0], line["bbox"][2]
  
  line_width = x2 - block_x0
  block_width = block_x2 - block_x0
  
  return (line_width >= block_width * 0.99)

def startsWithNumberedList(prev_line, line, sepa_check = False):
    # 현재 줄이 숫자+점 형식으로 시작하는가 (1., 2., ...)
    
    patterns = [
        r"^(\d+\.)+\s+",          # 1.3.2. 1.3.3. ...
        r"^\d+\.\s+",             # 1. 2. ...
        r"^\(\d+\)\s+",           # (1)
        r"^\[\d+\]\s+",           # [1]
        r"^\d+\)\s+",             # 1)
        r"^[a-z]\.\s+",        # a. 
        r"^\([a-zA-Z]\)\s+",      # (a) (B)
        r"^[①-⑳]\s+",            # 특수 숫자 (① ~ ⑳)
        r"^[가-힣]\.\s+",         # 가. 나. ...
        r"^\([가-힣]\)\s+",       # (가)
    ]
    
    if (sepa_check):
      patterns = [
        r"^(\d+\.)+\s+",          # 1.3.2. 1.3.3. ...
        r"^\d+\.\s+",             # 1. 2. ...
        r"^\[\d+\]\s+",           # [1]
        r"^\d+\)\s+",             # 1)
        r"^\([a-zA-Z]\)\s+",      # (a) (B)
        r"^[①-⑳]\s+",            # 특수 숫자 (① ~ ⑳)
        r"^[가-힣]\.\s+",         # 가. 나. ...
        r"^\([가-힣]\)\s+",       # (가)
    ]
      
    text = lineText(line).strip()
    
    return any(re.match(p, text.strip()) for p in patterns)


def calculateAverageGap(lines: List[Dict], rotate: int) -> float:
    """
    진행 방향에 따라 수직 gap 평균 계산
    rotate: 0/180이면 y축 기준, 90/270이면 x축 기준
    """
    gaps = []
    for i in range(len(lines) - 1):
        bbox1 = lines[i]["bbox"]
        bbox2 = lines[i+1]["bbox"]
        if rotate in (0, 180):
            gap = bbox2[1] - bbox1[3]  # 위쪽 y - 아래쪽 y
        else:
            gap = bbox2[0] - bbox1[2]  # 왼쪽 x - 오른쪽 x
        if gap > 0:
            gaps.append(gap)
    return sum(gaps) / len(gaps) if gaps else 0