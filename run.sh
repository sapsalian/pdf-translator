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
        echo -e "${YELLOW}   Python 3.8 이상을 설치해주세요.${NC}"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION 감지됨${NC}"

# Python 버전 확인 (3.10 이상 필요)
REQUIRED_VERSION="3.10"
if $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ Python 버전이 요구사항을 만족합니다 (3.10 이상)${NC}"
else
    echo -e "${RED}❌ Python 3.10 이상이 필요합니다. 현재 버전: $PYTHON_VERSION${NC}"
    echo -e "${YELLOW}   Python 3.10 이상을 설치한 후 다시 시도해주세요.${NC}"
    exit 1
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
    read -p "가상환경을 자동으로 생성하고 활성화하시겠습니까? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 가상환경 생성 (없는 경우에만)
        if [ ! -d "venv" ]; then
            echo -e "${BLUE}📦 가상환경을 생성합니다...${NC}"
            $PYTHON_CMD -m venv venv --upgrade-deps
            if [ $? -ne 0 ]; then
                echo -e "${YELLOW}⚠️  --upgrade-deps 옵션으로 실패. 기본 방식으로 재시도...${NC}"
                $PYTHON_CMD -m venv venv
                if [ $? -ne 0 ]; then
                    echo -e "${RED}❌ 가상환경 생성에 실패했습니다.${NC}"
                    exit 1
                fi
            fi
            
            # pip 설치 확인 및 복구
            echo -e "${BLUE}🔧 pip 설치를 확인합니다...${NC}"
            source venv/bin/activate
            if ! python -m pip --version &> /dev/null; then
                echo -e "${YELLOW}⚠️  pip가 없습니다. ensurepip으로 설치합니다...${NC}"
                python -m ensurepip --upgrade
                if [ $? -ne 0 ]; then
                    echo -e "${RED}❌ pip 설치에 실패했습니다.${NC}"
                    echo -e "${YELLOW}   수동으로 pip를 설치해주세요: curl https://bootstrap.pypa.io/get-pip.py | python${NC}"
                    exit 1
                fi
            fi
            deactivate
        fi
        
        # 가상환경 활성화
        echo -e "${BLUE}🔧 가상환경을 활성화합니다...${NC}"
        source venv/bin/activate
        export VIRTUAL_ENV="$(pwd)/venv"
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
if ! $PYTHON_CMD -c "import pymupdf, openai, ultralytics, numpy" &> /dev/null; then
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
echo -e "${BLUE}🔑 OpenAI API 키 확인 중...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY 환경변수가 설정되지 않았습니다.${NC}"
    echo -e "${YELLOW}   다음 중 하나의 방법으로 설정해주세요:${NC}"
    echo -e "${YELLOW}   1. export OPENAI_API_KEY=\"your-api-key\"${NC}"
    echo -e "${YELLOW}   2. .env 파일에 OPENAI_API_KEY=your-api-key 추가${NC}"
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
    echo -e "${RED}❌ 프로그램 실행 중 오류가 발생했습니다. (종료 코드: $EXIT_CODE)${NC}"
fi

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}                   실행 완료                              ${NC}"
echo -e "${CYAN}============================================================${NC}"

exit $EXIT_CODE