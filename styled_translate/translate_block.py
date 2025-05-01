from typing import Dict, List
from styled_translate.assign_style import SpanStyle
from openai import OpenAI
import re

client = OpenAI()

def blockTextWithStyleTags(block: Dict, style_dict: Dict[int, 'SpanStyle']) -> str:
    """
    block의 span들을 순회하며 다음과 같은 처리를 수행:
    
    - block["primary_style_id"]에 해당하는 span은 그대로 출력
    - 그렇지 않은 스타일은 [[n]]...[[/n]] 형식으로 감쌈
      - 단, superscript인 경우 [[s{n}]]...[[/s{n}]] 형식 사용
    - span 간의 x 간격이 평균 글자 너비의 0.9배 이상이면 공백(" ") 삽입
    - 줄(line)이 바뀔 때마다 줄 간 개행 삽입

    Args:
        block (Dict): PyMuPDF의 텍스트 블록 (type=0)
        style_dict (Dict[int, SpanStyle]): 스타일 ID → SpanStyle 매핑

    Returns:
        str: 스타일 태그 및 공백이 포함된 문자열
    """
    primary_id = block.get("primary_style_id")
    output = []

    for line in block.get("lines", []):
        line_text = ""          # 현재 줄의 누적 문자열
        prev_span = None        # 이전 span 저장용

        for span in line.get("spans", []):
            span_text = span.get("text", "")
            style_id = span.get("style_id")

            # 이전 span과의 간격(gap)에 따라 공백 삽입 여부 결정
            if prev_span is not None:
                prev_end = prev_span["bbox"][2]       # 이전 span의 x 끝 좌표
                curr_start = span["bbox"][0]          # 현재 span의 x 시작 좌표
                gap = curr_start - prev_end           # 두 span 간 간격

                # 글자 너비 추정
                prev_width = prev_span["bbox"][2] - prev_span["bbox"][0]
                curr_width = span["bbox"][2] - span["bbox"][0]

                # 문자당 평균 너비 계산 (0 division 방지)
                prev_char_width = prev_width / max(len(prev_span["text"]), 1)
                curr_char_width = curr_width / max(len(span_text), 1)
                avg_char_width = (prev_char_width + curr_char_width) / 2

                # gap이 평균 글자 너비의 0.9배 이상이면 공백 추가
                if gap >= avg_char_width * 0.9:
                    line_text += " "

            # 스타일 태그 처리
            if style_id == primary_id:
                # 주 스타일이면 태그 없이 그대로 출력
                line_text += span_text
            else:
                # superscript면 태그에 's' 접두어 추가
                style = style_dict.get(style_id)
                tag_prefix = f"s{style_id}" if style and style.is_superscript else f"{style_id}"
                line_text += f"[[{tag_prefix}]]{span_text}[[/{tag_prefix}]]"

            prev_span = span  # 다음 span을 위한 갱신

        # 줄(line) 단위로 누적, 줄 간에는 개행 삽입
        output.append(line_text)

    # 전체 줄을 개행으로 이어붙여 반환
    return "\n".join(output)



