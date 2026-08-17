from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_permission
from app.models.client import Client
from app.models.support_ticket import SupportTicket, TicketStatus
from app.models.user import User
from app.schemas.support_ticket import (
    SupportSummaryOut,
    SupportTicketCreate,
    SupportTicketOut,
    SupportTicketUpdate,
)
from app.services.audit import log_audit

router = APIRouter(tags=["support_tickets"])

RESOURCE = "support_tickets"


def _serialize(ticket: SupportTicket) -> dict:
    return {"id": ticket.id, "severity": ticket.severity.value, "status": ticket.status.value}


@router.get("/clients/{client_id}/support-tickets", response_model=list[SupportTicketOut])
def list_tickets(
    client_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    return db.query(SupportTicket).filter(SupportTicket.client_id == client_id).order_by(SupportTicket.opened_at.desc()).all()


@router.get("/clients/{client_id}/support-tickets/summary", response_model=SupportSummaryOut)
def get_summary(
    client_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_permission(RESOURCE, "view")),
):
    tickets = db.query(SupportTicket).filter(SupportTicket.client_id == client_id).all()
    open_tickets = [t for t in tickets if t.status not in (TicketStatus.RESOLVIDO, TicketStatus.FECHADO)]
    critical_open = [t for t in open_tickets if t.severity.value == "critica"]
    scores = [t.satisfaction_score for t in tickets if t.satisfaction_score is not None]
    avg_satisfaction = round(sum(scores) / len(scores), 2) if scores else None

    return SupportSummaryOut(
        open_tickets=len(open_tickets),
        critical_open_tickets=len(critical_open),
        total_tickets=len(tickets),
        avg_satisfaction=avg_satisfaction,
    )


@router.post("/clients/{client_id}/support-tickets", response_model=SupportTicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    client_id: str,
    payload: SupportTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "create")),
):
    if not db.get(Client, client_id):
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    ticket = SupportTicket(client_id=client_id, created_by_id=current_user.id, **payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    log_audit(db, actor=current_user, action="create", resource_type=RESOURCE, resource_id=ticket.id, after=_serialize(ticket))
    return ticket


@router.patch("/support-tickets/{ticket_id}", response_model=SupportTicketOut)
def update_ticket(
    ticket_id: str,
    payload: SupportTicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "edit")),
):
    ticket = db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado.")

    before = _serialize(ticket)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)

    log_audit(db, actor=current_user, action="update", resource_type=RESOURCE, resource_id=ticket.id, before=before, after=_serialize(ticket))
    return ticket


@router.delete("/support-tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(RESOURCE, "delete")),
):
    ticket = db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado.")
    db.delete(ticket)
    db.commit()
    log_audit(db, actor=current_user, action="delete", resource_type=RESOURCE, resource_id=ticket_id)
