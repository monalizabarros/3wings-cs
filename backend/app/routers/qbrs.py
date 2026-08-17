from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_permission
from app.models.action_plan import ActionPlan
from app.models.client import Client
from app.models.qbr import QBR, QBRStatus
from app.models.user import User
from app.schemas.action_plan import ActionPlanOut
from app.schemas.qbr import QBRComplete, QBRCreate, QBROut, QBRUpdate
from app.services.audit import log_audit

router = APIRouter(tags=["qbrs"])

RESOURCE = "qbrs"


def _serialize(qbr: QBR) -> dict:
    return {"id": qbr.id, "status": qbr.status.value, "scheduled_date": str(qbr.scheduled_date)}


@router.get("/clients/{client_id}/qbrs", response_model=list[QBROut])
def list_qbrs(
    client_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    return db.query(QBR).filter(QBR.client_id == client_id).order_by(QBR.scheduled_date.desc()).all()


@router.post("/clients/{client_id}/qbrs", response_model=QBROut, status_code=status.HTTP_201_CREATED)
def create_qbr(
    client_id: str,
    payload: QBRCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "create")),
):
    if not db.get(Client, client_id):
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    qbr = QBR(client_id=client_id, created_by_id=current_user.id, **payload.model_dump())
    db.add(qbr)
    db.commit()
    db.refresh(qbr)

    log_audit(db, actor=current_user, action="create", resource_type=RESOURCE, resource_id=qbr.id, after=_serialize(qbr))
    return qbr


@router.patch("/qbrs/{qbr_id}", response_model=QBROut)
def update_qbr(
    qbr_id: str,
    payload: QBRUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "edit")),
):
    qbr = db.get(QBR, qbr_id)
    if not qbr:
        raise HTTPException(status_code=404, detail="QBR não encontrado.")

    before = _serialize(qbr)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(qbr, field, value)
    db.commit()
    db.refresh(qbr)

    log_audit(db, actor=current_user, action="update", resource_type=RESOURCE, resource_id=qbr.id, before=before, after=_serialize(qbr))
    return qbr


@router.post("/qbrs/{qbr_id}/complete", response_model=QBROut)
def complete_qbr(
    qbr_id: str,
    payload: QBRComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "edit")),
):
    qbr = db.get(QBR, qbr_id)
    if not qbr:
        raise HTTPException(status_code=404, detail="QBR não encontrado.")
    if qbr.status == QBRStatus.REALIZADO:
        raise HTTPException(status_code=400, detail="Este QBR já foi concluído.")

    before = _serialize(qbr)
    qbr.status = QBRStatus.REALIZADO
    qbr.completed_at = datetime.now(timezone.utc)
    qbr.achievements = payload.achievements
    qbr.challenges = payload.challenges
    qbr.next_period_goals = payload.next_period_goals
    db.commit()
    db.refresh(qbr)

    log_audit(db, actor=current_user, action="update", resource_type=RESOURCE, resource_id=qbr.id, before=before, after=_serialize(qbr))
    return qbr


@router.delete("/qbrs/{qbr_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_qbr(
    qbr_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "delete")),
):
    qbr = db.get(QBR, qbr_id)
    if not qbr:
        raise HTTPException(status_code=404, detail="QBR não encontrado.")
    db.delete(qbr)
    db.commit()
    log_audit(db, actor=current_user, action="delete", resource_type=RESOURCE, resource_id=qbr_id)


@router.post("/qbrs/{qbr_id}/action-plan", response_model=ActionPlanOut, status_code=status.HTTP_201_CREATED)
def create_qbr_action_plan(
    qbr_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "edit")),
):
    qbr = db.get(QBR, qbr_id)
    if not qbr:
        raise HTTPException(status_code=404, detail="QBR não encontrado.")
    if qbr.action_plan_id:
        raise HTTPException(status_code=400, detail="Este QBR já tem um plano de ação vinculado.")

    plan = ActionPlan(
        client_id=qbr.client_id,
        title=f"Plano de ação — QBR {qbr.scheduled_date}",
        description=qbr.next_period_goals,
        created_by_id=current_user.id,
    )
    db.add(plan)
    db.flush()
    qbr.action_plan_id = plan.id
    db.commit()
    db.refresh(plan)

    log_audit(db, actor=current_user, action="create", resource_type="action_plans", resource_id=plan.id, after={"title": plan.title, "qbr_id": qbr.id})
    return plan
