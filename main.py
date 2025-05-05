import pymupdf
from preprocess.preprocess import preProcess
from text_extract.draw_bbox import drawBBox
from yolo.yolo_inference.model_init import initModel
from text_extract.text_extract import blockText
import sys, os
from draw_info.block_info import *
import threading
from concurrent.futures import ThreadPoolExecutor
import time
from styled_translate.translate_with_style import translateWithStyle

def preProcessPage(page, model):
  # read page text as a dictionary, suppressing extra spaces in CJK fonts
    blocks = preProcess(page, model)
    # blocks = page.get_text("dict", flags=1, sort=True)["blocks"] 
    
    translateWithStyle(blocks, page)
    
    # for b in blocks:
        # print(b)
        # print(b["bbox"])
        # drawBBox(b["bbox"], page)
        # drawAlignmentLabel(page, b)
        # drawClassNameLable(page, b)
      
        # for l in b["lines"]:
        #     drawBBox(l["bbox"], page, 0.1)  
            # for s in l["spans"]:   
              # drawBBox(s["bbox"], page, 0.2)
            
     # blocks = detect_objects_from_page(page)
    
    # for b in blocks:
    #     print(b["bbox"], b["class_name"])
    #     drawBBox(b["bbox"], page)
    #     draw_alignment_label(page, b)
        # print(blockText(b))
      
        # for l in b["lines"]:
            # drawBBox(l["bbox"], page, 0.1)  
            # for s in l["spans"]:   
            #   drawBBox(s["bbox"], page, 0.2)
      
'''

def makeOutputUsingThreads(pdf_name):
  doc = pymupdf.open("inputFile/" + pdf_name)
  
  model = initModel()
  
  threads = []
  for page in doc:
    t = threading.Thread(target=preProcessPage, args=(page, model))
    threads.append(t)
    t.start()
    
  for t in threads:
    t.join()
    
  doc.save("outputFile/output_" + pdf_name, garbage=3, clean=True, deflate=True)

'''

def makeOutputUsingExecutor(pdf_name):
    doc = pymupdf.open("inputFile/" + pdf_name)
    pages = list(doc)

    model = initModel()
    
    def process_page(page):
        preProcessPage(page, model)

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(process_page, pages)

    doc.save("outputFile/output_" + pdf_name, garbage=3, clean=True, deflate=True)
    

def makeOutput(pdf_name):
  doc = pymupdf.open("inputFile/" + pdf_name)
  
  model = initModel()
  
  for page in doc[2:3]:
    preProcessPage(page, model)
    
    
  doc.save("outputFile/output_" + pdf_name, garbage=3, clean=True, deflate=True)



if __name__ == "__main__":

    start_time = time.time()  # 시작 시각 기록
  
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
        
    end_time = time.time()  # 종료 시각 기록

    print(f"총 실행 시간: {end_time - start_time:.2f}초")
  