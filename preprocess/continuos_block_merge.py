import pymupdf
import math
from util.line_utils import isLinesStartWithSameX

def hasSameDirection(lineA, lineB, tolerance=0.2):
        """
        두 라인의 dir 속성을 비교해 방향이 유사한지 확인.
        tolerance는 라디안 각도 기준 허용 오차.
        """
        if "dir" not in lineA or "dir" not in lineB:
            return False  # 방향 정보가 없으면 비교 불가

        dirA = lineA["dir"]
        dirB = lineB["dir"]

        # 내적 → 코사인 유사도
        dot = dirA[0] * dirB[0] + dirA[1] * dirB[1]
        dot = max(min(dot, 1), -1)  # 소수점 오류 방지

        angle = math.acos(dot)
        return angle < tolerance
      
def mergeBlocksByLineOverlap(blocks):
    """
    라인의 x 간격, y 겹침, 방향 유사성을 기반으로 block들을 병합한다.
    병합된 block은 line들의 bbox 넓이 합산 기준으로 가장 넓은 class_name을 갖는다.
    """
    if not blocks:
        return []

    # block의 마지막 line을 가져오는 함수
    def getLastLine(block):
        return block["lines"][-1] if block.get("lines") else None

    # block의 첫 번째 line을 가져오는 함수
    def getFirstLine(block):
        return block["lines"][0] if block.get("lines") else None

    # line의 bbox를 기준으로 넓이(area)를 계산하는 함수
    def get_block_area(block):
        x0, y0, x1, y1 = block["bbox"]
        return max(0, x1 - x0) * max(0, y1 - y0)

    # 여러 block을 병합할 때 가장 넓은 class_name을 결정하는 함수
    def decide_class_name(blocks_to_merge):
        """
        병합할 블록들의 line을 순회하면서:
        - class_name별로 bbox 넓이(area)를 합산하고
        - 가장 넓은 class_name을 최종 class_name으로 선택한다.
        """
        area_by_class = {}

        for block in blocks_to_merge:
            class_name = block.get("class_name", "Text")
            area = get_block_area(block)
            area_by_class[class_name] = area_by_class.get(class_name, 0) + area

        if area_by_class:
            return max(area_by_class.items(), key=lambda x: x[1])[0]
        else:
            return "Text"

    merged_blocks = []
    used_indices = set()  # 이미 병합에 사용된 블록의 인덱스를 저장

    i = 0
    while i < len(blocks):
        if i in used_indices:
            i += 1
            continue

        group = [blocks[i]]  # 병합할 블록 그룹을 초기화
        used_indices.add(i)

        current_block = blocks[i]

        # 이후 블록들과 병합 조건을 비교
        for j in range(i + 1, len(blocks)):
            if j in used_indices:
                continue

            next_block = blocks[j]
            last_line = getLastLine(current_block)
            next_first_line = getFirstLine(next_block)

            if not last_line or not next_first_line:
                continue

            # span 정보: font size 기준으로 허용 x 간격 설정
            last_span = last_line["spans"][-1]
            first_span = next_first_line["spans"][0]

            # 조건 1: x 간격이 적절한지 확인
            x_gap = next_first_line["bbox"][0] - last_line["bbox"][2]
            font_size_max = max(last_span["size"], first_span["size"])
            x_gap_close = -font_size_max * 2.5 <= x_gap <= font_size_max * 2.5

            # 조건 2: y축으로 충분히 겹치는지 확인
            y0_a, y3_a = last_line["bbox"][1], last_line["bbox"][3]
            y0_b, y3_b = next_first_line["bbox"][1], next_first_line["bbox"][3]
            y_overlap = max(0, min(y3_a, y3_b) - max(y0_a, y0_b))
            min_height = min(y3_a - y0_a, y3_b - y0_b)
            y_overlap_enough = y_overlap >= min_height * 0.5

            # 조건 3: line의 진행 방향이 일치하는지 확인
            line_aligned = hasSameDirection(last_line, next_first_line)

            # 모든 조건을 만족하면 group에 추가
            if x_gap_close and y_overlap_enough and line_aligned:
                group.append(next_block)
                used_indices.add(j)
                current_block = next_block  # 병합 기준을 업데이트

        # group을 병합하여 하나의 block으로 생성
        merged_lines = []
        merged_bbox = [float('inf'), float('inf'), float('-inf'), float('-inf')]

        for block in group:
            merged_lines.extend(block["lines"])
            merged_bbox[0] = min(merged_bbox[0], block["bbox"][0])
            merged_bbox[1] = min(merged_bbox[1], block["bbox"][1])
            merged_bbox[2] = max(merged_bbox[2], block["bbox"][2])
            merged_bbox[3] = max(merged_bbox[3], block["bbox"][3])

        merged_block = {
            "lines": merged_lines,
            "bbox": merged_bbox,
            "type": group[0].get("type", 0),  # 첫 block의 type을 그대로 사용
            "class_name": decide_class_name(group)  # 병합된 block의 class_name 결정
        }

        merged_blocks.append(merged_block)
        i += 1

    return merged_blocks

  
  
