from ultralytics import YOLO
import os
import json
import pymupdf
import numpy as np

# 클래스 ID
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

# 모델 로드
model_path = os.path.join(os.path.dirname(__file__), 'model', 'best.pt')
model = YOLO(model_path)

def detect_objects_as_json_a_page(i, name, page):
  img = page.get_pixmap()
  img.save(f"./image/{name}_{i}.png")

  results = model(f"./image/{name}_{i}.png")

  # JSON 결과 구성
  
  output = []

  for r in results:
    for box in r.boxes:
      class_id = int(box.cls[0])
      conf = float(box.conf[0])
      xyxy = box.xyxy[0].tolist()
          
      output.append({
        "class_id": class_id,
        "class_name": CATEGORY_ID_TO_NAME.get(class_id, "unknown"),
        "confidence": round(conf, 4),
        "bbox": {
          "x1": round(xyxy[0], 2),
          "y1": round(xyxy[1], 2),
          "x2": round(xyxy[2], 2),
          "y2": round(xyxy[3], 2)
        }
      })

  return output

def detect_objects_as_json(pdf_path, name, page_num = None):
  doc = pymupdf.open(pdf_path)

  page_output = []

  if page_num is None:
    for i, page in enumerate(doc):
      result = detect_objects_as_json_a_page(i, name, page)
      page_output.append(result)
  else:
    for i, page in enumerate(doc):
      if i is not page_num:
        continue
      result = detect_objects_as_json_a_page(i, name, page)
      page_output.append(result)

  return json.dumps(page_output, indent=2)

def detect_objects_from_page(page):
    pix = page.get_pixmap(dpi=150)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    
    if pix.n == 4:  # RGBA → RGB로 변환
        img = img[:, :, :3]

    results = model(img)
    output = []
    
    scale = 72 / 150  # 원래 크기로 돌리는 비율
    
    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()

            output.append({
                "class_id": class_id,
                "class_name": CATEGORY_ID_TO_NAME.get(class_id, "unknown"),
                "confidence": round(conf, 4),
                "bbox": [
                    round(xyxy[0]* scale, 2),
                    round(xyxy[1]* scale, 2),
                    round(xyxy[2]* scale, 2),
                    round(xyxy[3]* scale, 2)
                ]
            })

    return output