from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_permission
from app.models.client import Client, ClientStatus
from app.models.renewal import ChurnRecord, Renewal, RenewalStatus
from app.models.user import User
from app.schemas.renewal import (
    ChurnRecordOut,
    RenewalComplete,
    RenewalCreate,
    RenewalOut,
    RenewalUpdate,
    RenewalWithClientOut,
)
from app.services.audit import log_audit

router = APIRouter(tags=["renewals"])

RESOURCE = "renewals"


def _serialize(renewal: Renewal) -> dict:
    return {"id": renewal.id, "status": renewal.status.value, "contract_end_date": str(renewal.contract_end_date)}


@router.get("/clients/{client_id}/renewals", response_model=list[RenewalOut])
def list_renewals(
    client_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    return db.query(Renewal).filter(Renewal.client_id == client_id).order_by(Renewal.contract_end_date.desc()).all()


@router.post("/clients/{client_id}/renewals", response_model=RenewalOut, status_code=status.HTTP_201_CREATED)
def create_renewal(
    client_id: str,
    payload: RenewalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "create")),
):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    renewal = Renewal(client_id=client_id, created_by_id=current_user.id, **payload.model_dump())
    db.add(renewal)
    client.renewal_date = renewal.contract_end_date
    db.commit()
    db.refresh(renewal)

    log_audit(db, actor=current_user, action="create", resource_type=RESOURCE, resource_id=renewal.id, after=_serialize(renewal))
    return renewal


@router.patch("/renewals/{renewal_id}", response_model=RenewalOut)
def update_renewal(
    renewal_id: str,
    payload: RenewalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "edit")),
):
    renewal = db.get(Renewal, renewal_id)
    if not renewal:
        raise HTTPException(status_code=404, detail="Renovação não encontrada.")
    if renewal.status in (RenewalStatus.RENOVADO, RenewalStatus.NAO_RENOVADO):
        raise HTTPException(status_code=400, detail="Esta renovação já foi concluída.")

    before = _serialize(renewal)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(renewal, field, value)
    db.commit()
    db.refresh(renewal)

    log_audit(db, actor=current_user, action="update", resource_type=RESOURCE, resource_id=renewal.id, before=before, after=_serialize(renewal))
    return renewal


@router.post("/renewals/{renewal_id}/complete", response_model=RenewalOut)
def complete_renewal(
    renewal_id: str,
    payload: RenewalComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "edit")),
):
    """RF-129 a RF-134: concluir o ciclo de renovação. Renovado reabre o
    cliente como ativo e agenda o próximo vencimento de contrato; não
    renovado muda o cliente para churn e cria o registro formal (RF-132)."""
    renewal = db.get(Renewal, renewal_id)
    if not renewal:
        raise HTTPException(status_code=404, detail="Renovação não encontrada.")
    if renewal.status in (RenewalStatus.RENOVADO, RenewalStatus.NAO_RENOVADO):
        raise HTTPException(status_code=400, detail="Esta renovação já foi concluída.")

    client = db.get(Client, renewal.client_id)
    before = _serialize(renewal)

    if payload.renewed:
        if not payload.next_contract_end_date:
            raise HTTPException(status_code=400, detail="Informe a nova data de vencimento do contrato.")
        renewal.status = RenewalStatus.RENOVADO
        client.renewal_date = payload.next_contract_end_date
        if client.status in (ClientStatus.EM_RENOVACAO, ClientStatus.EM_RISCO):
            client.status = ClientStatus.ATIVO
    else:
        if not payload.churn_category:
            raise HTTPException(status_code=400, detail="Informe a categoria do motivo de churn.")
        renewal.status = RenewalStatus.NAO_RENOVADO
        client.status = ClientStatus.CHURN
        client.renewal_date = None
        churn = ChurnRecord(
            client_id=client.id,
            renewal_id=renewal.id,
            churn_date=date.today(),
            category=payload.churn_category,
            description=payload.churn_description,
            lost_value=payload.lost_value if payload.lost_value is not None else renewal.renewal_value,
            created_by_id=current_user.id,
        )
        db.add(churn)

    renewal.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(renewal)

    log_audit(db, actor=current_user, action="update", resource_type=RESOURCE, resource_id=renewal.id, before=before, after=_serialize(renewal))
    return renewal


@router.get("/renewals/upcoming", response_model=list[RenewalWithClientOut])
def list_upcoming_renewals(
    days: int = 90,
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    limit = date.today() + timedelta(days=days)
    results = []
    for renewal, client in (
        db.query(Renewal, Client)
        .join(Client, Renewal.client_id == Client.id)
        .filter(Renewal.status.notin_(["renovado", "nao_renovado"]), Renewal.contract_end_date <= limit)
        .order_by(Renewal.contract_end_date.asc())
        .all()
    ):
        data = RenewalOut.model_validate(renewal).model_dump()
        data["client_name"] = client.trade_name or client.corporate_name
        results.append(data)
    return results


@router.get("/churn-records", response_model=list[ChurnRecordOut])
def list_churn_records(
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    return db.query(ChurnRecord).order_by(ChurnRecord.churn_date.desc()).all()
