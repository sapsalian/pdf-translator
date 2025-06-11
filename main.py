from styled_translate.translate_pdf import translatePdfInParallel
from preprocess.pdf_summary import summarizeTest
from text_extract.text_extract import printEscapedBlocksFromPdf
from preprocess.preprocess_test import preprocessedBlockDraw
import sys, os
import time

if __name__ == "__main__":

    start_time = time.time()  # 시작 시각 기록
  
    input_folder = "inputFile"
    
    # 인자 유무 확인
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        # 폴더 내 모든 PDF 파일 처리
        for filename in os.listdir(input_folder):
            if filename.lower().endswith(".pdf"):
                print(f"Processing: {filename}")
                # preprocessedBlockDraw(filename, "한국어", "English", 50)
                translatePdfInParallel(filename, "한국어", "English", 50)
    else:
        # 지정된 파일만 처리
        pdf_name = sys.argv[1]
        print(f"Processing: {pdf_name}")
        translatePdfInParallel(pdf_name, "한국어", "English", 50)
        # printEscapedBlocksFromPdf("inputFile/" +pdf_name, 3)
        # preprocessedBlockDraw(pdf_name, "한국어", "English", 50)
        
    end_time = time.time()  # 종료 시각 기록

    print(f"총 실행 시간: {end_time - start_time:.2f}초")
  