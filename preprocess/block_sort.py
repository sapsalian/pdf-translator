def sortLinesInBlocks(blocks):
    """
    각 block 안의 line들을 y 좌표(origin 기준) 기준으로 정렬합니다.
    
    Parameters:
        blocks (list): pymupdf에서 추출한 blocks 리스트
    
    Returns:
        list: 정렬된 block 리스트 (각 block의 lines는 y 기준 정렬됨)
    """
    for block in blocks:
        if "lines" in block:
            block["lines"].sort(key=lambda line: line["bbox"][1])
    return blocks