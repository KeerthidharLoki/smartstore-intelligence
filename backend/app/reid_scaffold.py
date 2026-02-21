"""
Re-Identification Scaffold — v2 Foundation

This module provides the appearance embedding hook for multi-camera person re-ID.
In v2, replace the stub extractor with OSNet (torchreid) and wire up
cross-camera Hungarian matching with this interface.

Multi-Camera Pipeline (v2 design):
  Camera A tracks -> embeddings ->
                                  \\> Hungarian matching -> unified global IDs
  Camera B tracks -> embeddings ->

  Distance metric: cosine similarity on L2-normalized 512-d vectors
  Threshold: sim > 0.7 -> same person across cameras
"""

import numpy as np
import cv2


class AppearanceExtractor:
    """
    Extracts appearance embeddings per tracked bounding box.
    Current: returns a normalized pixel-histogram vector (stub).
    v2: replace with OSNet from torchreid for 512-d semantic embeddings.
    """

    EMBED_DIM = 128  # v2 target: 512 with OSNet
    TARGET_SIZE = (64, 128)  # width, height (standard Re-ID crop)

    def extract(self, frame: np.ndarray, bbox: tuple) -> np.ndarray:
        """
        Args:
            frame: BGR frame
            bbox: (x1, y1, x2, y2)
        Returns:
            L2-normalized embedding vector of shape (EMBED_DIM,)
        """
        x1, y1, x2, y2 = [int(v) for v in bbox[:4]]
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            return np.zeros(self.EMBED_DIM)

        crop = frame[y1:y2, x1:x2]
        crop_resized = cv2.resize(crop, self.TARGET_SIZE)

        # Stub: color histogram as proxy embedding
        # v2 TODO: replace with OSNet forward pass
        hist = cv2.calcHist(
            [crop_resized], [0, 1, 2], None,
            [8, 8, 8], [0, 256, 0, 256, 0, 256],
        )
        embedding = hist.flatten()[: self.EMBED_DIM]
        if len(embedding) < self.EMBED_DIM:
            embedding = np.pad(embedding, (0, self.EMBED_DIM - len(embedding)))

        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding.astype(np.float32)

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Returns cosine similarity [0, 1]. Use > 0.7 as re-ID match threshold."""
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)
