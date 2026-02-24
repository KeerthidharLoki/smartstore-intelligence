import threading
import time
from collections import deque

import cv2
import numpy as np

from .config import Settings
from .detector import PersonDetector
from .tracker import PersonTracker
from .analytics import HeatMap, DwellTracker, CustomerCounter
from .queue_detector import QueueDetector


class VideoPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._detector = PersonDetector(settings.CONFIDENCE)
        self._tracker = PersonTracker(settings.MAX_TRACK_AGE)
        self._heatmap = HeatMap(settings.FRAME_HEIGHT, settings.FRAME_WIDTH, settings.HEATMAP_DECAY)
        self._dwell = DwellTracker(settings.DWELL_WINDOW_SEC)
        self._counter = CustomerCounter(settings.PEAK_WINDOW_SEC)
        self._queue = QueueDetector(settings.ALERT_THRESHOLD)

        self._frame: bytes | None = None
        self._frame_lock = threading.Lock()
        self._stats: dict = {}
        self._stats_lock = threading.Lock()
        self._heatmap_bytes: bytes | None = None

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._start_time = time.time()
        self._fps_deque: deque = deque(maxlen=30)
        self._completed_sessions: list = []

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self):
        source = self.settings.VIDEO_SOURCE
        try:
            source = int(source)
        except ValueError:
            pass

        cap = cv2.VideoCapture(source)
        frame_counter = 0

        while not self._stop_event.is_set():
            if not cap.isOpened():
                time.sleep(1)
                cap = cv2.VideoCapture(source)
                continue

            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = cv2.resize(frame, (self.settings.FRAME_WIDTH, self.settings.FRAME_HEIGHT))
            t_start = time.time()

            detections = self._detector.detect(frame)
            tracks = self._tracker.update(detections, frame)

            ts = time.time()
            active_ids = {int(t[4]) for t in tracks}
            self._heatmap.update(tracks)
            self._heatmap.decay_step()
            self._dwell.update(active_ids, ts)
            self._counter.update(len(active_ids), ts)
            queue_result = self._queue.update(tracks)

            annotated = frame.copy()
            for (x1, y1, x2, y2, tid) in tracks:
                cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 100), 2)
                cv2.putText(
                    annotated, f"ID:{int(tid)}", (int(x1), int(y1) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 100), 1,
                )

            _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
            frame_bytes = buf.tobytes()

            frame_counter += 1
            if frame_counter % 10 == 0:
                hm = self._heatmap.render()
                with self._frame_lock:
                    self._heatmap_bytes = hm

            elapsed = time.time() - t_start
            self._fps_deque.append(elapsed)
            fps = 1.0 / (sum(self._fps_deque) / len(self._fps_deque) + 1e-6)

            dwell_stats = self._dwell.get_stats()
            stats = {
                "current_count": len(active_ids),
                "session_count": dwell_stats["session_count"],
                "avg_dwell_sec": round(dwell_stats["avg_dwell_sec"], 1),
                "median_dwell_sec": round(dwell_stats["median_dwell_sec"], 1),
                "peak_count": self._counter.get_peak(),
                "queue_alert": queue_result["queue_alert"],
                "queue_score": round(queue_result["queue_score"], 3),
                "queue_size": queue_result["queue_size"],
                "alert_threshold": self.settings.ALERT_THRESHOLD,
                "uptime_sec": round(time.time() - self._start_time, 1),
                "fps": round(fps, 1),
            }

            with self._stats_lock:
                self._stats = stats
            with self._frame_lock:
                self._frame = frame_bytes

        cap.release()

    def get_frame(self) -> bytes | None:
        with self._frame_lock:
            return self._frame

    def get_stats(self) -> dict:
        with self._stats_lock:
            return dict(self._stats)

    def get_heatmap(self) -> bytes | None:
        with self._frame_lock:
            return self._heatmap_bytes

    def get_sessions(self, limit: int = 100) -> list:
        return self._dwell.get_sessions(limit)

    def update_config(self, update):
        if update.alert_threshold is not None:
            self.settings.ALERT_THRESHOLD = update.alert_threshold
            self._queue.alert_threshold = update.alert_threshold
        if update.confidence is not None:
            self.settings.CONFIDENCE = update.confidence
            self._detector.confidence = update.confidence
        if update.video_source is not None:
            self.settings.VIDEO_SOURCE = update.video_source
