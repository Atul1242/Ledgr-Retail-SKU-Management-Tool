#!/bin/bash
# Convenience wrapper: discovers the host's LAN IP and brings up Ledgr
# with that exposed to the container, so the Android scanner's pairing
# QR encodes a phone-reachable URL.
set -e
LAN_IP="$(hostname -I | awk '{print $1}')"
if [ -z "$LAN_IP" ]; then
  echo "Couldn't auto-detect LAN IP. Falling back to localhost — pair the Android app via manual URL entry." >&2
fi
echo "Starting Ledgr — pairing QR will encode http://${LAN_IP:-localhost}:${WEB_PORT:-5000}"
LEDGR_PUBLIC_HOST="${LAN_IP}" docker compose up "$@"
