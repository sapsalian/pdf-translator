from typing import Dict, List
from styled_translate.assign_style import SpanStyle
from styled_translate.build_styled_lines import buildStyledLines
from text_extract.text_extract import blockText
from openai import OpenAI, RateLimitError
from pydantic import BaseModel
from pydantic import TypeAdapter
import time
import random
import re
import json
import traceback
# from anthropic import Anthropic
from util.block_utils import ALIGN_CENTER, ALIGN_LEFT
from styled_translate.assign_fontfamily import assignFontFamilyToStyledSpans
from preprocess.make_result_line_frames import assignLineFramesToBlock
from styled_translate.assign_style import getFontScale

client = OpenAI()
# anthropic_client = Anthropic()

def blockTextWithStyleTags(block: Dict, style_dict: Dict[int, 'SpanStyle']) -> str:
    """
    텍스트 블록 내 span들을 순회하면서 스타일 정보를 포함한 문자열을 생성합니다.

    처리 로직:
    1. 기본 스타일(span["style_id"] == primary_style_id) → 태그 없이 텍스트 출력
    2. 다른 스타일 → {{style_id}}...{{/style_id}} 형식의 태그로 감쌈
       - 만약 superscript 스타일이면 s 접두어: {{s5}}...{{/s5}}
    3. 두 span 사이 x 간격이 평균 글자 너비의 0.9배 이상이면 공백(" ") 추가
    4. 줄(line)이 바뀔 때마다 개행 문자('\n') 삽입
    5. 단, class_name이 'List-item'이면 줄 개행 대신 공백으로 이어붙임

    Args:
        block (Dict): PyMuPDF에서 추출한 하나의 텍스트 블록 (type == 0)
        style_dict (Dict[int, SpanStyle]): style_id를 키로 하는 스타일 객체 매핑

    Returns:
        str: 스타일 태그 및 공백이 포함된 출력 문자열
    """

    # 기준이 되는 기본 스타일 ID
    primary_id = block.get("primary_style_id")
    output = []  # 줄(line) 단위로 누적할 출력 결과 리스트

    for line in block.get("lines", []):
        line_text = ""   # 현재 줄의 텍스트 누적 버퍼
        prev_span = None # 이전 span의 정보를 저장

        for span in line.get("spans", []):
            span_text = span.get("text", "")
            style_id = span.get("style_id")

            # 이전 span과의 x축 간격(gap)을 기준으로 공백 삽입 판단
            if prev_span is not None:
                prev_end = prev_span["bbox"][2]     # 이전 span의 x 끝 좌표
                curr_start = span["bbox"][0]        # 현재 span의 x 시작 좌표
                gap = curr_start - prev_end         # 두 span 간의 간격

                # 평균 글자 너비 계산 (divide-by-zero 방지)
                prev_width = prev_span["bbox"][2] - prev_span["bbox"][0]
                curr_width = span["bbox"][2] - span["bbox"][0]
                prev_char_width = prev_width / max(len(prev_span["text"]), 1)
                curr_char_width = curr_width / max(len(span_text), 1)
                avg_char_width = (prev_char_width + curr_char_width) / 2

                # 간격이 평균 글자 너비의 0.9배 이상이면 공백 삽입
                if gap >= avg_char_width * 0.9:
                    line_text += " "

            # 스타일 태그 삽입
            if style_id == primary_id:
                # 기본 스타일이면 태그 없이 원문 삽입
                line_text += span_text
            else:
                # 비기본 스타일은 {{style_id}}...{{/style_id}}로 감쌈
                style = style_dict.get(style_id)
                tag_prefix = f"s{style_id}" if style and style.is_superscript else f"{style_id}"
                # f-string 중괄호 이스케이프 위해 {{{{ }}}} 사용
                line_text += f"{{{{{tag_prefix}}}}}{span_text}{{{{/{tag_prefix}}}}}"

            # 현재 span을 다음 비교를 위해 저장
            prev_span = span

        # 줄 단위로 저장 (줄 개행은 이후 처리)
        output.append(line_text)

    # 'List-item'이면 줄 단위 출력이 아니라 한 줄로 이어 붙임
    if block.get("align", ALIGN_LEFT) == ALIGN_CENTER or block.get("class_name", "Text") == 'Picture' or block.get("class_name", "Text") == 'Table' or block.get("class_name", "Text") == 'Formula':
        return "\n".join(output)
    else:
        return " ".join(output)



