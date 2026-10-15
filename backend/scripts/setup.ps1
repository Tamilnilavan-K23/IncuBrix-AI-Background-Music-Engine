$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (-not (Test-Path '.\incubrix_env\Scripts\python.exe')) { python -m venv incubrix_env }
& '.\incubrix_env\Scripts\python.exe' -m pip install --upgrade pip
& '.\incubrix_env\Scripts\python.exe' -m pip install -r requirements.txt
