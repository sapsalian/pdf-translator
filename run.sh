#!/bin/bash

# PDF 번역기 실행 스크립트
# 이 스크립트는 PDF 번역 프로그램을 쉽게 실행할 수 있도록 도와줍니다.

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 헤더 출력
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}                    PDF 번역기 시작                         ${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Python 버전 확인
echo -e "${BLUE}🐍 Python 버전 확인 중...${NC}"
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python이 설치되지 않았습니다.${NC}"
        echo -e "${YELLOW}   Python 3.10.12 이상을 설치해주세요.${NC}"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION 감지됨${NC}"

# Python 버전 확인 (3.10.12 이상 필요)
REQUIRED_VERSION="3.10.12"
PYTHON_OK=false

if $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 10, 12) else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ Python 버전이 요구사항을 만족합니다 (3.10.12 이상)${NC}"
    PYTHON_OK=true
else
    echo -e "${RED}❌ Python 3.10.12 이상이 필요합니다. 현재 버전: $PYTHON_VERSION${NC}"
fi

# ensurepip / venv 확인
NEED_VENV_FIX=false
if ! $PYTHON_CMD -c "import venv, ensurepip" &> /dev/null; then
    echo -e "${YELLOW}⚠️ Python은 설치되어 있으나 'venv' 또는 'ensurepip' 모듈이 없습니다.${NC}"
    NEED_VENV_FIX=true
fi

if [[ "$PYTHON_OK" == false || "$NEED_VENV_FIX" == true ]]; then
    echo ""
    echo -e "${CYAN}📦 Python 3.10.12 및 venv 모듈 자동 설치 옵션:${NC}"
    echo -e "${CYAN}   - Ubuntu/Debian: apt를 통한 설치 (python3.10 + venv + pip)${NC}"
    echo -e "${CYAN}   - CentOS/RHEL: yum/dnf를 통한 설치${NC}"
    echo -e "${CYAN}   - macOS: Homebrew를 통한 설치${NC}"
    echo ""
    read -p "Python 3.10.12와 필요한 모듈을 자동으로 설치하시겠습니까? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🔧 시스템 감지 및 Python 설치/수정 중...${NC}"

        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v apt &> /dev/null; then
                echo -e "${BLUE}📦 Ubuntu/Debian 감지됨. apt로 설치합니다...${NC}"
                sudo apt update
                sudo apt install -y python3.10 python3.10-venv python3.10-pip

                if command -v python3.10 &> /dev/null; then
                    PYTHON_CMD="python3.10"
                    echo -e "${GREEN}✅ Python 3.10.12 및 모듈 설치 완료${NC}"
                else
                    echo -e "${RED}❌ Python 3.10.12 설치 실패${NC}"
                    exit 1
                fi

            elif command -v yum &> /dev/null; then
                echo -e "${BLUE}📦 CentOS/RHEL 감지됨. yum으로 설치합니다...${NC}"
                sudo yum install -y python3.10 python3.10-pip
                PYTHON_CMD="python3.10"

            elif command -v dnf &> /dev/null; then
                echo -e "${BLUE}📦 Fedora/RHEL 감지됨. dnf로 설치합니다...${NC}"
                sudo dnf install -y python3.10 python3.10-pip
                PYTHON_CMD="python3.10"

            else
                echo -e "${RED}❌ 지원되지 않는 Linux 배포판입니다${NC}"
                exit 1
            fi

        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                echo -e "${BLUE}📦 macOS 감지됨. Homebrew로 설치합니다...${NC}"
                brew install python@3.10
                PYTHON_CMD="python3.10"
            else
                echo -e "${RED}❌ Homebrew가 설치되지 않았습니다${NC}"
                exit 1
            fi
        else
            echo -e "${RED}❌ 지원되지 않는 운영체제입니다${NC}"
            exit 1
        fi

        # 최종 버전 확인
        PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
        echo -e "${GREEN}✅ 업데이트된 Python 버전: $PYTHON_VERSION${NC}"
    else
        echo -e "${YELLOW}⚠️ 설치를 건너뜁니다. 수동으로 Python 3.10.12 및 venv 모듈을 설치해주세요.${NC}"
        exit 1
    fi
fi

# ensurepip 확인 (venv용 모듈 포함 여부 확인)
if ! $PYTHON_CMD -c "import ensurepip" &> /dev/null; then
    echo -e "${YELLOW}⚠️ ensurepip 모듈이 없습니다. venv 모듈 설치 필요...${NC}"
    if command -v apt &> /dev/null; then
        echo -e "${BLUE}📦 apt로 python3.10-venv 설치 시도 중...${NC}"
        sudo apt install -y python3.10-venv
    fi
fi


