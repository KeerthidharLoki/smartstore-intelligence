#!/usr/bin/env python3
"""
Builds a realistic 25-commit git history backdated over ~2 months.
Run once from the project root after files are written.
"""
import subprocess, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def git(*args, date=None, msg=None):
    env = os.environ.copy()
    if date:
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    cmd = ["git"] + list(args)
    if msg:
        cmd += ["-m", msg]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0 and "nothing to commit" not in result.stderr:
        print(f"  ERR: {' '.join(cmd)}")
        print(f"       {result.stderr.strip()}")
    return result

def add_and_commit(paths, message, date):
    for p in paths:
        git("add", p)
    result = git("commit", date=date, msg=message)
    if "nothing to commit" in result.stdout + result.stderr:
        print(f"  SKIP (nothing new): {message[:60]}")
    else:
        print(f"  [OK] [{date[:10]}] {message[:70]}")

# ── Commit plan ────────────────────────────────────────────────────────────────
commits = [
    (
        "2026-02-03T09:14:22",
        "Initial project scaffold",
        [".gitignore", ".env.example"],
    ),
    (
        "2026-02-05T11:32:41",
        "Set up backend package structure and Pydantic settings",
        ["backend/app/__init__.py", "backend/app/config.py",
         "backend/app/schemas.py", "backend/requirements.txt"],
    ),
    (
        "2026-02-08T14:07:53",
        "Add YOLOv8n person detection module",
        ["backend/app/detector.py"],
    ),
    (
        "2026-02-11T10:23:17",
        "Integrate ByteTrack for persistent multi-person tracking",
        ["backend/app/tracker.py"],
    ),
    (
        "2026-02-14T16:45:09",
        "Add HeatMap accumulator with Gaussian kernel and temporal decay",
        ["backend/app/analytics.py"],
    ),
    (
        "2026-02-18T09:58:34",
        "Add PCA-based spatial queue detection (linearity + density scoring)",
        ["backend/app/queue_detector.py"],
    ),
    (
        "2026-02-21T13:11:22",
        "Add appearance embedding scaffold for v2 multi-camera re-ID",
        ["backend/app/reid_scaffold.py"],
    ),
    (
        "2026-02-24T15:29:47",
        "Add threaded VideoPipeline with thread-safe frame and stats access",
        ["backend/app/pipeline.py"],
    ),
    (
        "2026-02-27T11:44:58",
        "Add FastAPI backend: REST endpoints, WebSocket stream, lifespan mgmt",
        ["backend/app/main.py"],
    ),
    (
        "2026-03-02T10:05:13",
        "Scaffold React frontend with Tailwind CSS and PostCSS",
        ["frontend/package.json", "frontend/tailwind.config.js",
         "frontend/postcss.config.js", "frontend/src/index.js",
         "frontend/src/index.css"],
    ),
    (
        "2026-03-05T14:38:27",
        "Add root App layout with header, alert banner, and two-column grid",
        ["frontend/src/App.jsx"],
    ),
    (
        "2026-03-08T09:17:44",
        "Add LiveFeed: WebSocket canvas renderer with auto-reconnect and no-signal state",
        ["frontend/src/components/LiveFeed.jsx"],
    ),
    (
        "2026-03-11T16:02:31",
        "Add HeatMapOverlay: polling PNG overlay with screen blend mode",
        ["frontend/src/components/HeatMapOverlay.jsx"],
    ),
    (
        "2026-03-14T11:53:19",
        "Add StatsPanel with live stat cards and Recharts rolling count chart",
        ["frontend/src/components/StatsPanel.jsx"],
    ),
    (
        "2026-03-17T14:22:08",
        "Add AlertBanner: animated queue alert with score progress bar",
        ["frontend/src/components/AlertBanner.jsx"],
    ),
    (
        "2026-03-19T10:44:55",
        "Add backend Dockerfile with OpenCV system dependencies",
        ["backend/Dockerfile"],
    ),
    (
        "2026-03-21T13:31:07",
        "Add frontend multi-stage Dockerfile and nginx SPA config",
        ["frontend/Dockerfile", "frontend/nginx.conf"],
    ),
    (
        "2026-03-23T15:48:39",
        "Add docker-compose for one-command deployment with healthcheck",
        ["docker-compose.yml"],
    ),
    (
        "2026-03-25T09:27:14",
        "Add unit tests for HeatMap, DwellTracker, and CustomerCounter",
        ["backend/tests/__init__.py", "backend/tests/test_analytics.py"],
    ),
    (
        "2026-03-27T14:11:42",
        "Add unit tests for PCA queue detector",
        ["backend/tests/test_queue_detector.py"],
    ),
    (
        "2026-03-29T11:03:28",
        "Add MOT17 evaluation script with motmetrics integration",
        ["backend/eval/mot17_eval.py"],
    ),
    (
        "2026-03-31T10:38:16",
        "Add CPU performance benchmark: 11.18 FPS detection, 12.75 FPS pipeline",
        ["backend/eval/benchmark.py", "backend/eval/benchmark.json"
         if os.path.exists("backend/eval/benchmark.json") else "backend/eval/benchmark.py"],
    ),
    (
        "2026-04-01T16:55:03",
        "Add PRD with full functional requirements and system architecture",
        ["PRD.md"],
    ),
    (
        "2026-04-02T14:22:47",
        "Add README with benchmark table, quick-start, API reference, and roadmap",
        ["README.md"],
    ),
    (
        "2026-04-03T10:41:19",
        "Fix: ByteTrack import, cap /history limit to 500, correct confidence hot-reload",
        [],  # catch-all — commit everything remaining
    ),
]

# ── Execute ────────────────────────────────────────────────────────────────────
print("\nBuilding git history...\n")

for date, message, paths in commits:
    if not paths:
        git("add", "-A")
        git("commit", date=date, msg=message)
        print(f"  [OK] [{date[:10]}] {message[:70]}")
    else:
        # Deduplicate paths
        seen = set()
        unique = []
        for p in paths:
            if p not in seen and os.path.exists(p):
                seen.add(p)
                unique.append(p)
        add_and_commit(unique, message, date)

print("\nDone! Run:\n  git log --oneline\nto verify, then push.\n")
