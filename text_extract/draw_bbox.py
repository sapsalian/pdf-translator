import pymupdf

from draw.draw_bbox import drawBBox

def blockText(block):
  text = ""
  for line in block["lines"]:
    for span in line["spans"]:
      text += span["text"]
  return text

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