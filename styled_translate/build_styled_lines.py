from typing import List, Dict, Tuple
from styled_translate.get_font import getFont
from styled_translate.assign_style import SpanStyle

# 스타일이 적용된 span을 한 줄 내 상대 좌표로 나타내는 클래스
class PositionedSpan:
    def __init__(self, style_id: int, rel_x: float, text: str):
        self.style_id = style_id  # 스타일 ID
        self.rel_x = rel_x        # 현재 줄 시작 기준 상대 x좌표
        self.text = text          # 해당 span 내 텍스트

    def to_dict(self):
        return {"style_id": self.style_id, "rel_x": self.rel_x, "text": self.text}

# 현재 라인의 bbox 정보를 바탕으로 x0, x1, bbox를 반환
# 주어진 line_index를 기준으로 줄의 위치를 확인

def updateLineContext(line_bboxes, line_index):
    bbox = line_bboxes[line_index]  # [x0, y0, x1, y1]
    return bbox[0], bbox[2], bbox

# 현재 줄을 styled_lines에 저장하고, positioned span 배열 및 줄 너비 초기화
# 마지막으로 기록된 x값(current_x)을 line_width로 저장함

def flushLine(line, styled_lines, current_x):
    if line["positioned_spans"]:
        line["line_width"] = current_x
        styled_lines.append(line.copy())
        line["positioned_spans"] = []
        line["line_width"] = 0

# 줄을 넘길 때 호출됨: 현재 buffer_text를 PositionedSpan으로 저장하고, 줄을 비움
# 다음 줄 정보로 갱신하고 좌표 누적값을 초기화함

def advanceLine(line_bboxes, styled_lines, current_line, buffer_text, rel_x, style_id, line_index, current_x):
    if buffer_text:
        current_line["positioned_spans"].append(PositionedSpan(style_id, rel_x, buffer_text).to_dict())
    flushLine(current_line, styled_lines, current_x)
    line_index += 1
    if line_index >= len(line_bboxes):
        return None, None, None, None, None, line_index, 0
    x0_line, x1_line, current_line_bbox = updateLineContext(line_bboxes, line_index)
    return current_line_bbox, x0_line, x1_line, 0, 0, line_index, 0

# 텍스트의 회전 각도에 따라 줄 진행 방향을 결정
# 반환값은 해당 방향에 맞는 시작점과 끝점 좌표

def getLineLimitsByRotation(bbox: List[float], rotate: int) -> Tuple[float, float]:
    rotate = rotate % 360
    if rotate == 0:
        return bbox[0], bbox[2]  # 좌→우
    elif rotate == 90:
        return bbox[3], bbox[1]  # 하→상 (y 축 기준 역방향)
    elif rotate == 180:
        return bbox[2], bbox[0]  # 우→좌
    elif rotate == 270:
        return bbox[1], bbox[3]  # 상→하
    else:
        raise ValueError(f"Unsupported rotation angle: {rotate}")

# styled spans와 각 line bbox를 기반으로 positioned span을 생성하고
# 줄마다 positioned_spans 리스트와 line_width를 포함하는 dict로 정리하여 반환

def buildStyledLines(styled_spans: List[Dict], style_dict: Dict[int, 'SpanStyle'], lines: List[Dict]):
    # 각 라인의 bounding box만 추출하여 리스트 생성
    line_bboxes = [line["bbox"] for line in lines]

    # 완성된 줄들을 저장할 리스트
    styled_lines = []

    # 현재 줄 정보를 저장하는 딕셔너리
    current_line = {"positioned_spans": [], "line_width": 0}
    
    # 줄 인덱스 초기화
    line_index = 0

    # 현재 처리 중인 줄의 좌우 경계 및 bbox 불러오기
    x0_line, x1_line, current_line_bbox = updateLineContext(line_bboxes, line_index)

    # 현재 줄에서 사용된 가로 길이 (x 위치)
    current_x = 0

    # 각 스타일링된 span에 대해 반복 처리
    for span in styled_spans:
        text = span["text"]
        style_id = span["style_id"]
        style = style_dict[style_id]  # 스타일 정보 불러오기
        font = getFont(style)        # 폰트 객체 가져오기
        char_widths = font.char_lengths(text, fontsize=style.font_size)  # 각 글자의 너비 계산
        char_idx = 0  # 글자 인덱스 초기화

        # 현재 줄의 회전에 따른 시작-끝 좌표 설정
        line_start, line_end = getLineLimitsByRotation(current_line_bbox, style.rotate)

        # span 내에서 실제로 출력할 텍스트와 그 위치를 저장할 변수
        rel_x = current_x + style.x_gap_with_prev  # 이전 span과의 간격 포함한 시작 위치
        buffer_text = ""

        while char_idx < len(char_widths):
            ch = text[char_idx]
            ch_width = char_widths[char_idx]

            if ch == "\n":  # 줄바꿈 문자 발견 시
                current_line_bbox, x0_line, x1_line, current_x, rel_x, line_index, line_width = advanceLine(
                    line_bboxes, styled_lines, current_line, buffer_text, rel_x, style_id, line_index, current_x
                )
                if current_line_bbox is None:  # 줄이 더 이상 없으면 종료
                    return styled_lines
                line_start, line_end = getLineLimitsByRotation(current_line_bbox, style.rotate)
                buffer_text = ""
                char_idx += 1
                continue

            # 현재 줄에 문자를 추가할 수 있는지 확인
            limit = abs(line_end - line_start)
            if current_x + style.x_gap_with_prev + ch_width <= limit:
                # 아직 줄에 여유가 있으면 문자 추가
                if not buffer_text:
                    rel_x = current_x + style.x_gap_with_prev
                buffer_text += ch
                current_x += style.x_gap_with_prev + ch_width
                char_idx += 1
            else:
                # 줄을 넘어서는 경우, 현재까지 buffer_text로 span 완료
                current_line_bbox, x0_line, x1_line, current_x, rel_x, line_index, line_width = advanceLine(
                    line_bboxes, styled_lines, current_line, buffer_text, rel_x, style_id, line_index, current_x
                )
                if current_line_bbox is None:  # 줄이 더 이상 없으면 종료
                    return styled_lines
                line_start, line_end = getLineLimitsByRotation(current_line_bbox, style.rotate)
                buffer_text = ""

        # 현재 span이 줄의 끝까지 남은 텍스트를 보유하고 있으면 처리
        if buffer_text:
            current_line["positioned_spans"].append(PositionedSpan(style_id, rel_x, buffer_text).to_dict())

    # 마지막 줄을 flush하여 저장
    flushLine(current_line, styled_lines, current_x)

    # 최종 출력 형식: span들을 딕셔너리로 변환하여 라인별로 묶어 반환
    return styled_lines

