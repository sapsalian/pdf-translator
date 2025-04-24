import re
from text_extract.text_extract import lineText

def getFirstXExceptBullet(line):
    """
    line["spans"] 안에서 글머리 기호 패턴을 제거한 후, 남은 첫 글자의 x0 좌표를 반환
    """
    if not starts_with_bullet(None, line) and not starts_with_numbered_list(None, line):
      return line["spans"][0]["bbox"][0]
    
    # bullet-like 패턴 목록(공백 없는 경우 포함)
    BULLET_PATTERNS = [
        r"^(\d+\.)+\s*",          # 1.3.2. 1.3.3. ...
        r"^\d+\.\s*",             # 1. 2. ...
        r"^\(\d+\)\s*",           # (1)
        r"^\[\d+\]\s*",           # [1]
        r"^\d+\)\s*",             # 1)
        r"^[a-z]\.\s*",        # a. 
        r"^\([a-zA-Z]\)\s*",      # (a) (B)
        r"^[①-⑳]\s*",            # 특수 숫자 (① ~ ⑳)
        r"^[가-힣]\.\s*",         # 가. 나. ...
        r"^\([가-힣]\)\s*",       # (가)
        r"^[\u2022\u2023\u25AA\u25E6\u25BA\-\*\"\+\u2219\u25CB\u25E6\u2023\u2192\u2714\u2726\"]\s*"
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
        r"^[\u2022\u2023\u25AA\u25E6\u25BA\-\*\"\+\u2219\u25CB\u25E6\u2023\u2192\u2714\u2726\"]\s+"
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
  
def isLinesStartWithSameX(line1, line2):
  x1 = getFirstXExceptBullet(line1)
  x2 = getFirstXExceptBullet(line2)
  char_width = min(getFirstCharacterWidth(line1), getFirstCharacterWidth(line2))
  return abs(x1 - x2) <= char_width * 1

def starts_with_bullet(_, line):
    # 현재 줄이 불릿 기호로 시작하는가
    text = lineText(line)
    return bool(re.match(r"^[\u2022\u2023\u25AA\u25E6\u25BA\-\*\"\+\u2219\u25CB\u25E6\u2023\u2192\u2714\u2726\"]\s+", text))

def starts_with_numbered_list(_, line, sepa_check = False):
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
      
    text = lineText(line)
    
    return any(re.match(p, text.strip()) for p in patterns)