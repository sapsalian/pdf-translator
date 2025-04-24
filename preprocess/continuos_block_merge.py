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
    y 간격이 좁고 x축 너비 기준으로 50% 이상 겹치는 블락들을 병합한 새로운 블락 리스트 반환
    """

    def get_block_top_y(block):
        for line in block.get("lines", []):
            return line["bbox"][1]
        return float("inf")

    def get_block_width(block):
        x0, _, x1, _ = block["bbox"]
        return x1 - x0

    def get_x_overlap_ratio(block1, block2):
        x0_1, _, x1_1, _ = block1["bbox"]
        x0_2, _, x1_2, _ = block2["bbox"]
        overlap = max(0, min(x1_1, x1_2) - max(x0_1, x0_2))
        min_width = min(get_block_width(block1), get_block_width(block2))
        return overlap / min_width if min_width > 0 else 0

    def get_vertical_gap_and_min_height(block1, block2):
        line1 = block1["lines"][-1]
        line2 = block2["lines"][0]

        y1_bottom = line1["bbox"][3]
        y2_top = line2["bbox"][1]

        h1 = line1["bbox"][3] - line1["bbox"][1]
        h2 = line2["bbox"][3] - line2["bbox"][1]
        min_height = min(h1, h2)

        return y2_top - y1_bottom, min_height

    def can_merge(prev, curr):
        vertical_gap, min_height = get_vertical_gap_and_min_height(prev, curr)

        if vertical_gap > 0.5 * min_height:
            return False

        if get_x_overlap_ratio(prev, curr) < 0.5:
            return False

        if not hasSameDirection(prev["lines"][-1], curr["lines"][0]):
            return False

        return True

    def group_blocks_by_y_then_x(blocks):
        return sorted(blocks, key=lambda b: (get_block_top_y(b), b["bbox"][0]))

    blocks = group_blocks_by_y_then_x(blocks)
    used = [False] * len(blocks)  # 병합에 사용된 블락 표시
    merged_blocks = []

    for i, base in enumerate(blocks):
        if used[i]:
            continue

        current = {
            "lines": base["lines"][:],
            "bbox": base["bbox"][:],
            "type": base.get("type", 0)
        }
        used[i] = True

        for j in range(i + 1, len(blocks)):
            if used[j]:
                continue

            vertical_gap, min_height = get_vertical_gap_and_min_height(current, blocks[j])
            if vertical_gap > 0.5 * min_height:
                break

            if can_merge(current, blocks[j]):
                # 병합
                current["lines"].extend(blocks[j]["lines"])
                used[j] = True

                # bbox 확장
                x0 = min(current["bbox"][0], blocks[j]["bbox"][0])
                y0 = min(current["bbox"][1], blocks[j]["bbox"][1])
                x1 = max(current["bbox"][2], blocks[j]["bbox"][2])
                y1 = max(current["bbox"][3], blocks[j]["bbox"][3])
                current["bbox"] = [x0, y0, x1, y1]

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
  