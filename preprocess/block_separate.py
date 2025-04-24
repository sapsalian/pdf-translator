import pymupdf
import re
from text_extract.text_extract import lineText
from util.line_utils import *
from util.block_utils import *


# 블록 다시 나누기 전, 한 라인 내에 단순 스페이스 이상으로 멀리 떨어져 있는 요소들은 따로 블락으로 나누는 전처리 하기.

# block 내의 line들을 순회하며, 윗 라인의 내용과 연결되지 않는 라인이 나오면 새로운 블락으로 끊기.
# 새로 끊긴 block의 리스트를 반환.
'''
기준1: 들여쓰기 되어 있는가? 즉, 윗 라인보다 시작지점이 문자 하나 크기 이상 더 오른쪽에 있는가.
기준2: 윗라인이 ".", ":", "!", 등 문장의 마침을 나타내는 특수문자로 끝나는가.
기준3: 윗라인의 너비가 block 너비 기준 70% 이하인가
기준4: 현재라인이 대문자로 시작하고, 두번째 문자는 소문자인가
기준5: 현재라인이 하이픈이나 불렛 포인트 등 리스트를 나타내는 특수문자로 시작하는가
기준6: 현재라인이 "1.", "2." 등 순서 있는 리스트의 형태로 시작하는가
'''


  
def is_indent(prev_line, line):
    # 현재 줄이 이전 줄보다 들여쓰기 되어 있는가(불릿포인트 제거했을 때 기준으로)
    # if (starts_with_bullet(None, prev_line) or starts_with_numbered_list(None, prev_line)):
    #   return False
    
    if isLinesStartWithSameX(prev_line, line):
      return False
    
    prev_x = prev_line["bbox"][0]
    line_x = line["bbox"][0]
    
    span = line["spans"][0]
    x0, y0, x1, y1 = span["bbox"]
    span_width = x1 - x0  
    avg_char_width = span_width / len(span["text"])
    
    return line_x - prev_x >= avg_char_width * 0.8

def ends_with_punctuation(prev_line, _, block_bbox, align):
    # 이전 줄이 마침 기호로 끝나는가(동시에 좌측 정렬일 때는 block 너비의 97% 이하여야 함.)
    
    text = "".join(span["text"] for span in prev_line["spans"]).strip()
    return text and text[-1] in ".:!?" and (align == ALIGN_CENTER or is_short_line(prev_line, _, block_bbox, 0.97))

# --- 블록 분리 여부 판단 함수 ---

def should_split_block(prev_line, line, block_bbox, align):
    # print (lineText(prev_line) + "////" + lineText(line))
    if align == ALIGN_CENTER:
      return any([
        ends_with_punctuation(prev_line, line, block_bbox, align),
        starts_with_bullet(prev_line, line),
        starts_with_numbered_list(prev_line, line, True) and not (isLineFull(prev_line, block_bbox) and isLinesStartWithSameX(prev_line, line, False)),
      ])

    # print(
    #   is_indent(prev_line, line),
    #   ends_with_punctuation(prev_line, line, block_bbox, align),
    #   is_short_line(prev_line, line, block_bbox),
    #   # starts_with_upper(prev_line, line),
    #   starts_with_bullet(prev_line, line),
    #   starts_with_numbered_list(prev_line, line, True) and not (isLineFull(prev_line, block_bbox) and isLinesStartWithSameX(prev_line, line, False))
    # )
    return any([
        is_indent(prev_line, line),
        ends_with_punctuation(prev_line, line, block_bbox, align),
        is_short_line(prev_line, line, block_bbox),
        # starts_with_upper(prev_line, line),
        starts_with_bullet(prev_line, line),
        starts_with_numbered_list(prev_line, line, True) and not (isLineFull(prev_line, block_bbox) and isLinesStartWithSameX(prev_line, line, False)),
    ])


# --- bbox 계산 함수 ---

def calculate_bbox(current_block_lines, original_block):
    # 상단 좌표: 첫 번째 줄 y0
    y0 = current_block_lines[0]["bbox"][1]
    # 하단 좌표: 마지막 줄 y3
    y3 = current_block_lines[-1]["bbox"][3]
    # 좌우 좌표는 기존 블록에서 유지
    x0 = original_block["bbox"][0]
    x2 = original_block["bbox"][2]
    return [x0, y0, x2, y3]


# --- 메인 블록 분리 함수 ---

def separateBlock(block):
    lines = block.get("lines", [])
    if not lines:
        return []

    separated_blocks = []
    current_block = [lines[0]]
    prev_line = lines[0]
    current_bbox = list(prev_line["bbox"])  # ← 리스트로 바꿔야 값 변경 가능

    def update_bbox(bbox1, bbox2):
        # bbox1을 bbox2를 포함하도록 확장
        return [
            min(bbox1[0], bbox2[0]),  # x0
            min(bbox1[1], bbox2[1]),  # y0
            max(bbox1[2], bbox2[2]),  # x1
            max(bbox1[3], bbox2[3]),  # y1
        ]
        
    def getRealBbox(current_bbox, original_bbox): 
        # 라인 따라 계산된 bbox에서 x 오른쪽 경계만 yolo의 것을 그대로 따르기
        return [
            current_bbox[0],  # x0
            current_bbox[1],  # y0
            original_bbox[2],  # x1
            current_bbox[3],  # y1
        ]
        

    for line in lines[1:]:
        if (should_split_block(prev_line, line, block["bbox"], block["align"]) if len(current_block) == 1 else should_split_block(prev_line, line, current_bbox, block["align"])):
            separated_blocks.append({
                "type": block.get("type", 0),
                "align": block.get("align", ALIGN_LEFT),
                "bbox": getRealBbox(current_bbox, block["bbox"]),
                "lines": current_block
            })
            current_block = [line]
            current_bbox = list(line["bbox"])  # 새 블록 시작 시 bbox 초기화
        else:
            current_block.append(line)
            current_bbox = update_bbox(current_bbox, line["bbox"])  # 기존 bbox 확장

        prev_line = line

    if current_block:
        separated_blocks.append({
            "type": block.get("type", 0),
            "align": block.get("align", ALIGN_LEFT),
            "bbox": getRealBbox(current_bbox, block["bbox"]),
            "lines": current_block
        })

    return separated_blocks

def extractTrueBlocks(blocks):
  new_blocks = []
  
  for b in blocks:  
    separatedBlocks = separateBlock(b)
    new_blocks.extend(separatedBlocks)
    
  return new_blocks

def drawBBox(bbox, page, radius=None):
  [x1,y1, x2,y2] = bbox
  [p1, p2] = [pymupdf.Point(x1,y1), pymupdf.Point(x2, y2)]
  bbox_rect = pymupdf.Rect(p1, p2)
  page.draw_rect(rect=bbox_rect, radius=radius)

if __name__ == "__main__":
  doc = pymupdf.open("b.pdf")

  for page in doc[23:24]:
    blocks = page.get_text("dict", flags=1, sort=True)["blocks"]
    blocks = extractTrueBlocks(blocks)
    for b in blocks:
      text = ""
      for l in b["lines"]:
        # drawBBox(l["bbox"],page)
        for s in l["spans"]:
          text += s["text"]
      # print(text)
      drawBBox(b["bbox"], page)
  doc.save("draw_bbox_b.pdf", garbage=3, clean=True, deflate=True)

  