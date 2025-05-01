# 모델 로드
from ultralytics import YOLO
import os

def initModel():
  model_path = os.path.join(os.path.dirname(__file__), 'model', 'best.pt')
  model = YOLO(model_path)
  return model