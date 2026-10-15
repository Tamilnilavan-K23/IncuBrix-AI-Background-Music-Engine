$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (Test-Path '.\incubrix_env\Scripts\Activate.ps1') { . '.\incubrix_env\Scripts\Activate.ps1' }
pytest -q
