#!/usr/bin/env bash
# Gera as imagens linux/amd64 e empacota tudo em deploy/ para enviar ao servidor.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p deploy
docker buildx build --platform linux/amd64 --load -t cs-backend:latest ./backend
docker buildx build --platform linux/amd64 --load -t cs-frontend:latest ./frontend
docker save cs-backend:latest cs-frontend:latest | gzip > deploy/cs-images.tar.gz
cp docker-compose.prod.yml deploy/
cp deploy-templates/backend.env.example deploy-templates/.env.example deploy/
echo "Pronto: deploy/ ($(du -sh deploy | cut -f1))"
