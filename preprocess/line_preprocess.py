import pymupdf

'''
같은 줄 내 bbox간 거리 멀지 않은 애들 한 line으로 묶어주는 작업 이후,
block preprocess에서, line사이 거리가 먼애들은 다른 블락으로 분리해주기.
'''

def lineText(line) :
  text = ""
  for s in line["spans"]:
      text += s["text"]
  return text

def blockText(block):
  text = ""
  for line in block["lines"]:
    text += lineText(line)
  return text

# 블락 내에 50% 이상 겹치는 line들 병합
def mergeLinesWithOverlap(block):
    lines = block["lines"]
    if not lines:
        return []

    merged_lines = []
    current_line = lines[0]

    for next_line in lines[1:]:
        # 이전 줄과 다음 줄의 마지막/첫 span
        cur_span = current_line["spans"][-1]
        next_span = next_line["spans"][0]

        # 조건 1: y축 방향으로 충분히 겹치는가?
        y0_a, y3_a = current_line["bbox"][1], current_line["bbox"][3]
        y0_b, y3_b = next_line["bbox"][1], next_line["bbox"][3]

        # 두 bbox의 y축 overlap 계산
        overlap = max(0, min(y3_a, y3_b) - max(y0_a, y0_b))

        # 두 라인 중 높이가 더 낮은 라인을 기준으로 겹친 비율 계산
        height_a = y3_a - y0_a
        height_b = y3_b - y0_b
        min_height = min(height_a, height_b)

        significant_y_overlap = overlap >= min_height * 0.2

        # 조건 2: x 간격이 폰트 크기 기준 허용 범위 내
        x_gap = next_line["bbox"][0] - current_line["bbox"][2]
        tab_threshold = max(cur_span["size"], next_span["size"]) * 2.5
        close_x = -tab_threshold <= x_gap <= tab_threshold
        
        
        # print(min_height, overlap, x_gap, tab_threshold, lineText(next_line))

        if significant_y_overlap and close_x:
            # 병합
            current_line["spans"].extend(next_line["spans"])
            current_line["bbox"] = (
                current_line["bbox"][0],                              # x0 유지
                min(current_line["bbox"][1], next_line["bbox"][1]),  # y0 상단으로 확장
                next_line["bbox"][2],                                # x2 확장
                max(current_line["bbox"][3], next_line["bbox"][3])   # y3 하단으로 확장
            )
        else:
            merged_lines.append(current_line)
            current_line = next_line

    merged_lines.append(current_line)
    block["lines"] = merged_lines
    return block
  
def linePreprocess(blocks):
  # block = mergeLinesWithCloseGap(block)
    new_blocks = []
    
    for b in blocks: 
        new_blocks.append(mergeLinesWithOverlap(b))
  
    return new_blocks


def drawBBox(bbox, page, radius=None):
  [x1,y1, x2,y2] = bbox
  [p1, p2] = [pymupdf.Point(x1,y1), pymupdf.Point(x2, y2)]
  bbox_rect = pymupdf.Rect(p1, p2)
  page.draw_rect(rect=bbox_rect, radius=radius)

if __name__ == "__main__":
  doc = pymupdf.open("b.pdf")
  
  for page in doc[23:24]:
    # read page text as a dictionary, suppressing extra spaces in CJK fonts
    blocks = page.get_text("dict", flags=1, sort=True)["blocks"]
    blocks = linePreprocess(blocks)
        
    for b in blocks:
        drawBBox(b["bbox"], page)
        print(blockText(b), b["bbox"])
      
        # for l in b["lines"]:
            # drawBBox(l["bbox"], page, 0.1)  
            # for s in l["spans"]:   
            #   drawBBox(s["bbox"], page, 0.2)
      
  doc.save("draw_bbox_b.pdf", garbage=3, clean=True, deflate=True)
  