def parseStyledText(translated_text: str, primary_style_id: int) -> List[Dict[str, int | str]]:
    """
    스타일 태그가 포함된 번역 텍스트를 파싱하여 styled span 리스트를 생성합니다.

    입력 텍스트에는 다음과 같은 스타일 태그가 포함될 수 있습니다:
        - [[3]]텍스트[[/3]]   → 스타일 ID 3
        - [[s4]]텍스트[[/s4]] → 윗첨자 스타일, 스타일 ID 4

    이 함수는 위와 같은 태그를 기준으로 텍스트를 분리하고,
    각 텍스트 구간에 해당하는 style_id (int)를 부여합니다.
    태그가 없는 일반 텍스트는 기본 스타일 ID(primary_style_id)를 부여합니다.

    Args:
        translated_text (str): 스타일 태그가 포함된 번역 결과 문자열
        primary_style_id (int): 태그 없는 일반 텍스트에 부여할 기본 스타일 ID

    Returns:
        List[Dict[str, int | str]]: 스타일이 부여된 span 목록
            예시: [{"style_id": 3, "text": "H"}, {"style_id": 1, "text": "입니다."}]
    """

    # 스타일 태그 패턴 정의
    # [[s3]]text[[/s3]] 또는 [[2]]text[[/2]] 와 같은 구조를 캡처
    pattern = re.compile(r'\[\[(s?\d+)\]\](.*?)\[\[/\1\]\]', re.DOTALL)

    result = []         # 최종 styled span 리스트
    last_index = 0      # 마지막으로 처리된 인덱스 위치

    # 모든 스타일 태그를 순차적으로 탐색
    for match in pattern.finditer(translated_text):
        start, end = match.span()           # 현재 태그 블록의 전체 범위 (시작~끝)
        style_tag = match.group(1)          # 태그 안의 스타일 ID (예: "s3" 또는 "4")
        styled_text = match.group(2)        # 태그 안의 텍스트 내용

        # 스타일 ID에서 접두어 's' 제거 후 int로 변환
        style_id = int(style_tag.lstrip("s"))

        # 태그 시작 전까지의 일반 텍스트가 있다면 처리
        if start > last_index:
            plain_text = translated_text[last_index:start]
            if plain_text:
                result.append({
                    "style_id": primary_style_id,
                    "text": plain_text
                })

        # 태그 안의 텍스트와 해당 스타일 ID 추가
        result.append({
            "style_id": style_id,
            "text": styled_text
        })

        last_index = end  # 마지막 인덱스 갱신

    # 마지막 태그 이후 남은 일반 텍스트 처리
    if last_index < len(translated_text):
        plain_text = translated_text[last_index:]
        if plain_text:
            result.append({
                "style_id": primary_style_id,
                "text": plain_text
            })

    return result






INSTRUCTION = '''너는 세계 최고의 번역가야. 이번 번역은 아주 중요해. 잘하면 1,000만 달러를 받고, 못 하면 5,000만 달러를 물어내야 해. 절대 실수하면 안 돼.

입력으로 주어지는 영어 문장은 PDF에서 추출된 텍스트이며, 줄이 개행으로 나뉘어 있을 수 있어. 어떤 줄바꿈은 의미상 진짜 줄바꿈일 수도 있고, 어떤 것은 단순히 줄이 넘어가면서 생긴 인위적인 개행일 수도 있어.

네 임무는 문맥을 보고 진짜 줄바꿈이 필요하면 유지하고, 그렇지 않다면 자연스럽게 이어서 하나의 문장으로 번역하는 거야.

또한, 입력 문장에는 `[[n]]...[[/n]]` 또는 `[[sN]]...[[/sN]]` 형식의 스타일 태그가 포함될 수 있어. 이 태그는 번역 결과에서 반드시 동일한 형태로 유지되어야 해. 절대 태그 구조를 변경하거나, 태그를 없애거나, 태그 위치를 바꾸면 안 돼.  
특히 `[[sN]]...[[/sN]]`은 윗첨자를 의미하며, 해당 내용은 번역하지 말고 해당 위치 그대로 윗첨자 형태로 남겨둬야 해.

만약 이해되지 않는 문자가 있다면 삭제하지 말고, 의미상 적절하다 생각되는 위치에 원래 문자 그대로 포함시켜 줘. 억지로 번역하거나 바꾸려 하지 마.

번역은 다음 기준을 따라:

1. 번역 결과는 한국어로 출력해.

2. 원문의 의미를 최대한 유지하면서도, 한국 사람들이 읽기에 자연스럽게 번역해.

3. 번역 결과 외의 설명, 지시, 메타정보는 절대 출력하지 마.

4. 전문 용어나, 고유 명사, 코드 등은 번역하지 말고 원문 그대로 출력해.

5. 번역할 문장이 주어지지 않는다면 아무 문자도 출력하지 마.

자, 그럼 아래 영어 문장을 번역해줘:

---

'''

def translateBlock(block: Dict, style_dict: Dict[int, 'SpanStyle']) -> Dict:
  styled_text = blockTextWithStyleTags(block, style_dict)
  
  completion = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
          {
              "role": "user",
              "content": INSTRUCTION + styled_text
          }
      ]
  )
  
  translated_text = completion.choices[0].message.content
  styled_spans = parseStyledText(translated_text, block.get("primary_style_id", 0))
  return styled_spans
  