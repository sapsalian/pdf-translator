from styled_translate.translate_pdf import translatePdfInParallel
from preprocess.pdf_summary import summarizeTest
from text_extract.text_extract import printEscapedBlocksFromPdf
from preprocess.preprocess_test import preprocessedBlockDraw
import sys, os
import time

from util.console_utils import (Colors, print_header, print_info, print_success, 
                               print_error, print_processing, print_separator,
                               print_stage_progress, clear_screen, ask_yes_no)


def get_pdf_path():
    """사용자로부터 PDF 파일 경로 입력받기"""
    print_info("파일 경로를 입력하거나 파일을 드래그해서 끌어오세요:")
    print(f"{Colors.CYAN}📁 파일 경로: {Colors.END}", end="")
    pdf_path = input().strip().strip('"\'')  # 따옴표 제거
    
    if not pdf_path:
        print_error("파일 경로가 입력되지 않았습니다.")
        return None
    
    pdf_path = os.path.abspath(pdf_path)
    if not os.path.exists(pdf_path):
        print_error(f"파일을 찾을 수 없습니다: {pdf_path}")
        return None
    
    if not pdf_path.lower().endswith('.pdf'):
        print_error("PDF 파일만 처리할 수 있습니다.")
        return None
    
    return pdf_path


def translate_single_file(pdf_path):
    """단일 PDF 파일 번역 처리"""
    start_time = time.time()
    
    print_separator()
    print_processing(f"파일 처리 중: {os.path.basename(pdf_path)}")
    print_info(f"경로: {pdf_path}")
    print_separator()
    
    # 4단계 과정 시작
    print_stage_progress("문서 파악 및 용어집 추출 중", 1, 4)
    
    translatePdfInParallel(pdf_path, "English", "한국어", 50)
        
    end_time = time.time()

    # 번역 완료 안내
    dir_path = os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_filename = f"{base_name}-ko.pdf"
    
    print()  # 줄바꿈
    print_separator()
    print_success(f"번역 완료! 총 실행 시간: {end_time - start_time:.2f}초")
    print_info(f"번역된 파일이 저장되었습니다: {output_filename}")
    print_info(f"저장 위치: {dir_path}")
    print_separator()


def main():
    """메인 함수"""
    # 메인 프로그램 시작 전 화면 클리어
    clear_screen()
    print_header("PDF 파일 번역 프로그램")
    
    # 명령행 인자로 파일이 제공된 경우
    if len(sys.argv) >= 2 and sys.argv[1].strip():
        pdf_path = sys.argv[1].strip().strip('"\'')
        pdf_path = os.path.abspath(pdf_path)
        
        if os.path.exists(pdf_path) and pdf_path.lower().endswith('.pdf'):
            translate_single_file(pdf_path)
        else:
            print_error("올바른 PDF 파일 경로를 제공해주세요.")
            return
    
    # 번역 루프
    while True:
        # 명령행 인자가 없거나, 추가 파일을 번역하는 경우
        if len(sys.argv) < 2 or not sys.argv[1].strip():
            pdf_path = get_pdf_path()
        else:
            # 첫 번째 파일 번역 후 추가 파일 번역 여부 확인
            sys.argv = []  # 명령행 인자 초기화
            if not ask_yes_no("다른 파일을 더 번역하시겠습니까?"):
                break
            pdf_path = get_pdf_path()
        
        if pdf_path is None:
            if ask_yes_no("다시 시도하시겠습니까?"):
                continue
            else:
                break
        
        translate_single_file(pdf_path)
        
        # 번역 완료 후 추가 번역 여부 확인
        if not ask_yes_no("다른 파일을 더 번역하시겠습니까?"):
            break
    
    print()
    print_info("프로그램을 종료합니다. 감사합니다!")


if __name__ == "__main__":
    main()