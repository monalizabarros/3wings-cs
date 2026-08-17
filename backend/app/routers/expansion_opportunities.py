from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_permission
from app.models.client import Client
from app.models.expansion_opportunity import ExpansionOpportunity
from app.models.user import User
from app.schemas.expansion_opportunity import (
    ExpansionOpportunityCreate,
    ExpansionOpportunityOut,
    ExpansionOpportunityUpdate,
    ExpansionOpportunityWithClientOut,
)
from app.schemas.pagination import Page
from app.services.audit import log_audit

router = APIRouter(tags=["expansion_opportunities"])

RESOURCE = "expansion_opportunities"


def _serialize(opp: ExpansionOpportunity) -> dict:
    return {"id": opp.id, "type": opp.type.value, "stage": opp.stage.value}


@router.get("/clients/{client_id}/expansion-opportunities", response_model=list[ExpansionOpportunityOut])
def list_opportunities(
    client_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    return (
        db.query(ExpansionOpportunity)
        .filter(ExpansionOpportunity.client_id == client_id)
        .order_by(ExpansionOpportunity.created_at.desc())
        .all()
    )


@router.post("/clients/{client_id}/expansion-opportunities", response_model=ExpansionOpportunityOut, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    client_id: str,
    payload: ExpansionOpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "create")),
):
    if not db.get(Client, client_id):
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    opp = ExpansionOpportunity(client_id=client_id, created_by_id=current_user.id, **payload.model_dump())
    db.add(opp)
    db.commit()
    db.refresh(opp)

    log_audit(db, actor=current_user, action="create", resource_type=RESOURCE, resource_id=opp.id, after=_serialize(opp))
    return opp


@router.patch("/expansion-opportunities/{opportunity_id}", response_model=ExpansionOpportunityOut)
def update_opportunity(
    opportunity_id: str,
    payload: ExpansionOpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "edit")),
):
    opp = db.get(ExpansionOpportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada.")

    before = _serialize(opp)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(opp, field, value)
    db.commit()
    db.refresh(opp)

    log_audit(db, actor=current_user, action="update", resource_type=RESOURCE, resource_id=opp.id, before=before, after=_serialize(opp))
    return opp


@router.delete("/expansion-opportunities/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "delete")),
):
    opp = db.get(ExpansionOpportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada.")
    db.delete(opp)
    db.commit()
    log_audit(db, actor=current_user, action="delete", resource_type=RESOURCE, resource_id=opportunity_id)


@router.get("/expansion-opportunities", response_model=Page[ExpansionOpportunityWithClientOut])
def list_all_opportunities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    query = (
        db.query(ExpansionOpportunity, Client)
        .join(Client, ExpansionOpportunity.client_id == Client.id)
        .filter(ExpansionOpportunity.stage.notin_(["ganha", "perdida"]))
        .order_by(ExpansionOpportunity.created_at.desc())
    )
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    results = []
    for opp, client in rows:
        data = ExpansionOpportunityOut.model_validate(opp).model_dump()
        data["client_name"] = client.trade_name or client.corporate_name
        results.append(data)
    return Page(items=results, total=total, page=page, page_size=page_size)
