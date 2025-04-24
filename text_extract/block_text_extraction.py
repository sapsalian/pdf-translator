import pymupdf


doc = pymupdf.open("b.pdf")

def extractBBoxText(bbox, page, radius=None):
  [x1,y1, x2,y2] = bbox
  [p1, p2] = [pymupdf.Point(x1,y1), pymupdf.Point(x2, y2)]
  bbox_rect = pymupdf.Rect(p1, p2)
  text = page.get_text("text", clip=bbox_rect, flags=11)
  print(text)
  

for page in doc[6:7]:
  # read page text as a dictionary, suppressing extra spaces in CJK fonts
  blocks = page.get_text("dict", flags=11, sort=True)["blocks"] 
  for b in blocks: 
      # extractBBoxText(b["bbox"], page)
    
      for l in b["lines"]:
          extractBBoxText(b["bbox"], page) 
          # for s in l["spans"]:   
          #   extractBBoxText(b["bbox"], page)