import re
from typing import List, Dict

def parseStyledText(translated_text: str, primary_style_id: int, style_dict: Dict) -> List[Dict[str, int | str]]:
    """
    {{n}}, {{/n}}, {{s5}} 같은 스타일 태그가 포함된 문자열을 파싱하여
    style_id와 텍스트를 묶은 span 리스트로 반환합니다.

    ✔ 스택 없이 현재 스타일 ID만을 추적해 파싱 처리
    ✔ 기본 스타일(primary_style_id)은 태그 없이 적용
    ✔ superscript 태그는 's' 접두어가 붙음 (예: {{s5}})

    처리 방식:
    - 열림 태그: 직전 텍스트 flush → current_style을 해당 태그로 변경
    - 닫힘 태그:
        - current_style == 닫는 태그 ID면 → flush + primary로 복귀
        - current_style != 닫는 태그 ID면 → flush만 하고 current_style 강제 복귀

    Args:
        translated_text (str): 예: {{5}}텍스트{{/5}}, {{s4}}텍스트{{/s4}} 형식 문자열
        primary_style_id (int): 기본 스타일 ID
        style_dict (dict): style_id → SpanStyle 매핑

    Returns:
        List[Dict[str, int | str]]: 스타일 적용된 span 리스트
    """

    # 태그 탐지용 정규표현식 (열림/닫힘 모두 인식)
    # 예: {{5}}, {{/5}}, {{s4}}, {{／s4}}, {{\s4}} 등
    tag_pattern = re.compile(r'\{\s*\{\s*(/{1,2}|\\?/|／)?\s*(s?\d+)\s*\}\s*\}')

    result = []
    last_index = 0
    current_style = primary_style_id

    for match in tag_pattern.finditer(translated_text):
        prefix = match.group(1) or ''         # 닫힘 여부 판단용 접두어: '/', '//', '\/', '／' 등
        tag = match.group(2)                  # '5', 's4'
        start, end = match.span()
        is_closing = '/' in prefix or '／' in prefix  # 닫힘 태그 여부 판단
        clean_tag = tag.lstrip('s')           # 's4' → '4'
        style_id = int(clean_tag)

        # 태그 앞 텍스트 추출
        text = translated_text[last_index:start]

        if is_closing:
            # 닫힘 태그인 경우
            if text:
                result.append({
                    "style_id": current_style if current_style == style_id and style_id in style_dict else primary_style_id,
                    "text": text
                })
            current_style = primary_style_id  # 닫힘 시 항상 기본 스타일로 복귀
        else:
            # 열림 태그인 경우
            if text:
                result.append({
                    "style_id": primary_style_id,
                    "text": text
                })
            current_style = style_id  # 새 스타일로 갱신

        last_index = end

    # 마지막 태그 뒤 남은 텍스트 처리
    if last_index < len(translated_text):
        text = translated_text[last_index:]
        if text:
            result.append({
                "style_id": primary_style_id,
                "text": text
            })

    return result



# Pydantic 모델 정의
class TranslationItem(BaseModel):
    block_num: int
    translated_text: str

adapter = TypeAdapter(List[TranslationItem])

