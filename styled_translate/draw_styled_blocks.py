from typing import List, Dict, Tuple
import pymupdf
from styled_translate.get_font import getFontPath, getFontName
from styled_translate.assign_style import SpanStyle, dirToRotation
from text_edit.text_delete import deleteTextBlocks
from util.line_utils import calculateAverageGap

def getRotatedBbox(original_bbox, rotate):
  x0, y0, x1, y1 = original_bbox
  
  if rotate == 0:
    return (x0, y0, x1, y1)
  elif rotate == 180:
    return (x1, y1, x0, y0)
  elif rotate == 90:
    return (y1, x0, y0, x1)
  elif rotate == 270:
    return (y0, x1, y1, x0)

def movePosWithRotation(x, y, hor_offset, vert_offset, rotate):
  if rotate == 0:
    return (x + hor_offset, y - vert_offset)
  elif rotate == 180:
    return (x - hor_offset, y + vert_offset)
  elif rotate == 90:
    return (x - vert_offset, y - hor_offset)
  elif rotate == 270:
    return (x + vert_offset, y + hor_offset)
  
def getLineStartHor(block, line, styled_line, rotate):
    block_start_hor, _, block_end_hor, _ = getRotatedBbox(block["bbox"], rotate)
    line_start_hor, _, _, line_base_vert = getRotatedBbox(line["bbox"], rotate)  # 좌측 경계, 우측 경계, 상단 y 좌표
    
    is_center_aligned = block.get("align", "left") == "center"
    
    
    # 중앙 정렬인 경우 블락 중간 배치 기준 여백 적용, 아니면 line의 처음에서 시작
    if is_center_aligned:
        return block_start_hor + (block_end_hor - block_start_hor - styled_line["line_width"]) / 2
    else:
        return line_start_hor
    
def getDrawPosition(line_start_hor, line_base_vert, rel_x, rel_y, rotate):
    x, y = line_start_hor, line_base_vert
    
    if rotate == 90 or rotate == 270:
        x, y = line_base_vert, line_start_hor
        
    return movePosWithRotation(x, y, rel_x, rel_y, rotate)
        

def calculateExtraGap(block: Dict, selected_lines: List[Dict], original_avg_gap: float, rotate: int) -> float:
    """
    진행 방향에 맞춰 전체 block과 선택된 line 목록 기반으로 추가 gap 계산
    """
    block_bbox = block["bbox"]
    block_dim = (block_bbox[3] - block_bbox[1]) if rotate in (0, 180) else (block_bbox[2] - block_bbox[0])

    # 각 line의 수직 높이 합산
    lines_dim = 0
    for line in selected_lines:
        bbox = line["bbox"]
        dim = (bbox[3] - bbox[1]) if rotate in (0, 180) else (bbox[2] - bbox[0])
        lines_dim += dim

    num_lines = len(selected_lines)
    new_gap_total = block_dim + original_avg_gap - lines_dim
    return (new_gap_total / num_lines - original_avg_gap) if num_lines > 1 else 0 

def shiftLinesInDirection(lines: List[Dict], extra_gap: float, rotate: int) -> List[Dict]:
    """
    진행 방향 기준으로 bbox를 shift
    rotate: 0/180이면 y축 이동, 90/270이면 x축 이동
    """
    adjusted_lines = []
    shift = 0
    for line in lines:
        x0, y0, x1, y1 = line["bbox"]
        if rotate in (0, 180):
            new_bbox = [x0, y0 + shift, x1, y1 + shift]
        else:
            new_bbox = [x0 + shift, y0, x1 + shift, y1]
        adjusted_lines.append({
            "bbox": new_bbox,
            "dir": line["dir"]
        })
        shift += extra_gap
    return adjusted_lines

def adjustLinesWithGap(block: Dict, num_lines: int) -> List[Dict]:
    """
    block["lines"]에서 상위 num_lines개의 line만 남기고,
    진행 방향에 맞춰 bbox 간격 조정
    """
    lines = block.get("lines", [])
    if not lines or num_lines >= len(lines):
        return lines  # 그대로 반환

    selected_lines = lines[:num_lines]
    
    if len(selected_lines) == 0:
        return []

    # 진행 방향 결정
    dir = selected_lines[0]["dir"]
    rotate = dirToRotation(dir)

    original_avg_gap = calculateAverageGap(selected_lines, rotate)
    extra_gap = calculateExtraGap(block, selected_lines, original_avg_gap, rotate)

    return shiftLinesInDirection(selected_lines, extra_gap, rotate)


def drawStyledLines(block: Dict, style_dict: Dict[int, SpanStyle], page: pymupdf.Page):
    styled_lines = block.get("styled_lines", [])  # buildStyledLines 결과
    
    if (block.get("class_name") == "Text"):
        lines = adjustLinesWithGap(block, len(styled_lines))  # 각 줄의 bbox
    else:
        lines = block["lines"]  # 각 줄의 bbox
    
    if len(styled_lines) == 0:
        return

    for line, styled_line in zip(lines, styled_lines):

        dir = line["dir"]
        rotate = dirToRotation(dir)
        
        line_start_hor = getLineStartHor(block, line, styled_line, rotate)
        line_base_vert = getRotatedBbox(line["bbox"], rotate)[3]

        for span in styled_line["positioned_spans"]:
            style_id = span["style_id"]
            text = span["text"]
            rel_x = span["rel_x"]

            style = style_dict[style_id]
            font_path = getFontPath(style)
            font_name = getFontName(style)
            
            
            # print(text, style.x_gap_with_prev, style.y_offset, style.is_bold)

            x, y = getDrawPosition(line_start_hor, line_base_vert, rel_x, style.y_offset, rotate)
            
            # print(
            #     "point=" + f'({x}, {y})',
            #     "text=" + text,
            #     "fontfile=" + font_path,
            #     "fontname=" + font_name,
            #     "fontsize=" + str(style.font_size),
            #     "color=" + str(style.font_color),
            #     "rotate=" + str(style.rotate),
            #     )

            # 텍스트 삽입
            page.insert_text(
                point=(x, y),
                text=text,
                fontfile=font_path,
                fontname=font_name,
                fontsize=style.font_size,
                color=style.font_color,
                rotate=style.rotate,
            )

# 각 block의 styled_lines를 이용하여 page에 텍스트를 그리는 함수
def replaceTranslatedBlocks(blocks: List[Dict], style_dict: Dict[int, SpanStyle], page: pymupdf.Page):
    deleteTextBlocks(page, [block for block in blocks if block["to_be_translated"]])
    
    for block in blocks:
        if block["to_be_translated"]:
            drawStyledLines(block, style_dict, page)


def replaceTranslatedFile(page_infos, file_path, output_path):
    page_info_map = {page_info["page_num"]: page_info for page_info in page_infos}
    
    with pymupdf.open(file_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            page_info = page_info_map[page_num]
            
            blocks = page_info["blocks"]
            style_dict = page_info["style_dict"]
            
            replaceTranslatedBlocks(blocks, style_dict, page)
        
        doc.save(output_path, garbage=3, clean=True, deflate=True)
    
    

  