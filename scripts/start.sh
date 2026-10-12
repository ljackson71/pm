#!/usr/bin/env sh
set -e
cd "$(dirname "$0")/.."
docker build -t pm .
docker rm -f pm >/dev/null 2>&1 || true
docker run -d --name pm -p 8000:8000 --env-file .env -v "$(pwd)/data:/app/data" pm
echo "Running at http://localhost:8000"
