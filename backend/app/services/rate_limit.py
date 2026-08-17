"""Rate limiting simples em memória para o endpoint de login (RF de segurança:
proteção básica contra força bruta).

Limitação conhecida: o estado vive em memória do processo, então não
funciona corretamente atrás de múltiplos workers/réplicas sem um backend
compartilhado (Redis, etc.). Adequado para o deployment atual (um único
processo uvicorn) — se o backend crescer para múltiplos workers, trocar por
um limiter com storage compartilhado.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, status

MAX_ATTEMPTS = 10
WINDOW_SECONDS = 15 * 60

_attempts: dict[str, list[float]] = defaultdict(list)


def _prune(key: str, now: float) -> None:
    _attempts[key] = [t for t in _attempts[key] if now - t < WINDOW_SECONDS]


def check_rate_limit(key: str) -> None:
    now = time.time()
    _prune(key, now)
    if len(_attempts[key]) >= MAX_ATTEMPTS:
        retry_after = max(1, int(WINDOW_SECONDS - (now - _attempts[key][0])))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Tente novamente em alguns minutos.",
            headers={"Retry-After": str(retry_after)},
        )


def record_failure(key: str) -> None:
    _attempts[key].append(time.time())


def reset(key: str) -> None:
    _attempts.pop(key, None)
