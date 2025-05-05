from yolo.yolo_inference.detection import detect_objects_from_page
from text_extract.text_extract import blockText

def adjustBlockBbox(block, left_bound, right_bound):
  block_bbox = block["bbox"]
  block["bbox"] = (left_bound, block_bbox[1], right_bound, block_bbox[3])
  
  for line in block.get("lines", []):
    line_bbox = line["bbox"]
    line["bbox"] = (line_bbox[0], line_bbox[1], right_bound, line_bbox[3])

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
            else:
              adjustBlockBbox(block, block_bbox[0], block_bbox[2])



def adjustBlocksFromYolo(blocks, yolo_objects):
  adjust_objects = [block for block in yolo_objects if (block["class_name"] not in ["Picture", "Table", "Formula"]) ]
  adjustBlocks(blocks, adjust_objects)