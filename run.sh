#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────
# Ledgr — one-shot launcher.
# Auto-creates .env · checks prerequisites · auto-routes a free port ·
# brings up Postgres + Flask + scheduler · waits for the app to be ready ·
# prints clear next steps.
# ────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── ANSI colors (with TTY detection — falls back to plain text in pipes) ──
if [ -t 1 ]; then
  C_RESET='\033[0m'; C_BOLD='\033[1m'
  C_RED='\033[31m'; C_GREEN='\033[32m'; C_YELLOW='\033[33m'; C_BLUE='\033[34m'; C_CYAN='\033[36m'; C_GREY='\033[90m'
else
  C_RESET=''; C_BOLD=''; C_RED=''; C_GREEN=''; C_YELLOW=''; C_BLUE=''; C_CYAN=''; C_GREY=''
fi

step()    { printf "${C_CYAN}▶${C_RESET}  %s\n" "$1"; }
ok()      { printf "${C_GREEN}✓${C_RESET}  %s\n" "$1"; }
warn()    { printf "${C_YELLOW}⚠${C_RESET}  %s\n" "$1"; }
err()     { printf "${C_RED}✗${C_RESET}  %s\n" "$1"; }
hint()    { printf "   ${C_GREY}↳ %s${C_RESET}\n" "$1"; }
section() { printf "\n${C_BOLD}%s${C_RESET}\n" "$1"; }

trap 'err "Setup failed at line $LINENO. Re-run after fixing the issue above."' ERR

