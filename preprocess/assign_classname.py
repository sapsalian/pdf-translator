def assignClassNameToBlocks(blocks, yolo_objects):
    """
    각 block에 대해 yolo_objects를 참고하여 class_name을 부여한다.

    - 겹치는 yolo object가 있을 경우: 겹친 면적이 가장 큰 class_name을 사용한다.
    - 겹치는 yolo object가 없을 경우: "Text"를 기본 class_name으로 설정한다.
    """

    # bbox의 높이를 구하는 함수
    def get_height(bbox):
        return bbox[3] - bbox[1]

    # bbox의 너비를 구하는 함수
    def get_width(bbox):
        return bbox[2] - bbox[0]

    # 두 bbox 사이의 수직 방향 겹침 길이를 구하는 함수
    def get_vertical_overlap(bbox1, bbox2):
        y0 = max(bbox1[1], bbox2[1])
        y1 = min(bbox1[3], bbox2[3])
        return max(0, y1 - y0)

    # 두 bbox 사이의 수평 방향 겹침 길이를 구하는 함수
    def get_horizontal_overlap(bbox1, bbox2):
        x0 = max(bbox1[0], bbox2[0])
        x1 = min(bbox1[2], bbox2[2])
        return max(0, x1 - x0)

    # 두 bbox 사이의 실제 겹치는 면적(=가로 × 세로)을 계산하는 함수
    def get_overlap_area(bbox1, bbox2):
        vertical = get_vertical_overlap(bbox1, bbox2)
        horizontal = get_horizontal_overlap(bbox1, bbox2)
        return vertical * horizontal

    # blocks를 하나씩 순회
    for block in blocks:
        block_bbox = block.get("bbox")
        if not block_bbox:
            # bbox가 없는 경우 class_name을 "Text"로 설정하고 건너뜀
            block["class_name"] = "Text"
            continue

        matching_objects = []  # block과 충분히 겹치는 yolo object 저장 리스트

        # 모든 yolo object들과 겹침 여부 판단
        for obj in yolo_objects:
            obj_bbox = obj.get("bbox")
            if not obj_bbox:
                continue

            # 겹침 길이 계산
            vertical_overlap = get_vertical_overlap(block_bbox, obj_bbox)
            horizontal_overlap = get_horizontal_overlap(block_bbox, obj_bbox)

            # block과 yolo object의 최소 높이/너비 계산
            min_height = min(get_height(block_bbox), get_height(obj_bbox))
            min_width = min(get_width(block_bbox), get_width(obj_bbox))

            # 높이, 너비 겹침 비율 계산
            height_ratio = vertical_overlap / min_height if min_height > 0 else 0
            width_ratio = horizontal_overlap / min_width if min_width > 0 else 0

            # 높이 50% 이상, 너비 80% 이상 겹치면 matching으로 판단
            if height_ratio >= 0.5 and width_ratio >= 0.8:
                overlap_area = get_overlap_area(block_bbox, obj_bbox)
                matching_objects.append((obj["class_name"], overlap_area))

        if matching_objects:
            # class_name별로 겹친 면적을 합산
            area_by_class = {}
            for class_name, area in matching_objects:
                area_by_class[class_name] = area_by_class.get(class_name, 0) + area

            # 가장 총 면적이 큰 class_name을 선택
            dominant_class = max(area_by_class.items(), key=lambda x: x[1])[0]
            block["class_name"] = dominant_class
        else:
            # 겹치는 yolo object가 없으면 기본 class_name은 "Text"
            block["class_name"] = "Text"
