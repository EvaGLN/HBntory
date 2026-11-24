#!/usr/bin/env bash
# Start every HBntory service in the background, in the right order.
# Usage: ./start.sh        (stop everything with Ctrl+C)
#
# Optional: PRODUCTS_API_DIR=/path/to/hbntory-products-api ./start.sh
# Logs of each service are written in the "logs" folder.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTS_API_DIR="${PRODUCTS_API_DIR:-$ROOT/../hbntory-products-api}"
LOGS="$ROOT/logs"

# Same variables in every service. An absolute path for the database makes
# the Backoffice and the AI service use the same file.
export DATABASE_URL="${DATABASE_URL:-sqlite:///$ROOT/hbntory.db}"
export SECRET_KEY="${SECRET_KEY:-change-me-to-a-long-random-string}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-adminpass1}"
export PRODUCT_API_URL="${PRODUCT_API_URL:-http://localhost:5001/api/v1}"

PIDS=()
STARTED_DOCKER=0

# Stop everything this script started.
cleanup() {
    trap - EXIT
    echo
    echo "Stopping the services..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null
    done
    if [ "$STARTED_DOCKER" = "1" ]; then
        (cd "$PRODUCTS_API_DIR" && docker compose down)
    fi
}

# Print an error and quit.
fail() {
    echo "ERROR: $1" >&2
    exit 1
}

# Wait until an URL answers (up to 60 seconds). $1 = URL, $2 = service name.
wait_for() {
    for _ in $(seq 1 60); do
        if curl -sf -o /dev/null "$1"; then
            echo "  $2 is ready"
            return 0
        fi
        sleep 1
    done
    fail "$2 did not answer at $1. Read its log in $LOGS"
}

# Ctrl+C or kill -> exit, which runs cleanup.
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Checks before starting anything.
[ -f "$ROOT/.venv/bin/activate" ] || fail "virtual environment not found. Create it first (see README, Setup instructions)."
command -v curl > /dev/null || fail "curl is not installed."
mkdir -p "$LOGS"
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

# 1. Products API (Docker)
echo "1/4 Products API"
if curl -sf -o /dev/null http://localhost:5001/health; then
    echo "  already running, left untouched"
else
    command -v docker > /dev/null || fail "docker not found. Start Docker Desktop and enable the WSL integration (see README)."
    [ -d "$PRODUCTS_API_DIR" ] || fail "folder not found: $PRODUCTS_API_DIR (set PRODUCTS_API_DIR)."
    (cd "$PRODUCTS_API_DIR" && docker compose up -d --build) > "$LOGS/products_api.log" 2>&1 \
        || fail "docker compose failed. Read $LOGS/products_api.log"
    STARTED_DOCKER=1
    wait_for http://localhost:5001/health "Products API"
fi

# 2. Database seed (safe to run again) then Backoffice
echo "2/4 Backoffice"
(cd "$ROOT/backoffice" && python seed.py) > "$LOGS/seed.log" 2>&1 \
    || fail "seed failed. Read $LOGS/seed.log"
(cd "$ROOT/backoffice" && exec python app.py) > "$LOGS/backoffice.log" 2>&1 &
PIDS+=($!)
wait_for http://localhost:5000/ "Backoffice"

# 3. Ollama
echo "3/4 Ollama"
if curl -sf -o /dev/null http://localhost:11434/; then
    echo "  already running, left untouched"
else
    command -v ollama > /dev/null || fail "ollama not found (see README, Prerequisites)."
    ollama serve > "$LOGS/ollama.log" 2>&1 &
    PIDS+=($!)
    wait_for http://localhost:11434/ "Ollama"
fi
ollama list 2> /dev/null | grep -q "qwen3:8b" \
    || echo "  WARNING: model qwen3:8b not found. Run: ollama pull qwen3:8b"

# 4. AI Query Service
echo "4/4 AI Query Service"
(cd "$ROOT/ai_service" && exec python -m flask --app run_ai run --port 5002) > "$LOGS/ai_service.log" 2>&1 &
PIDS+=($!)
wait_for http://localhost:5002/ "AI Query Service"

echo
echo "Everything is running:"
echo "  Backoffice       http://localhost:5000/"
echo "  Client web page  http://localhost:5002/"
echo "  Products API     http://localhost:5001/health"
echo "Logs: $LOGS"
echo "Press Ctrl+C to stop."
wait