def mergeBlocksByYGap(blocks, src_lang, target_lang):
    """
    y 간격이 좁고 x축 너비 기준으로 50% 이상 겹치는 블락들을 병합한 새로운 블락 리스트 반환.
    병합된 block의 class_name은 가장 넓이를 많이 차지한 class_name으로 결정한다.
    """

    # block의 최상단 y좌표를 가져오는 함수
    def get_block_top_y(block):
        for line in block.get("lines", []):
            return line["bbox"][1]
        return float("inf")

    # block의 너비를 계산하는 함수
    def get_block_width(block):
        x0, _, x1, _ = block["bbox"]
        return x1 - x0

    # 두 block의 x축(수평) 방향 겹침 비율을 계산하는 함수
    def get_x_overlap_ratio(block1, block2):
        x0_1, _, x1_1, _ = block1["bbox"]
        x0_2, _, x1_2, _ = block2["bbox"]
        overlap = max(0, min(x1_1, x1_2) - max(x0_1, x0_2))
        min_width = min(get_block_width(block1), get_block_width(block2))
        return overlap / min_width if min_width > 0 else 0

    # 두 block 사이의 수직 간격과 최소 높이를 계산하는 함수
    def get_vertical_gap_and_min_height(block1, block2):
        line1 = block1["lines"][-1]  # block1의 마지막 line
        line2 = block2["lines"][0]   # block2의 첫번째 line

        y1_bottom = line1["bbox"][3]
        y2_top = line2["bbox"][1]

        h1 = line1["bbox"][3] - line1["bbox"][1]
        h2 = line2["bbox"][3] - line2["bbox"][1]
        min_height = min(h1, h2)

        return y2_top - y1_bottom, min_height

    # 두 block을 병합할 수 있는지 판단하는 함수
    def can_merge(prev, curr, src_lang, target_lang):
        vertical_gap, min_height = get_vertical_gap_and_min_height(prev, curr)

        if src_lang == "English" and vertical_gap > 0.5 * min_height:
            return False # y 간격이 크면 더 이상 병합 불가
        if src_lang == "한국어" and vertical_gap > 0.8 * min_height:
            return False

        if get_x_overlap_ratio(prev, curr) < 0.5:  # x축 겹침이 50% 미만이면 병합 불가
            return False

        if not hasSameDirection(prev["lines"][-1], curr["lines"][0]):  # 방향(읽기 흐름)이 다르면 병합 불가
            return False

        return True

    # 한 line의 bbox 넓이를 계산하는 함수
    def get_block_area(block):
        x0, y0, x1, y1 = block["bbox"]
        return max(0, x1 - x0) * max(0, y1 - y0)

    # 여러 block을 병합할 때 class_name을 결정하는 함수
    def decide_class_name(blocks_to_merge):
        """
        병합할 블럭들에 대해:
        - 각 line의 class_name별 bbox 넓이(area)를 합산하고
        - 가장 넓은 class_name을 최종 선택한다.
        """
        area_by_class = {}

        for block in blocks_to_merge:
            class_name = block.get("class_name", "Text")  # 없는 경우 기본값 Text
            area = get_block_area(block)
            area_by_class[class_name] = area_by_class.get(class_name, 0) + area

        if area_by_class:
            # 총 넓이가 가장 큰 class_name 반환
            return max(area_by_class.items(), key=lambda x: x[1])[0]
        else:
            return "Text"

    # 병합을 위해 blocks를 y좌표 → x좌표 순서로 정렬하는 함수
    def group_blocks_by_y_then_x(blocks):
        return sorted(blocks, key=lambda b: (get_block_top_y(b), b["bbox"][0]))

    # 1. block 정렬
    blocks = group_blocks_by_y_then_x(blocks)
    used = [False] * len(blocks)  # 병합에 사용된 블록 표시
    merged_blocks = []

    # 2. block들을 순서대로 병합
    for i, base in enumerate(blocks):
        if used[i]:
            continue

        group = [base]  # base block과 병합할 그룹 초기화
        used[i] = True

        # base 다음 block들과 비교
        for j in range(i + 1, len(blocks)):
            if used[j]:
                continue

            vertical_gap, min_height = get_vertical_gap_and_min_height(group[-1], blocks[j])
            if src_lang == "English" and vertical_gap > 0.5 * min_height:
                break  # y 간격이 크면 더 이상 병합 불가
            if src_lang == "한국어" and vertical_gap > 0.8 * min_height:
                break

            if can_merge(group[-1], blocks[j], src_lang, target_lang):
                group.append(blocks[j])
                used[j] = True

        # 3. 그룹을 하나의 block으로 병합
        merged_lines = []
        merged_bbox = [float('inf'), float('inf'), float('-inf'), float('-inf')]
        for block in group:
            merged_lines.extend(block["lines"])
            merged_bbox[0] = min(merged_bbox[0], block["bbox"][0])
            merged_bbox[1] = min(merged_bbox[1], block["bbox"][1])
            merged_bbox[2] = max(merged_bbox[2], block["bbox"][2])
            merged_bbox[3] = max(merged_bbox[3], block["bbox"][3])

        # 병합된 블럭 생성
        merged_block = {
            "lines": merged_lines,
            "bbox": merged_bbox,
            "type": group[0].get("type", 0),  # 첫 블럭의 type 사용
            "class_name": decide_class_name(group)  # 병합된 class_name 결정 (넓이 기준)
        }

        merged_blocks.append(merged_block)

    return merged_blocks



