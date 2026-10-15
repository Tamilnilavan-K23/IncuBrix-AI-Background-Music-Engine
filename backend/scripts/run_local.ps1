$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (Test-Path '.\incubrix_env\Scripts\Activate.ps1') { . '.\incubrix_env\Scripts\Activate.ps1' }
try {
    $ready = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/ready' -TimeoutSec 2 -ErrorAction Stop
    Write-Host "IncuBrix API is already running at http://127.0.0.1:8000 (status: $($ready.status))."
    return
} catch {
    # No responding API found; start one below.
}
& '.\incubrix_env\Scripts\python.exe' -m uvicorn app.main:app --host 127.0.0.1 --port 8000
