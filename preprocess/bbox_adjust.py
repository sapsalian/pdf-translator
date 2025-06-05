from text_extract.text_extract import blockText
from util.line_utils import calculateAverageGap
from styled_translate.assign_style import dirToRotation
from util.block_utils import *

# 주어진 두 bbox가 진행 방향(rotate 기준)에서 얼마나 겹치는지 비율을 계산
# rotate: 0/180 → x축 기준, 90/270 → y축 기준
# 반환값: 0~1 사이의 겹침 비율

def bboxOverlapRatio(bbox1, bbox2, rotate):
    if rotate in (0, 180):
        x0_1, _, x1_1, _ = bbox1
        x0_2, _, x1_2, _ = bbox2
        overlap = max(0, min(x1_1, x1_2) - max(x0_1, x0_2))
        union = max(x1_1, x1_2) - min(x0_1, x0_2)
    else:
        _, y0_1, _, y1_1 = bbox1
        _, y0_2, _, y1_2 = bbox2
        overlap = max(0, min(y1_1, y1_2) - max(y0_1, y0_2))
        union = max(y1_1, y1_2) - min(y0_1, y0_2)
    return overlap / union if union > 0 else 0

# bbox의 진행 방향 기준 길이 반환
# rotate가 0/180이면 높이(y축), 90/270이면 너비(x축)
def bboxLength(bbox, rotate):
    return bbox[3] - bbox[1] if rotate in (0, 180) else bbox[2] - bbox[0]

# 두 line이 겹칠 경우, 짧은 쪽 기준으로 bbox를 조정하여 겹침 방지
# line_gap: 줄 간 간격 보정치
# rotate: 진행 방향 (0/90/180/270)
def adjustLinesIfOverlap(prevLine, currLine, line_gap, rotate, overlapThreshold=0.7):
    prevBBox, currBBox = prevLine["bbox"], currLine["bbox"]
    overlap_ratio = bboxOverlapRatio(prevBBox, currBBox, rotate)
    order_check = currBBox[1] < prevBBox[3] if rotate in (0, 180) else currBBox[0] < prevBBox[2]

    if overlap_ratio >= overlapThreshold and order_check:
        prev_len = bboxLength(prevBBox, rotate)
        curr_len = bboxLength(currBBox, rotate)

        if curr_len < prev_len:
            # currLine이 더 짧으면 prevLine을 currLine 시작 위치까지 줄임
            if rotate in (0, 180):
                prevLine["bbox"] = (prevBBox[0], prevBBox[1], prevBBox[2], currBBox[1] - line_gap)
            else:
                prevLine["bbox"] = (prevBBox[0], prevBBox[1], currBBox[0] - line_gap, prevBBox[3])
        else:
            # prevLine이 더 짧으면 currLine 시작을 prevLine 끝 다음으로 이동
            if rotate in (0, 180):
                currLine["bbox"] = (currBBox[0], prevBBox[3] + line_gap, currBBox[2], currBBox[3])
            else:
                currLine["bbox"] = (prevBBox[2] + line_gap, currBBox[1], currBBox[2], currBBox[3])

# block 전체 및 내부 line들을 우측 경계(rightBound)에 맞춰 정렬하고, 줄 간 겹침 조정
# 중앙 정렬시 내부 line들을 블락의 좌우측 경계 모두에 맞춤.
def adjustBlockBbox(block, leftBound, rightBound):
    blockBBox = block["bbox"]
    block["bbox"] = (leftBound, blockBBox[1], rightBound, blockBBox[3])
    lines = block.get("lines", [])
    if not lines:
        return

    rotate = dirToRotation(lines[0]["dir"])
    line_gap = calculateAverageGap(lines, rotate)

    for i in range(len(lines)):
        x0, y0, x1, y1 = lines[i]["bbox"]
        if block["align"] == ALIGN_CENTER:
            lines[i]["bbox"] = (leftBound, y0, rightBound, y1)
        else:
            lines[i]["bbox"] = (x0, y0, rightBound, y1)
        if i > 0:
            adjustLinesIfOverlap(lines[i - 1], lines[i], line_gap, rotate)

# block들의 bbox를 YOLO 등 외부 객체들의 bbox 기준으로 보정하는 함수
def adjustBlocks(blocks, adjust_objects):
    # 진행 방향에 따라 bbox의 너비/높이 반환
    def getDimensions(bbox, rotate):
        return (bbox[3] - bbox[1], bbox[2] - bbox[0]) if rotate in (0, 180) else (bbox[2] - bbox[0], bbox[3] - bbox[1])

    # 진행 방향에 따라 교차 길이 계산
    def getIntersection(b1, b2, rotate):
        if rotate in (0, 180):
            height = max(0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
            width = max(0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
        else:
            height = max(0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
            width = max(0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
        return height, width

    for block in blocks:
        block_bbox = block.get("bbox")
        lines = block.get("lines", [])
        if not block_bbox or not lines:
            continue

        rotate = dirToRotation(lines[0]["dir"])
        adjustBlockBbox(block, block_bbox[0], block_bbox[2])

        matching_adj_bboxes = []
        for adj_block in adjust_objects:
            adj_bbox = adj_block.get("bbox")
            if not adj_bbox:
                continue

            block_h, block_w = getDimensions(block_bbox, rotate)
            adj_h, adj_w = getDimensions(adj_bbox, rotate)
            inter_h, inter_w = getIntersection(block_bbox, adj_bbox, rotate)

            height_ratio = inter_h / min(block_h, adj_h) if min(block_h, adj_h) > 0 else 0
            width_ratio = inter_w / min(block_w, adj_w) if min(block_w, adj_w) > 0 else 0

            if height_ratio >= 0.5 and width_ratio >= 0.8:
                matching_adj_bboxes.append(adj_bbox)

        if not matching_adj_bboxes:
            continue

        # 겹치는 bbox들의 좌/우/상/하 경계 계산
        left = min(b[0] for b in matching_adj_bboxes)
        right = max(b[2] for b in matching_adj_bboxes)
        top = min(b[1] for b in matching_adj_bboxes)
        bottom = max(b[3] for b in matching_adj_bboxes)

        # block 위아래가 과하게 벗어난 경우 무시
        first_h = bboxLength(lines[0]["bbox"], rotate) if lines else 5
        last_h = bboxLength(lines[-1]["bbox"], rotate) if lines else 5
        if top > block_bbox[1] + first_h * 0.8 or bottom < block_bbox[3] - last_h * 0.8:
            continue

        # block의 좌우 폭 기준으로 겹침 비율 판단
        intersection = min(right, block_bbox[2]) - max(left, block_bbox[0])
        union = max(right, block_bbox[2]) - min(left, block_bbox[0])
        correct_ratio = intersection / union if union > 0 else 0

        # 겹치는 정도가 부족하면 YOLO 기준 bbox로 보정
        if correct_ratio < 0.97:
            adjustBlockBbox(block, left, right)
            
# block들의 bbox를 조정하는 함수.
def adjustBlocksWithoutYolo(blocks):
    

    for block in blocks:
        block_bbox = block.get("bbox")
        lines = block.get("lines", [])
        if not block_bbox or not lines:
            continue

        adjustBlockBbox(block, block_bbox[0], block_bbox[2])


# YOLO 결과 중 텍스트 블럭으로 판단되는 것만 필터링하여 adjustBlocks 호출
def adjustBlocksFromYolo(blocks, yolo_objects):
    adjust_objects = [b for b in yolo_objects if b["class_name"] not in ["Picture", "Table", "Formula"]]
    # adjustBlocks(blocks, adjust_objects)
    adjustBlocksWithoutYolo(blocks)
