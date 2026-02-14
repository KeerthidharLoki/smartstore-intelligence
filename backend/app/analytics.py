import time
from collections import deque

import cv2
import numpy as np


class HeatMap:
    def __init__(self, height: int, width: int, decay: float = 0.995):
        self.accumulator = np.zeros((height // 4, width // 4), dtype=np.float32)
        self.decay = decay
        self._height = height // 4
        self._width = width // 4

        # Precompute 41x41 Gaussian kernel, sigma=10
        ksize = 41
        sigma = 10
        ax = np.arange(ksize) - ksize // 2
        xx, yy = np.meshgrid(ax, ax)
        kernel = np.exp(-(xx ** 2 + yy ** 2) / (2 * sigma ** 2))
        self._kernel = (kernel / kernel.sum()).astype(np.float32)
        self._krad = ksize // 2

    def update(self, tracks: list[tuple]):
        for track in tracks:
            x1, y1, x2, y2 = track[0], track[1], track[2], track[3]
            cx = int((x1 + x2) // 2) // 4
            cy = int((y1 + y2) // 2) // 4

            # Kernel bounds in accumulator space
            acc_y1 = max(0, cy - self._krad)
            acc_y2 = min(self._height, cy + self._krad + 1)
            acc_x1 = max(0, cx - self._krad)
            acc_x2 = min(self._width, cx + self._krad + 1)

            # Corresponding kernel slice
            k_y1 = acc_y1 - (cy - self._krad)
            k_y2 = k_y1 + (acc_y2 - acc_y1)
            k_x1 = acc_x1 - (cx - self._krad)
            k_x2 = k_x1 + (acc_x2 - acc_x1)

            if acc_y2 > acc_y1 and acc_x2 > acc_x1:
                self.accumulator[acc_y1:acc_y2, acc_x1:acc_x2] += (
                    self._kernel[k_y1:k_y2, k_x1:k_x2]
                )

    def decay_step(self):
        self.accumulator *= self.decay

    def render(self) -> bytes:
        acc = self.accumulator
        max_val = acc.max()
        if max_val > 0:
            normalized = (acc / max_val * 255).astype(np.uint8)
        else:
            normalized = np.zeros_like(acc, dtype=np.uint8)

        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)

        # Add alpha channel at 50% transparency (128)
        alpha = np.full((*colored.shape[:2], 1), 128, dtype=np.uint8)
        bgra = np.concatenate([colored, alpha], axis=2)

        _, buf = cv2.imencode(".png", bgra)
        return buf.tobytes()


class DwellTracker:
    def __init__(self, window_sec: int = 60):
        self._window_sec = window_sec
        self._tracks: dict[int, dict] = {}
        self._completed: deque = deque()

    def update(self, active_ids: set[int], timestamp: float):
        # Complete tracks no longer active
        lost_ids = set(self._tracks.keys()) - active_ids
        for tid in lost_ids:
            self._complete(tid, timestamp)

        # Update or create active tracks
        for tid in active_ids:
            if tid in self._tracks:
                self._tracks[tid]["last_seen"] = timestamp
            else:
                self._tracks[tid] = {"first_seen": timestamp, "last_seen": timestamp}

    def _complete(self, track_id: int, timestamp: float):
        track = self._tracks.pop(track_id, None)
        if track is None:
            return
        dwell = track["last_seen"] - track["first_seen"]
        self._completed.append(
            {"track_id": track_id, "dwell_sec": dwell, "ended_at": track["last_seen"]}
        )

    def get_stats(self) -> dict:
        now = time.time()
        cutoff = now - self._window_sec
        recent = [s["dwell_sec"] for s in self._completed if s["ended_at"] >= cutoff]

        if not recent:
            return {"avg_dwell_sec": 0.0, "median_dwell_sec": 0.0, "session_count": 0}

        avg = float(np.mean(recent))
        median = float(np.median(recent))
        return {
            "avg_dwell_sec": avg,
            "median_dwell_sec": median,
            "session_count": len(recent),
        }

    def get_sessions(self, limit: int = 100) -> list[dict]:
        sessions = list(self._completed)
        return sessions[-limit:]


class CustomerCounter:
    def __init__(self, peak_window_sec: int = 300):
        self._peak_window_sec = peak_window_sec
        self._peak_history: deque = deque()

    def update(self, current_count: int, timestamp: float):
        self._peak_history.append((current_count, timestamp))
        cutoff = timestamp - self._peak_window_sec
        while self._peak_history and self._peak_history[0][1] < cutoff:
            self._peak_history.popleft()

    def get_peak(self) -> int:
        if not self._peak_history:
            return 0
        return max(count for count, _ in self._peak_history)
