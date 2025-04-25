import pymupdf
from preprocess.preprocess import preProcess
from text_extract.draw_bbox import drawBBox
from yolo.yolo_inference.detection import detect_objects_from_page
import sys, os

def draw_alignment_label(page, block, font_size=8):
    align = block.get("align", "")
    if not align:
        return

    x0, y0, _, _ = block["bbox"]
    label_pos = (x0, y0 - font_size - 1)  # 블럭 상단 바로 위

    page.insert_text(
        label_pos,
        align.upper(),  # 예: CENTER, LEFT, RIGHT
        fontsize=font_size,
        fill=(1, 0, 0),  # 빨간색
    )
    
def makeOutput(pdf_name):
  doc = pymupdf.open("inputFile/" + pdf_name)
  
  for page in doc:
    # read page text as a dictionary, suppressing extra spaces in CJK fonts
    # blocks = preProcess(page)
    # blocks = page.get_text("dict", flags=1, sort=True)["blocks"] 
    
    blocks = detect_objects_from_page(page)
    
    for b in blocks:
        print(b["bbox"])
        drawBBox(b["bbox"], page)
        # draw_alignment_label(page, b)
        # print(blockText(b))
      
        # for l in b["lines"]:
        #     drawBBox(l["bbox"], page, 0.1)  
            # for s in l["spans"]:   
            #   drawBBox(s["bbox"], page, 0.2)
      
  doc.save("outputFile/output_" + pdf_name, garbage=3, clean=True, deflate=True)


if __name__ == "__main__":
    input_folder = "inputFile"
    
    # 인자 유무 확인
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        # 폴더 내 모든 PDF 파일 처리
        for filename in os.listdir(input_folder):
            if filename.lower().endswith(".pdf"):
                print(f"Processing: {filename}")
                makeOutput(filename)
    else:
        # 지정된 파일만 처리
        pdf_name = sys.argv[1]
        print(f"Processing: {pdf_name}")
        makeOutput(pdf_name)
  