clear || true
printf "${C_BOLD}${C_YELLOW}"
cat <<'BANNER'
   __         __         _
  / /  ___ __/ /__ ____ (_)____
 / /__/ -_) _  / _ `/ _/ /___/
/____/\__/\_,_/\_, /_/ /_/
              /___/
BANNER
printf "${C_RESET}"
printf "  ${C_GREY}Demand-forecasting AI for FMCG distributors${C_RESET}\n\n"

# ──────────────────────────────────────────────────────────────────────
# 1. Pre-flight checks
# ──────────────────────────────────────────────────────────────────────
section "Pre-flight checks"

if ! command -v docker >/dev/null 2>&1; then
  err "Docker is not installed."
  hint "Install Docker Desktop: https://docs.docker.com/get-docker/"
  exit 1
fi
ok "Docker found ($(docker --version | awk '{print $3}' | tr -d ','))"

# Pick the Compose flavor available on this host (v2 plugin or v1 standalone).
if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  err "Docker Compose is not installed."
  hint "Either upgrade Docker Desktop (which bundles Compose v2) or"
  hint "install the standalone binary: https://docs.docker.com/compose/install/"
  exit 1
fi
ok "Compose found (${COMPOSE[*]})"

# Docker daemon reachable?
if ! docker info >/dev/null 2>&1; then
  err "Docker daemon is not running (or your user can't reach it)."
  hint "On Linux: sudo systemctl start docker  &&  sudo usermod -aG docker \$USER  (then log back in)"
  hint "On macOS / Windows: launch Docker Desktop and wait for the whale icon to settle."
  exit 1
fi
ok "Docker daemon is running"

# ──────────────────────────────────────────────────────────────────────
# 2. .env auto-create
# ──────────────────────────────────────────────────────────────────────
section "Configuration"

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    ok ".env auto-created from .env.example"
    hint "Edit .env later if you want to plug in your OpenRouter API key for live AI chat."
  else
    warn ".env.example missing — proceeding with built-in compose defaults."
  fi
else
  ok ".env already exists (left untouched)"
fi

# ──────────────────────────────────────────────────────────────────────
# 3. LAN IP detection (so the Android scanner pairing QR is routable)
# ──────────────────────────────────────────────────────────────────────
detect_lan_ip() {
  # Linux
  if command -v hostname >/dev/null 2>&1; then
    local ip
    ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
    if [ -n "$ip" ]; then echo "$ip"; return; fi
  fi
  # macOS / BSD
  if command -v ipconfig >/dev/null 2>&1; then
    ipconfig getifaddr en0 2>/dev/null && return
    ipconfig getifaddr en1 2>/dev/null && return
  fi
  # Generic fallback
  if command -v ip >/dev/null 2>&1; then
    ip route get 1.1.1.1 2>/dev/null | awk '/src/ {for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}'
  fi
}
LAN_IP="$(detect_lan_ip || true)"
if [ -n "${LAN_IP:-}" ]; then
  ok "LAN IP detected: ${C_BOLD}${LAN_IP}${C_RESET}  ${C_GREY}(used by Android scanner pairing QR)${C_RESET}"
else
  warn "Couldn't auto-detect a LAN IP. Android pairing will need a manual URL entry."
fi

# ──────────────────────────────────────────────────────────────────────
# 4. Port conflict — auto-route to a free one
# ──────────────────────────────────────────────────────────────────────
WEB_PORT="${WEB_PORT:-5000}"

is_port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1
  elif command -v ss >/dev/null 2>&1; then
    ss -lnt "sport = :$port" 2>/dev/null | grep -q ":$port"
  elif command -v netstat >/dev/null 2>&1; then
    netstat -an 2>/dev/null | grep -E "[.:]$port .*LISTEN" >/dev/null
  else
    return 1   # can't check — assume free
  fi
}

ORIG_PORT="$WEB_PORT"
if is_port_in_use "$WEB_PORT"; then
  warn "Port ${ORIG_PORT} is already in use."
  for candidate in 5001 5050 5500 8000 8080 8888; do
    if ! is_port_in_use "$candidate"; then
      WEB_PORT="$candidate"
      ok "Auto-routing to port ${C_BOLD}${WEB_PORT}${C_RESET} instead."
      break
    fi
  done
  if [ "$WEB_PORT" = "$ORIG_PORT" ]; then
    err "Could not find any free port from 5001/5050/5500/8000/8080/8888."
    hint "Free up port 5000 (lsof -ti:5000 | xargs kill) or set WEB_PORT manually."
    exit 1
  fi
else
  ok "Port ${WEB_PORT} is free"
fi
export WEB_PORT

# ──────────────────────────────────────────────────────────────────────
# 5. Boot the stack (detached so we can wait for health)
# ──────────────────────────────────────────────────────────────────────
section "Booting the stack"

step "Postgres + Flask web (gunicorn) + APScheduler"
# Extra flags the caller passed through (e.g. --build to force rebuild after a code change).
LEDGR_PUBLIC_HOST="${LEDGR_PUBLIC_HOST:-${LAN_IP:-}}" \
  WEB_PORT="$WEB_PORT" \
  "${COMPOSE[@]}" up -d --remove-orphans "$@"

# ──────────────────────────────────────────────────────────────────────
# 6. Health wait — poll /login until 200
# ──────────────────────────────────────────────────────────────────────
section "Waiting for the app to be ready"
printf "${C_GREY}First boot runs Postgres init + schema migration + seed + the 6-step pipeline.\n"
printf "Expected: ~60s on a clean machine, ~5s on subsequent boots.${C_RESET}\n\n"

if ! command -v curl >/dev/null 2>&1; then
  warn "curl not installed — skipping health probe. Open http://localhost:${WEB_PORT}/ in ~60s."
else
  printf "${C_CYAN}Probing http://localhost:${WEB_PORT}/login${C_RESET}  "
  TRIES=0
  MAX_TRIES=60   # 60 × 2s = 120s
  while ! curl -fsS --max-time 2 "http://localhost:${WEB_PORT}/login" >/dev/null 2>&1; do
    TRIES=$((TRIES + 1))
    if [ "$TRIES" -ge "$MAX_TRIES" ]; then
      printf "\n"
      err "App didn't come up within $((MAX_TRIES * 2))s. Check logs:"
      hint "${COMPOSE[*]} logs --tail=80 web"
      exit 1
    fi
    printf "${C_GREY}.${C_RESET}"
    sleep 2
  done
  printf "\n"
  ok "App is up and answering"
fi

# ──────────────────────────────────────────────────────────────────────
# 7. Success summary
# ──────────────────────────────────────────────────────────────────────
section "Ledgr is ready"
printf "  ${C_BOLD}Dashboard:${C_RESET}    ${C_BLUE}http://localhost:${WEB_PORT}${C_RESET}\n"
if [ -n "${LAN_IP:-}" ] && [ "$WEB_PORT" = "$ORIG_PORT" ]; then
  printf "  ${C_BOLD}From phone:${C_RESET}   ${C_BLUE}http://${LAN_IP}:${WEB_PORT}${C_RESET}  ${C_GREY}(same Wi-Fi)${C_RESET}\n"
fi
printf "  ${C_BOLD}Demo login:${C_RESET}   ${C_GREEN}owner@sunrise.com${C_RESET} / ${C_GREEN}sunrise2024${C_RESET}\n"
printf "\n"
printf "  ${C_BOLD}Live logs:${C_RESET}    ${COMPOSE[*]} logs -f web\n"
printf "  ${C_BOLD}Stop:${C_RESET}         ${COMPOSE[*]} down\n"
printf "  ${C_BOLD}Reset all:${C_RESET}    ${COMPOSE[*]} down -v\n"
printf "\n${C_GREEN}Have at it.${C_RESET}\n"
