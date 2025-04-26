import pymupdf
from preprocess.continuos_block_merge import mergeContinuosBlocks
from preprocess.block_separate import extractTrueBlocks
from preprocess.line_preprocess import linePreprocess
from preprocess.block_align_check import assignAlignToBlocks
from preprocess.bbox_adjust import adjustBlocksFromYolo
from yolo.yolo_inference.detection import detect_objects_from_page

'''
1. 블록 병합
2. 라인 병합
3. 블록 다시 나누기
'''


'''---------------------preprocess-----------------------'''

def preProcess(page):
  blocks = page.get_text("dict", flags=1, sort=True)["blocks"]
  blocks = mergeContinuosBlocks(blocks)
  blocks = linePreprocess(blocks)
  
  # yolo_objects = detect_objects_from_page(page)
  # adjustBlocksFromYolo(blocks, yolo_objects)
  
  assignAlignToBlocks(blocks) 
  # blocks = extractTrueBlocks(blocks) 
  
  return blocks


'''-----------------------utility----------------------'''

def drawBBox(bbox, page, radius=None):
  [x1,y1, x2,y2] = bbox
  [p1, p2] = [pymupdf.Point(x1,y1), pymupdf.Point(x2, y2)]
  bbox_rect = pymupdf.Rect(p1, p2)
  page.draw_rect(rect=bbox_rect, radius=radius)
  
  
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

'''----------------main----------------------------------'''

if __name__ == "__main__":
  doc = pymupdf.open("b.pdf")
  
  for page in doc:
    # read page text as a dictionary, suppressing extra spaces in CJK fonts
    blocks = preProcess(page)
        
    for b in blocks:
        drawBBox(b["bbox"], page)
        # print(blockText(b))
      
        # for l in b["lines"]:
        #     drawBBox(l["bbox"], page, 0.1)  
            # for s in l["spans"]:   
            #   drawBBox(s["bbox"], page, 0.2)
      
  doc.save("_b.pdf", garbage=3, clean=True, deflate=True)
  