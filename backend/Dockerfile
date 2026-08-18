FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data
ENV CS_DATABASE_URL=sqlite:////app/data/cs.db

EXPOSE 8010

# CS_SECRET_KEY precisa ser passado no ambiente do container (não tem
# default aqui de propósito — ver app/core/config.py). alembic upgrade e o
# seed rodam a cada start; ambos são idempotentes.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8010"]