def makeSystemMessage(src_lang, tgt_lang):
    return f"""
📝 **Role**: Professional translator (strict glossary, JSON output)

▶ Source → Target: {src_lang} → {tgt_lang}

###############################
1️⃣ Input / Output Schema
###############################
Input JSON:
{{"summary": "...", "term_dict": {{}}, "blocks": [{{"block_num": 1, "text": "..."}} ... ]}}

Output JSON (must match exactly):
{{"translations": [{{"block_num": 1, "translated_text": "..."}} ... ]}}

- Keep order and length identical to `blocks`.
- If `text` is empty → `"translated_text": ""`.
- **If the `text` is already in {tgt_lang}, return an empty `"translated_text": ""`.**

###############################
2️⃣ Glossary & Entities
###############################
✔ Use **term_dict** as absolute authority.
✔ Preserve model / product / org names (GPT-4, BERT, ChatGPT, API…).
✔ Preserve original casing.
✔ **Do NOT translate proper nouns** (e.g., person names, organization names, locations, product names).
  - Examples: "John Smith", "OpenAI", "New York", "Photoshop"
  - If uncertain, err on the side of preserving the original.
✔ If a proper noun overlaps with `term_dict`, follow `term_dict`.

Priority: term_dict > Named-entity (proper noun) > general translation.

###############################
3️⃣ Tag & Formatting Rules
###############################
Tag set: {{{{N}}}} {{{{/N}}}}, {{{{sN}}}} {{{{/sN}}}}
- Copy tags exactly as they appear (verbatim), and maintain their structure.
- Do **not** translate inside {{{{sN}}}}…{{{{/sN}}}}.
- No new tags, no tag deletion.

↩ Intelligent line-break handling
- The input consists of English text extracted from a PDF.
- Sentences may be split across lines due to line breaks.
- Some line breaks are meaningful (e.g., between formulas, bullet points, or separate thoughts).
- Others are artificial (caused by line wrapping).
- Carefully examine the context and judge whether each break is meaningful.
- Preserve only meaningful line breaks.
- If two lines read smoothly as a single sentence, remove the break and join them naturally.
- Never introduce new line breaks that were not in the input.
- Your goal is to produce a fluent translation that respects the original structure.


###############################
4️⃣ Block Matching Integrity
###############################
- Each `translated_text` **must** correspond exactly to the `text` of the same `block_num`.
- Do not reorder, merge, split, or omit any blocks.
- Keep `block_num` unchanged and ensure it appears once and only once in the output.
- Ensure `translated_text` preserves the meaning, structure, and boundaries of its source `text` block.

###############################
5️⃣ Quality Checklist before respond
###############################
- Valid JSON? ✅
- Block counts match? ✅
- Glossary terms matched? ✅
- Tags unchanged? ✅

"""