# 가상환경 확인 및 자동 설정
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  가상환경이 활성화되지 않았습니다.${NC}"
    echo ""
    echo -e "${CYAN}📚 가상환경의 장점:${NC}"
    echo -e "${CYAN}   - 시스템 Python과 패키지 충돌 방지${NC}"
    echo -e "${CYAN}   - 프로젝트별 독립적인 패키지 관리${NC}"
    echo -e "${CYAN}   - 시스템 환경을 깨끗하게 유지${NC}"
    echo ""
    read -p "운영체제에 맞는 가상환경(translator-venv)을 자동 생성하고 활성화할까요? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
            echo -e "${BLUE}📦 Windows 환경 감지됨. 가상환경 생성 및 pip 업그레이드...${NC}"
            $PYTHON_CMD -m venv translator-venv --system-site-packages --upgrade-deps
            if [ $? -ne 0 ]; then
                echo -e "${RED}❌ 가상환경 생성 실패 ${NC}"
                exit 1
            fi
            echo -e "${BLUE}🔧 가상환경을 활성화합니다...${NC}"
            source ./translator-venv/Scripts/activate
        else
            echo -e "${BLUE}📦 Linux/macOS 환경 감지됨. 가상환경 생성 및 pip 업그레이드...${NC}"
            $PYTHON_CMD -m venv translator-venv --system-site-packages --upgrade-deps
            if [ $? -ne 0 ]; then
                echo -e "${RED}❌ 가상환경 생성 실패 ($PYTHON_CMD -m venv translator-venv)${NC}"
                exit 1
            fi
            echo -e "${BLUE}🔧 가상환경을 활성화합니다...${NC}"
            source ./translator-venv/bin/activate
        fi

        export VIRTUAL_ENV="$(pwd)/translator-venv"
        export PATH="$VIRTUAL_ENV/bin:$PATH"
        echo -e "${GREEN}✅ 가상환경이 활성화되었습니다${NC}"
    else
        echo -e "${YELLOW}⚠️  전역 환경에서 실행합니다. 패키지 충돌이 발생할 수 있습니다.${NC}"
    fi
else
    echo -e "${GREEN}✅ 가상환경 활성화됨: $VIRTUAL_ENV${NC}"
fi


# requirements.txt 존재 확인
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt 파일을 찾을 수 없습니다.${NC}"
    echo -e "${YELLOW}   프로젝트 루트 디렉토리에서 실행해주세요.${NC}"
    exit 1
fi

# pip 명령어 결정
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    PIP_CMD="$PYTHON_CMD -m pip"
fi

# 의존성 설치 확인
echo -e "${BLUE}📦 의존성 패키지 확인 중...${NC}"
if ! $PYTHON_CMD -c "import pymupdf, openai, ultralytics, numpy, modal" &> /dev/null; then
    echo -e "${YELLOW}⚠️  일부 패키지가 설치되지 않았습니다.${NC}"
    read -p "지금 설치하시겠습니까? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}📦 패키지 설치 중...${NC}"
        $PIP_CMD install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}⚠️  $PIP_CMD로 실패. python -m pip으로 재시도...${NC}"
            $PYTHON_CMD -m pip install -r requirements.txt
            if [ $? -ne 0 ]; then
                echo -e "${RED}❌ 패키지 설치에 실패했습니다.${NC}"
                exit 1
            fi
        fi
        echo -e "${GREEN}✅ 패키지 설치 완료${NC}"
    else
        echo -e "${YELLOW}설치를 건너뜁니다. 오류가 발생할 수 있습니다.${NC}"
    fi
else
    echo -e "${GREEN}✅ 모든 필수 패키지가 설치되어 있습니다${NC}"
fi

# OpenAI API 키 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    read -p "OpenAI API 키를 입력하세요: " -r
    export OPENAI_API_KEY="$REPLY"
    echo -e "${GREEN}✅ API 키가 설정되었습니다${NC}"
else
    echo -e "${GREEN}✅ OpenAI API 키가 설정되어 있습니다${NC}"
fi

# main.py 존재 확인
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py 파일을 찾을 수 없습니다.${NC}"
    echo -e "${YELLOW}   프로젝트 루트 디렉토리에서 실행해주세요.${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${GREEN}🚀 PDF 번역기를 시작합니다...${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# 메인 프로그램 실행
$PYTHON_CMD main.py "$@"

# 실행 결과 확인
EXIT_CODE=$?
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 프로그램이 성공적으로 완료되었습니다!${NC}"
else
    echo -e "${RED}❌ 프로그램 실행 중 오류가 발생했습니다. \(종료 코드: $EXIT_CODE\)${NC}"
fi

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}                   실행 완료                              ${NC}"
echo -e "${CYAN}============================================================${NC}"

exit $EXIT_CODE
