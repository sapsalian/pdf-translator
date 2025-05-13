import pymupdf
from preprocess.preprocess import preProcess
from preprocess.paged_info import getPageInfos
from text_extract.draw_bbox import drawBBox
from yolo.yolo_inference.model_init import initModel
from text_extract.text_extract import blockText
import sys, os
from draw_info.block_info import *
from concurrent.futures import ThreadPoolExecutor
import time
from styled_translate.translate_with_style import translateWithStyle
from styled_translate.draw_styled_blocks import replaceTranslatedFile

def preProcessPage(page_info):
  # read page text as a dictionary, suppressing extra spaces in CJK fonts
    blocks = preProcess(page_info)
    # blocks = page.get_text("dict", flags=1, sort=True)["blocks"] 
    
    translateWithStyle(page_info)
    
    # for b in blocks:
        # print(b)
        # print(b["bbox"])
        # drawBBox(b["bbox"], page)
        # drawAlignmentLabel(page, b)
        # drawClassNameLable(page, b)
      
        # for l in b["lines"]:
            # drawBBox(l["bbox"], page, 0.1)  
            # for s in l["spans"]:   
              # drawBBox(s["bbox"], page, 0.2)
            
     # blocks = detect_objects_from_page(page)odel)

        # print(blockText(b))
      
        # for l in b["lines"]:
            # drawBBox(l["bbox"], page, 0.1)  
            # for s in l["spans"]:   
            #   drawBBox(s["bbox"], page, 0.2)
            
      


def makeOutputUsingExecutor(pdf_name):
    file_path = "inputFile/" + pdf_name

    page_infos = getPageInfos(file_path)
    
    def process_page(page_info):
        preProcessPage(page_info)

    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(process_page, page_infos)
    
    output_path = "outputFile/output_" + pdf_name
    replaceTranslatedFile(page_infos, file_path, output_path)
    

    

def makeOutput(pdf_name):
    file_path = "inputFile/" + pdf_name

    page_infos = getPageInfos(file_path)
  
    for page_info in page_infos:
        preProcessPage(page_info)
        
    output_path = "outputFile/output_" + pdf_name
    replaceTranslatedFile(page_infos, file_path, output_path)
        
    
    



if __name__ == "__main__":

    start_time = time.time()  # 시작 시각 기록
  
    input_folder = "inputFile"
    
    # 인자 유무 확인
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        # 폴더 내 모든 PDF 파일 처리
        for filename in os.listdir(input_folder):
            if filename.lower().endswith(".pdf"):
                print(f"Processing: {filename}")
                makeOutputUsingExecutor(filename)
    else:
        # 지정된 파일만 처리
        pdf_name = sys.argv[1]
        print(f"Processing: {pdf_name}")
        makeOutputUsingExecutor(pdf_name)
        
    end_time = time.time()  # 종료 시각 기록

    print(f"총 실행 시간: {end_time - start_time:.2f}초")
  