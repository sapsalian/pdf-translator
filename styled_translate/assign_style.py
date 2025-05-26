import math
from typing import List, Dict, Tuple
from text_extract.text_extract import *
from typing import Optional

# 방향 벡터(dir)를 기반으로 회전 각도(0, 90, 180, 270 중 가장 가까운 값) 계산
# 예: (1, 0) → 0도, (0, -1) → 90도 등
# 페이지 상 텍스트가 어떤 방향으로 배치되어 있는지 파악할 때 사용
def dirToRotation(dir):
    x, y = dir
    angle_rad = math.atan2(-y, x)
    angle_deg = (math.degrees(angle_rad)) % 360
    closest_90 = int(round(angle_deg / 90.0)) * 90 % 360
    return closest_90

# 하나의 span에 대한 스타일 정보를 담는 클래스
# 텍스트 스타일을 비교/관리하기 위해 정의됨
class SpanStyle:
    def __init__(self,
                 is_superscript: bool,
                 y_offset: float,
                 x_gap_with_prev: float,
                 font_size: float,
                 is_italic: bool,
                 is_bold: bool,
                 font_color: Tuple[float, float, float],
                 rotate: float,
                 link_num: Optional[int]):
        self.is_superscript = is_superscript
        self.y_offset = y_offset  # 라인 기준에서 얼마나 떠 있는지
        self.x_gap_with_prev = x_gap_with_prev  # 이전 span과의 거리
        self.font_size = font_size * 0.8
        self.is_italic = is_italic
        self.is_bold = is_bold
        self.font_color = font_color
        self.rotate = rotate  # 텍스트 회전 방향
        self.link_num = link_num

    def __eq__(self, other):
        if not isinstance(other, SpanStyle):
            return False

        return (
            self.is_superscript == other.is_superscript and
            round(self.y_offset, 1) == round(other.y_offset, 1) and
            round(self.x_gap_with_prev, 1) == round(other.x_gap_with_prev, 1) and
            round(self.font_size, 1) == round(other.font_size, 1) and
            self.is_italic == other.is_italic and
            self.is_bold == other.is_bold and
            all(a == b for a, b in zip(self.font_color, other.font_color)) and
            self.rotate == other.rotate and
            self.link_num == other.link_num
        )

    def __hash__(self):
        # 스타일 중복 제거를 위한 해시 처리
        return hash((
            self.is_superscript,
            round(self.y_offset, 1),
            round(self.x_gap_with_prev, 1),
            round(self.font_size, 1),
            self.is_italic,
            self.is_bold,
            self.font_color,
            round(self.rotate, 1),
            self.link_num
        ))

    def __repr__(self):
        return f"SpanStyle({self.__dict__})"
      
    def to_dict(self):
        return {
            "is_superscript": self.is_superscript,
            "y_offset": self.y_offset,
            "x_gap_with_prev": self.x_gap_with_prev,
            "font_size": self.font_size,
            "is_italic": self.is_italic,
            "is_bold": self.is_bold,
            "font_color": self.font_color,
            "rotate": self.rotate,
            "link_num": self.link_num
        }


# 중복되지 않는 스타일을 관리하고 각 스타일에 고유 ID를 부여하는 클래스
class StyleManager:
    def __init__(self):
        self.styles: Dict[int, SpanStyle] = {}
        self.style_to_id: Dict[SpanStyle, int] = {}
        self.counter = 0

    def getStyleId(self, style: SpanStyle) -> int:
        # 이미 등록된 스타일이면 기존 ID 반환
        if style in self.style_to_id:
            return self.style_to_id[style]
        else:
            # 새로운 스타일이면 ID 부여 후 저장
            style_id = self.counter
            self.styles[style_id] = style
            self.style_to_id[style] = style_id
            self.counter += 1
            return style_id

# 색상 정보 추출 (정수형 색상 값을 RGB 튜플로 변환)
def intToRgb(color_int):
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return (r / 255, g / 255, b / 255)

def extractFontColor(span: Dict) -> Tuple[float, float, float]:
    color = span.get("color", 0)
    return intToRgb(color)

# 폰트 크기 추출
def extractFontSize(span: Dict) -> float:
    return span.get("size", 0)

# 플래그 비트값에서 스타일 속성 추출
# 윗첨자: 1, 기울임: 2, 볼드: 16
# PyMuPDF span 객체의 flags 값을 사용
def extractFontFlags(span: Dict) -> Tuple[bool, bool, bool]:
    flags = span.get("flags", 0)
    # pymupdf 기준 superscript 판별은 부정확하므로 항상 False 반환
    is_superscript = False
    is_italic = bool(flags & 2)
    is_bold = bool(flags & 16)
    return is_superscript, is_italic, is_bold

