from typing import List, Dict, Tuple

'''
1. 줄여야 하는 폰트 배수 설정.
	줄여야 하는 폰트 배수 = (한글문자 평균 가로폭 / 영어 문자 평균 가로폭)/(한->영 변환시 글자 수 증가 배수)
	만약, 줄여야 하는 폰트 배수가 0.7이면, 모든 line의 세로폭과 gap을 0.7배 해줘야 함.
	줄여야 하는 폰트 배수가 1 미만일 때만 적용.
2. 라인을 가로폭 기준으로 그룹화 하기
    다음라인이랑 현재라인 폭을 봤을때, (겹치는거/더 큰거) 값이 0.8이상일때만 같은 그룹, 아니면 거기서 끊기
3. 그룹들을 돌면서 그룹별 line_frame 들 만들기. 
    - line_frame에 들어가야 할 요소
        - bbox
        - dir
    - line_frame 만드는 법
        1) 그룹의 좌우 경계 구하기(line중 가장 왼쪽 경계와, 가장 오른쪽 경계 저장)
        2) 그룹의 위쩍, 아래쪽 경계 구하기(그룹 첫째 라인의 위쪽 경계와 마지막 라인의 아래쪽 경계)
        3) 기존의 line들 옮겨오기(bbox 높이와 gap을 줄여야하는 폰트 배수를 곱한만큼 줄이며 옮겨오기)
        4) 새로운 line들 추가하기. 그룹의 아래쪽 경계를 넘어가지 않을때까지((line의 평균 gap* 배수) 를 gap으로 쓰고 (line의 평균 bbox 높이 * 배수)를 bbox 높이로 사용하며, 그룹의 좌우경계를 bbox의 좌우 경계로 사용해 추가)
        5) 다 넣고 남는 여백(그룹의 아래쪽 경계 - 새로 만들어진 line_frames의 아래쪽 경계)을 gap 개수(line_frame 개수 - 1)로 나눠, 나온 값을 모든 gap들에 재분배하기
        평균 gap 구할때는 양수인 gap들만 사용하기.
4. 그룹별 line_frame들 합쳐서 result_line_frames 만들고, block의 속성에 할당
'''

def calculate_bbox_scale(src_lang: str, target_lang: str) -> float:
    font_scale_map = {
        "한국어": {
            "English": 0.7,
        },
        
        "English": {
            "한국어": 1,
        },
    }
    return font_scale_map[src_lang][target_lang]


def groupLinesByHorizontalOverlap(lines: List[Dict]) -> List[List[Dict]]:
    """
    pymupdf의 라인 리스트를 받아, 가로폭이 겹치는 정도를 기준으로 그룹화합니다.
    겹치는 정도가 충분히 크면 (80% 이상) 같은 그룹으로 보고, 그렇지 않으면 새 그룹으로 나눕니다.

    Args:
        lines (List[Dict]): PyMuPDF에서 추출한 라인 리스트.
            각 line은 최소한 "bbox" 키를 가지고 있어야 하며,
            bbox는 [x0, y0, x1, y1] 형식의 좌표값입니다.

    Returns:
        List[List[Dict]]: 가로폭 기준으로 그룹화된 라인들의 리스트.
            각 그룹은 겹치는 정도가 80% 이상인 라인들로 구성됩니다.
    """

    def overlap_ratio(bbox1, bbox2) -> float:
        """
        두 bbox의 x축 기준 겹침 비율을 계산합니다.

        Args:
            bbox1, bbox2: 각 라인의 bbox (x0, y0, x1, y1)

        Returns:
            float: 겹치는 길이 / 전체 길이 (합집합 기준). 0 ~ 1 사이 값.
        """
        x0_1, _, x1_1, _ = bbox1
        x0_2, _, x1_2, _ = bbox2

        # 두 bbox의 x축 겹치는 길이 계산
        overlap = max(0, min(x1_1, x1_2) - max(x0_1, x0_2))

        # 두 bbox의 x축 전체 범위 (합집합)
        union = max(x1_1, x1_2) - min(x0_1, x0_2)

        # 0으로 나누지 않도록 예외 처리
        return overlap / union if union != 0 else 0

    groups = []  # 최종 결과로 반환할 그룹 리스트
    current_group = []  # 현재 묶고 있는 그룹

    for idx, line in enumerate(lines):
        # 첫 라인은 무조건 새로운 그룹의 시작
        if not current_group:
            current_group.append(line)
            continue

        prev_bbox = current_group[-1]['bbox']  # 이전 라인의 bbox
        curr_bbox = line['bbox']               # 현재 라인의 bbox

        # 이전 라인과 현재 라인의 가로폭 겹침 비율 계산
        if overlap_ratio(prev_bbox, curr_bbox) >= 0.8:
            # 겹침 비율이 충분하므로 현재 그룹에 포함
            current_group.append(line)
        else:
            # 겹침이 부족하므로 그룹을 끊고, 새 그룹 시작
            groups.append(current_group)
            current_group = [line]

    # 마지막 그룹이 남아있다면 추가
    if current_group:
        groups.append(current_group)

    return groups


def calculateGroupBoundaries(group: List[Dict]) -> Tuple[float, float, float, float]:
    """
    각 그룹의 경계를 계산합니다.
    - 좌우 경계: 그룹 내 모든 line의 bbox 중 가장 왼쪽(x0), 가장 오른쪽(x1)
    - 위아래 경계: 그룹의 첫 번째 line의 y0, 마지막 line의 y1
    """
    left_x = min(line["bbox"][0] for line in group)
    right_x = max(line["bbox"][2] for line in group)
    top_y = group[0]["bbox"][1]
    bottom_y = group[-1]["bbox"][3]
    return left_x, right_x, top_y, bottom_y

