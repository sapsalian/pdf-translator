from typing import List, Dict
from styled_translate.get_font_family import getFontFamily

def assignFontFamilyToStyledSpans(styled_spans: List[Dict], target_language: str) -> List[Dict]:
    """
    각 styled_span["text"]를 문자 단위로 분해하고,
    각 문자에 대해 getFontFamily로 폰트 패밀리를 확인한 후,
    같은 폰트 그룹으로 묶고, 폰트가 달라지면 새로운 styled_span을 생성합니다.

    Returns:
        List[Dict]: font_family가 명시된 styled_span 리스트
    """
    new_styled_spans = []

    for span in styled_spans:
        text = span.get("text", "")
        style_id = span.get("style_id")

        if not text:
            continue

        # 첫 글자 기반 초기화
        try:
            current_font_family = getFontFamily(text[0], target_language)
            current_text = text[0]
        except:
            current_font_family = 'NotoSans'
            current_text = ' '
        

        for char in text[1:]:
            try:
                font_family = getFontFamily(char, target_language)
            except Exception as e:
                print(e)
                font_family = current_font_family
                char = " "
                
            if font_family == current_font_family:
                current_text += char
            else:
                # font가 바뀌면 새 styled_span 추가
                new_styled_spans.append({
                    "style_id": style_id,
                    "text": current_text,
                    "font_family": current_font_family
                })
                current_font_family = font_family
                current_text = char

        # 마지막 누적 텍스트 저장
        new_styled_spans.append({
            "style_id": style_id,
            "text": current_text,
            "font_family": current_font_family
        })

    return new_styled_spans