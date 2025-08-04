from concurrent.futures import ThreadPoolExecutor
from preprocess.paged_info import getFileInfo
from preprocess.preprocess import preProcessPageInfos
from styled_translate.draw_styled_blocks import replaceTranslatedFile
from styled_translate.translate_with_style import translateWithStyle
from draw.draw_blocks import drawBlocks
from draw.draw_yolo_objs import drawYoloObjects
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.console_utils import print_stage_progress, print_page_progress, start_translation_animation, stop_animation


def translatePdf(pdf_path, src_lang, target_lang):
    file_info = getFileInfo(pdf_path, src_lang, target_lang)
    
    term_dict = file_info["term_dict"]
    
    page_infos = file_info["page_infos"]
    preProcessPageInfos(page_infos)

    for page_info in page_infos:
        translateWithStyle(page_info, term_dict, src_lang, target_lang)

    # 출력 경로를 같은 디렉토리에 파일명-ko.pdf로 설정
    dir_path = os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.join(dir_path, f"{base_name}-ko.pdf")
    replaceTranslatedFile(page_infos, pdf_path, output_path)


def translatePdfInParallel(pdf_path, src_lang, target_lang, max_workers=30):
    pdf_name = os.path.basename(pdf_path)
    
    # drawYoloObjects(pdf_path, pdf_name)

    # 파일 정보 로드 (YOLO 결과 및 페이지 분할 정보 등 포함)
    file_info = getFileInfo(pdf_path, src_lang, target_lang, max_workers=max_workers)
    
    term_dict = file_info["term_dict"]  # 용어집
    page_infos = file_info["page_infos"]  # 페이지별 정보
    total_pages = len(page_infos)
    
    preProcessPageInfos(page_infos, src_lang, target_lang)  # 텍스트 전처리 등

    print_stage_progress("번역 중", 3, 4)
    
    # 번역 애니메이션 시작
    animation_running = [start_translation_animation("translation")]  # 리스트로 감싸서 수정 가능하게
    
    # 페이지별 번역 상황을 추적하기 위한 카운터
    completed_pages = [0]  # 리스트로 감싸서 closure에서 수정 가능하게 함
    
    def translate_page_with_progress(page_info):
        translateWithStyle(page_info, term_dict, src_lang, target_lang)
        completed_pages[0] += 1
        # 애니메이션을 잠시 멈추고 진행상황 출력
        stop_animation(animation_running[0])
        print_page_progress(completed_pages[0], total_pages)
        print()  # 줄바꿈
        # 마지막 페이지가 아니면 애니메이션 다시 시작
        if completed_pages[0] < total_pages:
            animation_running[0] = start_translation_animation()
    
    # 병렬 번역 처리: 각 페이지에 대해 translateWithStyle(page_info, term_dict) 호출
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(translate_page_with_progress, page_infos)
    
    # 최종 애니메이션 중지
    stop_animation(animation_running[0])
        
    # drawBlocks(page_infos, pdf_path, pdf_name, block_mark= True, class_mark= True)

    print_stage_progress("번역본 파일을 생성하는 중", 4, 4)
    
    # 번역 결과로 새로운 PDF 생성 - 같은 디렉토리에 파일명-ko.pdf로 저장
    dir_path = os.path.dirname(pdf_path)
    base_name = os.path.splitext(pdf_name)[0]
    output_path = os.path.join(dir_path, f"{base_name}-ko.pdf")
    replaceTranslatedFile(page_infos, pdf_path, output_path)