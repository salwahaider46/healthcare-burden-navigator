#!/usr/bin/env bash
# ============================================================
# Healthcare Burden Navigator — Stop Script
# Stops the backend and frontend processes started by setup.sh
# ============================================================

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

stop_process() {
    local name="$1"
    local pidfile="$LOG_DIR/$name.pid"

    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            echo -e "${GREEN}[INFO]${NC}  Stopped $name (PID $PID)"
        else
            echo -e "${YELLOW}[WARN]${NC}  $name (PID $PID) was not running."
        fi
        rm -f "$pidfile"
    else
        echo -e "${YELLOW}[WARN]${NC}  No PID file for $name. Trying port kill..."
    fi
}

# Stop backend (port 8000)
stop_process "backend"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Stop frontend (port 5173)
stop_process "frontend"
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

echo ""
echo -e "${GREEN}All services stopped.${NC}"
echo -e "Docker Postgres is still running. To stop it:"
echo -e "  ${YELLOW}docker compose -f backend/fhir_docker_setup/docker-compose.yml down${NC}"
echo ""
