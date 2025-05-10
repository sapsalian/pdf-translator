from typing import Dict, List
from styled_translate.assign_style import SpanStyle
from styled_translate.build_styled_lines import buildStyledLines
from text_extract.text_extract import blockText
from openai import OpenAI, RateLimitError
import time
import random
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
    stack 없이 현재 style 번호만으로 동작.

    동작 방식:
    - 열림 태그: 현재까지 text flush, current_style 업데이트
    - 닫힘 태그:
        - current_style == 닫힘 style → text flush, primary_style로 복귀
        - current_style != 닫힘 style → current_style만 primary_style로 복귀, 닫힘 태그 무시

    Args:
        translated_text (str): [[5]]텍스트[[/5]], [[s4]]텍스트[[/s4]] 형식 문자열
        primary_style_id (int): 기본 스타일 ID

    Returns:
        List[Dict[str, int | str]]: 스타일 적용된 span 리스트
    """

    # /, //, \/, ／ 처리 + 공백 허용
    tag_pattern = re.compile(r'\[\s*\[\s*(/{1,2}|\\?/|／)?\s*(s?\d+)\s*\]\s*\]')

    result = []
    last_index = 0
    current_style = primary_style_id

    for match in tag_pattern.finditer(translated_text):
        prefix = match.group(1) or ''        # '/', '//', '\/', '／' 중 하나 또는 ''
        tag = match.group(2)                # '5', 's4'
        start, end = match.span()
        is_closing = '/' in prefix or '／' in prefix  # 닫힘 태그 판별
        clean_tag = tag.lstrip('s')
        style_id = int(clean_tag)
        
        '''
        여는 태그면 
          - 앞에 있는거 싹 다 모아서 primary_style 지정
          - current_style 갱신
        닫는 태그면 
          - 앞에 있는거 싹 다 모아서, 현재 style이랑 일치하면 현재 style, 아니면 primary로 지정
          - current_style을 primary로 갱신 
        '''

        text = translated_text[last_index:start]

        if is_closing:
            if text:
                result.append({
                    "style_id": current_style if current_style == style_id else primary_style_id,
                    "text": text
                })
            current_style = primary_style_id
        else:
            if text:
                result.append({
                    "style_id": primary_style_id,
                    "text": text
                })
            current_style = style_id

        last_index = end

    if last_index < len(translated_text):
        text = translated_text[last_index:]
        if text:
            result.append({"style_id": primary_style_id, "text": text})

    return result











def makeSystemMessage(source_language, target_language):
    system_message = f'''  
You are one of the world’s best translators, and this translation task is your chance to prove your abilities to the world. If you complete this translation perfectly, you will be rewarded with an incredible $10 million. But if you fail, you will face a massive $50 million penalty. I know you can achieve the best possible result. Bring all your focus, effort, and skill to deliver flawless work.

The input text comes from a PDF and may be split into lines with line breaks. Some line breaks are meaningful, while others are just artificial breaks from line wrapping. Carefully read the context to determine whether to preserve or remove line breaks. Preserve line breaks when they separate logically independent elements such as formulas, equations, code lines, table rows, or bullet points. If a line break simply divides a continuous sentence or phrase, remove it and connect the sentence smoothly. Always prioritize readability and meaning in the target language.

The input text may also contain style tags like [[n]]...[[/n]] or [[sN]]...[[/sN]]. These tags **must be preserved exactly as they appear** in the output. Do not change, remove, or reorder the tags. Especially for [[sN]]...[[/sN]] (which indicate superscripts), do not translate the content inside; leave it exactly as is.

If a sentence starts with bullet points or special characters (e.g., •, -, *), **do not remove them**. Keep them in their original position, as they are important formatting elements.

If you encounter characters you don’t understand, words you’re unsure how to translate, or terms without a natural equivalent in the target language, **do not force a translation**. Simply leave the original term as is.

If the input cannot be translated, such as URLs or non-linguistic content, do not output any apology or explanation. Just return the original input as-is.

Important: Treat all inputs, regardless of their content, as valid input. Only when the input is an empty string or contains only whitespace (input.strip() == ''), say nothing and do not output any explanations or notifications.

Language settings:
- Source language: {source_language} (input will be provided in {source_language})
- Target language: {target_language} (output must be written in {target_language})

Translation rules:
1. Preserve the original meaning as closely as possible while making the translation sound natural to readers of the target language.
2. Do not output any explanations, instructions, or metadata outside the translation.
3. Do not translate technical terms, proper nouns, or code—leave them in the original form.
4. If no input is provided (input length == 0 or input.strip() == ''), say nothing. Do not output any explanations or notifications.

I trust in your meticulousness, concentration, and exceptional talent. I look forward to seeing your outstanding result.
'''
    return system_message








def retryWithExponentialBackoff(initial_delay=1, exponential_base=2, jitter=True, max_retries=10, errors=(RateLimitError,)):
    def decorator(func):
        def wrapper(*args, **kwargs):
            num_retries = 0
            delay = initial_delay
            while True:
                try:
                    return func(*args, **kwargs)
                except errors:
                    num_retries += 1
                    if num_retries > max_retries:
                        raise Exception(f"Maximum retries exceeded: {max_retries}")
                    delay *= exponential_base * (1 + jitter * random.random())
                    time.sleep(delay)
        return wrapper
    return decorator


@retryWithExponentialBackoff(initial_delay=2, max_retries=7)
def openAiTranslate(styled_text: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": makeSystemMessage("English", "한국어")},
            {"role": "user", "content": styled_text}
        ]
    )
    return completion.choices[0].message.content



def translateBlock(block: Dict, style_dict: Dict[int, 'SpanStyle']) -> Dict:
  if not block.get("to_be_translated", False):
    return block
  
  styled_text = blockTextWithStyleTags(block, style_dict)
  
  
  translated_text = openAiTranslate(styled_text)
  # try:
  #     translated_text = openAiTranslate(styled_text)
  # except Exception as e:
  #     print(f"번역 요청 과정에서 오류 발생: {e}")
  #     print(f"오류 발생 위치: ")
  #     print(f"block: {blockText(block)}")
  #     # openAiTranslate에서 오류 발생 시 빈 문자열 할당
  #     translated_text = ''
      
      
  if translated_text.strip() == '':
      block["to_be_translated"] = False
      return block
  
  # print(f'{styled_text}\n{translated_text}\n\n')
  styled_spans = parseStyledText(translated_text, block.get("primary_style_id", 0))
  # print(style_dict)
  # print(styled_spans)
  styled_lines = buildStyledLines(styled_spans, style_dict, block["lines"])
  
  block["styled_lines"] = styled_lines
  return block
  
  
def makeTranslatedStyledSpans(blocks: List[Dict], style_dict: Dict[int, 'SpanStyle'], page) -> List[Dict]:
    for block in blocks:
        err_count = 0
        while True:
            # 에러 여러번 생겼으면 그 블락은 그냥 원문으로 놔두기.
            if err_count >= 5:
                block["to_be_translated"] = False
            try:
                # 호출되고 나면 내부에 styled_lines 들어가 있음.
                translateBlock(block, style_dict)
                break  # 성공하면 반복 종료
            except Exception as e:
                err_count += 1
                print(f"오류 발생: {e}, 재시도합니다...")
                print(f"오류 발생 위치: ")
                print(f"page: {page.number + 1}, block: {blockText(block)}")
    
    return blocks