from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    VIDEO_SOURCE: str = "0"
    ALERT_THRESHOLD: int = 8
    CONFIDENCE: float = 0.4
    MAX_TRACK_AGE: int = 30
    HEATMAP_DECAY: float = 0.995
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480
    TARGET_FPS: int = 15
    DWELL_WINDOW_SEC: int = 60
    PEAK_WINDOW_SEC: int = 300

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
