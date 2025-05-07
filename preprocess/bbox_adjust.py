from yolo.yolo_inference.detection import detect_objects_from_page
from text_extract.text_extract import blockText

def bboxXOverlapRatio(bbox1, bbox2):
    """
    bbox1, bbox2의 x축 방향 겹치는 비율 계산.
    기준: 두 bbox의 x축 너비 합집합 (union)
    """
    x0_1, _, x1_1, _ = bbox1
    x0_2, _, x1_2, _ = bbox2

    # 겹치는 길이
    overlap = max(0, min(x1_1, x1_2) - max(x0_1, x0_2))
    # union 너비 = (두 bbox를 모두 포함하는 구간의 길이)
    union_width = max(x1_1, x1_2) - min(x0_1, x0_2)

    return overlap / union_width if union_width > 0 else 0



def bboxYLength(bbox):
    """
    bbox의 y축 길이 계산.
    """
    return bbox[3] - bbox[1]


def adjustLinesIfOverlap(prevLine, currLine, overlapThreshold=0.7):
    """
    prevLine과 currLine의 x축 겹침 비율과 y축 위치 관계를 확인하고,
    조건을 만족하면 y 경계를 y축 길이가 더 짧은 쪽에 맞춰 조정.
    """
    prevBBox = prevLine["bbox"]
    currBBox = currLine["bbox"]

    xOverlap = bboxXOverlapRatio(prevBBox, currBBox)

    # x축 70% 이상 겹치고, currLine의 위쪽 경계가 prevLine 아래쪽보다 위인지 확인
    if xOverlap >= overlapThreshold and currBBox[1] < prevBBox[3]:
        prevHeight = bboxYLength(prevBBox)
        currHeight = bboxYLength(currBBox)

        if currHeight < prevHeight:
            # currLine 쪽 y 경계에 prevLine 맞춤
            prevLine["bbox"] = (
                prevBBox[0], 
                prevBBox[1], 
                prevBBox[2], 
                currBBox[1]
            )
        else:
            # prevLine 쪽 y 경계에 currLine 맞춤
            currLine["bbox"] = (
                currBBox[0], 
                prevBBox[3], 
                currBBox[2], 
                currBBox[3]
            )


def adjustBlockBbox(block, leftBound, rightBound):
    """
    block 및 line bbox 조정.
    - 좌우 경계(leftBound, rightBound) 고정
    - x축 겹침 70% 이상 + y축 꼬임 → y축 짧은 쪽 기준 정렬
    """
    blockBBox = block["bbox"]
    block["bbox"] = (leftBound, blockBBox[1], rightBound, blockBBox[3])

    lines = block.get("lines", [])
    prevLine = None

    for line in lines:
        lineBBox = line["bbox"]
        # line 우측 경계 고정
        line["bbox"] = (lineBBox[0], lineBBox[1], rightBound, lineBBox[3])

        if prevLine:
            adjustLinesIfOverlap(prevLine, line)

        prevLine = line


def adjustBlocks(blocks, adjust_objects):
    """
    blocks 리스트 안의 블럭들의 경계 (왼쪽 x0, 오른쪽 x1)를 adjust_objects를 참고하여 수정한다.

    Args:
        blocks (list): 알고리즘으로 감지한 블럭 리스트
        adjust_objects (list): yolo로 감지한 블럭 리스트
    """

    def get_height(bbox):
        """Bounding box의 높이를 반환한다."""
        return bbox[3] - bbox[1]

    def get_width(bbox):
        """Bounding box의 너비를 반환한다."""
        return bbox[2] - bbox[0]

    def get_vertical_overlap(bbox1, bbox2):
        """두 bounding box 사이의 수직 방향 교집합 높이를 계산한다."""
        y0 = max(bbox1[1], bbox2[1])
        y1 = min(bbox1[3], bbox2[3])
        return max(0, y1 - y0)

    def get_horizontal_overlap(bbox1, bbox2):
        """두 bounding box 사이의 수평 방향 교집합 너비를 계산한다."""
        x0 = max(bbox1[0], bbox2[0])
        x1 = min(bbox1[2], bbox2[2])
        return max(0, x1 - x0)

    for block in blocks:
        block_bbox = block.get("bbox")
        if not block_bbox:
            continue  # bbox가 없는 경우는 건너뜀
          
        # block의 모든 line들을 block의 우측 경계에 맞게 수정
        adjustBlockBbox(block, block_bbox[0], block_bbox[2])

        matching_adj_bboxes = []

        # adjust_objects 안의 각 객체를 순회하며 매칭되는 bbox 찾기
        for adj_block in adjust_objects:
            adj_bbox = adj_block.get("bbox")
            if not adj_bbox:
                continue

            # 교집합 영역 계산
            vertical_overlap = get_vertical_overlap(block_bbox, adj_bbox)
            horizontal_overlap = get_horizontal_overlap(block_bbox, adj_bbox)

            # 최소 높이/너비 기준 비율 계산
            min_height = min(get_height(block_bbox), get_height(adj_bbox))
            min_width = min(get_width(block_bbox), get_width(adj_bbox))

            height_ratio = vertical_overlap / min_height if min_height > 0 else 0
            width_ratio = horizontal_overlap / min_width if min_width > 0 else 0

            # 높이 겹침이 0.5 너비 겹침이 0.8 이상이면 같은 영역으로 판단
            if height_ratio >= 0.5 and width_ratio >= 0.8:
                matching_adj_bboxes.append(adj_bbox)

        # 매칭된 adjust_block 들이 있을 경우
        if matching_adj_bboxes:
            # 매칭된 블럭들 중 가장 왼쪽과 가장 오른쪽 좌표를 결정
            left_bound = min(b[0] for b in matching_adj_bboxes)
            right_bound = max(b[2] for b in matching_adj_bboxes)
            upper_bound = min(b[1] for b in matching_adj_bboxes)
            lower_bound = max(b[3] for b in matching_adj_bboxes)
            
            lines = block.get("lines", [])
            first_height = (lines[0]["bbox"][3] - lines[0]["bbox"][1]) if len(lines) > 0 else 5
            last_height = (lines[-1]["bbox"][3] - lines[-1]["bbox"][1]) if len(lines) > 0 else 5
            
            if upper_bound > block_bbox[1] + first_height * 0.8  or lower_bound < block_bbox[3] - last_height * 0.8: # 만약 yolo 블락이 텍스트를 덜 잡았으면 적용하지 않기
              continue
            
            intersection = min(right_bound, block_bbox[2]) - max(left_bound, block_bbox[0])
            union = max(right_bound, block_bbox[2]) - min(left_bound, block_bbox[0])

            correct_ratio = intersection/union if union > 0 else 0
            
            if correct_ratio < 0.97:
              # 만약 너비 교집합/합집합이 0.9 미만이면, 알고리즘의 블락이 잘못 잡힌 것
              # yolo에서 잡은 block 정보 이용해, block의 bbox를 수정
              adjustBlockBbox(block, left_bound, right_bound)



def adjustBlocksFromYolo(blocks, yolo_objects):
  adjust_objects = [block for block in yolo_objects if (block["class_name"] not in ["Picture", "Table", "Formula"]) ]
  adjustBlocks(blocks, adjust_objects)