"""
콘솔 출력 유틸리티 모듈

PDF 번역 프로그램에서 사용되는 다양한 콘솔 출력 함수들을 제공합니다.
색상, 아이콘, 애니메이션을 포함한 사용자 친화적인 터미널 인터페이스를 구현합니다.
"""

import os
import time
import threading


class Colors:
    """ANSI 색상 코드 상수 클래스"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# =============================================================================
# 기본 메시지 출력 함수들
# =============================================================================

def print_header(text):
    """예쁜 헤더 출력"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_info(text):
    """정보 메시지 출력"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


def print_success(text):
    """성공 메시지 출력"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def ask_yes_no(question):
    """사용자에게 예/아니오 질문"""
    while True:
        print(f"{Colors.YELLOW}❓ {question} (y/n): {Colors.END}", end="")
        answer = input().lower().strip()
        if answer in ['y', 'yes', '예', 'ㅇ']:
            return True
        elif answer in ['n', 'no', '아니오', '아니요', 'ㄴ']:
            return False
        else:
            print_error("y(예) 또는 n(아니오)로 답해주세요.")


def print_error(text):
    """에러 메시지 출력"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    """경고 메시지 출력"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_processing(text):
    """진행상황 메시지 출력"""
    print(f"{Colors.BOLD}{Colors.YELLOW}🔄 {text}{Colors.END}")


# =============================================================================
# 구분선 및 레이아웃 함수들
# =============================================================================

def print_separator():
    """구분선 출력"""
    print(f"{Colors.CYAN}{'-'*60}{Colors.END}")


def print_subseparator():
    """작은 구분선 출력"""
    print(f"{Colors.CYAN}{'-'*40}{Colors.END}")


def clear_screen():
    """화면 클리어"""
    os.system('cls' if os.name == 'nt' else 'clear')


# =============================================================================
# 진행률 표시 함수들
# =============================================================================

def print_stage_progress(stage_name, current_stage, total_stages):
    """단계별 진행상황 출력"""
    print(f"\r\033[K{Colors.BOLD}{Colors.HEADER}▶ 단계 {current_stage}/{total_stages}: {stage_name}{Colors.END}")


def print_page_progress(current_page, total_pages):
    """페이지 진행상황 출력"""
    print(f"\r\033[K{Colors.GREEN}📝 페이지 {current_page}/{total_pages} 번역 완료{Colors.END}", end='', flush=True)


def print_detailed_progress(current_blocks, total_blocks, current_page, total_pages, stage_name="번역 중"):
    """블록 단위까지 포함한 세밀한 진행상황 출력"""
    if total_blocks == 0:
        overall_percent = 0
    else:
        overall_percent = int((current_blocks / total_blocks) * 100)
    
    print(f"\r\033[K{Colors.YELLOW}{stage_name}{Colors.END} {overall_percent:3d}% - {Colors.GREEN}페이지 {current_page}/{total_pages}{Colors.END}", end='', flush=True)


# =============================================================================
# 애니메이션 관련 함수들
# =============================================================================

# 애니메이션 패턴 상수
ANIMATION_PATTERNS = [
    ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],  # 스피너
    ["🌍", "🌎", "🌏"],  # 지구본 회전
    ["✨", "⭐", "🌟", "💫"]  # 반짝임
]

ANIMATION_MESSAGES = {
    "summary": [
        "문서 내용을 파악하고 있어요",
        "핵심 용어를 찾고 있어요",
        "요약 및 용어집 추출 중",
        "AI가 문서를 분석하고 있어요",
    ],
    "layout": [
        "문서 구조를 파악하고 있어요",
        "레이아웃 분석 중",
        "텍스트 블록을 분석하고 있어요",
        "페이지 레이아웃을 처리하고 있어요",
    ],
    "translation": [
        "AI가 열심히 번역하고 있어요",
        "번역 중",
        "잠시만 기다려주세요",
        "번역 작업 진행중"
    ]
}


def print_translation_animation(message, animation_type=0):
    """번역 중 애니메이션 출력 (단발성)"""
    pattern = ANIMATION_PATTERNS[animation_type % len(ANIMATION_PATTERNS)]
    
    for symbol in pattern:
        print(f"\r\033[K{Colors.CYAN}{symbol} {message}{Colors.END}", end='', flush=True)
        time.sleep(0.2)


def start_translation_animation(stage="translation"):
    """번역 애니메이션 시작 (백그라운드 스레드)"""
    animation_running = [True]  # 리스트로 감싸서 수정 가능하게
    
    def animate():
        pattern_idx = 0
        message_idx = 0
        counter = 0
        messages = ANIMATION_MESSAGES.get(stage, ANIMATION_MESSAGES["translation"])
        
        while animation_running[0]:
            pattern = ANIMATION_PATTERNS[pattern_idx]
            message = messages[message_idx]
            
            for symbol in pattern:
                if not animation_running[0]:
                    break
                print(f"\r\033[K{Colors.CYAN}{symbol} {message}{Colors.END}", end='', flush=True)
                time.sleep(0.3)
            
            counter += 1
            if counter % 5 == 0:  # 5번마다 패턴 변경
                pattern_idx = (pattern_idx + 1) % len(ANIMATION_PATTERNS)
            if counter % 8 == 0:  # 8번마다 메시지 변경
                message_idx = (message_idx + 1) % len(messages)
    
    thread = threading.Thread(target=animate, daemon=True)
    thread.start()
    
    return animation_running


def stop_animation(animation_running):
    """애니메이션 중지"""
    if animation_running:
        animation_running[0] = False
        time.sleep(0.5)  # 애니메이션이 완전히 멈출 때까지 대기
        print("\r\033[K", end='', flush=True)  # 애니메이션 텍스트 지우기