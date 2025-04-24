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
    if not blocks:
        return []

    def getLastLine(block):
        return block["lines"][-1] if block.get("lines") else None

    def getFirstLine(block):
        return block["lines"][0] if block.get("lines") else None

    merged_blocks = []
    used_indices = set()  # 이미 병합에 사용된 블록 인덱스

    i = 0
    while i < len(blocks):
        if i in used_indices:
            i += 1
            continue

        current_block = blocks[i]
        merged = False

        for j in range(i + 1, len(blocks)):
            if j in used_indices:
                continue

            next_block = blocks[j]
            last_line = getLastLine(current_block)
            next_first_line = getFirstLine(next_block)

            if not last_line or not next_first_line:
                continue

            # span 정보
            last_span = last_line["spans"][-1]
            first_span = next_first_line["spans"][0]

            # 조건 1: x 간격
            x_gap = next_first_line["bbox"][0] - last_line["bbox"][2]
            font_size_max = max(last_span["size"], first_span["size"])
            x_gap_close = -font_size_max * 2.5 <= x_gap <= font_size_max * 2.5

            # 조건 2: y축 겹침
            y0_a, y3_a = last_line["bbox"][1], last_line["bbox"][3]
            y0_b, y3_b = next_first_line["bbox"][1], next_first_line["bbox"][3]
            y_overlap = max(0, min(y3_a, y3_b) - max(y0_a, y0_b))
            min_height = min(y3_a - y0_a, y3_b - y0_b)
            y_overlap_enough = y_overlap >= min_height * 0.5
            
            # 조건 3: line의 진행방향 유사
            line_aligned = hasSameDirection(last_line, next_first_line)

            if x_gap_close and y_overlap_enough and line_aligned:
                # 병합 수행
                current_block["lines"].extend(next_block["lines"])
                cur_bbox = current_block["bbox"]
                next_bbox = next_block["bbox"]
                current_block["bbox"] = [
                    min(cur_bbox[0], next_bbox[0]),
                    min(cur_bbox[1], next_bbox[1]),
                    max(cur_bbox[2], next_bbox[2]),
                    max(cur_bbox[3], next_bbox[3])
                ]
                used_indices.add(j)
                merged = True  # 병합 발생
                break  # 첫 번째 조건 만족하는 블록만 병합하고 break

        merged_blocks.append(current_block)
        i += 1

    return merged_blocks
  
def mergeBlocksByYGap(blocks):
    """
    비슷한 x 시작점과 y 간격이 좁은 블락들을 병합한 새로운 블락 리스트를 반환합니다.
    """
    def get_block_top_y(block):
        for line in block.get("lines", []):
            return line["bbox"][1]
        return float("inf")

    def get_first_font_size(block):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if span.get("text"):
                    return span.get("size", 12)
        return 12

    def can_merge(prev, curr):
    # x축 시작점 유사 여부 판단
        if not isLinesStartWithSameX(prev["lines"][-1], curr["lines"][0]):
            return False

        # y축 거리 유사 여부 판단 (라인 높이 기준)
        prev_last_line = prev["lines"][-1]
        curr_first_line = curr["lines"][0]

        prev_y0, prev_y1 = prev_last_line["bbox"][1], prev_last_line["bbox"][3]
        curr_y0, curr_y1 = curr_first_line["bbox"][1], curr_first_line["bbox"][3]

        prev_line_height = prev_y1 - prev_y0
        curr_line_height = curr_y1 - curr_y0
        min_height = min(prev_line_height, curr_line_height)

        vertical_gap = curr_y0 - prev_y1
        if vertical_gap > 0.5 * min_height:
            return False
          
        if not hasSameDirection(prev["lines"][-1], curr["lines"][0]):
            return False
        return True


    def group_blocks_by_x_position(blocks, indent_chars=4):
        groups = []

        for block in blocks:
            block_x = block["bbox"][0]
            font_size = get_first_font_size(block)
            tolerance = font_size *  indent_chars

            matched = False
            for group in groups:
                ref_x = group["ref_x"]
                if abs(block_x - ref_x) <= tolerance:
                    group["blocks"].append(block)
                    matched = True
                    break

            if not matched:
                groups.append({"ref_x": block_x, "blocks": [block]})

        # 각 그룹 내에서 y축 기준 정렬
        for group in groups:
            group["blocks"].sort(key=lambda b: get_block_top_y(b))

        # 그룹 전체를 ref_x 기준 정렬하고 평탄화
        groups.sort(key=lambda g: g["ref_x"])
        sorted_blocks = [block for group in groups for block in group["blocks"]]
        return sorted_blocks


    # 정렬
    blocks = group_blocks_by_x_position(blocks)

    merged_blocks = []
    current = None

    for block in blocks:
        if not current:
            current = block
            continue

        if can_merge(current, block):
            current["lines"].extend(block["lines"])
            # bbox 확장
            x0 = min(current["bbox"][0], block["bbox"][0])
            y0 = min(current["bbox"][1], block["bbox"][1])
            x1 = max(current["bbox"][2], block["bbox"][2])
            y1 = max(current["bbox"][3], block["bbox"][3])
            current["bbox"] = [x0, y0, x1, y1]
        else:
            merged_blocks.append(current)
            current = block

    if current:
        merged_blocks.append(current)

    return merged_blocks


def mergeContinuosBlocks(blocks):
  blocks = mergeBlocksByLineOverlap(blocks)
  blocks = mergeBlocksByYGap(blocks)
  
  return blocks
  

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
  