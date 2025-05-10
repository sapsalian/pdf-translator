from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pymupdf 
import numpy as np
from ultralytics import YOLO  
import os

app = FastAPI()  # FastAPI 앱 생성

# YOLO 모델에서 사용될 클래스 ID → 이름 매핑
CATEGORY_ID_TO_NAME = {
    0: "Caption",
    1: "Footnote",
    2: "Formula",
    3: "List-item",
    4: "Page-footer",
    5: "Page-header",
    6: "Picture",
    7: "Section-header",
    8: "Table",
    9: "Text",
    10: "Title"
}

def initModel():
    """
    YOLO 모델 초기화 함수.
    요청마다 이 함수를 호출해 YOLO 모델을 새로 로드합니다.
    """
    model_path = os.path.join(os.path.dirname(__file__), 'model', 'best.pt')
    model = YOLO(model_path)
    return model

def detectObjectFromPage(page, model):
    """
    PDF 페이지에서 객체 탐지를 수행하는 함수.
    
    Args:
        page (pymupdf.Page): PDF 페이지 객체
        model (YOLO): YOLO 모델 객체

    Returns:
        list: 탐지된 객체 정보의 리스트
    """
    # PDF 페이지를 이미지(pixmap)로 렌더링 (150 DPI 해상도)
    pix = page.get_pixmap(dpi=150)
    
    # pixmap 데이터를 numpy 배열로 변환 (H, W, C)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    
    # RGBA 이미지일 경우 RGB로 변환 (알파 채널 제거)
    if pix.n == 4:
        img = img[:, :, :3]

    # YOLO로 이미지에서 객체 탐지 수행
    results = model(img)
    
    output = []
    scale = 72 / 150  # PDF 좌표계(72 DPI)로 변환하기 위한 스케일

    # YOLO 탐지 결과 순회
    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])  # 클래스 ID
            conf = float(box.conf[0])  # 신뢰도
            xyxy = box.xyxy[0].tolist()  # 바운딩 박스 좌표 [x1, y1, x2, y2]

            output.append({
                "class_id": class_id,
                "class_name": CATEGORY_ID_TO_NAME.get(class_id, "unknown"),
                "confidence": round(conf, 4),
                "bbox": [
                    round(xyxy[0] * scale, 2),
                    round(xyxy[1] * scale, 2),
                    round(xyxy[2] * scale, 2),
                    round(xyxy[3] * scale, 2)
                ]
            })

    return output

@app.post("/detect")
async def detect_objects_in_pdf(pdf_file: UploadFile = File(...)):
    """
    FastAPI 엔드포인트: 업로드된 PDF 파일에서 각 페이지의 YOLO 탐지 결과 반환.
    
    Args:
        pdf_file (UploadFile): 클라이언트로부터 업로드된 PDF 파일

    Returns:
        JSONResponse:
        - 성공 시:
            [
                {
                    "page_num": <페이지 번호 (1부터 시작)>,
                    "objects": [
                        {
                            "class_id": <YOLO 클래스 ID (숫자)>,
                            "class_name": <클래스 이름 (예: 'Title', 'Text')>,
                            "confidence": <탐지 신뢰도 (0~1 사이, 소수점 4자리)>,
                            "bbox": [x1, y1, x2, y2]  # PDF 좌표계 기준 바운딩 박스 (좌상단, 우하단)
                        },
                        ...
                    ]
                },
                ...
            ]
        
        - 에러 시:
            {
                "error": <에러 메시지>
            }
    """
    try:
        # YOLO 모델 요청마다 새로 로드
        model = initModel()

        # 업로드된 PDF 파일 내용을 메모리에서 읽음
        content = await pdf_file.read()
        
        # pymupdf로 PDF 열기
        doc = pymupdf.open(stream=content, filetype="pdf")
        results = []

        # PDF 각 페이지 순회
        for page_num in range(len(doc)):
            page = doc[page_num]
            objects = detectObjectFromPage(page, model)
            results.append({
                'page_num': page_num + 1,  # 1부터 시작하는 페이지 번호
                'objects': objects         # 탐지된 객체 배열
            })

        doc.close()
        return JSONResponse(content=results)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

