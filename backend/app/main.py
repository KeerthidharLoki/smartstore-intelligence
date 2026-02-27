import asyncio
import json
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .config import Settings
from .pipeline import VideoPipeline
from .schemas import (
    ConfigUpdate,
    HealthResponse,
    HistoryResponse,
    SessionRecord,
    StatsResponse,
)

settings = Settings()
pipeline: VideoPipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    pipeline = VideoPipeline(settings)
    pipeline.start()
    yield
    pipeline.stop()


app = FastAPI(title="SmartStore Intelligence", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_start_time = time.time()


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", uptime_sec=round(time.time() - _start_time, 1))


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    s = pipeline.get_stats()
    if not s:
        return StatsResponse(
            current_count=0,
            session_count=0,
            avg_dwell_sec=0.0,
            median_dwell_sec=0.0,
            peak_count=0,
            queue_alert=False,
            queue_score=0.0,
            queue_size=0,
            alert_threshold=settings.ALERT_THRESHOLD,
            uptime_sec=round(time.time() - _start_time, 1),
            fps=0.0,
        )
    return StatsResponse(**s)


@app.get("/heatmap")
async def get_heatmap():
    hm = pipeline.get_heatmap()
    if hm is None:
        return Response(content=b"", media_type="image/png", status_code=204)
    return Response(content=hm, media_type="image/png")


@app.post("/config")
async def update_config(update: ConfigUpdate):
    pipeline.update_config(update)
    return {"status": "updated"}


@app.get("/history", response_model=HistoryResponse)
async def get_history(limit: int = 100) -> HistoryResponse:
    limit = min(max(1, limit), 500)  # clamp 1–500
    sessions = pipeline.get_sessions(limit)
    records = [SessionRecord(**s) for s in sessions]
    return HistoryResponse(sessions=records, total=len(records))


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            frame = pipeline.get_frame()
            if frame is not None:
                stats = pipeline.get_stats()
                metadata = {
                    "current_count": stats.get("current_count", 0),
                    "queue_alert": stats.get("queue_alert", False),
                    "queue_score": stats.get("queue_score", 0.0),
                    "fps": stats.get("fps", 0.0),
                }
                await websocket.send_text(json.dumps(metadata))
                await websocket.send_bytes(frame)
            await asyncio.sleep(1 / max(settings.TARGET_FPS, 1))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
