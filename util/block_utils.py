# 정렬 상수 정의
ALIGN_CENTER = "center"
ALIGN_LEFT = "left"

def get_average_char_width(line):
    total_width = 0
    total_chars = 0

    for span in line.get("spans", []):
        text = span.get("text", "")
        width = span.get("bbox", [0, 0, 0, 0])[2] - span.get("bbox", [0, 0, 0, 0])[0]
        total_width += width
        total_chars += len(text)

    if total_chars == 0:
        return 0  # 빈 라인인 경우

    return total_width / total_chars

def getBlockAlignment(block):
    lines = block.get("lines", [])
    if not lines:
        return ALIGN_LEFT  # 빈 블락은 기본적으로 좌측 정렬로 간주

    block_x0, _, block_x1, _ = block["bbox"]
    block_center_x = (block_x0 + block_x1) / 2

    for line in lines:
        line_x0, _, line_x1, _ = line["bbox"]
        line_center_x = (line_x0 + line_x1) / 2

        avg_char_width = get_average_char_width(line)
        tolerance = avg_char_width * 0.5  # 평균 문자 폭의 0.5배 이내면 중앙정렬로 간주

        diff = abs(line_center_x - block_center_x)
        if diff > tolerance:
            return ALIGN_LEFT  # 하나라도 중앙에서 벗어나면 좌측 정렬

    return ALIGN_CENTER  # 모든 라인이 중앙 정렬