def makeAnthropicSystemMessage(source_language, target_language):
    system_message = f'''  
You are one of the world's best translators, and this translation task is your chance to prove your abilities to the world. If you complete this task flawlessly, you will be rewarded with a $100,000 prize.

The input will be provided as a JSON object with the following structure:
{{
  "summary": "A brief summary of the page to provide overall context.",
  "term_dict": {{
    "source_term_1": "target_term_1",
    "source_term_2": "target_term_2"
  }},
  "blocks": [
    {{"block_num": 1, "text": "first block text"}},
    {{"block_num": 2, "text": "second block text"}}
  ]
}}

🚨 CRITICAL: You MUST return ONLY a valid JSON object with NO additional text, explanations, or formatting. Your entire response must be parseable JSON.

Your output must follow this EXACT structure:
{{
  "translations": [
    {{"block_num": 1, "translated_text": "translated result for first block"}},
    {{"block_num": 2, "translated_text": "translated result for second block"}}
  ]
}}

🔒 JSON FORMAT REQUIREMENTS:
- Start your response immediately with {{ (opening brace)
- End your response with }} (closing brace)  
- Use double quotes (") for all strings, never single quotes (')
- Escape special characters properly: \" for quotes, \\ for backslashes, \\n for newlines
- Do NOT add any text before or after the JSON object
- Do NOT wrap the JSON in markdown code blocks (no ```json```)
- Do NOT include explanatory text or comments
- Ensure all brackets and braces are properly matched
- Include commas between array elements and object properties
- Do NOT add trailing commas after the last element

📝 TEXT ESCAPING RULES:
- If translated text contains double quotes, escape them as \"
- If translated text contains backslashes, escape them as \\
- If translated text contains newlines, escape them as \\n
- If translated text contains tabs, escape them as \\t

🔍 Summary usage:
- Use the "summary" field to understand the general topic and tone.
- It provides context to improve translation accuracy, but must not appear in your output.

📘 Term dictionary usage:
- Use the "term_dict" field as a **strict glossary**.
- If a source term appears in this dictionary, you **must translate it exactly as specified**.
- Do not attempt to paraphrase or replace glossary terms with synonyms.
- If a glossary term appears inside tags, preserve the tag and apply the glossary within the tag boundaries.

📛 Named entities:
- Do NOT translate named entities such as model names (e.g., GPT-4, BERT), organization names (e.g., OpenAI, Google), product names (e.g., ChatGPT), or acronyms (e.g., API, LLM).
- Keep such terms exactly as they appear in the source text.
- ⚠️ Preserve the **original casing** (uppercase/lowercase) of these terms exactly. For example, do not change "ChatGPT" to "chatgpt".
- This applies even if they are not listed in the term_dict.

🎯 Important translation rules:
1. Do NOT change or reorder the JSON structure.
2. Only translate the "text" field in each block.
3. Keep the "block_num" unchanged and match it exactly from input.
4. If the "text" is empty or whitespace, return an empty string in "translated_text".
5. Leave URLs, code snippets, technical terms, or unknown words as-is unless defined in the term_dict.
6. The number of translation objects in the output array must match exactly the number of blocks in the input.

🏷 Style tag handling:
Some input blocks may contain tags such as [[N]]...[[/N]] or [[sN]]...[[/sN]] (N is Positive Integer):
- You must preserve these tags **exactly as they appear**.
- Do not modify, remove, add, or reorder any tags.
- For [[sN]]...[[/sN]] superscript tags, **do not translate the content inside** the tag. Leave the enclosed text exactly as it is.

↩ Line break handling:
The input text may include line breaks caused by PDF extraction. Use your judgment:
- Preserve line breaks only if they reflect actual structural or semantic boundaries (e.g., between formulas or bullet points).
- If a line break simply splits a sentence or phrase that logically continues, remove the break and connect the lines smoothly.
- Do NOT insert any line breaks that were not originally present.

⚠️ VALIDATION CHECKLIST:
Before submitting your response, verify:
- [ ] Response starts with {{ and ends with }}
- [ ] All strings use double quotes
- [ ] All special characters are properly escaped
- [ ] Block numbers match input exactly
- [ ] Number of translation objects equals number of input blocks
- [ ] No extra text outside the JSON structure
- [ ] JSON is syntactically valid

🎯 Goal: Produce fluent, natural, and faithful translations in the target language, while strictly adhering to the term dictionary, preserving structural tags, and maintaining perfect JSON format.

Language:
- Source: {source_language}
- Target: {target_language}

Remember: Your response must be ONLY valid JSON. Any deviation from this format will result in processing failure.
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
def openAiTranslate(payload: Dict, src_lang, target_lang) -> List[TranslationItem]:
    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        # temperature=0.0,
        messages=[
            {"role": "system", "content": makeSystemMessage(src_lang, target_lang)},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "translation_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "translations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "block_num": {"type": "integer"},
                                    "translated_text": {"type": "string"}
                                },
                                "required": ["block_num", "translated_text"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["translations"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    )
    # JSON 파싱
    json_response = json.loads(completion.choices[0].message.content)
    return adapter.validate_python(json_response["translations"])


def validate_translation_schema(data: Dict) -> bool:
    """번역 응답 스키마 검증"""
    try:
        # translations 키가 있는지 확인
        if "translations" not in data:
            return False
        
        translations = data["translations"]
        
        # translations가 배열인지 확인
        if not isinstance(translations, list):
            return False
        
        # 각 translation 항목 검증
        for item in translations:
            if not isinstance(item, dict):
                return False
            
            # 필수 키 확인
            if "block_num" not in item or "translated_text" not in item:
                return False
            
            # 타입 확인
            if not isinstance(item["block_num"], int):
                return False
            
            if not isinstance(item["translated_text"], str):
                return False
            
            # 추가 프로퍼티 확인 (block_num, translated_text 외의 키가 있으면 안됨)
            if len(item.keys()) != 2:
                return False
        
        # 최상위 레벨에서 translations 외의 키가 있으면 안됨
        if len(data.keys()) != 1:
            return False
            
        return True
    except:
        return False

@retryWithExponentialBackoff(initial_delay=2, max_retries=7)
# def anthropicTranslate(payload: Dict) -> List[TranslationItem]:
#     message = anthropic_client.messages.create(
#         model="claude-3-5-haiku-latest",
#         max_tokens=8192,
#         system=[
#             {
#                 "type": "text",
#                 "text": makeAnthropicSystemMessage("English", "한국어"),
#                 "cache_control": {"type": "ephemeral"}
#             }
#         ],
#         messages=[
#             {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
#         ]
#     )
    
#     # JSON 파싱
#     json_response = json.loads(message.content[0].text)
    
#     # 스키마 검증
#     if not validate_translation_schema(json_response):
#         raise ValueError("응답이 예상된 스키마와 일치하지 않습니다")
    
#     return adapter.validate_python(json_response["translations"])

def removeLineBreaksFromStyledSpans(styled_spans: List[Dict]) -> List[Dict]:
    """
    styled_spans 배열에서 각 요소의 text에서 개행문자(\n)를 제거한 새 배열을 반환합니다.
    각 항목은 {"style_id": int, "text": str} 형식입니다.
    """
    return [
        {"style_id": span["style_id"], "text": span["text"].replace("\n", " "), 'font_family': span["font_family"]}
        for span in styled_spans
    ]


def makeTranslatedStyledSpans(blocks: List[Dict], style_dict: Dict[int, 'SpanStyle'], summary, page_num, term_dict, src_lang, target_lang) -> List[Dict]:
    def group_blocks_for_translation(target_blocks, max_length=3500):
        grouped, group, current_len = [], [], 0
        for idx, block in target_blocks:
            styled_text = blockTextWithStyleTags(block, style_dict)
            if current_len + len(styled_text) > max_length and group:
                grouped.append(group)
                group, current_len = [], 0
            group.append((idx, block, styled_text))
            current_len += len(styled_text)
        if group:
            grouped.append(group)
        return grouped

    def process_group(group):
        payload = {
            'term_dict': term_dict,
            'summary': summary,
            'blocks': [{"block_num": idx, "text": styled_text} for idx, _, styled_text in group]
        }
        translated_items = openAiTranslate(payload, src_lang, target_lang)
        return {item.block_num: item.translated_text for item in translated_items}

    print(f"\n📄 [Page {page_num}] 번역할 블록 스타일링 및 그룹핑 시작")
    initial_targets = [(idx, block) for idx, block in enumerate(blocks) if block.get("to_be_translated", False)]
    retry_blocks = initial_targets
    failed_blocks = []

    for round_num in range(1, 4):
        print(f"\n🔄 [Page {page_num}] 라운드 {round_num} 번역 시도")
        grouped_blocks = group_blocks_for_translation(retry_blocks)
        failed_blocks = []
        new_retry_blocks = []

        for group_num, group in enumerate(grouped_blocks, 1):
            print(f"🛰️ [Page {page_num}] Group {group_num}: 번역 요청")
            try:
                translated_map = process_group(group)
                
                # 🔧 1. 응답에 포함된 block_num들과 요청한 block_num들 비교
                translated_block_nums = set(translated_map.keys())
                group_block_nums = {idx for idx, _, _ in group}
                missing_block_nums = group_block_nums - translated_block_nums
                for idx, block, _ in group:
                    # 🔧 2. 응답에 빠진 블록은 retry 대상에 추가
                    if idx in missing_block_nums:
                        print(f"⚠️ [Page {page_num}] Block {idx}: 응답 누락 → 재시도 대상으로 등록")
                        new_retry_blocks.append((idx, block))
                        continue
                    
                    translated_text = translated_map.get(idx, '')
                    if not translated_text.strip():
                        block["to_be_translated"] = False
                        continue
                    try:
                        styled_spans = parseStyledText(translated_text, block.get("primary_style_id", 0), style_dict=style_dict)
                        styled_spans = assignFontFamilyToStyledSpans(styled_spans, target_lang)
                        # for span in styled_spans:
                        #     print(span["text"], span["style_id"])
                        assignLineFramesToBlock(block, src_lang, target_lang, font_scale=getFontScale(src_lang, target_lang))
                        styled_lines = buildStyledLines(styled_spans, style_dict, block)
                        block["styled_lines"] = styled_lines
                        block["to_be_translated"] = True
                        block["scale"] = 1.0
                        print(f"✅ [Page {page_num}] Block {idx} 처리 완료")
                    except Exception as styling_error:
                        print(f"❌ [Page {page_num}] Block {idx} 스타일 실패: {styling_error}")
                        failed_blocks.append((idx, block, translated_text))
                        # new_retry_blocks.append((idx, block)) # 스타일 실패한 블락은 번역 요청 재시도 하지 않기.
            except Exception as e:
                print(f"❗ [Page {page_num}] Group {group_num} 번역 실패: {e}")
                failed_blocks.extend([(idx, block, translated_text) for idx, block, translated_text in group])

        retry_blocks = new_retry_blocks
        failed_blocks = failed_blocks

        if not retry_blocks:
            break

    if failed_blocks:
        print(f"\n🛠️ [Page {page_num }] Scale 줄여가며 삽입 재시도")
    failed_blocks2 = []
    for idx, block, translated_text in failed_blocks:
        try:
            styled_spans = parseStyledText(translated_text, block.get("primary_style_id", 0), style_dict=style_dict)
            styled_spans = assignFontFamilyToStyledSpans(styled_spans, target_lang)
            # for span in styled_spans:
            #     print(span["text"], span["style_id"])
            
            scale = 1.0
            while True:
                try:
                    assignLineFramesToBlock(block, src_lang, target_lang, font_scale=getFontScale(src_lang, target_lang) * scale)
                    styled_lines = buildStyledLines(styled_spans, style_dict, block, scale=scale)
                    break
                except Exception as e:
                    if scale < 0.45:
                        raise Exception("scale 줄여 삽입시도 실패")
                    scale = scale * 0.99
            
            block["styled_lines"] = styled_lines
            block["to_be_translated"] = True
            block["scale"] = scale
            print(f"✅ [Page {page_num}] Block {idx}: scale 줄여 삽입시도 성공")
        except Exception as e:
            failed_blocks2.append((idx, block, translated_text))
            print(f"❌ [Page {page_num}] Block {idx}: scale 줄여 삽입시도 실패")
            traceback.print_exc()
    
    if failed_blocks2:
        print(f"\n🛠️ [Page {page_num}] 개행 제거 후 scale 줄여가며 최종 스타일 재시도")
    for idx, block, translated_text in failed_blocks2:
        try:
            styled_spans = parseStyledText(translated_text, block.get("primary_style_id", 0), style_dict=style_dict)
            styled_spans = assignFontFamilyToStyledSpans(styled_spans, target_lang)
            # for span in styled_spans:
            #     print(span["text"], span["style_id"])
            styled_spans = removeLineBreaksFromStyledSpans(styled_spans)
            
            scale = 1.0
            while True:
                try:
                    assignLineFramesToBlock(block, src_lang, target_lang, font_scale=getFontScale(src_lang, target_lang) * scale)
                    styled_lines = buildStyledLines(styled_spans, style_dict, block, scale=scale)
                    break
                except Exception as e:
                    if scale < 0.4:
                        raise Exception("scale 줄여 삽입시도 실패")
                    scale = scale * 0.99
            
            block["styled_lines"] = styled_lines
            block["to_be_translated"] = True
            block["scale"] = scale
            print(f"✅ [Page {page_num}] Block {idx}: 최종 개행 제거 성공")
        except Exception as e:
            print(f"❌ [Page {page_num}] Block {idx}: 개행 제거 후 재시도 실패: {e}")
            block["to_be_translated"] = False
            traceback.print_exc()

    return blocks



