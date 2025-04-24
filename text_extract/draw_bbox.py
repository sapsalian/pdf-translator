import pymupdf

def blockText(block):
  text = ""
  for line in block["lines"]:
    for span in line["spans"]:
      text += span["text"]
  return text

def drawBBox(bbox, page, radius=None):
  [x1,y1, x2,y2] = bbox
  [p1, p2] = [pymupdf.Point(x1,y1), pymupdf.Point(x2, y2)]
  bbox_rect = pymupdf.Rect(p1, p2)
  page.draw_rect(rect=bbox_rect, radius=radius)
  
if __name__ == "__main__":
  doc = pymupdf.open("e.pdf")
  for page in doc:
    # read page text as a dictionary, suppressing extra spaces in CJK fonts
    blocks = page.get_text("dict", flags=1, sort=True)["blocks"] 
    for b in blocks: 
        # print(blockText(b))
        drawBBox(b["bbox"], page)
        print(b["bbox"], blockText(b))
      
        # for l in b["lines"]:
        #     drawBBox(l["bbox"], page, 0.1)  
            # for s in l["spans"]:   
            #   drawBBox(s["bbox"], page, 0.2)
      
  doc.save("draw_bbox_e.pdf", garbage=3, clean=True, deflate=True)