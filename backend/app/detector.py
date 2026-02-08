import numpy as np
from ultralytics import YOLO


class PersonDetector:
    def __init__(self, confidence: float = 0.4):
        self.model = YOLO("yolov8n.pt")
        self.confidence = confidence

    def detect(self, frame: np.ndarray) -> list[tuple]:
        results = self.model(frame, conf=self.confidence, classes=[0], verbose=False)
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return []
        detections = []
        for box in boxes:
            coords = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            x1, y1, x2, y2 = coords
            detections.append((float(x1), float(y1), float(x2), float(y2), conf))
        return detections