def mergeContinuosBlocks(blocks, src_lang, target_lang):
  blocks = mergeBlocksByLineOverlap(blocks)
  blocks = mergeBlocksByYGap(blocks, src_lang, target_lang)
  
  return blocks


def mergeContinuosBlocks2(blocks):
    """
    Picture, Formula, Table을 제외한 block들에 대해서만 mergeBlocksByLineOverlap과 mergeBlocksByYGap을 적용한 뒤,
    제외했던 Picture, Formula, Table block들을 다시 합쳐서 반환한다.
    """

    if not blocks:
        return []

    # 1. Picture, Formula, Table block은 따로 분리
    special_blocks = []
    normal_blocks = []

    for block in blocks:
        class_name = block.get("class_name", "Text")
        if class_name in ("Picture", "Formula", "Table"):
            special_blocks.append(block)
        else:
            normal_blocks.append(block)

    # 2. 나머지 블록들만 mergeBlocksByLineOverlap과 mergeBlocksByYGap 적용
    merged_normal_blocks = mergeBlocksByLineOverlap(normal_blocks)
    merged_normal_blocks = mergeBlocksByYGap(merged_normal_blocks)

    # 3. 병합 완료된 normal_blocks + special_blocks 합치기
    merged_blocks = merged_normal_blocks + special_blocks

    return merged_blocks

  

def drawBBox(bbox, page, radius=None):
  [x1,y1, x2,y2] = bbox
  [p1, p2] = [pymupdf.Point(x1,y1), pymupdf.Point(x2, y2)]
  bbox_rect = pymupdf.Rect(p1, p2)
  page.draw_rect(rect=bbox_rect, radius=radius)
  
if __name__ == "__main__":
  doc = pymupdf.open("c.pdf")

  for page in doc:
    # read page text as a dictionary, suppressing extra spaces in CJK fonts
    blocks = page.get_text("dict", flags=11, sort=True)["blocks"]
    blocks = mergeContinuosBlocks(blocks)
    
    for b in blocks: 
        drawBBox(b["bbox"], page)
      
        # for l in b["lines"]:
        #     drawBBox(l["bbox"], page, 0.1)  
            # for s in l["spans"]:   
            #   drawBBox(s["bbox"], page, 0.2)
      
  doc.save("draw_bbox_c.pdf", garbage=3, clean=True, deflate=True)
  