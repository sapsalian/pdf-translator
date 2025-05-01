from threading import Lock
import numpy as np


model_lock = Lock()  # 전역 lock


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

def detectObjectFromPage(page, model):
    pix = page.get_pixmap(dpi=150)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    
    if pix.n == 4:  # RGBA → RGB로 변환
        img = img[:, :, :3]

    with model_lock:
        results = model(img)  # 🔐 여기만 lock으로 보호
        
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