# 회전 방향에 따라 라인 기준 위치와 origin의 거리 계산 (y_offset)
# 윗첨자 여부 판별에 사용
# 회전 방향마다 기준 축이 다르기 때문에 방향별로 처리함
def calculateYOffset(line_y_ref: float, span: Dict, bbox: List[float], rotate: float) -> float:
    origin = span.get("origin")
    if origin:
        origin_x, origin_y = origin[0], origin[1]
    else:
        # rotate 방향에 따라 fallback origin 위치 계산
        if rotate == 0:
            origin_x, origin_y = bbox[0], bbox[3]  # bottom-left
        elif rotate == 180:
            origin_x, origin_y = bbox[2], bbox[1]  # top-right
        elif rotate == 90:
            origin_x, origin_y = bbox[2], bbox[3]  # bottom-right
        elif rotate == 270:
            origin_x, origin_y = bbox[0], bbox[1]  # top-left
        else:
            origin_x, origin_y = bbox[0], bbox[3]  # default to bottom-left

    if rotate == 0:
        return line_y_ref - origin_y  # 아래에서 위로
    elif rotate == 180:
        return origin_y - line_y_ref  # 위에서 아래로
    elif rotate == 90:
        return line_y_ref - origin_x  # 오른쪽에서 왼쪽
    elif rotate == 270:
        return origin_x - line_y_ref  # 왼쪽에서 오른쪽
    else:
        return 0.0  # fallback

# 회전 방향에 따라 이전 span과의 거리 계산 (진행 방향 기준)
def calculateXGap(prev_bbox: List[float], curr_bbox: List[float], rotate: float) -> float:
    if not prev_bbox:
        return 0.0

    if rotate == 0:
        return curr_bbox[0] - prev_bbox[2]  # 좌→우
    elif rotate == 180:
        return prev_bbox[0] - curr_bbox[2]  # 우→좌
    elif rotate == 90:
        return curr_bbox[1] - prev_bbox[3]  # 상→하
    elif rotate == 270:
        return prev_bbox[1] - curr_bbox[3]  # 하→상
    else:
        return 0.0

# 하나의 span으로부터 스타일 객체 생성 + 현재 bbox 반환
# 라인 기준 위치(line_y_ref) 및 이전 span bbox 필요
def isSuperScript(y_offset: float, font_size: float) -> bool:
    return y_offset > font_size * 0.7

def createSpanStyle(span: Dict, line_y_ref: float, prev_bbox: List[float], rotate: float) -> Tuple[SpanStyle, List[float]]:
    bbox = span.get("bbox", [0, 0, 0, 0])
    font_size = extractFontSize(span)
    _, is_italic, is_bold = extractFontFlags(span)
    color_rgb = extractFontColor(span)
    y_offset = calculateYOffset(line_y_ref, span, bbox, rotate)
    x_gap = calculateXGap(prev_bbox, bbox, rotate)

    is_superscript_flag = isSuperScript(y_offset, font_size)

    style = SpanStyle(
        is_superscript=is_superscript_flag,
        y_offset=y_offset,
        x_gap_with_prev=x_gap,
        font_size=font_size,
        is_italic=is_italic,
        is_bold=is_bold,
        font_color=color_rgb,
        rotate=rotate,
        link_num= span.get("link_num", None)
    )
    return style, bbox

# 라인의 회전 방향에 따라 라인의 기준 위치값(y 또는 x)을 결정
# rotate=0 → 내림조가(ymax), rotate=90 → 오른\uc쪽(xmax) 등
def getLineReferenceY(line: Dict, rotate: float) -> float:
    bbox = line["bbox"]
    if rotate == 0:
        return bbox[3]  # bottom
    elif rotate == 180:
        return bbox[1]  # top
    elif rotate == 90:
        return bbox[2]  # right
    elif rotate == 270:
        return bbox[0]  # left
    else:
        return bbox[3]  # fallback

# 전체 block 리스트 순회하며 각 span에 style_id 부여 + style 사전 생성
# block → line → span 순으로 순회하며 스타일 분석
def assignSpanStyle(blocks: List[Dict]) -> Dict[int, SpanStyle]:
    style_manager = StyleManager()

    for block in blocks:
        if block.get("type") != 0:
            continue  # 텍스트 블록(type=0)만 처리

        for line in block.get("lines", []):
            rotate = dirToRotation(line["dir"])
            line_y_ref = getLineReferenceY(line, rotate)
            prev_bbox = None  # 이전 span의 bbox 저장

            for span in line.get("spans", []):
                # 현재 span에서 스타일 추출
                style, bbox = createSpanStyle(span, line_y_ref, prev_bbox, rotate)
                prev_bbox = bbox  # 후신 span을 위한 bbox 갱신

                # 스타일 ID 등록 및 span에 부여
                span["style_id"] = style_manager.getStyleId(style)

    return style_manager.styles


def assignSpanStyleTest(blocks):
    style_dict = assignSpanStyle(blocks)

    for style_id, style in style_dict.items():
        print(f"[{style_id}] {style}")

    for block in blocks:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                print(span.get("text", ""), f"[{span['style_id']}]")
