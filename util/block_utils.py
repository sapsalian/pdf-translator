# 정렬 상수 정의
from text_extract.text_extract import lineText

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

    all_lines_attached_to_sides = True  # 모든 줄이 양 끝에 붙어있는지 확인

    for line in lines:
        if lineText(line).strip() == '':
            continue  # 빈 라인은 무시
        
        line_x0, _, line_x1, _ = line["bbox"]
        line_center_x = (line_x0 + line_x1) / 2

        avg_char_width = get_average_char_width(line)
        tolerance = avg_char_width * 1  # 평균 문자 폭 기준

        # 중앙 정렬 여부 확인
        diff_center = abs(line_center_x - block_center_x)
        if diff_center > tolerance: # 중앙 정렬에서 벗어났으면 바로 좌측정렬 반환
            return ALIGN_LEFT

        # 양 끝 붙어있는지 확인
        diff_left = abs(line_x0 - block_x0)
        diff_right = abs(line_x1 - block_x1)
        if diff_left > avg_char_width * 1.5 or diff_right > avg_char_width * 2:
            all_lines_attached_to_sides = False        
  
    # for문에서 나왔으면 모든 라인이 블락 중간에 있었다는 것.
  
    if all_lines_attached_to_sides:
        if block.get("class_name", "Text") in ['Title', 'Picture'] and len(lines) == 1:
            return ALIGN_CENTER
        return ALIGN_LEFT

    # 붙어있는게 아니고 중앙 정렬 조건을 만족하면
    return ALIGN_CENTER
