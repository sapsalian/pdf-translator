from styled_translate.assign_style import SpanStyle
from collections import Counter
from typing import List, Dict

def assignPrimaryStyleId(blocks: List[Dict], style_dict: Dict[int, 'SpanStyle']) -> List[Dict]:
    """
    각 block 내에서 superscript가 아닌 span 중 가장 많이 등장한(text 길이 기준) style_id를
    'primary_style_id'로 지정합니다.
    superscript만 있는 경우, superscript 중에서 가장 긴 스타일을 primary로 지정합니다.

    Args:
        blocks (list): span에 'style_id'가 포함된 block 리스트
        style_dict (dict): style_id -> SpanStyle 매핑

    Returns:
        list: 각 block에 'primary_style_id' 키가 추가된 blocks
    """
    for block in blocks:
        style_counter = Counter()
        superscript_counter = Counter()

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                style_id = span.get("style_id")
                if style_id is None:
                    continue

                style = style_dict.get(style_id)
                if not style:
                    continue

                text_len = len(span["text"])
                if style.is_superscript:
                    superscript_counter[style_id] += text_len
                else:
                    style_counter[style_id] += text_len

        if style_counter:
            primary_style_id = style_counter.most_common(1)[0][0]
        elif superscript_counter:
            primary_style_id = superscript_counter.most_common(1)[0][0]
        else:
            primary_style_id = None

        block["primary_style_id"] = primary_style_id

    return blocks
