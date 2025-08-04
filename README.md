# PDF 번역기 🔄📄

AI 기반 PDF 문서 번역 도구입니다. 영어 PDF 문서를 한국어로 자동 번역하며, 원본 레이아웃과 스타일을 최대한 유지합니다.

## ✨ 주요 기능

- 🎯 **고품질 번역**: OpenAI GPT 모델을 활용한 정확한 번역
- 🎨 **레이아웃 보존**: 원본 문서의 레이아웃, 폰트, 스타일, 링크 등을 유지
- 🎯 **용어집 관리**: 문서별 핵심 용어를 자동 추출하여 일관된 번역

## 🚀 빠른 시작

### 간편 실행 (권장) 🎯

가장 쉬운 방법! 모든 설정을 자동으로 처리해줍니다:

```bash
git clone https://github.com/sapsalian/pdf-translator.git
cd pdf-translator
./run.sh
```

스크립트가 자동으로 다음을 처리합니다:

- Python 환경 확인
- 패키지 설치
- OpenAI API 키 설정 안내
- 프로그램 실행

### 수동 설치 및 실행

세부 설정을 직접 관리하고 싶다면:

#### 1. 저장소 클론

```bash
git clone https://github.com/your-username/pdfTranslate.git
cd pdfTranslate
```

#### 2. 가상환경 설정 (권장)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
```

#### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

#### 4. OpenAI API 키 설정

환경변수로 설정:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

또는 `.env` 파일 생성:

```
OPENAI_API_KEY=your-api-key-here
```

#### 5. 실행

```bash
python main.py
```

## 📋 시스템 요구사항

### Python 패키지

- Python 3.8 이상
- PyMuPDF (PDF 처리)
- OpenAI (AI 번역)
- Ultralytics (YOLO 모델)
- NumPy, Pydantic 등

### 시스템 의존성

- **Linux/macOS**: 대부분 기본 설치됨
- **Windows**: 추가 설정 필요 없음

## 🎯 사용법

### 기본 사용법

1. 프로그램 실행
2. PDF 파일 경로 입력 또는 드래그 앤 드롭
3. 번역 과정 4단계 진행:
   - 📊 **1단계**: 문서 파악 및 용어집 추출
   - 🔍 **2단계**: 레이아웃 분석
   - 🔄 **3단계**: AI 번역
   - 💾 **4단계**: 번역본 파일 생성
4. 완료 후 `원본파일명-ko.pdf` 형태로 저장

### 연속 번역

번역 완료 후 "다른 파일을 더 번역하시겠습니까?"에서 'y'를 입력하면 계속해서 다른 파일을 번역할 수 있습니다.

## 📁 프로젝트 구조

```
pdfTranslate/
├── main.py                    # 메인 실행 파일
├── requirements.txt           # Python 의존성
├── run.sh                    # 실행 스크립트
├── README.md                 # 이 파일
├── util/                     # 유틸리티 함수들
├── preprocess/              # 전처리 모듈
├── styled_translate/        # 스타일 보존 번역
├── text_extract/           # 텍스트 추출
├── yolo/                   # YOLO 모델 추론
└── outputFile/             # 번역된 파일 저장소
```

## 🔧 고급 설정

### 번역 언어 변경

`main.py`에서 언어 설정을 변경할 수 있습니다:

```python
translatePdfInParallel(pdf_path, "English", "한국어", 50)
# 첫 번째: 원본 언어, 두 번째: 번역 언어, 세 번째: 병렬 처리 수
```

### 성능 조정

병렬 처리 수를 조정하여 성능을 최적화할 수 있습니다:

- 더 빠른 처리: 숫자를 높임 (더 많은 CPU/메모리 사용)
- 안정적인 처리: 숫자를 낮춤 (리소스 절약)

## 🚨 문제 해결

### 일반적인 문제들

1. **OpenAI API 키 오류**

   - API 키가 올바르게 설정되었는지 확인
   - 계정에 충분한 크레딧이 있는지 확인

2. **PDF 읽기 오류**

   - PDF 파일이 손상되지 않았는지 확인
   - 파일 경로에 특수문자가 없는지 확인

### 로그 및 디버깅

문제 발생 시 다음을 확인하세요:

- 콘솔 출력 메시지
- 입/출력 파일 권한
- 네트워크 연결 (OpenAI API 호출용)

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 AGPL-3.0 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

문제가 있으시면 GitHub Issues에 등록해 주세요.

---

⭐ **이 프로젝트가 도움이 되셨다면 스타를 눌러주세요!**
