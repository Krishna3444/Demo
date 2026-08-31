#!/usr/bin/env bash
# start.sh — convenience launcher for the Dhaniti dashboard.
# Starts the FastAPI backend (serving the API + built React app).
#
# Usage:
#   ./start.sh            # starts the server on port 5000 (override with PORT=...)
#   ./start.sh --stop     # stops the server
#   ./start.sh --status   # shows running status
#
# Environment:
#   PORT                  port to listen on (default 5000)
#   DHANITI_USE_VENV=1    use backend/venv if present (default: auto)
#
set -e
cd "$(dirname "$0")/backend"

# Prefer an activated virtualenv; optionally use the bundled one.
if [ -z "${VIRTUAL_ENV:-}" ] && [ -n "$(command -v python3)" ]; then
    PYTHON=python3
elif [ -n "${VIRTUAL_ENV:-}" ]; then
    PYTHON=python
else
    PYTHON=python3
fi

PID_FILE=".server.pid"
LOG_FILE="logs/server.log"
mkdir -p logs

PORT="${PORT:-5000}"

is_running() {
    [ -f "$PID_FILE" ] || return 1
    PID=$(cat "$PID_FILE")
    kill -0 "$PID" 2>/dev/null
}

case "${1:-start}" in
    --stop)
        if is_running; then
            PID=$(cat "$PID_FILE")
            kill "$PID"
            echo "Stopped server (PID $PID)"
            rm -f "$PID_FILE"
        else
            echo "Server not running (no PID file)"
            rm -f "$PID_FILE"
        fi
        ;;
    --status)
        if is_running; then
            PID=$(cat "$PID_FILE")
            echo "Server running (PID $PID) — http://localhost:$PORT"
        else
            echo "Server not running"
        fi
        ;;
    start|"")
        if is_running; then
            PID=$(cat "$PID_FILE")
            echo "Server already running (PID $PID) — http://localhost:$PORT"
            echo "Stop it first with: ./start.sh --stop"
            exit 0
        fi

        # Ensure the SQLite database exists (loads CSVs on a fresh checkout).
        if [ ! -f "../dhaniti_loans.db" ]; then
            echo "[start] Database not found — running load_data.py first..."
            DATABASE_PATH="../dhaniti_loans.db" $PYTHON load_data.py
        fi

        # Ensure the built frontend exists (build it if missing and npm is available).
        if [ ! -f "static/index.html" ] && command -v npm >/dev/null 2>&1; then
            echo "[start] Frontend build missing — building React app..."
            (cd ../frontend && npm install --no-audit --no-fund --legacy-peer-deps && npm run build)
        fi

        echo "[start] Launching FastAPI on http://localhost:$PORT"
        setsid $PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" > "$LOG_FILE" 2>&1 < /dev/null &
        APP_PID=$!
        echo $APP_PID > "$PID_FILE"
        sleep 3
        if kill -0 "$APP_PID" 2>/dev/null; then
            echo "[start] Server is running on http://localhost:$PORT"
            echo "[start] API docs:  http://localhost:$PORT/docs"
            echo "[start] Log:       $LOG_FILE"
            echo "[start] Stop with: ./start.sh --stop"
        else
            echo "[start] ERROR: server failed to start. See $LOG_FILE"
            tail -20 "$LOG_FILE"
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 [start|--stop|--status]"
        exit 1
        ;;
esac
