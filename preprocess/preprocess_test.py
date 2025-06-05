from concurrent.futures import ThreadPoolExecutor
from preprocess.paged_info import getFileInfoWithoutSummary
from preprocess.preprocess import preProcessPageInfos
from styled_translate.draw_styled_blocks import replaceTranslatedFile
from styled_translate.translate_with_style import translateWithStyle
from draw.draw_blocks import drawBlocks
from draw.draw_yolo_objs import drawYoloObjects
import pymupdf

def preprocessedBlockDraw(pdf_name, max_workers=30):
    file_path = "inputFile/" + pdf_name
    
    # drawYoloObjects(file_path, pdf_name)

    # 파일 정보 로드 (YOLO 결과 및 페이지 분할 정보 등 포함)
    file_info = getFileInfoWithoutSummary(file_path)
    
    page_infos = file_info["page_infos"]  # 페이지별 정보
    
    
    
    preProcessPageInfos(page_infos)  # 텍스트 전처리 등
    
    for page_info in page_infos:
        print(len(page_info["blocks"]))
        print("--------------------------------")

    drawBlocks(page_infos, file_path, pdf_name, block_mark = True, line_mark= True)

