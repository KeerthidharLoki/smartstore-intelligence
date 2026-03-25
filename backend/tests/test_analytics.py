"""
Unit tests for HeatMap, DwellTracker, and CustomerCounter classes.
Actual implementations expected in backend/app/analytics.py
"""

import sys
import os
import time
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.analytics import HeatMap, DwellTracker, CustomerCounter


# ---------------------------------------------------------------------------
# HeatMap tests
# ---------------------------------------------------------------------------

class TestHeatMap:

    def test_heatmap_initial_zero(self):
        """Accumulator should be all zeros after construction."""
        hm = HeatMap(480, 640)
        assert hm.accumulator.sum() == 0

    def test_heatmap_update_increases(self):
        """Calling update() with a track should increase the accumulator max."""
        hm = HeatMap(480, 640)
        tracks = [(100, 100, 200, 200, 1)]  # (x1, y1, x2, y2, track_id)
        hm.update(tracks)
        assert hm.accumulator.max() > 0

    def test_heatmap_decay(self):
        """After 100 decay steps from a fully-set accumulator, max should be < 0.7."""
        hm = HeatMap(480, 640)
        hm.accumulator[:] = 1.0
        for _ in range(100):
            hm.decay_step()
        assert hm.accumulator.max() < 0.7

    def test_heatmap_render_returns_bytes(self):
        """render() should return bytes with length > 100 (valid image data)."""
        hm = HeatMap(480, 640)
        tracks = [(50, 50, 150, 150, 1)]
        hm.update(tracks)
        result = hm.render()
        assert isinstance(result, bytes)
        assert len(result) > 100

    def test_heatmap_multiple_tracks(self):
        """update() with 3 tracks should produce a positive accumulator sum."""
        hm = HeatMap(480, 640)
        tracks = [
            (10, 10, 80, 80, 1),
            (200, 150, 300, 250, 2),
            (400, 300, 500, 400, 3),
        ]
        hm.update(tracks)
        assert hm.accumulator.sum() > 0


# ---------------------------------------------------------------------------
# DwellTracker tests
# ---------------------------------------------------------------------------

class TestDwellTracker:

    def test_dwell_new_track(self):
        """A track that just started should show session_count=0 (still active)."""
        dt = DwellTracker()
        dt.update({1}, timestamp=0.0)
        stats = dt.get_stats()
        assert stats['session_count'] == 0

    def test_dwell_complete_track(self):
        """
        Track id=1 enters at t=0, still present at t=5, then disappears at t=10.
        Completed dwell should be roughly 5–10 seconds.
        """
        dt = DwellTracker()
        dt.update({1}, timestamp=0.0)
        dt.update({1}, timestamp=5.0)
        dt.update(set(), timestamp=10.0)   # id=1 removed → session completed
        stats = dt.get_stats()
        assert stats['session_count'] == 1
        assert 5.0 <= stats['avg_dwell_sec'] <= 10.0

    def test_dwell_multiple_sessions(self):
        """Three tracks enter and leave; session_count should be 3."""
        dt = DwellTracker()
        dt.update({1, 2, 3}, timestamp=0.0)
        dt.update(set(), timestamp=5.0)    # all three leave
        stats = dt.get_stats()
        assert stats['session_count'] == 3

    def test_dwell_window_filtering(self):
        """
        Sessions completed more than the stats window ago should not appear in
        get_stats() results.
        """
        dt = DwellTracker()
        old_timestamp = time.time() - 200  # 200 s ago, beyond typical 60–120 s window
        # Directly inject a stale completed session
        dt._completed.append({
            'track_id': 99,
            'dwell': 5.0,
            'ended_at': old_timestamp,
        })
        stats = dt.get_stats()
        assert stats['session_count'] == 0


# ---------------------------------------------------------------------------
# CustomerCounter tests
# ---------------------------------------------------------------------------

class TestCustomerCounter:

    def test_counter_peak_tracking(self):
        """Peak should equal the maximum count seen across all updates."""
        cc = CustomerCounter()
        now = time.time()
        for i, count in enumerate([1, 5, 3, 8, 2]):
            cc.update(count, timestamp=now + i)
        assert cc.get_peak() == 8

    def test_counter_peak_window_expiry(self):
        """
        An entry with count=10 at a very old timestamp should be pruned;
        after a fresh update with count=1 the peak should be 1.
        """
        cc = CustomerCounter()
        old_timestamp = time.time() - 10_000  # far in the past
        cc.update(10, timestamp=old_timestamp)
        cc.update(1, timestamp=time.time())
        assert cc.get_peak() == 1
