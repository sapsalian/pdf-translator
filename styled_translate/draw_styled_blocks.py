from typing import List, Dict, Tuple
import pymupdf
from styled_translate.get_font import getFontPath, getFontName
from styled_translate.assign_style import SpanStyle
from text_extract.text_extract import blockText


# 각 block의 styled_lines를 이용하여 page에 텍스트를 그리는 함수
def renderStyledSpans(blocks: List[Dict], style_dict: Dict[int, SpanStyle], page: pymupdf.Page):
    for block in blocks:
        lines = block["lines"]  # 각 줄의 bbox
        styled_lines = block["styled_lines"]  # buildStyledLines 결과
        is_center_aligned = block.get("align", "left") == "center"
        block_x0, _, block_x1, _ = block["bbox"]

        for line, styled_line in zip(lines, styled_lines):
            line_bbox = line["bbox"]
            line_x0, _, line_x1, line_y0 = line_bbox  # 좌측 경계, 우측 경계, 상단 y 좌표
            baseline_y = line_y0
            line_width = styled_line["line_width"]

            # 중앙 정렬인 경우 여백 적용, 아니면 좌측 정렬
            if is_center_aligned:
                print(line_x0)
                line_start_x = block_x0 + (block_x1 - block_x0 - line_width) / 2
            else:
                line_start_x = line_x0

            for span in styled_line["positioned_spans"]:
                style_id = span["style_id"]
                text = span["text"]
                rel_x = span["rel_x"]

                style = style_dict[style_id]
                font_path = getFontPath(style)
                font_name = getFontName(style)
                
                
                # print(text, style.x_gap_with_prev, style.y_offset, style.is_bold)

                x = line_start_x + rel_x
                y = baseline_y - style.y_offset  # y_offset 적용 (기본적으로 line의 y0 기준)
                
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

  