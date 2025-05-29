import pymupdf
from yolo.yolo_inference.detection import detectObjectsFromFile
from preprocess.pdf_summary import summarizePdfInChunks, summarizePdfInChunksParallel
from draw.draw_blocks import drawBlocks
import modal
import json


def getYoloObjects(file_path):
    '''
    pdf 이름 받아서, yolo에 요청 보내고 탐지된 객체 배열 반환 받는 함수.

    반환 타입: 
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
    '''
    
    return detectObjectsFromFile(file_path)
    
def getYoloObjectsFromRemote(file_path):
    
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
    
    modal_detect = modal.Function.from_name("yolo-inference-app", "detect_objects_in_pdf")
    modal_result_string = modal_detect.remote(pdf_bytes)
    
    yolo_objects = json.loads(modal_result_string)
    return yolo_objects


def getFileInfo(file_path, max_workers=30):
    '''
    file_path 받아서, 페이지별 blocks 반환받는 함수. 페이지별 링크 정보도 포함.
    
    반환 값:
    [
        {
            "page_num": 1,
            "blocks": page.get_text("dict", flags=1, sort=True)["blocks"] 로 얻은 block 정보 배열,
            "links": [
                {
                    "kind": 링크 종류 (예: LINK_URI, LINK_GOTO, 등),
                    "from": 링크가 걸린 사각형 위치 (Rect),
                    "uri": 외부 URL일 경우 대상 주소,
                    "page": 내부 링크일 경우 목적지 페이지 번호,
                    "xref": PDF 내부 객체 참조 번호,
                    "to": 이동할 위치 정보 등
                },
                ...
            ],
            "yolo_objects": getYoloObjects(file_path) 해서 얻어온 값 중 해당 페이지의 객체 배열
        },
        ...
    ]
    '''
    results = []
    paged_yolo = {item["page_num"]: item["objects"] for item in getYoloObjectsFromRemote(file_path)}
    
    summaries_with_terms = summarizePdfInChunksParallel(file_path, max_workers=max_workers)
    term_dict = summaries_with_terms["term_dict"]
    summary_dict = {s["page"]: s["summary"] for s in summaries_with_terms["summaries"]}

    with pymupdf.open(file_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            # blocks 추출
            blocks = page.get_text("dict", flags=1, sort=True)["blocks"]

            # links 추출 
            links = page.get_links()

            results.append({
                "page_num": page_num,
                "blocks": blocks,
                "links": links,
                "yolo_objects": paged_yolo.get(page_num, []),
                "summary": summary_dict.get(page_num, "")
            })

    return {
        "term_dict": term_dict,
        "page_infos": results
    }

def getFileInfoWithoutSummary(file_path):
    '''
    file_path 받아서, 페이지별 blocks 반환받는 함수. 페이지별 링크 정보도 포함.
    
    반환 값:
    [
        {
            "page_num": 1,
            "blocks": page.get_text("dict", flags=1, sort=True)["blocks"] 로 얻은 block 정보 배열,
            "links": [
                {
                    "kind": 링크 종류 (예: LINK_URI, LINK_GOTO, 등),
                    "from": 링크가 걸린 사각형 위치 (Rect),
                    "uri": 외부 URL일 경우 대상 주소,
                    "page": 내부 링크일 경우 목적지 페이지 번호,
                    "xref": PDF 내부 객체 참조 번호,
                    "to": 이동할 위치 정보 등
                },
                ...
            ],
            "yolo_objects": getYoloObjects(file_path) 해서 얻어온 값 중 해당 페이지의 객체 배열
        },
        ...
    ]
    '''
    results = []
    paged_yolo = {item["page_num"]: item["objects"] for item in getYoloObjectsFromRemote(file_path)}

    with pymupdf.open(file_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            # blocks 추출
            blocks = page.get_text("dict", flags=1, sort=True)["blocks"]

            # links 추출 
            links = page.get_links()

            results.append({
                "page_num": page_num,
                "blocks": blocks,
                "links": links,
                "yolo_objects": paged_yolo.get(page_num, []),
            })

    return {
        "page_infos": results
    }
