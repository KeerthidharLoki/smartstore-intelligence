import numpy as np
from boxmot import ByteTrack


class PersonTracker:
    def __init__(self, max_age: int = 30):
        self.tracker = ByteTrack(track_buffer=max_age)
        self.max_age = max_age

    def update(self, detections: list[tuple], frame: np.ndarray) -> list[tuple]:
        if not detections:
            empty = np.empty((0, 6), dtype=np.float32)
            self.tracker.update(empty, frame)
            return []

        # boxmot expects (N, 6): [x1, y1, x2, y2, conf, class_id]
        dets_array = np.array(
            [[x1, y1, x2, y2, conf, 0] for (x1, y1, x2, y2, conf) in detections],
            dtype=np.float32,
        )

        tracked = self.tracker.update(dets_array, frame)

        if tracked is None or len(tracked) == 0:
            return []

        # Output columns: [x1, y1, x2, y2, track_id, conf, cls, idx]
        results = []
        for row in tracked:
            x1, y1, x2, y2 = float(row[0]), float(row[1]), float(row[2]), float(row[3])
            track_id = int(row[4])
            results.append((x1, y1, x2, y2, track_id))
        return results
