# 3Wings CS

Sistema de Customer Success da 3Wings — FastAPI + SQLite no backend, React + Vite no frontend.

## Rodando localmente

### Backend

```bash
cd backend
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # depois preencha CS_SECRET_KEY (openssl rand -hex 32)
alembic upgrade head
python -m app.seed     # cria o admin e a matriz de permissões padrão
uvicorn app.main:app --reload --port 8010
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testes

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Os testes usam um SQLite temporário isolado por execução (nunca tocam em `cs.db`) e recriam o schema antes de cada teste — não precisam de `alembic upgrade head` rodado antes.

## Migrações de banco (Alembic)

Todo schema é versionado via Alembic — `app/migrations.py` (ALTER TABLE manual) não existe mais.

```bash
# depois de mudar um modelo em app/models/:
alembic revision --autogenerate -m "descrição da mudança"
alembic upgrade head
```

Revise sempre o arquivo gerado antes de commitar — autogenerate nem sempre acerta 100% (ex.: renomear coluna vira "drop + add").

## CI

`.github/workflows/ci.yml` roda em todo push/PR para `main`: testes do backend (pytest) e typecheck + build do frontend (`tsc -b && vite build`).

## Docker

```bash
export CS_SECRET_KEY=$(openssl rand -hex 32)
docker compose up --build
```

Backend em `http://localhost:8010`, frontend em `http://localhost:5173`. O container do backend roda `alembic upgrade head` e o seed automaticamente a cada start (ambos idempotentes).

Para notificação por e-mail de alertas críticos, configure `CS_SMTP_*` no `.env` (ver `backend/.env.example`) — sem isso, o envio vira um no-op logado.

## Deploy no servidor Linux (porta 10012 + Traefik)

Local: `./scripts/build-images.sh` (gera `deploy/` com as imagens linux/amd64, o compose de produção e os templates de env).
Servidor (pasta própria, ex.: `cs-app/`):

```bash
docker load < cs-images.tar.gz
cp backend.env.example backend.env   # preencha CS_SECRET_KEY, CS_ADMIN_PASSWORD, SMTP
cp .env.example .env                 # CS_DOMAIN=cs.3wings.com.br
mkdir -p data
docker compose -f docker-compose.prod.yml up -d
```

Acesso: `http://SERVIDOR:10012` e `https://cs.3wings.com.br` (Traefik, rede `traefik_network` já existente). Atualizar: gerar novas imagens, `docker load` e `docker compose -f docker-compose.prod.yml up -d`. Backup: copiar `data/cs.db`.
