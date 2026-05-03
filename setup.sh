#!/usr/bin/env bash
# ============================================================
# Healthcare Burden Navigator — Full Setup Script
# Starts Postgres, creates the DB, seeds providers, and
# launches the backend + frontend.
# ============================================================
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
DOCKER_DIR="$BACKEND_DIR/fhir_docker_setup"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ----------------------------------------------------------
# 1. Check prerequisites
# ----------------------------------------------------------
info "Checking prerequisites..."

command -v docker >/dev/null 2>&1    || error "Docker is not installed. Please install Docker first."
command -v python3 >/dev/null 2>&1   || error "Python3 is not installed. Please install Python 3.10+ first."
command -v npm >/dev/null 2>&1       || error "npm is not installed. Please install Node.js 18+ first."

info "All prerequisites found."

# ----------------------------------------------------------
# 2. Start PostgreSQL via Docker Compose
# ----------------------------------------------------------
info "Starting PostgreSQL via Docker Compose..."

if [ ! -f "$DOCKER_DIR/.env" ]; then
    cp "$DOCKER_DIR/.env.example" "$DOCKER_DIR/.env"
    info "Created $DOCKER_DIR/.env from .env.example"
fi

docker compose -f "$DOCKER_DIR/docker-compose.yml" up -d

info "Waiting for Postgres to be healthy..."
for i in $(seq 1 30); do
    if docker exec fhir_postgres pg_isready -U fhir_user -d fhir_demo >/dev/null 2>&1; then
        info "Postgres is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        error "Postgres did not become healthy in 30 seconds."
    fi
    sleep 1
done

# ----------------------------------------------------------
# 3. Create the healthcare_nav database (if it doesn't exist)
# ----------------------------------------------------------
DB_EXISTS=$(docker exec fhir_postgres psql -U fhir_user -d fhir_demo -tAc \
    "SELECT 1 FROM pg_database WHERE datname='healthcare_nav'" 2>/dev/null || echo "")

if [ "$DB_EXISTS" = "1" ]; then
    info "Database 'healthcare_nav' already exists."
else
    info "Creating database 'healthcare_nav'..."
    docker exec fhir_postgres psql -U fhir_user -d fhir_demo -c "CREATE DATABASE healthcare_nav;"
    info "Database created."
fi

# ----------------------------------------------------------
# 4. Configure backend .env
# ----------------------------------------------------------
if [ ! -f "$BACKEND_DIR/.env" ]; then
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    # Update DATABASE_URL to match Docker credentials
    sed -i.bak 's|DATABASE_URL=.*|DATABASE_URL=postgresql://fhir_user:fhir_password@localhost:5432/healthcare_nav|' "$BACKEND_DIR/.env"
    rm -f "$BACKEND_DIR/.env.bak"
    warn "Created $BACKEND_DIR/.env — please add your GEMINI_API_KEY to this file."
else
    info "Backend .env already exists."
fi

# ----------------------------------------------------------
# 5. Set up Python virtual environment
# ----------------------------------------------------------
info "Setting up Python environment..."

if [ ! -d "$BACKEND_DIR/.venv" ]; then
    python3 -m venv "$BACKEND_DIR/.venv"
    info "Created virtual environment at $BACKEND_DIR/.venv"
fi

"$BACKEND_DIR/.venv/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"
info "Python dependencies installed."

# ----------------------------------------------------------
# 6. Seed the database
# ----------------------------------------------------------
info "Seeding the database..."
"$BACKEND_DIR/.venv/bin/python" "$BACKEND_DIR/seed_providers.py"

# ----------------------------------------------------------
# 7. Install frontend dependencies
# ----------------------------------------------------------
info "Installing frontend dependencies..."
npm install --prefix "$FRONTEND_DIR" --silent
info "Frontend dependencies installed."

# ----------------------------------------------------------
# 8. Start backend (background, persists after terminal close)
# ----------------------------------------------------------
info "Starting backend on port 8000..."

LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

# Kill any existing process on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

nohup "$BACKEND_DIR/.venv/bin/uvicorn" main:app --host 0.0.0.0 --port 8000 \
    --app-dir "$BACKEND_DIR" \
    > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"

# Wait for backend to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:8000/ >/dev/null 2>&1; then
        info "Backend is running (PID $BACKEND_PID)."
        break
    fi
    if [ "$i" -eq 15 ]; then
        error "Backend failed to start. Check $LOG_DIR/backend.log"
    fi
    sleep 1
done

# ----------------------------------------------------------
# 9. Start frontend (background, persists after terminal close)
# ----------------------------------------------------------
info "Starting frontend on port 5173..."

# Kill any existing process on port 5173
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

nohup npm run dev --prefix "$FRONTEND_DIR" -- --host 0.0.0.0 \
    > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$LOG_DIR/frontend.pid"

sleep 3
info "Frontend is running (PID $FRONTEND_PID)."

# ----------------------------------------------------------
# Done
# ----------------------------------------------------------
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
# Detect public IP for EC2 (falls back to localhost)
PUBLIC_IP=$(curl -s --max-time 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

echo -e "  Backend API:  ${YELLOW}http://$PUBLIC_IP:8000${NC}"
echo -e "  API docs:     ${YELLOW}http://$PUBLIC_IP:8000/docs${NC}"
echo -e "  Frontend:     ${YELLOW}http://$PUBLIC_IP:5173${NC}"
echo ""
echo -e "  Backend PID:  $BACKEND_PID"
echo -e "  Frontend PID: $FRONTEND_PID"
echo ""
echo -e "  Logs:         ${YELLOW}$LOG_DIR/backend.log${NC}"
echo -e "                ${YELLOW}$LOG_DIR/frontend.log${NC}"
echo ""
echo -e "  To stop:      ${YELLOW}./stop.sh${NC}"
echo ""
