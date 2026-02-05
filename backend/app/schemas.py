from typing import Optional
from pydantic import BaseModel


class StatsResponse(BaseModel):
    current_count: int
    session_count: int
    avg_dwell_sec: float
    median_dwell_sec: float
    peak_count: int
    queue_alert: bool
    queue_score: float
    queue_size: int
    alert_threshold: int
    uptime_sec: float
    fps: float


class ConfigUpdate(BaseModel):
    video_source: Optional[str] = None
    alert_threshold: Optional[int] = None
    confidence: Optional[float] = None


class SessionRecord(BaseModel):
    track_id: int
    dwell_sec: float
    ended_at: float


class HistoryResponse(BaseModel):
    sessions: list[SessionRecord]
    total: int


class HealthResponse(BaseModel):
    status: str
    uptime_sec: float
