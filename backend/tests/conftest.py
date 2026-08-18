"""Configuração compartilhada de testes.

Crítico: as variáveis de ambiente abaixo precisam ser definidas ANTES de
qualquer import de `app.*`, porque `app.core.config` as lê no momento do
import (module-level) e `app.database` cria o engine com base nelas. Por
isso este bloco fica no topo do arquivo, antes dos imports de `app`.
"""

import os
import tempfile

_db_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="cs-test-")
os.environ["CS_SECRET_KEY"] = "test-secret-key-0123456789abcdef0123456789abcdef"
os.environ["CS_DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["CS_CORS_ORIGINS"] = "http://localhost:5173"
os.environ.setdefault("CS_ACCESS_TOKEN_EXPIRE_MINUTES", "480")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import seed as seed_module  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import RoleName, User  # noqa: E402
from app.services import rate_limit  # noqa: E402

ADMIN_EMAIL = "admin@3wings.com.br"
ADMIN_PASSWORD = "trocar123"


@pytest.fixture(autouse=True)
def _reset_state():
    """Recria o schema do zero (via Base.metadata direto — testes não
    passam pelo Alembic, é mais rápido e não precisa de migração real) e
    reaplica o seed antes de cada teste, para garantir isolamento total
    entre testes. Também limpa o rate limiter de login, que é um estado em
    memória global do processo."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_module.run()
    rate_limit._attempts.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def login(client: TestClient, email: str, password: str) -> dict:
    res = client.post("/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def admin_headers(client):
    return login(client, ADMIN_EMAIL, ADMIN_PASSWORD)


def make_user(db, *, name: str, email: str, role: RoleName, password: str = "senha123") -> User:
    user = User(name=name, email=email, role=role, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def make_headers(client, db):
    """Cria um usuário com o perfil pedido e retorna os headers de auth já
    logados. Uso: `make_headers(RoleName.CS)`."""

    def _make(role: RoleName, email: str | None = None) -> dict:
        email = email or f"user-{role.value}@3wings.com.br"
        make_user(db, name=f"Teste {role.value}", email=email, role=role)
        return login(client, email, "senha123")

    return _make
