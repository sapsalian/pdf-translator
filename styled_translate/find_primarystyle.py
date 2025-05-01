from collections import Counter
from typing import List, Dict
from styled_translate.assign_style import SpanStyle

def assignPrimaryStyleId(blocks: List[Dict], style_dict: Dict[int, 'SpanStyle']) -> List[Dict]:
    """
    각 block 내에서 superscript가 아닌 span 중 가장 많이 등장한 style_id를
    'primary_style_id'로 지정합니다.

    Args:
        blocks (list): span에 'style_id'가 포함된 block 리스트
        style_dict (dict): style_id -> SpanStyle 매핑

    Returns:
        list: 각 block에 'primary_style_id' 키가 추가된 blocks
    """
    for block in blocks:
        style_counter = Counter()

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                style_id = span.get("style_id")
                if style_id is None:
                    continue

                style = style_dict.get(style_id)
                if style and not style.is_superscript:
                    style_counter[style_id] += 1

        if style_counter:
            primary_style_id = style_counter.most_common(1)[0][0]
            block["primary_style_id"] = primary_style_id
        else:
            block["primary_style_id"] = None  # superscript 제외 시 후보가 없을 경우

    return blocks
