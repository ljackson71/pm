$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
docker build -t pm .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker rm -f pm 2>$null | Out-Null
docker run -d --name pm -p 8000:8000 --env-file .env -v "${PWD}/data:/app/data" pm
Write-Host "Running at http://localhost:8000"
