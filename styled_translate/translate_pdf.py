from concurrent.futures import ThreadPoolExecutor
from preprocess.paged_info import getFileInfo
from preprocess.preprocess import preProcessPageInfos
from styled_translate.draw_styled_blocks import replaceTranslatedFile
from styled_translate.translate_with_style import translateWithStyle
from draw.draw_blocks import drawBlocks
from draw.draw_yolo_objs import drawYoloObjects


def translatePdf(pdf_name):
    file_path = "inputFile/" + pdf_name

    file_info = getFileInfo(file_path)
    
    term_dict = file_info["term_dict"]
    
    page_infos = file_info["page_infos"]
    preProcessPageInfos(page_infos)

    for page_info in page_infos:
        translateWithStyle(page_info, term_dict)

    output_path = "outputFile/output_" + pdf_name
    replaceTranslatedFile(page_infos, file_path, output_path)


def translatePdfInParallel(pdf_name, max_workers=30):
    file_path = "inputFile/" + pdf_name
    
    # drawYoloObjects(file_path, pdf_name)

    # 파일 정보 로드 (YOLO 결과 및 페이지 분할 정보 등 포함)
    file_info = getFileInfo(file_path, max_workers=max_workers)
    
    term_dict = file_info["term_dict"]  # 용어집
    page_infos = file_info["page_infos"]  # 페이지별 정보
    
    preProcessPageInfos(page_infos)  # 텍스트 전처리 등

    # 병렬 번역 처리: 각 페이지에 대해 translateWithStyle(page_info, term_dict) 호출
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(lambda page_info: translateWithStyle(page_info, term_dict), page_infos)
        
    # drawBlocks(page_infos, file_path, pdf_name, block_mark= True, class_mark= True)

    # 번역 결과로 새로운 PDF 생성
    output_path = "outputFile/output_" + pdf_name
    replaceTranslatedFile(page_infos, file_path, output_path)