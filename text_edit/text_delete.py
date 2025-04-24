import pymupdf


def bbox_to_quad(bbox):
    """
    bbox (x0, y0, x1, y1)를 quad 4점 좌표로 변환
    시계방향 기준: 좌상단 → 우상단 → 우하단 → 좌하단

    Returns:
        list of 4 tuples: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    """
    x0, y0, x1, y1 = bbox
    return pymupdf.Quad(
        (x0, y0),  # 좌상단
        (x1, y0),  # 우상단
        (x1, y1),  # 우하단
        (x0, y1),  # 좌하단
    )

def deleteTextBlocks(page, blocks):
  for b in blocks:
    quad = bbox_to_quad(b["bbox"])
    page.add_redact_annot(quad)
    
  page.apply_redactions(0)
  
  

if __name__ == "__main__":
  doc = pymupdf.open("a.pdf")
  for page in doc:
      text_to_delete = page.search_for("If you want to make money", quads=True)
      if(text_to_delete):
          for quad in text_to_delete:
              page.add_redact_annot(quad)
          page.apply_redactions(0)

  doc.save("new.pdf", garbage=3, clean=True, deflate=True)