from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database import get_db
from app.deps import get_current_user, require_permission
from app.models.user import RoleName, User
from app.schemas.client import UserOption
from app.schemas.pagination import Page
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.audit import log_audit
from app.services.pagination import paginate

router = APIRouter(prefix="/users", tags=["users"])

RESOURCE = "users"


@router.get("/options/cs", response_model=list[UserOption])
def list_cs_options(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Lista leve (id/nome/perfil) de usuários CS/Gestor de CS, para uso em
    seletores de 'responsável' em outros módulos (ex: clientes)."""
    return (
        db.query(User)
        .filter(User.role.in_([RoleName.CS, RoleName.GESTOR_CS]), User.is_active.is_(True))
        .order_by(User.name)
        .all()
    )


def _serialize(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active,
    }


@router.get("", response_model=Page[UserOut])
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    query = db.query(User).order_by(User.name)
    items, total = paginate(query, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "create")),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Já existe um usuário com este e-mail.")

    user = User(
        name=payload.name,
        email=payload.email,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit(
        db,
        actor=current_user,
        action="create",
        resource_type=RESOURCE,
        resource_id=user.id,
        after=_serialize(user),
    )
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "edit")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    before = _serialize(user)

    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        user.hashed_password = hash_password(data.pop("password"))
    else:
        data.pop("password", None)
    for field, value in data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    log_audit(
        db,
        actor=current_user,
        action="update",
        resource_type=RESOURCE,
        resource_id=user.id,
        before=before,
        after=_serialize(user),
    )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "delete")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Você não pode excluir seu próprio usuário.")

    before = _serialize(user)
    db.delete(user)
    db.commit()

    log_audit(
        db,
        actor=current_user,
        action="delete",
        resource_type=RESOURCE,
        resource_id=user_id,
        before=before,
    )