def calculateAverageHeight(group: List[Dict]) -> float:
    """
    그룹 내 line들의 평균 높이를 계산합니다.
    """
    heights = [abs(line["bbox"][3] - line["bbox"][1]) for line in group]
    return sum(heights) / len(heights) if heights else 1

def calculateAverageGap(group: List[Dict]) -> float:
    """
    그룹 내 line 간의 평균 양수 간격(gap)을 계산합니다.
    """
    gaps = []
    for i in range(1, len(group)):
        prev_y1 = group[i - 1]["bbox"][3]
        curr_y0 = group[i]["bbox"][1]
        gap = curr_y0 - prev_y1
        if gap > 0:
            gaps.append(gap)
    return sum(gaps) / len(gaps) if gaps else 0

def makeLineFramesFromGroups(groups: List[List[Dict]], bbox_scale: float) -> List[Dict]:
    """
    각 그룹의 라인들을 다음 절차에 따라 line_frame으로 재구성합니다:
      1) 그룹의 좌우/상하 경계를 계산
      2) 평균 bbox 높이와 평균 gap 계산
      3) 기존 라인들을 폰트 배율만큼 축소하여 위에서부터 차례대로 재배치
      4) 남은 공간을 평균 크기 기반의 가상 라인들로 채움
      5) 마지막 여백을 모든 gap에 재분배하여 공간 정렬

    Args:
        groups (List[List[Dict]]): pymupdf의 line들을 가로폭 기준으로 묶은 그룹 리스트
        font_scale (float): 기존 line의 높이와 간격을 줄일 배수 (예: 0.8)

    Returns:
        List[Dict]: 모든 그룹에서 생성된 line_frame들의 리스트. 각 frame은 bbox, dir 포함.
    """
    line_frames = []

    for group in groups:
        # 1) 그룹의 경계 계산
        left_x, right_x, top_y, bottom_y = calculateGroupBoundaries(group)
        current_y = top_y
        dir_value = group[0].get("dir", (1, 0))  # 기본 dir은 첫 라인의 dir 또는 (1, 0)

        # 2) 평균 높이 및 평균 gap 계산 (gap은 양수만 사용)
        avg_height = calculateAverageHeight(group)
        avg_gap = calculateAverageGap(group)

        # 3) 기존 라인을 축소하여 옮기기
        for i, line in enumerate(group):
            x0, y0, x1, y1 = line["bbox"]
            orig_height = y1 - y0
            height = orig_height * bbox_scale

            # 이전 라인과의 간격 계산 및 축소 적용
            if i > 0:
                prev_line_y1 = group[i - 1]["bbox"][3]
                raw_gap = y0 - prev_line_y1
                gap = raw_gap * bbox_scale
                current_y += gap  # 줄어든 gap만큼 아래로 이동

            # 줄어든 높이로 새로운 bbox 생성
            line_frames.append({
                "bbox": [x0, current_y, x1, current_y + height],
                "dir": line.get("dir", (1, 0))
            })

            current_y += height  # 다음 줄 위치 갱신

        # 4) 가상 라인 추가: 남은 공간을 평균 크기로 채움
        scaled_height = avg_height * bbox_scale
        scaled_gap = avg_gap * bbox_scale
        
        while current_y + scaled_height <= bottom_y:
            current_y += scaled_gap  # gap 먼저 적용
            line_frames.append({
                "bbox": [left_x, current_y, right_x, current_y + scaled_height],
                "dir": dir_value  # 첫 라인의 dir 사용
            })
            current_y += scaled_height

        # 5) 남은 여백을 모든 gap에 재분배 (단일 루프로 최적화)
        final_bottom = line_frames[-1]["bbox"][3]
        remaining_space = bottom_y - final_bottom
        gap_count = len(line_frames) - 1

        if gap_count > 0 and remaining_space > 0:
            extra_gap = remaining_space / gap_count  # 각 gap에 추가할 값
            offset = 0
            for i in range(len(line_frames)):
                if i > 0:
                    offset += extra_gap  # 두 번째 line부터 누적 offset 적용
                x0, y0, x1, y1 = line_frames[i]["bbox"]
                line_frames[i]["bbox"] = [x0, y0 + offset, x1, y1 + offset]

    return line_frames


def assignLineFramesToBlocks(blocks: List[Dict], src_lang: str, target_lang: str) -> None:
    """
    각 block에 대해 line들을 그룹화하고, 축소 배율을 적용하여 line_frame들을 계산한 후
    block["line_frames"]에 결과를 저장합니다.

    Args:
        blocks (List[Dict]): PyMuPDF의 블록 리스트. 각 block은 "lines" 키를 포함해야 함.
        src_lang (str): 원본 언어 (예: "한국어")
        target_lang (str): 대상 언어 (예: "English")

    Returns:
        None: 각 block이 직접 수정됨 (line_frames가 추가됨)
    """
    bbox_scale = calculate_bbox_scale(src_lang, target_lang)

    for block in blocks:
        lines = block.get("lines", [])

        if not lines:
            block["line_frames"] = []
            continue

        # 1. 라인을 가로폭 기준으로 그룹화
        groups = groupLinesByHorizontalOverlap(lines)

        # 2. 그룹을 기반으로 축소 및 보정된 라인 프레임 생성
        line_frames = makeLineFramesFromGroups(groups, bbox_scale)

        # 3. 결과 저장
        block["line_frames"] = line_frames
