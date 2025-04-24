import pymupdf
from preprocess.preprocess import preProcess
from text_extract.draw_bbox import drawBBox
import sys, os

def makeOutput(pdf_name):
  doc = pymupdf.open("inputFile/" + pdf_name)
  
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
      
  doc.save("output_" + pdf_name, garbage=3, clean=True, deflate=True)



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
  