param([int]$ApiPort=8001,[int]$WebPort=5173,[switch]$LLM)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
Set-Location $root
if (-not $LLM) { $env:BUTTERFLYLAB_REAL_LLM_ENABLED='0' }
if (-not (Test-Path '.venv/Scripts/python.exe')) { py -3.14 -m venv .venv }
& '.venv/Scripts/python.exe' -m backend.check_environment *> $null
if ($LASTEXITCODE -ne 0) {
    & '.venv/Scripts/python.exe' -m pip install -r backend/requirements.lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency setup failed' }
}
& '.venv/Scripts/python.exe' -m backend.check_environment
if ($LASTEXITCODE -ne 0) { throw 'Unsupported runtime' }
Push-Location frontend
npm ls --depth=0 --silent | Out-Null
if ($LASTEXITCODE -ne 0) {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency setup failed; close this project dev servers before reinstalling locked native packages' }
}
Pop-Location
$env:VITE_API_URL='/api'
$env:BUTTERFLYLAB_DEV_BACKEND="http://127.0.0.1:$ApiPort"
if (Get-NetTCPConnection -LocalPort $ApiPort -State Listen -ErrorAction SilentlyContinue) { throw "Port $ApiPort is occupied; choose another -ApiPort" }
if (Get-NetTCPConnection -LocalPort $WebPort -State Listen -ErrorAction SilentlyContinue) { throw "Port $WebPort is occupied; choose another -WebPort" }
$api=Start-Process -FilePath "$root/.venv/Scripts/python.exe" -ArgumentList '-m','uvicorn','backend.api:app','--host','127.0.0.1','--port',"$ApiPort" -WorkingDirectory $root -WindowStyle Hidden -PassThru
Write-Host "ButterflyLab: http://127.0.0.1:$WebPort/ (Rule/Mock free; Real requires explicit gates)"
try { Set-Location "$root/frontend"; npm run dev -- --host 127.0.0.1 --port $WebPort }
finally { if (-not $api.HasExited) { $api.Kill() }; Set-Location $root }
