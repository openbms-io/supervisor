#!/usr/bin/env bash
set -euo pipefail

# Start local infra (NanoMQ + reverse proxy) and the Designer app.
# - Infra (docker compose) exposes: TCP 1883, WS via proxy at 3000 (/mqtt)
# - Designer (Next.js) runs on port 3001; proxy on 3000 forwards / → 3001

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT_DIR/infra"

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1"; exit 1; }; }

compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    echo "docker compose not found. Install Docker Desktop or docker-compose."; exit 1
  fi
}

wait_port() {
  local host="$1"; local port="$2"; local name="$3"; local tries=60
  for i in $(seq 1 "$tries"); do
    if nc -z "$host" "$port" >/dev/null 2>&1; then
      echo "✔ $name is ready on $host:$port"; return 0
    fi
    sleep 0.5
  done
  echo "✖ Timeout waiting for $name on $host:$port"; return 1
}

echo "▶ Checking prerequisites..."
need_cmd docker
need_cmd nc
need_cmd pnpm

echo "▶ Ensuring Docker daemon is available..."
if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running. Please start Docker Desktop and retry."; exit 1
fi

echo "▶ Bringing up infra (NanoMQ + proxy) if needed..."
pushd "$INFRA_DIR" >/dev/null
compose up -d
popd >/dev/null

echo "▶ Waiting for broker (TCP 1883) and proxy (HTTP 3000)..."
wait_port localhost 1883 "MQTT broker (NanoMQ)" || true
wait_port localhost 3000 "Reverse proxy (Nginx)" || true

echo "▶ Building shared schemas (bms-schemas)..."
pushd "$ROOT_DIR" >/dev/null
pnpm --filter bms-schemas build
popd >/dev/null

echo "▶ Starting Designer (Next.js) on port 3001..."
echo "   Access the app at http://localhost:3000 (proxied)"
echo "   Browser MQTT connects to ws://localhost:3000/mqtt"

pushd "$ROOT_DIR" >/dev/null
PORT=3001 pnpm --filter designer dev
popd >/dev/null
