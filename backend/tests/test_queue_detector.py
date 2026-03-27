"""
Unit tests for QueueDetector class.
Actual implementation expected in backend/app/queue_detector.py
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.queue_detector import QueueDetector


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_track(x1, y1, x2, y2, tid):
    """Return a track tuple (x1, y1, x2, y2, track_id)."""
    return (x1, y1, x2, y2, tid)


# ---------------------------------------------------------------------------
# QueueDetector tests
# ---------------------------------------------------------------------------

class TestQueueDetector:

    def test_empty_tracks(self):
        """No tracks → score=0.0, alert=False, size=0."""
        qd = QueueDetector()
        result = qd.update([])
        assert result['score'] == 0.0
        assert result['alert'] is False
        assert result['size'] == 0

    def test_two_people_no_alert(self):
        """
        2 tracks is below the minimum required for linearity analysis (3) and
        below any reasonable alert threshold.
        """
        qd = QueueDetector()
        tracks = [
            make_track(100, 100, 160, 200, 1),
            make_track(200, 100, 260, 200, 2),
        ]
        result = qd.update(tracks)
        assert result['score'] == 0.0
        assert result['alert'] is False

    def test_threshold_alert(self):
        """
        8 people meets or exceeds the default alert_threshold=8, so alert must
        be True regardless of linearity.
        """
        qd = QueueDetector()  # default alert_threshold should be <= 8
        tracks = [
            make_track(x, y, x + 50, y + 100, i)
            for i, (x, y) in enumerate([
                (50, 100), (150, 300), (300, 50), (400, 400),
                (100, 500), (500, 200), (250, 350), (350, 150),
            ])
        ]
        result = qd.update(tracks)
        assert result['alert'] is True

    def test_linear_queue_high_score(self):
        """
        8 tracks in a tight horizontal line should produce a high linearity
        (queue_score > 0.5).
        """
        qd = QueueDetector(alert_threshold=10)
        # y=240, x from 50 to 50+7*75=575, step 75
        tracks = [
            make_track(50 + i * 75, 215, 50 + i * 75 + 50, 265, i)
            for i in range(8)
        ]
        result = qd.update(tracks)
        assert result['score'] > 0.5, (
            f"Expected queue_score > 0.5 for a straight line, got {result['score']}"
        )

    def test_scattered_crowd_lower_linearity(self):
        """
        6 randomly scattered tracks should produce a lower linearity score
        than the perfectly linear case.
        """
        rng = np.random.default_rng(seed=42)
        qd = QueueDetector(alert_threshold=10)
        xs = rng.integers(20, 600, size=6)
        ys = rng.integers(20, 460, size=6)
        tracks = [
            make_track(int(x), int(y), int(x) + 50, int(y) + 100, i)
            for i, (x, y) in enumerate(zip(xs, ys))
        ]
        result = qd.update(tracks)

        # Build the linear reference score
        linear_tracks = [
            make_track(50 + i * 75, 215, 50 + i * 75 + 50, 265, i)
            for i in range(8)
        ]
        linear_result = QueueDetector(alert_threshold=10).update(linear_tracks)

        assert result['score'] < linear_result['score'], (
            f"Scattered score {result['score']} should be lower than "
            f"linear score {linear_result['score']}"
        )

    def test_score_range(self):
        """Queue score must always be in [0.0, 1.0]."""
        qd = QueueDetector(alert_threshold=10)
        test_cases = [
            [],
            [make_track(100, 100, 150, 200, 0)],
            [make_track(50 + i * 75, 215, 100 + i * 75, 265, i) for i in range(8)],
        ]
        for tracks in test_cases:
            result = qd.update(tracks)
            assert 0.0 <= result['score'] <= 1.0, (
                f"Score {result['score']} out of [0, 1] for tracks={tracks}"
            )
