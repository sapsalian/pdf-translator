# 문서 객체 추론 모델
이 모듈의 모델은 `yolov8n`을 `PubLayNet`데이터로 학습시킨 모델입니다. 이미지 경로를 넣으면 객체를 인식하여 인식된 객체의 분류와 위치 정보를 `JSON`형식으로 반환합니다.

## How to use
먼저 `yolo`를 돌리기 위해서 라이브러리를 설치해야합니다.
```bash
pip install ultralytics
```

패키지를 활용할 때는 이 README가 있는 폴더 전체를 실행할 프로젝트 폴더 내에 위치시키고 아래처럼 사용해주세요. 페이지 번호를 생략하면 전체 페이지를 실행합니다.
```python
from yolo_inference import detect_objects_as_json

detect_objects_as_json("이미지 경로", 페이지 번호)
```

