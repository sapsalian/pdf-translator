from util.block_utils import *

def splitSpecialBlocks(blocks):
    """
    blocks를 순회하면서 block 내부 line들의 x축 gap과 y축 겹침을 기준으로 block을 분할하는 함수
    special block(class_name이 "Picture", "Formula", "Table" 중 하나)일 때만 적용함.

    조건:
    - 두 line 사이의 x축 gap이 두 line 너비 평균의 0.5배보다 크면 분할
    - 또는, xGap이 0 이상이고 y축 겹침률이 0이면 분할
    """

    def getLineBbox(line):
        # line의 bbox를 가져오는 함수
        return line.get("bbox", [0, 0, 0, 0])

    def getLineWidth(line):
        # line의 너비를 계산하는 함수
        bbox = getLineBbox(line)
        return bbox[2] - bbox[0]

    def xGap(line1, line2):
        # 두 line 간 x축 gap을 계산 (겹쳐 있으면 0)
        x0_1, x1_1 = getLineBbox(line1)[0], getLineBbox(line1)[2]
        x0_2, x1_2 = getLineBbox(line2)[0], getLineBbox(line2)[2]

        if x1_1 < x0_2:
            return x0_2 - x1_1
        elif x1_2 < x0_1:
            return x0_1 - x1_2
        else:
            return 0

    def yOverlapRatio(line1, line2):
        # 두 line 간 y축 방향 겹침 비율 계산
        y0_1, y1_1 = getLineBbox(line1)[1], getLineBbox(line1)[3]
        y0_2, y1_2 = getLineBbox(line2)[1], getLineBbox(line2)[3]

        overlap = max(0, min(y1_1, y1_2) - max(y0_1, y0_2))
        min_height = min(y1_1 - y0_1, y1_2 - y0_2)
        return overlap / min_height if min_height > 0 else 0

    new_blocks = []

    for block in blocks:
        lines = block.get("lines", [])
        if not lines:
            continue

        class_name = block.get("class_name", "Text")
        if class_name not in ("Picture", "Formula", "Table"):
            new_blocks.append(block)
            continue

        current_block_lines = [lines[0]]  # 새 블록에 추가할 lines 초기화

        for i in range(1, len(lines)):
            prev_line = lines[i-1]
            curr_line = lines[i]

            avg_width = (getLineWidth(prev_line) + getLineWidth(curr_line)) / 2
            gap = xGap(prev_line, curr_line)
            y_overlap = yOverlapRatio(prev_line, curr_line)

            # gap이 너비 평균 0.5배보다 크거나, gap > 0 이고 y축 겹침이 없으면 분리
            if gap > avg_width * 0.5 or (gap > 0 and y_overlap == 0):
                new_blocks.append({
                    "type": block.get("type", 0),
                    "align": block.get("align", ALIGN_LEFT),
                    "class_name": block.get("class_name", "Text"),
                    "bbox": calculateBbox(current_block_lines),
                    "lines": current_block_lines
                })
                current_block_lines = [curr_line]
                continue

            current_block_lines.append(curr_line)

        # 마지막 block 저장
        if current_block_lines:
            new_blocks.append({
                "type": block.get("type", 0),
                "align": block.get("align", ALIGN_LEFT),
                "class_name": block.get("class_name", "Text"),
                "bbox": calculateBbox(current_block_lines),
                "lines": current_block_lines
            })

    return new_blocks


def calculateBbox(lines):
    """
    주어진 lines 리스트의 전체를 포함하는 bounding box를 계산
    """
    if not lines:
        return [0, 0, 0, 0]

    x0 = min(line["bbox"][0] for line in lines)
    y0 = min(line["bbox"][1] for line in lines)
    x1 = max(line["bbox"][2] for line in lines)
    y1 = max(line["bbox"][3] for line in lines)

    return [x0, y0, x1, y1]