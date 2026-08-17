from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_permission
from app.models.client import Client
from app.models.product_feedback import ProductFeedback
from app.models.user import User
from app.schemas.product_feedback import (
    ProductFeedbackCreate,
    ProductFeedbackOut,
    ProductFeedbackUpdate,
    ProductFeedbackWithClientOut,
)
from app.services.audit import log_audit

router = APIRouter(tags=["product_feedback"])

RESOURCE = "product_feedback"


def _serialize(fb: ProductFeedback) -> dict:
    return {"id": fb.id, "category": fb.category.value, "status": fb.status.value}


@router.get("/clients/{client_id}/product-feedback", response_model=list[ProductFeedbackOut])
def list_feedback(
    client_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    return (
        db.query(ProductFeedback)
        .filter(ProductFeedback.client_id == client_id)
        .order_by(ProductFeedback.created_at.desc())
        .all()
    )


@router.post("/clients/{client_id}/product-feedback", response_model=ProductFeedbackOut, status_code=status.HTTP_201_CREATED)
def create_feedback(
    client_id: str,
    payload: ProductFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "create")),
):
    if not db.get(Client, client_id):
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    fb = ProductFeedback(client_id=client_id, created_by_id=current_user.id, **payload.model_dump())
    db.add(fb)
    db.commit()
    db.refresh(fb)

    log_audit(db, actor=current_user, action="create", resource_type=RESOURCE, resource_id=fb.id, after=_serialize(fb))
    return fb


@router.patch("/product-feedback/{feedback_id}", response_model=ProductFeedbackOut)
def update_feedback(
    feedback_id: str,
    payload: ProductFeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "edit")),
):
    fb = db.get(ProductFeedback, feedback_id)
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback não encontrado.")

    before = _serialize(fb)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(fb, field, value)
    db.commit()
    db.refresh(fb)

    log_audit(db, actor=current_user, action="update", resource_type=RESOURCE, resource_id=fb.id, before=before, after=_serialize(fb))
    return fb


@router.delete("/product-feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(
    feedback_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "delete")),
):
    fb = db.get(ProductFeedback, feedback_id)
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback não encontrado.")
    db.delete(fb)
    db.commit()
    log_audit(db, actor=current_user, action="delete", resource_type=RESOURCE, resource_id=feedback_id)


@router.get("/product-feedback", response_model=list[ProductFeedbackWithClientOut])
def list_all_feedback(
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    results = []
    for fb, client in (
        db.query(ProductFeedback, Client)
        .join(Client, ProductFeedback.client_id == Client.id)
        .order_by(ProductFeedback.created_at.desc())
        .all()
    ):
        data = ProductFeedbackOut.model_validate(fb).model_dump()
        data["client_name"] = client.trade_name or client.corporate_name
        results.append(data)
    return results
