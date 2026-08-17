from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models.audit_log import AuditLog
from app.models.user import RoleName
from app.schemas.audit_log import AuditLogOut
from app.schemas.pagination import Page
from app.services.pagination import paginate

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=Page[AuditLogOut])
def list_audit_logs(
    resource_type: str | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(require_roles(RoleName.ADMINISTRADOR, RoleName.GESTAO, RoleName.GESTOR_CS)),
):
    query = db.query(AuditLog)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)
    query = query.order_by(AuditLog.created_at.desc())

    items, total = paginate(query, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)
