from yolo.yolo_inference.detection import detect_objects_from_page

def adjustBlockBbox(block, adjust_bbox):
  block_bbox = block["bbox"]
  block["bbox"] = (adjust_bbox[0], block_bbox[1], adjust_bbox[2], block_bbox[3])
  
  # for line in block.get("lines", []):
  #   line_bbox = line["bbox"]
  #   line["bbox"] = (line_bbox[0], line_bbox[1], adjust_bbox[2], line_bbox[3])

def adjustBlocks(blocks, adjust_objects):
    """
    blocks 리스트 안의 블럭들의 오른쪽 경계(x1)를 adjust_blocks를 참고해 수정한다.

    Args:
        blocks (list): 알고리즘으로 잡은 블럭 리스트
        adjust_blocks (list): yolo로 잡은 블럭 리스트
    """

    def get_height(bbox):
        return bbox[3] - bbox[1]

    def get_width(bbox):
        return bbox[2] - bbox[0]

    def get_vertical_overlap(bbox1, bbox2):
        y0 = max(bbox1[1], bbox2[1])
        y1 = min(bbox1[3], bbox2[3])
        return max(0, y1 - y0)

    def get_horizontal_overlap(bbox1, bbox2):
        x0 = max(bbox1[0], bbox2[0])
        x1 = min(bbox1[2], bbox2[2])
        return max(0, x1 - x0)

    for block in blocks:
        block_bbox = block.get("bbox")
        if not block_bbox:
            continue

        for adj_block in adjust_objects:
            adj_bbox = adj_block.get("bbox")
            if not adj_bbox:
                continue

            # 높이와 너비 교집합 계산
            vertical_overlap = get_vertical_overlap(block_bbox, adj_bbox)
            horizontal_overlap = get_horizontal_overlap(block_bbox, adj_bbox)

            # 각각의 비율 계산
            min_height = min(get_height(block_bbox), get_height(adj_bbox))
            min_width = min(get_width(block_bbox), get_width(adj_bbox))

            height_ratio = vertical_overlap / min_height if min_height > 0 else 0
            width_ratio = horizontal_overlap / min_width if min_width > 0 else 0

            # 둘 다 0.8 이상이면 같은 영역으로 판단
            if height_ratio >= 0.8 and width_ratio >= 0.8:
                # 오른쪽 경계 x좌표 수정
                adjustBlockBbox(block, adj_bbox)
                break  # 첫 번째 매칭되는 adjust_block만 사용하고 다음 block으로 넘어감

def adjustBlocksFromYolo(blocks, yolo_objects):
  adjust_objects = [block for block in yolo_objects if block["class_name"] == "Text"]
  adjustBlocks(blocks, adjust_objects)