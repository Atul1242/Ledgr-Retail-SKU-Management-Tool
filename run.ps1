# ────────────────────────────────────────────────────────────────────
# Ledgr — one-shot launcher (Windows PowerShell).
# Mirrors run.sh: pre-flight checks, .env auto-create, port auto-route,
# wait-for-ready, plain-English summary.
# Run with:  .\run.ps1
# ────────────────────────────────────────────────────────────────────
$ErrorActionPreference = 'Stop'
$Banner = @'
   __         __         _
  / /  ___ __/ /__ ____ (_)____
 / /__/ -_) _  / _ `/ _/ /___/
/____/\__/\_,_/\_, /_/ /_/
              /___/
'@

function Step($msg) { Write-Host "▶  $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "✓  $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "⚠  $msg" -ForegroundColor Yellow }
function Err($msg)  { Write-Host "✗  $msg" -ForegroundColor Red }
function Hint($msg) { Write-Host "   ↳ $msg" -ForegroundColor DarkGray }

Clear-Host
Write-Host $Banner -ForegroundColor Yellow
Write-Host "  Demand-forecasting AI for FMCG distributors`n" -ForegroundColor DarkGray

# ── 1. Pre-flight ──
Write-Host "`nPre-flight checks" -ForegroundColor White
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Err "Docker is not installed."
    Hint "Install Docker Desktop: https://docs.docker.com/get-docker/"
    exit 1
}
Ok "Docker found"

$Compose = $null
& docker compose version *>$null
if ($LASTEXITCODE -eq 0) { $Compose = @('docker','compose') }
elseif (Get-Command docker-compose -ErrorAction SilentlyContinue) { $Compose = @('docker-compose') }
else {
    Err "Docker Compose is not installed."
    Hint "Upgrade Docker Desktop to get Compose v2."
    exit 1
}
Ok "Compose found ($($Compose -join ' '))"

& docker info *>$null
if ($LASTEXITCODE -ne 0) {
    Err "Docker daemon is not running. Start Docker Desktop and wait for the whale icon to settle."
    exit 1
}
Ok "Docker daemon is running"

# ── 2. .env auto-create ──
Write-Host "`nConfiguration" -ForegroundColor White
if (-not (Test-Path .env)) {
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Ok ".env auto-created from .env.example"
        Hint "Edit .env later to plug in OPENROUTER_KEY for live AI chat."
    } else {
        Warn ".env.example missing — using built-in compose defaults."
    }
} else {
    Ok ".env already exists (left untouched)"
}

# ── 3. LAN IP detection ──
$LanIp = (Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Dhcp -ErrorAction SilentlyContinue |
          Sort-Object SkipAsSource | Select-Object -First 1 -ExpandProperty IPAddress)
if (-not $LanIp) {
    $LanIp = (Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway } |
              Select-Object -First 1 -ExpandProperty IPv4Address).IPAddress
}
if ($LanIp) { Ok "LAN IP detected: $LanIp  (used by Android scanner pairing QR)" }
else        { Warn "Couldn't auto-detect a LAN IP. Android pairing will need manual URL entry." }

# ── 4. Port auto-route ──
$WebPort = if ($env:WEB_PORT) { $env:WEB_PORT } else { 5000 }
function Test-PortInUse($port) {
    return (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).Count -gt 0
}
$OrigPort = $WebPort
if (Test-PortInUse $WebPort) {
    Warn "Port $WebPort is already in use."
    foreach ($candidate in 5001,5050,5500,8000,8080,8888) {
        if (-not (Test-PortInUse $candidate)) { $WebPort = $candidate; break }
    }
    if ($WebPort -eq $OrigPort) {
        Err "Could not find any free port from 5001/5050/5500/8000/8080/8888."
        exit 1
    }
    Ok "Auto-routing to port $WebPort instead."
} else { Ok "Port $WebPort is free" }
$env:WEB_PORT = $WebPort

# ── 5. Boot the stack ──
Write-Host "`nBooting the stack" -ForegroundColor White
Step "Postgres + Flask web (gunicorn) + APScheduler"
$env:LEDGR_PUBLIC_HOST = $LanIp
& $Compose[0] $Compose[1..($Compose.Length-1)] up -d --remove-orphans @args
if ($LASTEXITCODE -ne 0) { Err "Compose failed to start. See the output above."; exit 1 }

# ── 6. Health wait ──
Write-Host "`nWaiting for the app to be ready" -ForegroundColor White
Write-Host "First boot runs Postgres init + schema migration + seed + the 6-step pipeline." -ForegroundColor DarkGray
Write-Host "Expected: ~60s on a clean machine, ~5s on subsequent boots.`n" -ForegroundColor DarkGray

Write-Host -NoNewline "Probing http://localhost:$WebPort/login  " -ForegroundColor Cyan
$Tries = 0; $MaxTries = 60
while ($true) {
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:$WebPort/login" -TimeoutSec 2 -UseBasicParsing
        Write-Host ""
        Ok "App is up and answering"
        break
    } catch {
        $Tries++
        if ($Tries -ge $MaxTries) {
            Write-Host ""
            Err "App didn't come up within $($MaxTries * 2)s."
            Hint "Check logs: $($Compose -join ' ') logs --tail=80 web"
            exit 1
        }
        Write-Host -NoNewline "." -ForegroundColor DarkGray
        Start-Sleep -Seconds 2
    }
}

# ── 7. Summary ──
Write-Host "`nLedgr is ready" -ForegroundColor White
Write-Host "  Dashboard:   http://localhost:$WebPort" -ForegroundColor Blue
if ($LanIp -and ($WebPort -eq $OrigPort)) {
    Write-Host "  From phone:  http://${LanIp}:$WebPort  (same Wi-Fi)" -ForegroundColor Blue
}
Write-Host "  Demo login:  owner@sunrise.com / sunrise2024" -ForegroundColor Green
Write-Host ""
Write-Host "  Live logs:   $($Compose -join ' ') logs -f web"
Write-Host "  Stop:        $($Compose -join ' ') down"
Write-Host "  Reset all:   $($Compose -join ' ') down -v"
Write-Host "`nHave at it." -ForegroundColor Green
