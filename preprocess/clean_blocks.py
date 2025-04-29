from text_extract.text_extract import lineText

def cleanBlocks(blocks):
    """
    blocks 내의 모든 block 안에 있는 line 중에서
    lineText(line).strip() == "" 인 line을 삭제하고,
    남은 line이 없는 block도 삭제하여
    알맹이 있는 blocks만 반환한다.
    """

    cleaned_blocks = []

    for block in blocks:
        # 빈 line 제거
        cleaned_lines = [line for line in block.get("lines", []) if lineText(line).strip() != ""]

        if cleaned_lines:
            # line이 하나라도 남아있으면 block 추가
            new_block = dict(block)
            new_block["lines"] = cleaned_lines
            cleaned_blocks.append(new_block)

    return cleaned_blocks
