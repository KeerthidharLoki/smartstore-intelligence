import numpy as np


class QueueDetector:
    def __init__(self, alert_threshold: int = 8):
        self.alert_threshold = alert_threshold

    def update(self, tracks: list[tuple]) -> dict:
        """
        Returns: {queue_alert: bool, queue_score: float, queue_size: int}

        Algorithm:
        1. Extract bbox centers from tracks list of (x1,y1,x2,y2,track_id)
        2. If < 3 people -> return score=0.0, alert=False
        3. centers = np.array of shape (N, 2)
        4. PCA: compute covariance matrix, eigenvalues
        5. linearity_score = 1.0 - (min_eigenvalue / (max_eigenvalue + 1e-6))
           clamped to [0, 1]
        6. density_score = min(len(tracks) / self.alert_threshold, 1.0)
        7. queue_score = 0.6 * linearity_score + 0.4 * density_score
        8. queue_alert = queue_score > 0.5 or len(tracks) >= alert_threshold
        9. return result dict
        """
        queue_size = len(tracks)

        if queue_size < 3:
            return {"queue_alert": False, "queue_score": 0.0, "queue_size": queue_size}

        centers = np.array(
            [((t[0] + t[2]) / 2.0, (t[1] + t[3]) / 2.0) for t in tracks],
            dtype=np.float32,
        )

        cov = np.cov(centers.T)
        eigenvalues = np.linalg.eigvalsh(cov)
        min_eig = float(eigenvalues.min())
        max_eig = float(eigenvalues.max())

        linearity_score = float(np.clip(1.0 - (min_eig / (max_eig + 1e-6)), 0.0, 1.0))
        density_score = min(queue_size / self.alert_threshold, 1.0)
        queue_score = 0.6 * linearity_score + 0.4 * density_score
        queue_alert = queue_score > 0.5 or queue_size >= self.alert_threshold

        return {
            "queue_alert": bool(queue_alert),
            "queue_score": float(queue_score),
            "queue_size": queue_size,
        }
