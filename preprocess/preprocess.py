import pymupdf
from preprocess.continuos_block_merge import mergeContinuosBlocks
from preprocess.block_separate import extractTrueBlocks
from preprocess.line_preprocess import mergeContinuosLines
from preprocess.block_align_check import assignAlignToBlocks
from preprocess.bbox_adjust import adjustBlocksFromYolo
from preprocess.assign_classname import assignClassNameToBlocks
from preprocess.split_special_blocks import splitSpecialBlocks
from preprocess.clean_blocks import cleanBlocks



def preProcess(page_info):
    blocks = page_info.get("blocks", [])
    yolo_objects = page_info.get("yolo_objects", [])
    links = page_info.get("links", [])
    
    blocks = cleanBlocks(blocks)
    
    assignClassNameToBlocks(blocks, yolo_objects)
    
    blocks = mergeContinuosBlocks(blocks)
    blocks = mergeContinuosLines(blocks)
    
    blocks = splitSpecialBlocks(blocks)
    
    assignAlignToBlocks(blocks) 
    
    blocks = extractTrueBlocks(blocks) 
    
    adjustBlocksFromYolo(blocks, yolo_objects)
    
    page_info["blocks"] = blocks


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


def preProcessPageInfos(page_infos):
    for page_info in page_infos:
        preProcess(page_info)
  